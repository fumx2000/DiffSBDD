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

from covalent_ext import covapie_sample_index_qa_gate as qa  # noqa: E402


def write_csv(rows: list[dict[str, Any]], path: Path, fields: list[str]) -> None:
    output = REPO_ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def write_json(value: Any, path: Path) -> None:
    output = REPO_ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_summary(manifest: dict[str, Any]) -> None:
    text = f"""# CovaPIE Sample Index QA Gate v0 Summary

Step 14AE independently rereads the committed Step 14AD sample index CSV/JSON and source derived tables. It recomputes semantic consistency, actual source row counts, event and bond-distance traceability, and SHA256 fingerprints without modifying the sample index.

QA approval permits the next final-dataset design gate only. It does not rewrite the source `eligible_for_final_dataset_design=false` field and does not make any sample training-ready. No raw structure data, final dataset, split, leakage matrix, dataloader output, tensor, checkpoint, or training artifact is created.

The five canonical masks remain unchanged, including `scaffold_only / B3`. Feature semantics remain unknown and not finalized for training; feature-semantics audit and leakage/split design remain required before formal training.

- sample_index_row_qa_passed_count: `{manifest['sample_index_row_qa_passed_count']}`
- sample_index_schema_qa_passed_count: `{manifest['sample_index_schema_qa_passed_count']}`
- sample_index_source_traceability_qa_passed_count: `{manifest['sample_index_source_traceability_qa_passed_count']}`
- sample_index_fingerprint_verified_count: `{manifest['sample_index_fingerprint_verified_count']}`
- qa_approved_for_final_dataset_design_count: `{manifest['qa_approved_for_final_dataset_design_count']}`
- ready_for_covapie_final_dataset_design_gate: `{manifest['ready_for_covapie_final_dataset_design_gate']}`
- ready_for_training: `{manifest['ready_for_training']}`
- recommended_next_step: `{manifest['recommended_next_step']}`
"""
    output = REPO_ROOT / qa.SUMMARY_MD
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = qa.run_covapie_sample_index_qa_gate_v0()
    write_csv(result["precondition_rows"], qa.PRECONDITION_AUDIT_CSV, qa.PRECONDITION_COLUMNS)
    write_csv(result["row_qa_rows"], qa.ROW_QA_CSV, qa.ROW_QA_COLUMNS)
    write_csv(result["schema_qa_rows"], qa.SCHEMA_QA_CSV, qa.SCHEMA_QA_COLUMNS)
    write_csv(result["traceability_rows"], qa.TRACEABILITY_QA_CSV, qa.TRACEABILITY_QA_COLUMNS)
    write_csv(result["fingerprint_rows"], qa.FINGERPRINT_AUDIT_CSV, qa.FINGERPRINT_COLUMNS)
    write_csv(result["issue_rows"], qa.ISSUE_INVENTORY_CSV, qa.ISSUE_COLUMNS)
    write_csv(result["policy_rows"], qa.POLICY_CONTRACT_CSV, qa.POLICY_COLUMNS)
    write_csv(result["downstream_rows"], qa.DOWNSTREAM_READINESS_CSV, qa.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], qa.SAFETY_AUDIT_CSV, qa.SAFETY_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"])
    manifest = result["manifest"]
    print("covapie_sample_index_qa_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_sample_index_qa_gate_v0_blocked")
    for key in ["sample_index_row_qa_count", "sample_index_row_qa_passed_count", "sample_index_schema_qa_count", "sample_index_schema_qa_passed_count", "sample_index_source_traceability_qa_count", "sample_index_source_traceability_qa_passed_count", "sample_index_fingerprint_verified_count", "qa_issue_count", "qa_approved_for_final_dataset_design_count", "ready_for_covapie_final_dataset_design_gate", "ready_for_training", "feature_semantics_known_for_training", "unknown_atom_feature_policy_finalized_for_training", "feature_semantics_audit_required_before_training", "recommended_next_step", "blocking_reasons"]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

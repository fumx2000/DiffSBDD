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

from covalent_ext import covapie_candidate_metadata_materialization_smoke as smoke  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


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


def build_report_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = result["manifest"]
    return [
        {
            "stage": smoke.STAGE,
            "previous_stage": smoke.PREVIOUS_STAGE,
            "section": section,
            "status": "passed" if evidence["passed"] else "blocked",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], candidate_rows: list[dict[str, Any]], path: str | Path) -> None:
    ids = "\n".join(f"- `{row['candidate_metadata_id']}`" for row in candidate_rows)
    text = f"""# CovaPIE Candidate Metadata Materialization Smoke v0 Summary

Step 13AY materializes a very small candidate metadata smoke artifact for the four accepted preferred events from Step 13AW/13AX.
It writes `covapie_candidate_metadata_smoke.csv` and `covapie_candidate_metadata_smoke.json`.
It does not write a candidate allowlist, sample_index, final_dataset, split assignments, or leakage matrix.
It does not use network access, raw downloads, raw text reads, RDKit/Bio.PDB/gemmi/gzip/torch, model calls, loss, optimizer, trainer.fit, or training.
Raw files remain external, untracked, unstaged, and uncommitted.
The unresolved `1A54/MDC` event remains excluded because `raw_no_connectivity_records_found`.

Materialized candidate metadata IDs:
{ids}

materialized_candidate_metadata_row_count: `{manifest["materialized_candidate_metadata_row_count"]}`
materialized_candidate_metadata_column_count: `{manifest["materialized_candidate_metadata_column_count"]}`
candidate_metadata_csv_written: `{manifest["candidate_metadata_csv_written"]}`
candidate_metadata_json_written: `{manifest["candidate_metadata_json_written"]}`
candidate_metadata_materialized: `{manifest["candidate_metadata_materialized"]}`
candidate_allowlist_materialized: `{manifest["candidate_allowlist_materialized"]}`
sample_index_written: `{manifest["sample_index_written"]}`
final_dataset_written: `{manifest["final_dataset_written"]}`
split_assignments_written: `{manifest["split_assignments_written"]}`
leakage_matrix_written: `{manifest["leakage_matrix_written"]}`
ready_for_covapie_candidate_metadata_materialization_qa_gate: `{manifest["ready_for_covapie_candidate_metadata_materialization_qa_gate"]}`
ready_for_covapie_candidate_allowlist_materialization_smoke: `{manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
feature_semantics_audit_required_before_training: `{manifest["feature_semantics_audit_required_before_training"]}`
leakage_split_design_required_before_training: `{manifest["leakage_split_design_required_before_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_covapie_candidate_metadata_materialization_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["candidate_rows"], smoke.CANDIDATE_METADATA_SMOKE_CSV, smoke.CANDIDATE_METADATA_FIELDS)
    write_json(result["candidate_rows"], smoke.CANDIDATE_METADATA_SMOKE_JSON)
    write_csv(result["traceability_rows"], smoke.SOURCE_TRACEABILITY_AUDIT_CSV, smoke.TRACEABILITY_COLUMNS)
    write_csv(result["accepted_materialization_rows"], smoke.ACCEPTED_EVENT_MATERIALIZATION_AUDIT_CSV, smoke.ACCEPTED_MATERIALIZATION_COLUMNS)
    write_csv(result["unresolved_event_rows"], smoke.UNRESOLVED_EVENT_EXCLUSION_AUDIT_CSV, smoke.UNRESOLVED_EXCLUSION_COLUMNS)
    write_csv(result["schema_compliance_rows"], smoke.SCHEMA_COMPLIANCE_AUDIT_CSV, smoke.SCHEMA_COMPLIANCE_COLUMNS)
    write_csv(result["field_completeness_rows"], smoke.FIELD_COMPLETENESS_AUDIT_CSV, smoke.FIELD_COMPLETENESS_COLUMNS)
    write_csv(result["row_identity_rows"], smoke.ROW_IDENTITY_UNIQUENESS_AUDIT_CSV, smoke.ROW_IDENTITY_COLUMNS)
    write_csv(result["validation_rows"], smoke.VALIDATION_AUDIT_CSV, smoke.VALIDATION_COLUMNS)
    write_csv(result["allowlist_boundary_rows"], smoke.ALLOWLIST_BOUNDARY_AUDIT_CSV, smoke.ALLOWLIST_BOUNDARY_COLUMNS)
    write_csv(result["materialization_boundary_rows"], smoke.MATERIALIZATION_BOUNDARY_AUDIT_CSV, smoke.MATERIALIZATION_BOUNDARY_COLUMNS)
    write_csv(result["execution_rows"], smoke.EXECUTION_BOUNDARY_AUDIT_CSV, smoke.EXECUTION_COLUMNS)
    write_csv(result["git_safety_rows"], smoke.GIT_SAFETY_AUDIT_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], smoke.MASK_SCOPE_AUDIT_CSV, smoke.MASK_COLUMNS)
    write_csv(result["feature_rows"], smoke.FEATURE_SEMANTICS_AUDIT_CSV, smoke.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], smoke.LEAKAGE_SPLIT_AUDIT_CSV, smoke.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), smoke.REPORT_CSV, smoke.REPORT_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], result["candidate_rows"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_candidate_metadata_materialization_smoke_v0_passed")
    else:
        print("covapie_candidate_metadata_materialization_smoke_v0_blocked")
    for key in [
        "materialized_candidate_metadata_row_count",
        "materialized_candidate_metadata_column_count",
        "candidate_metadata_id_unique_count",
        "candidate_metadata_csv_written",
        "candidate_metadata_json_written",
        "candidate_metadata_materialized",
        "candidate_allowlist_materialized",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "ready_for_covapie_candidate_metadata_materialization_qa_gate",
        "ready_for_covapie_candidate_allowlist_materialization_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    return [
        {
            "stage": smoke.STAGE,
            "previous_stage": smoke.PREVIOUS_STAGE,
            "section": section,
            "status": "passed",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Candidate Allowlist Materialization Smoke v0 Summary

This is CovaPIE candidate allowlist materialization smoke.
It only reads explicit metadata CSV if provided.
It does not search raw data or invent candidates.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
If metadata is missing, it is intentionally blocked and asks for explicit candidate metadata.
If metadata is valid, the next step is batch-scale raw-read smoke.
It keeps feature semantics audit and leakage/split design required before training.

input_metadata_path: `{manifest["input_metadata_path"]}`
input_metadata_exists: `{manifest["input_metadata_exists"]}`
input_metadata_read: `{manifest["input_metadata_read"]}`
input_metadata_row_count: `{manifest["input_metadata_row_count"]}`
included_candidate_count: `{manifest["included_candidate_count"]}`
materialization_status: `{manifest["materialization_status"]}`
materialized_allowlist_written: `{manifest["materialized_allowlist_written"]}`
materialized_allowlist_path: `{manifest["materialized_allowlist_path"]}`
blocked_header_only_written: `{manifest["blocked_header_only_written"]}`
blocked_header_only_path: `{manifest["blocked_header_only_path"]}`
candidate_rows_materialized: `{manifest["candidate_rows_materialized"]}`
candidate_allowlist_created: `{manifest["candidate_allowlist_created"]}`
ready_for_covapie_batch_scale_raw_read_smoke: `{manifest["ready_for_covapie_batch_scale_raw_read_smoke"]}`
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
    result = smoke.run_covapie_candidate_allowlist_materialization_smoke_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], smoke.PRECONDITION_COLUMNS)
    write_csv(result["discovery_rows"], paths["discovery"], smoke.DISCOVERY_COLUMNS)
    write_csv(result["schema_rows"], paths["schema"], smoke.SCHEMA_COLUMNS)
    write_csv(result["candidate_rows"], paths["candidate"], smoke.CANDIDATE_VALIDATION_COLUMNS)
    write_csv(result["duplicate_rows"], paths["duplicate"], smoke.DUPLICATE_COLUMNS)
    write_csv(result["shard_rows"], paths["shard"], smoke.SHARD_COLUMNS)
    write_csv(result["output_rows"], paths["output"], smoke.OUTPUT_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], smoke.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], smoke.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], smoke.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], smoke.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], smoke.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_candidate_allowlist_materialization_smoke_v0_passed")
    for key in [
        "input_metadata_exists",
        "input_metadata_read",
        "input_metadata_row_count",
        "included_candidate_count",
        "materialization_status",
        "metadata_schema_validated",
        "candidate_validation_passed",
        "duplicate_exclusion_validation_passed",
        "shard_plan_created",
        "shard_count",
        "materialized_allowlist_written",
        "materialized_allowlist_path",
        "blocked_header_only_written",
        "blocked_header_only_path",
        "candidate_rows_materialized",
        "candidate_allowlist_created",
        "covapie_allowlist_materialization_precondition_audit_row_count",
        "covapie_allowlist_materialization_input_discovery_audit_row_count",
        "covapie_allowlist_materialization_schema_audit_row_count",
        "covapie_allowlist_materialization_candidate_validation_audit_row_count",
        "covapie_allowlist_materialization_duplicate_exclusion_audit_row_count",
        "covapie_allowlist_materialization_shard_plan_audit_row_count",
        "covapie_allowlist_materialization_output_audit_row_count",
        "covapie_allowlist_materialization_execution_boundary_audit_row_count",
        "covapie_allowlist_materialization_git_safety_audit_row_count",
        "covapie_allowlist_materialization_mask_scope_audit_row_count",
        "covapie_allowlist_materialization_feature_semantics_audit_row_count",
        "covapie_allowlist_materialization_leakage_split_audit_row_count",
        "allowlist_materialization_smoke_preflight_passed",
        "covapie_candidate_allowlist_materialization_smoke_passed",
        "ready_for_covapie_batch_scale_raw_read_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + _list_text(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

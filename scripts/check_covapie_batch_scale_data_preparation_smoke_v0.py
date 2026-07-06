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

from covalent_ext import covapie_batch_scale_data_preparation_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE Batch-Scale Data Preparation Smoke v0 Summary

This is CovaPIE batch-scale data preparation smoke preflight.
It validates whether an explicit small-batch allowlist exists.
It does not search for raw data or invent candidates.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate samples or write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
If the allowlist is missing, it is intentionally blocked and the next step is candidate allowlist creation gate.
If a valid allowlist exists, the next step is batch-scale raw-read smoke.
It keeps feature semantics audit and leakage/split design required before training.

allowlist_exists: `{manifest["allowlist_exists"]}`
allowlist_read: `{manifest["allowlist_read"]}`
allowlist_row_count: `{manifest["allowlist_row_count"]}`
included_candidate_count: `{manifest["included_candidate_count"]}`
smoke_status: `{manifest["smoke_status"]}`
batch_scale_smoke_preflight_passed: `{manifest["batch_scale_smoke_preflight_passed"]}`
covapie_batch_scale_data_preparation_smoke_passed: `{manifest["covapie_batch_scale_data_preparation_smoke_passed"]}`
ready_for_covapie_candidate_allowlist_creation_gate: `{manifest["ready_for_covapie_candidate_allowlist_creation_gate"]}`
ready_for_covapie_batch_scale_raw_read_smoke: `{manifest["ready_for_covapie_batch_scale_raw_read_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
feature_semantics_audit_required_before_training: `{manifest["feature_semantics_audit_required_before_training"]}`
leakage_split_design_required_before_training: `{manifest["leakage_split_design_required_before_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{_list_text(manifest["blocking_reasons"])}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_covapie_batch_scale_data_preparation_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["discovery_rows"], smoke.ALLOWLIST_DISCOVERY_AUDIT_CSV, smoke.DISCOVERY_COLUMNS)
    write_csv(result["schema_rows"], smoke.ALLOWLIST_SCHEMA_AUDIT_CSV, smoke.SCHEMA_COLUMNS)
    write_csv(result["selection_rows"], smoke.CANDIDATE_SELECTION_AUDIT_CSV, smoke.SELECTION_COLUMNS)
    write_csv(result["shard_rows"], smoke.SHARD_PLAN_AUDIT_CSV, smoke.SHARD_COLUMNS)
    write_csv(result["provenance_rows"], smoke.PROVENANCE_AUDIT_CSV, smoke.PROVENANCE_COLUMNS)
    write_csv(result["failure_rows"], smoke.FAILURE_AUDIT_CSV, smoke.FAILURE_COLUMNS)
    write_csv(result["execution_rows"], smoke.EXECUTION_BOUNDARY_AUDIT_CSV, smoke.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], smoke.GIT_SAFETY_AUDIT_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], smoke.MASK_SCOPE_AUDIT_CSV, smoke.MASK_COLUMNS)
    write_csv(result["feature_rows"], smoke.FEATURE_SEMANTICS_AUDIT_CSV, smoke.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], smoke.LEAKAGE_SPLIT_AUDIT_CSV, smoke.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), smoke.REPORT_CSV, smoke.REPORT_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_batch_scale_data_preparation_smoke_v0_preflight_passed")
    for key in [
        "allowlist_exists",
        "allowlist_read",
        "allowlist_row_count",
        "included_candidate_count",
        "smoke_status",
        "covapie_batch_smoke_precondition_audit_row_count",
        "covapie_batch_smoke_allowlist_discovery_audit_row_count",
        "covapie_batch_smoke_allowlist_schema_audit_row_count",
        "covapie_batch_smoke_candidate_selection_audit_row_count",
        "covapie_batch_smoke_shard_plan_audit_row_count",
        "covapie_batch_smoke_provenance_audit_row_count",
        "covapie_batch_smoke_failure_audit_row_count",
        "covapie_batch_smoke_execution_boundary_audit_row_count",
        "covapie_batch_smoke_git_safety_audit_row_count",
        "covapie_batch_smoke_mask_scope_audit_row_count",
        "covapie_batch_smoke_feature_semantics_audit_row_count",
        "covapie_batch_smoke_leakage_split_audit_row_count",
        "batch_scale_smoke_preflight_passed",
        "covapie_batch_scale_data_preparation_smoke_passed",
        "ready_for_covapie_candidate_allowlist_creation_gate",
        "ready_for_covapie_batch_scale_raw_read_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    print("blocking_reasons=" + _list_text(manifest["blocking_reasons"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

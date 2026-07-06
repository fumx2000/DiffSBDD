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

from covalent_ext import covapie_candidate_allowlist_creation_gate as gate  # noqa: E402


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
            "stage": gate.STAGE,
            "previous_stage": gate.PREVIOUS_STAGE,
            "section": section,
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Candidate Allowlist Creation Gate v0 Summary

This is CovaPIE candidate allowlist creation gate.
It creates only a header-only allowlist template.
It does not materialize real candidates.
It does not search raw data or invent candidates.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
The next step is candidate allowlist materialization smoke, which should only use explicit user or pipeline metadata.
It keeps feature semantics audit and leakage/split design required before training.

allowlist_template_path: `{manifest["allowlist_template_path"]}`
allowlist_template_written: `{manifest["allowlist_template_written"]}`
allowlist_template_header_only: `{manifest["allowlist_template_header_only"]}`
allowlist_template_data_row_count: `{manifest["allowlist_template_data_row_count"]}`
candidate_rows_materialized: `{manifest["candidate_rows_materialized"]}`
candidate_allowlist_created: `{manifest["candidate_allowlist_created"]}`
candidate_allowlist_template_created: `{manifest["candidate_allowlist_template_created"]}`
candidate_allowlist_creation_gate_passed: `{manifest["candidate_allowlist_creation_gate_passed"]}`
ready_for_covapie_candidate_allowlist_materialization_smoke: `{manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"]}`
ready_for_covapie_batch_scale_raw_read_smoke: `{manifest["ready_for_covapie_batch_scale_raw_read_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
feature_semantics_audit_required_before_training: `{manifest["feature_semantics_audit_required_before_training"]}`
leakage_split_design_required_before_training: `{manifest["leakage_split_design_required_before_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_candidate_allowlist_creation_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["schema_rows"], gate.SCHEMA_CONTRACT_CSV, gate.SCHEMA_COLUMNS)
    write_csv(result["candidate_source_rows"], gate.CANDIDATE_SOURCE_CONTRACT_CSV, gate.CONTRACT_COLUMNS)
    write_csv(result["selection_rule_rows"], gate.SELECTION_RULE_CONTRACT_CSV, gate.CONTRACT_COLUMNS)
    write_csv(result["manual_review_rows"], gate.MANUAL_REVIEW_CONTRACT_CSV, gate.CONTRACT_COLUMNS)
    write_csv(result["path_safety_rows"], gate.PATH_SAFETY_CONTRACT_CSV, gate.CONTRACT_COLUMNS)
    write_csv(result["duplicate_exclusion_rows"], gate.DUPLICATE_EXCLUSION_CONTRACT_CSV, gate.CONTRACT_COLUMNS)
    write_csv(result["template_rows"], gate.TEMPLATE_AUDIT_CSV, gate.TEMPLATE_AUDIT_COLUMNS)
    write_csv(result["execution_rows"], gate.EXECUTION_BOUNDARY_AUDIT_CSV, gate.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], gate.GIT_SAFETY_AUDIT_CSV, gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], gate.MASK_SCOPE_AUDIT_CSV, gate.MASK_COLUMNS)
    write_csv(result["feature_rows"], gate.FEATURE_SEMANTICS_AUDIT_CSV, gate.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], gate.LEAKAGE_SPLIT_AUDIT_CSV, gate.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), gate.REPORT_CSV, gate.REPORT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print(
        "covapie_candidate_allowlist_creation_gate_v0_passed"
        if manifest["all_checks_passed"]
        else "covapie_candidate_allowlist_creation_gate_v0_blocked"
    )
    for key in [
        "allowlist_template_path",
        "allowlist_template_written",
        "allowlist_template_header_only",
        "allowlist_template_column_count",
        "allowlist_template_data_row_count",
        "candidate_rows_materialized",
        "candidate_allowlist_created",
        "candidate_allowlist_template_created",
        "covapie_allowlist_creation_precondition_audit_row_count",
        "covapie_allowlist_schema_contract_row_count",
        "covapie_allowlist_candidate_source_contract_row_count",
        "covapie_allowlist_selection_rule_contract_row_count",
        "covapie_allowlist_manual_review_contract_row_count",
        "covapie_allowlist_path_safety_contract_row_count",
        "covapie_allowlist_duplicate_exclusion_contract_row_count",
        "covapie_allowlist_template_audit_row_count",
        "covapie_allowlist_execution_boundary_audit_row_count",
        "covapie_allowlist_git_safety_audit_row_count",
        "covapie_allowlist_mask_scope_audit_row_count",
        "covapie_allowlist_feature_semantics_audit_row_count",
        "covapie_allowlist_leakage_split_audit_row_count",
        "candidate_allowlist_creation_gate_passed",
        "ready_for_covapie_candidate_allowlist_materialization_smoke",
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

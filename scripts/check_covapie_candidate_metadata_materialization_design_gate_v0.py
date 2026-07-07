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

from covalent_ext import covapie_candidate_metadata_materialization_design_gate as design  # noqa: E402


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


def build_report_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = result["manifest"]
    return [
        {
            "stage": design.STAGE,
            "previous_stage": design.PREVIOUS_STAGE,
            "section": section,
            "status": "passed" if evidence["passed"] else "blocked",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Candidate Metadata Materialization Design Gate v0 Summary

Step 13AX is a candidate metadata materialization design gate.
It designs schema, field sources, deterministic row identity, validation rules, and the next first-four materialization smoke boundary.
It does not write candidate metadata rows.
It does not write an allowlist, sample_index, final_dataset, split assignments, or leakage matrix.
It does not use network access, raw downloads, raw text reads, RDKit/Bio.PDB/gemmi/gzip/torch, or training.
The future materialization smoke is limited to the four Step 13AW accepted preferred events.
The unresolved `1A54/MDC` event remains excluded until manual review or a future connectivity fallback design.

accepted_preferred_event_count: `{manifest["accepted_preferred_event_count"]}`
blocked_unresolved_event_count: `{manifest["blocked_unresolved_event_count"]}`
candidate_metadata_schema_field_count: `{manifest["candidate_metadata_schema_field_count"]}`
field_source_mapping_row_count: `{manifest["field_source_mapping_row_count"]}`
future_candidate_metadata_id_preview_count: `{manifest["future_candidate_metadata_id_preview_count"]}`
future_candidate_metadata_id_unique_count: `{manifest["future_candidate_metadata_id_unique_count"]}`
candidate_metadata_materialized: `{manifest["candidate_metadata_materialized"]}`
candidate_allowlist_materialized: `{manifest["candidate_allowlist_materialized"]}`
ready_for_covapie_candidate_metadata_materialization_smoke: `{manifest["ready_for_covapie_candidate_metadata_materialization_smoke"]}`
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
    result = design.run_covapie_candidate_metadata_materialization_design_gate_v0()
    write_csv(result["precondition_rows"], design.PRECONDITION_AUDIT_CSV, design.PRECONDITION_COLUMNS)
    write_csv(result["accepted_rows"], design.ACCEPTED_EVENT_INVENTORY_CSV, design.ACCEPTED_EVENT_COLUMNS)
    write_csv(result["unresolved_policy_rows"], design.UNRESOLVED_EXCLUSION_POLICY_CSV, design.UNRESOLVED_EXCLUSION_COLUMNS)
    write_csv(result["schema_rows"], design.SCHEMA_CONTRACT_CSV, design.SCHEMA_COLUMNS)
    write_csv(result["field_source_rows"], design.FIELD_SOURCE_MAPPING_CONTRACT_CSV, design.FIELD_SOURCE_COLUMNS)
    write_csv(result["row_identity_rows"], design.ROW_IDENTITY_CONTRACT_CSV, design.ROW_IDENTITY_COLUMNS)
    write_csv(result["validation_rows"], design.VALIDATION_CONTRACT_CSV, design.VALIDATION_COLUMNS)
    write_csv(result["plan_rows"], design.MATERIALIZATION_SMOKE_PLAN_CSV, design.SMOKE_PLAN_COLUMNS)
    write_csv(result["allowlist_rows"], design.CANDIDATE_ALLOWLIST_DEPENDENCY_CONTRACT_CSV, design.ALLOWLIST_DEPENDENCY_COLUMNS)
    write_csv(result["materialization_rows"], design.MATERIALIZATION_BOUNDARY_AUDIT_CSV, design.MATERIALIZATION_COLUMNS)
    write_csv(result["execution_rows"], design.EXECUTION_BOUNDARY_AUDIT_CSV, design.EXECUTION_COLUMNS)
    write_csv(result["git_safety_rows"], design.GIT_SAFETY_AUDIT_CSV, design.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], design.MASK_SCOPE_AUDIT_CSV, design.MASK_COLUMNS)
    write_csv(result["feature_rows"], design.FEATURE_SEMANTICS_AUDIT_CSV, design.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], design.LEAKAGE_SPLIT_AUDIT_CSV, design.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), design.REPORT_CSV, design.REPORT_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_candidate_metadata_materialization_design_gate_v0_passed")
    else:
        print("covapie_candidate_metadata_materialization_design_gate_v0_blocked")
    for key in [
        "accepted_preferred_event_count",
        "blocked_unresolved_event_count",
        "candidate_metadata_schema_field_count",
        "field_source_mapping_row_count",
        "future_candidate_metadata_id_preview_count",
        "future_candidate_metadata_id_unique_count",
        "candidate_metadata_materialized",
        "candidate_allowlist_materialized",
        "ready_for_covapie_candidate_metadata_materialization_smoke",
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

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

from covalent_ext import covapie_covpdb_raw_structure_event_annotation_qa_gate as qa  # noqa: E402


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
            "stage": qa.STAGE,
            "previous_stage": qa.PREVIOUS_STAGE,
            "section": section,
            "status": "passed" if evidence["passed"] else "blocked",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE CovPDB Raw Structure Event Annotation QA Gate v0 Summary

Step 13AW is a read-only QA gate over Step 13AV derived artifacts.
It does not use network access, does not rerun Step 13AV, does not download raw files, and does not read raw mmCIF/PDB text.
It checks raw file presence and git safety only, while raw files remain untracked and uncommitted.
It validates download integrity, raw storage safety, format coverage, struct_conn coverage, atom_site validation, event candidate field integrity, preferred event acceptance, and unresolved event handling.
It accepts the four preferred event-key cases for a future candidate metadata materialization design gate.
It keeps the 1A54/MDC no-connectivity case blocked for manual review or future fallback design.
It does not materialize candidate metadata, allowlists, sample_index, final_dataset, splits, or leakage matrices.
It does not train.

qa_accepted_preferred_event_count: `{manifest["qa_accepted_preferred_event_count"]}`
qa_blocked_unresolved_event_count: `{manifest["qa_blocked_unresolved_event_count"]}`
accepted_for_future_candidate_metadata_count: `{manifest["accepted_for_future_candidate_metadata_count"]}`
accepted_for_future_automatic_allowlist_count: `{manifest["accepted_for_future_automatic_allowlist_count"]}`
raw_files_exist_count: `{manifest["raw_files_exist_count"]}`
raw_files_tracked: `{manifest["raw_files_tracked"]}`
raw_files_staged: `{manifest["raw_files_staged"]}`
candidate_metadata_materialized: `{manifest["candidate_metadata_materialized"]}`
candidate_allowlist_materialized: `{manifest["candidate_allowlist_materialized"]}`
ready_for_covapie_candidate_metadata_materialization_design_gate: `{manifest["ready_for_covapie_candidate_metadata_materialization_design_gate"]}`
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
    result = qa.run_covapie_covpdb_raw_structure_event_annotation_qa_gate_v0()
    write_csv(result["precondition_rows"], qa.PRECONDITION_AUDIT_CSV, qa.PRECONDITION_COLUMNS)
    write_csv(result["download_integrity_rows"], qa.DOWNLOAD_INTEGRITY_QA_CSV, qa.DOWNLOAD_INTEGRITY_COLUMNS)
    write_csv(result["storage_safety_rows"], qa.STORAGE_SAFETY_QA_CSV, qa.STORAGE_SAFETY_COLUMNS)
    write_csv(result["format_coverage_rows"], qa.FORMAT_COVERAGE_QA_CSV, qa.FORMAT_COVERAGE_COLUMNS)
    write_csv(result["struct_conn_rows"], qa.STRUCT_CONN_COVERAGE_QA_CSV, qa.STRUCT_CONN_COVERAGE_COLUMNS)
    write_csv(result["atom_site_rows"], qa.ATOM_SITE_VALIDATION_QA_CSV, qa.ATOM_SITE_VALIDATION_COLUMNS)
    write_csv(result["candidate_field_rows"], qa.EVENT_CANDIDATE_FIELD_INTEGRITY_QA_CSV, qa.EVENT_CANDIDATE_FIELD_COLUMNS)
    write_csv(result["resolution_summary_rows"], qa.EVENT_KEY_RESOLUTION_SUMMARY_QA_CSV, qa.EVENT_KEY_RESOLUTION_SUMMARY_COLUMNS)
    write_csv(result["preferred_rows"], qa.PREFERRED_EVENT_ACCEPTANCE_QA_CSV, qa.PREFERRED_EVENT_ACCEPTANCE_COLUMNS)
    write_csv(result["unresolved_rows"], qa.UNRESOLVED_EVENT_HANDLING_QA_CSV, qa.UNRESOLVED_EVENT_HANDLING_COLUMNS)
    write_csv(result["readiness_rows"], qa.CANDIDATE_METADATA_READINESS_DECISION_QA_CSV, qa.CANDIDATE_METADATA_READINESS_COLUMNS)
    write_csv(result["materialization_rows"], qa.MATERIALIZATION_BOUNDARY_AUDIT_CSV, qa.MATERIALIZATION_COLUMNS)
    write_csv(result["execution_rows"], qa.EXECUTION_BOUNDARY_AUDIT_CSV, qa.EXECUTION_COLUMNS)
    write_csv(result["git_safety_rows"], qa.GIT_SAFETY_AUDIT_CSV, qa.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], qa.MASK_SCOPE_AUDIT_CSV, qa.MASK_COLUMNS)
    write_csv(result["feature_rows"], qa.FEATURE_SEMANTICS_AUDIT_CSV, qa.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], qa.LEAKAGE_SPLIT_AUDIT_CSV, qa.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), qa.REPORT_CSV, qa.REPORT_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"], qa.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_covpdb_raw_structure_event_annotation_qa_gate_v0_passed")
    else:
        print("covapie_covpdb_raw_structure_event_annotation_qa_gate_v0_blocked")
    for key in [
        "qa_accepted_preferred_event_count",
        "qa_blocked_unresolved_event_count",
        "accepted_for_future_candidate_metadata_count",
        "accepted_for_future_automatic_allowlist_count",
        "raw_files_exist_count",
        "raw_files_tracked",
        "raw_files_staged",
        "candidate_metadata_materialized",
        "candidate_allowlist_materialized",
        "ready_for_covapie_candidate_metadata_materialization_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

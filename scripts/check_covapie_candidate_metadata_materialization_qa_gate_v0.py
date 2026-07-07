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

from covalent_ext import covapie_candidate_metadata_materialization_qa_gate as qa_gate  # noqa: E402


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
            "stage": qa_gate.STAGE,
            "previous_stage": qa_gate.PREVIOUS_STAGE,
            "section": section,
            "status": "passed" if evidence["passed"] else "blocked",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Candidate Metadata Materialization QA Gate v0 Summary

Step 13AZ is a read-only QA gate for the Step 13AY four-row candidate metadata smoke artifacts.
It validates content integrity, schema order, row identity, traceability to Step 13AX/13AW/13AO, unresolved `1A54/MDC` exclusion, boundary safety, git safety, canonical masks, feature semantics blockers, and leakage/split blockers.
It does not write new candidate metadata.
It does not write a candidate allowlist, sample_index, final_dataset, split assignments, or leakage matrix.
It does not use network access, raw downloads, raw text reads, RDKit/Bio.PDB/gemmi/gzip/torch, model calls, loss, optimizer, trainer.fit, or training.
The next allowed step is a candidate allowlist materialization design gate, not allowlist materialization smoke and not training.

qa_candidate_metadata_row_count: `{manifest["qa_candidate_metadata_row_count"]}`
qa_candidate_metadata_column_count: `{manifest["qa_candidate_metadata_column_count"]}`
qa_candidate_metadata_id_unique_count: `{manifest["qa_candidate_metadata_id_unique_count"]}`
qa_unresolved_exclusion_preserved: `{manifest["qa_unresolved_exclusion_preserved"]}`
qa_traceability_passed: `{manifest["qa_traceability_passed"]}`
qa_content_integrity_passed: `{manifest["qa_content_integrity_passed"]}`
qa_boundary_safety_passed: `{manifest["qa_boundary_safety_passed"]}`
qa_git_safety_passed: `{manifest["qa_git_safety_passed"]}`
qa_training_blockers_passed: `{manifest["qa_training_blockers_passed"]}`
candidate_metadata_materialized_current_step: `{manifest["candidate_metadata_materialized_current_step"]}`
candidate_allowlist_materialized: `{manifest["candidate_allowlist_materialized"]}`
ready_for_covapie_candidate_allowlist_materialization_design_gate: `{manifest["ready_for_covapie_candidate_allowlist_materialization_design_gate"]}`
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
    result = qa_gate.run_covapie_candidate_metadata_materialization_qa_gate_v0()
    write_csv(result["precondition_rows"], qa_gate.PRECONDITION_AUDIT_CSV, qa_gate.PRECONDITION_COLUMNS)
    write_csv(result["content_rows"], qa_gate.CONTENT_INTEGRITY_CSV, qa_gate.CONTENT_COLUMNS)
    write_csv(result["traceability_rows"], qa_gate.TRACEABILITY_CSV, qa_gate.TRACEABILITY_COLUMNS)
    write_csv(result["unresolved_rows"], qa_gate.UNRESOLVED_EXCLUSION_CSV, qa_gate.UNRESOLVED_COLUMNS)
    write_csv(result["boundary_rows"], qa_gate.BOUNDARY_SAFETY_CSV, qa_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], qa_gate.GIT_SAFETY_CSV, qa_gate.GIT_SAFETY_COLUMNS)
    write_csv(result["training_blocker_rows"], qa_gate.TRAINING_BLOCKERS_CSV, qa_gate.TRAINING_BLOCKERS_COLUMNS)
    write_csv(build_report_rows(result), qa_gate.REPORT_CSV, qa_gate.REPORT_COLUMNS)
    write_json(result["manifest"], qa_gate.MANIFEST_JSON)
    write_summary(result["manifest"], qa_gate.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_candidate_metadata_materialization_qa_gate_v0_passed")
    else:
        print("covapie_candidate_metadata_materialization_qa_gate_v0_blocked")
    for key in [
        "qa_candidate_metadata_row_count",
        "qa_candidate_metadata_column_count",
        "qa_candidate_metadata_id_unique_count",
        "qa_unresolved_exclusion_preserved",
        "qa_traceability_passed",
        "qa_content_integrity_passed",
        "qa_boundary_safety_passed",
        "qa_git_safety_passed",
        "qa_training_blockers_passed",
        "candidate_metadata_materialized_current_step",
        "candidate_allowlist_materialized",
        "ready_for_covapie_candidate_allowlist_materialization_design_gate",
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

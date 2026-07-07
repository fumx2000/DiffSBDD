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

from covalent_ext import covapie_covpdb_complex_card_metadata_acquisition_qa_gate as qa  # noqa: E402


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
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE CovPDB Complex Card Metadata Acquisition QA Gate v0 Summary

This is a read-only QA gate for the Step 13AS complex-card metadata acquisition smoke artifacts.
It does not access the network.
It does not rerun the Step 13AS live acquisition check script.
It does not fetch complex cards.
It does not download raw structures, ligand SDF, ZIP/GZ, PDB, CIF, or mmCIF.
It does not save full HTML.
It does not modify the Step 13AS artifacts or parser.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

Step 13AS showed that five allowed CovPDB complex-card HTML pages were fetched successfully.
The current text parser did not resolve chain/residue/reactive atom/covalent bond atom pair fields.
Candidate metadata, allowlist materialization, raw-read smoke, and training therefore remain blocked.
The recommended next step is a sanitized CovPDB complex-card HTML structure probe design gate, not raw download or training.

attempted_card_count: `{manifest["attempted_card_count"]}`
fetch_succeeded_count: `{manifest["fetch_succeeded_count"]}`
fetch_failed_count: `{manifest["fetch_failed_count"]}`
minimal_event_key_resolved_card_count: `{manifest["minimal_event_key_resolved_card_count"]}`
preferred_event_key_resolved_card_count: `{manifest["preferred_event_key_resolved_card_count"]}`
partial_event_key_card_count: `{manifest["partial_event_key_card_count"]}`
unresolved_card_count: `{manifest["unresolved_card_count"]}`
future_candidate_metadata_possible_count: `{manifest["future_candidate_metadata_possible_count"]}`
future_automatic_allowlist_possible_count: `{manifest["future_automatic_allowlist_possible_count"]}`
ready_for_covapie_covpdb_complex_card_html_structure_probe_design_gate: `{manifest["ready_for_covapie_covpdb_complex_card_html_structure_probe_design_gate"]}`
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
    result = qa.run_covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0()
    write_csv(result["precondition_rows"], qa.PRECONDITION_AUDIT_CSV, qa.PRECONDITION_COLUMNS)
    write_csv(result["fetch_integrity_rows"], qa.FETCH_INTEGRITY_QA_CSV, qa.FETCH_INTEGRITY_COLUMNS)
    write_csv(result["html_safety_rows"], qa.HTML_SAFETY_QA_CSV, qa.HTML_SAFETY_COLUMNS)
    write_csv(result["label_summary_rows"], qa.LABEL_INVENTORY_SUMMARY_QA_CSV, qa.LABEL_SUMMARY_COLUMNS)
    write_csv(result["event_field_summary_rows"], qa.EVENT_FIELD_STATUS_SUMMARY_QA_CSV, qa.EVENT_FIELD_SUMMARY_COLUMNS)
    write_csv(result["event_key_summary_rows"], qa.EVENT_KEY_RESOLUTION_SUMMARY_QA_CSV, qa.EVENT_KEY_SUMMARY_COLUMNS)
    write_csv(result["unresolved_reason_rows"], qa.UNRESOLVED_REASON_QA_CSV, qa.UNRESOLVED_COLUMNS)
    write_csv(result["snippet_safety_rows"], qa.EVIDENCE_SNIPPET_SAFETY_QA_CSV, qa.SNIPPET_SAFETY_COLUMNS)
    write_csv(result["materialization_decision_rows"], qa.MATERIALIZATION_DECISION_QA_CSV, qa.MATERIALIZATION_DECISION_COLUMNS)
    write_csv(result["next_step_rows"], qa.NEXT_STEP_DECISION_QA_CSV, qa.NEXT_STEP_COLUMNS)
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
        print("covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0_passed")
    else:
        print("covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0_blocked")
    for key in [
        "attempted_card_count",
        "fetch_succeeded_count",
        "fetch_failed_count",
        "minimal_event_key_resolved_card_count",
        "preferred_event_key_resolved_card_count",
        "partial_event_key_card_count",
        "unresolved_card_count",
        "future_candidate_metadata_possible_count",
        "future_automatic_allowlist_possible_count",
        "ready_for_covapie_covpdb_complex_card_html_structure_probe_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())


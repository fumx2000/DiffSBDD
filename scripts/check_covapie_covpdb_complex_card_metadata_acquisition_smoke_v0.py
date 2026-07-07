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

from covalent_ext import covapie_covpdb_complex_card_metadata_acquisition_smoke as smoke  # noqa: E402


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
            "stage": smoke.STAGE,
            "previous_stage": smoke.PREVIOUS_STAGE,
            "section": section,
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE CovPDB Complex Card Metadata Acquisition Smoke v0 Summary

This is a controlled CovPDB complex-card HTML metadata acquisition smoke.
It fetches only the first five allowed CovPDB complex-card URLs from the committed metadata CSV.
It does not save complete HTML.
It does not follow links.
It does not download raw structures, ligand SDF, ZIP/GZ, PDB, CIF, or mmCIF.
It does not read raw/SDF/PDB/mmCIF/gzip content.
It does not use RDKit/Bio.PDB/gemmi.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

attempted_card_count: `{manifest["attempted_card_count"]}`
fetched_card_count: `{manifest["fetched_card_count"]}`
fetch_succeeded_count: `{manifest["fetch_succeeded_count"]}`
fetch_failed_count: `{manifest["fetch_failed_count"]}`
first_5_complex_card_urls: `{manifest["first_5_complex_card_urls"]}`
full_html_written: `{manifest["full_html_written"]}`
raw_html_artifact_written: `{manifest["raw_html_artifact_written"]}`
minimal_event_key_resolved_card_count: `{manifest["minimal_event_key_resolved_card_count"]}`
preferred_event_key_resolved_card_count: `{manifest["preferred_event_key_resolved_card_count"]}`
partial_event_key_card_count: `{manifest["partial_event_key_card_count"]}`
unresolved_card_count: `{manifest["unresolved_card_count"]}`
future_candidate_metadata_possible_count: `{manifest["future_candidate_metadata_possible_count"]}`
future_automatic_allowlist_possible_count: `{manifest["future_automatic_allowlist_possible_count"]}`
ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate: `{manifest["ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate"]}`
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
    result = smoke.run_covapie_covpdb_complex_card_metadata_acquisition_smoke_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], smoke.PRECONDITION_COLUMNS)
    write_csv(result["acquisition_plan_rows"], paths["plan"], smoke.ACQUISITION_PLAN_COLUMNS)
    write_csv(result["fetch_rows"], paths["fetch"], smoke.FETCH_AUDIT_COLUMNS)
    write_csv(result["safety_rows"], paths["safety"], smoke.HTML_SAFETY_COLUMNS)
    write_csv(result["label_rows"], paths["labels"], smoke.LABEL_INVENTORY_COLUMNS)
    write_csv(result["field_rows"], paths["fields"], smoke.EVENT_FIELD_COLUMNS)
    write_csv(result["snippet_rows"], paths["snippets"], smoke.SNIPPET_AUDIT_COLUMNS)
    write_csv(result["resolution_rows"], paths["resolution"], smoke.EVENT_KEY_RESOLUTION_COLUMNS)
    write_csv(result["failure_rows"], paths["failure"], smoke.FAILURE_TAXONOMY_COLUMNS)
    write_csv(result["readiness_rows"], paths["readiness"], smoke.READINESS_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], smoke.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], smoke.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], smoke.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], smoke.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], smoke.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_covpdb_complex_card_metadata_acquisition_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_covpdb_complex_card_metadata_acquisition_smoke_v0_blocked")
    for key in [
        "attempted_card_count",
        "fetched_card_count",
        "fetch_succeeded_count",
        "fetch_failed_count",
        "first_5_complex_card_urls",
        "minimal_event_key_resolved_card_count",
        "preferred_event_key_resolved_card_count",
        "partial_event_key_card_count",
        "unresolved_card_count",
        "future_candidate_metadata_possible_count",
        "future_automatic_allowlist_possible_count",
        "ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

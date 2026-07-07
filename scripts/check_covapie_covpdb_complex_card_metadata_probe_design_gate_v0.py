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

from covalent_ext import covapie_covpdb_complex_card_metadata_probe_design_gate as gate  # noqa: E402


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
            "stage": gate.STAGE,
            "previous_stage": gate.PREVIOUS_STAGE,
            "section": section,
            "status": "passed",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE CovPDB Complex Card Metadata Probe Design Gate v0 Summary

This is a CovaPIE complex-card metadata probe design gate.
It designs a future CovPDB complex-card HTML metadata acquisition smoke.
It does not fetch CovPDB complex-card pages in this step.
It does not use network.
It does not download raw structures, ligand SDF, ZIP/GZ, PDB, CIF, or mmCIF.
It does not read raw/SDF/PDB/mmCIF/gzip content.
It does not use RDKit/Bio.PDB/gemmi.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

The future acquisition smoke may only fetch HTML/text from CovPDB complex-card URLs already present in the committed metadata CSV.
The first acquisition smoke is capped at five cards, with no recursive crawling and no following download links.
Candidate metadata remains blocked until the minimal event key is explicit.
Automatic allowlist materialization remains blocked unless the preferred event key, including covalent_bond_atom_pair, is explicit.

metadata_csv_row_count: `{manifest["metadata_csv_row_count"]}`
metadata_csv_column_count: `{manifest["metadata_csv_column_count"]}`
complex_card_url_count: `{manifest["complex_card_url_count"]}`
first_5_complex_card_urls: `{manifest["first_5_complex_card_urls"]}`
target_field_contract_row_count: `{manifest["target_field_contract_row_count"]}`
allowed_url_contract_row_count: `{manifest["allowed_url_contract_row_count"]}`
forbidden_artifact_contract_row_count: `{manifest["forbidden_artifact_contract_row_count"]}`
parse_strategy_contract_row_count: `{manifest["parse_strategy_contract_row_count"]}`
event_key_resolution_contract_row_count: `{manifest["event_key_resolution_contract_row_count"]}`
failure_taxonomy_row_count: `{manifest["failure_taxonomy_row_count"]}`
ready_for_covapie_covpdb_complex_card_metadata_acquisition_smoke: `{manifest["ready_for_covapie_covpdb_complex_card_metadata_acquisition_smoke"]}`
ready_for_covapie_candidate_metadata_materialization: `{manifest["ready_for_covapie_candidate_metadata_materialization"]}`
ready_for_covapie_candidate_allowlist_materialization_smoke: `{manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"]}`
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
    result = gate.run_covapie_covpdb_complex_card_metadata_probe_design_gate_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], gate.PRECONDITION_COLUMNS)
    write_csv(result["target_rows"], paths["target"], gate.TARGET_FIELD_COLUMNS)
    write_csv(result["allowed_url_rows"], paths["allowed_url"], gate.ALLOWED_URL_COLUMNS)
    write_csv(result["forbidden_rows"], paths["forbidden"], gate.FORBIDDEN_ARTIFACT_COLUMNS)
    write_csv(result["parse_rows"], paths["parse"], gate.PARSE_STRATEGY_COLUMNS)
    write_csv(result["event_rows"], paths["event"], gate.EVENT_KEY_RESOLUTION_COLUMNS)
    write_csv(result["failure_rows"], paths["failure"], gate.FAILURE_TAXONOMY_COLUMNS)
    write_csv(result["readiness_rows"], paths["readiness"], gate.READINESS_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], gate.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], gate.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], gate.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], gate.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], gate.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_covpdb_complex_card_metadata_probe_design_gate_v0_passed")
    for key in [
        "metadata_csv_row_count",
        "metadata_csv_column_count",
        "complex_card_url_count",
        "first_5_complex_card_urls",
        "target_field_contract_row_count",
        "allowed_url_contract_row_count",
        "forbidden_artifact_contract_row_count",
        "parse_strategy_contract_row_count",
        "event_key_resolution_contract_row_count",
        "failure_taxonomy_row_count",
        "ready_for_covapie_covpdb_complex_card_metadata_acquisition_smoke",
        "ready_for_covapie_candidate_metadata_materialization",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

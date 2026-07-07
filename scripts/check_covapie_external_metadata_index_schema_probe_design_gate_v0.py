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

from covalent_ext import covapie_external_metadata_index_schema_probe_design_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE External Metadata Index Schema Probe Design Gate v0 Summary

This is a CovaPIE schema probe design gate.
It reads the local CovPDB manual metadata CSV produced by Step 13AO and rediscovered by Step 13AP.
It does not modify the metadata CSV, Step 13AO artifacts, or Step 13AP artifacts.
It does not use network.
It does not download raw structures or ligand files.
It does not read raw/SDF/PDB/mmCIF/gzip content.
It does not use RDKit/Bio.PDB/gemmi.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

Current conclusion:
CovPDB list metadata is enough to identify PDB-level ligand records, but it is not enough to build a CovaPIE covalent event allowlist.
The list metadata lacks chain ID, residue name, residue index, residue atom name, and covalent bond atom pair.
Joining by pdb_id alone remains forbidden.
The next step should probe CovPDB complex-card metadata before any raw download.

metadata_csv_row_count: `{manifest["metadata_csv_row_count"]}`
metadata_csv_column_count: `{manifest["metadata_csv_column_count"]}`
allowlist_required_column_count: `{manifest["allowlist_required_column_count"]}`
directly_mappable_allowlist_column_count: `{manifest["directly_mappable_allowlist_column_count"]}`
generated_future_allowlist_column_count: `{manifest["generated_future_allowlist_column_count"]}`
missing_critical_allowlist_column_count: `{manifest["missing_critical_allowlist_column_count"]}`
missing_deferred_allowlist_column_count: `{manifest["missing_deferred_allowlist_column_count"]}`
minimal_event_key_materializable: `{manifest["minimal_event_key_materializable"]}`
preferred_event_key_materializable: `{manifest["preferred_event_key_materializable"]}`
one_row_one_covalent_event_enforceable: `{manifest["one_row_one_covalent_event_enforceable"]}`
candidate_metadata_materialized: `{manifest["candidate_metadata_materialized"]}`
candidate_allowlist_materialized: `{manifest["candidate_allowlist_materialized"]}`
ready_for_covapie_covpdb_complex_card_metadata_probe_design_gate: `{manifest["ready_for_covapie_covpdb_complex_card_metadata_probe_design_gate"]}`
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
    result = gate.run_covapie_external_metadata_index_schema_probe_design_gate_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], gate.PRECONDITION_COLUMNS)
    write_csv(result["observed_schema_rows"], paths["observed"], gate.OBSERVED_SCHEMA_COLUMNS)
    write_csv(result["mapping_rows"], paths["mapping"], gate.MAPPING_COLUMNS)
    write_csv(result["missing_rows"], paths["missing"], gate.MISSING_PLAN_COLUMNS)
    write_csv(result["event_rows"], paths["event"], gate.EVENT_KEY_GAP_COLUMNS)
    write_csv(result["blocker_rows"], paths["blocker"], gate.CANDIDATE_BLOCKER_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], gate.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], gate.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], gate.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], gate.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], gate.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_external_metadata_index_schema_probe_design_gate_v0_passed")
    for key in [
        "metadata_csv_row_count",
        "metadata_csv_column_count",
        "allowlist_required_column_count",
        "directly_mappable_allowlist_column_count",
        "generated_future_allowlist_column_count",
        "missing_critical_allowlist_column_count",
        "missing_deferred_allowlist_column_count",
        "minimal_event_key_materializable",
        "preferred_event_key_materializable",
        "one_row_one_covalent_event_enforceable",
        "candidate_metadata_materialized",
        "candidate_allowlist_materialized",
        "ready_for_covapie_covpdb_complex_card_metadata_probe_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

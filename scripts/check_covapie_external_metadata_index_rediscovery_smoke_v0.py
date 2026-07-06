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

from covalent_ext import covapie_external_metadata_index_rediscovery_smoke as smoke  # noqa: E402


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
            "status": "passed",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE External Metadata Index Rediscovery Smoke v0 Summary

This is CovaPIE external metadata index rediscovery smoke.
It is the rerun-equivalent of Step 13AN after Step 13AO generated the manual CovPDB metadata CSV.
It does not overwrite historical Step 13AN artifacts.
It reads only the local manual metadata CSV header and rows.
It does not use network.
It does not download metadata or raw structures.
It does not copy the metadata CSV into the Step 13AP output root.
It does not read raw structure contents.
It does not read SDF/PDB/mmCIF/gzip.
It does not use RDKit/Bio.PDB/gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index/final dataset/split/leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
It preserves one row = one covalent ligand-residue event policy, but event keys are not materialized yet.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

metadata_index_file_exists: `{manifest["metadata_index_file_exists"]}`
metadata_index_file_read: `{manifest["metadata_index_file_read"]}`
metadata_index_row_count: `{manifest["metadata_index_row_count"]}`
metadata_index_column_count: `{manifest["metadata_index_column_count"]}`
first_5_pdb_ids: `{manifest["first_5_pdb_ids"]}`
first_5_het_codes: `{manifest["first_5_het_codes"]}`
external_metadata_index_rediscovery_smoke_passed: `{manifest["external_metadata_index_rediscovery_smoke_passed"]}`
metadata_index_rediscovery_status: `{manifest["metadata_index_rediscovery_status"]}`
ready_for_covapie_external_metadata_index_schema_probe_design_gate: `{manifest["ready_for_covapie_external_metadata_index_schema_probe_design_gate"]}`
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
    result = smoke.run_covapie_external_metadata_index_rediscovery_smoke_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], smoke.PRECONDITION_COLUMNS)
    write_csv(result["file_rows"], paths["file"], smoke.FILE_DISCOVERY_COLUMNS)
    write_csv(result["header_rows"], paths["header"], smoke.HEADER_PROBE_COLUMNS)
    write_csv(result["sample_rows"], paths["sample"], smoke.SAMPLE_ROWS_PROBE_COLUMNS)
    write_csv(result["schema_rows"], paths["schema"], smoke.SCHEMA_COLUMNS)
    write_csv(result["event_rows"], paths["event"], smoke.EVENT_KEY_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], smoke.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], smoke.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], smoke.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], smoke.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], smoke.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_external_metadata_index_rediscovery_smoke_v0_passed")
    for key in [
        "metadata_index_file_exists",
        "metadata_index_file_read",
        "metadata_index_row_count",
        "metadata_index_column_count",
        "first_5_pdb_ids",
        "first_5_het_codes",
        "external_metadata_index_rediscovery_smoke_passed",
        "metadata_index_rediscovery_status",
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

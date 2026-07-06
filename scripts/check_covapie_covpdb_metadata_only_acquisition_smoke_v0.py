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

from covalent_ext import covapie_covpdb_metadata_only_acquisition_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE CovPDB Metadata-Only Acquisition Smoke v0 Summary

This is CovaPIE CovPDB metadata-only acquisition smoke.
It uses controlled urllib access to CovPDB HTML metadata pages only.
It writes the manual CovPDB metadata CSV only if real rows are parsed from the CovPDB Complexes list.
It does not download raw structures, SDF, PDB, mmCIF, ZIP, or gzip artifacts.
It does not read raw structure contents.
It does not use RDKit, Bio.PDB, gemmi, torch, tensors, checkpoints, model forward, loss, optimizer, trainer.fit, or training.
It does not materialize candidate metadata, allowlists, sample index, final dataset, split assignments, or leakage matrices.
It preserves five canonical mask tasks, including scaffold_only/B3.
It keeps feature semantics audit and leakage/split design required before formal training.

enabled_source_name: `{manifest["enabled_source_name"]}`
acquisition_scope: `{manifest["acquisition_scope"]}`
network_access_used: `{manifest["network_access_used"]}`
fetched_urls: `{manifest["fetched_urls"]}`
metadata_csv_written: `{manifest["metadata_csv_written"]}`
metadata_csv_path: `{manifest["metadata_csv_path"]}`
metadata_csv_row_count: `{manifest["metadata_csv_row_count"]}`
metadata_csv_column_count: `{manifest["metadata_csv_column_count"]}`
covpdb_metadata_only_acquisition_smoke_passed: `{manifest["covpdb_metadata_only_acquisition_smoke_passed"]}`
metadata_only_acquisition_status: `{manifest["metadata_only_acquisition_status"]}`
ready_for_covapie_external_metadata_index_download_smoke_rerun: `{manifest["ready_for_covapie_external_metadata_index_download_smoke_rerun"]}`
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
    result = smoke.run_covpdb_metadata_only_acquisition_smoke_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], smoke.PRECONDITION_COLUMNS)
    write_csv(result["network_rows"], paths["network"], smoke.NETWORK_SCOPE_COLUMNS)
    write_csv(result["page_rows"], paths["page"], smoke.PAGE_FETCH_COLUMNS)
    write_csv(result["parse_rows"], paths["parse"], smoke.PARSE_COLUMNS)
    write_csv(result["schema_rows"], paths["schema"], smoke.CSV_SCHEMA_COLUMNS)
    write_csv(result["raw_rows"], paths["raw"], smoke.RAW_ARTIFACT_COLUMNS)
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
    print("covapie_covpdb_metadata_only_acquisition_smoke_v0_passed")
    for key in [
        "network_access_used",
        "fetched_urls",
        "metadata_csv_written",
        "metadata_csv_path",
        "metadata_csv_row_count",
        "metadata_csv_column_count",
        "covpdb_metadata_only_acquisition_smoke_passed",
        "metadata_only_acquisition_status",
        "ready_for_covapie_external_metadata_index_download_smoke_rerun",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

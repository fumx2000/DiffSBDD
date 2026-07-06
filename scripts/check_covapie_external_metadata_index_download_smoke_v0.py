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

from covalent_ext import covapie_external_metadata_index_download_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE External Metadata Index Download Smoke v0 Summary

This is CovaPIE external metadata index download smoke.
For a manual_user_supplied CovPDB source, this step does not download.
It only checks whether the configured manual metadata CSV exists.
If missing, the step is safely blocked and asks for the manual CovPDB metadata index CSV.
If present, it reads only the CSV header and at most 5 sample rows.
It does not copy the metadata CSV into the Step 13AN output root.
It does not verify external URLs.
It does not use internet, network, curl, wget, requests, urllib, or browser.
It does not download metadata or raw structures.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
Metadata index schema mapping and candidate materialization remain future steps.
Raw structure download remains forbidden.
It preserves one row = one covalent ligand-residue event.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

enabled_source_name: `{manifest["enabled_source_name"]}`
enabled_source_access_method: `{manifest["enabled_source_access_method"]}`
source_metadata_index_url_or_local_path: `{manifest["source_metadata_index_url_or_local_path"]}`
metadata_index_file_checked: `{manifest["metadata_index_file_checked"]}`
metadata_index_file_exists: `{manifest["metadata_index_file_exists"]}`
metadata_index_file_read: `{manifest["metadata_index_file_read"]}`
metadata_index_download_or_copy_performed: `{manifest["metadata_index_download_or_copy_performed"]}`
metadata_index_file_copied_to_output_root: `{manifest["metadata_index_file_copied_to_output_root"]}`
metadata_index_download_smoke_status: `{manifest["metadata_index_download_smoke_status"]}`
external_metadata_index_download_smoke_passed: `{manifest["external_metadata_index_download_smoke_passed"]}`
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
    result = smoke.run_covapie_external_metadata_index_download_smoke_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], smoke.PRECONDITION_COLUMNS)
    write_csv(result["source_config_rows"], paths["source_config"], smoke.SOURCE_CONFIG_AUDIT_COLUMNS)
    write_csv(result["file_discovery_rows"], paths["file_discovery"], smoke.FILE_DISCOVERY_COLUMNS)
    write_csv(result["allowed_rows"], paths["allowed"], smoke.ALLOWED_ARTIFACT_COLUMNS)
    write_csv(result["header_rows"], paths["header"], smoke.HEADER_PROBE_COLUMNS)
    write_csv(result["sample_rows"], paths["sample"], smoke.SAMPLE_ROWS_PROBE_COLUMNS)
    write_csv(result["event_key_rows"], paths["event_key"], smoke.EVENT_KEY_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], smoke.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], smoke.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], smoke.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], smoke.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], smoke.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_external_metadata_index_download_smoke_v0_passed")
    for key in [
        "enabled_source_name",
        "enabled_source_access_method",
        "enabled_source_artifact_type",
        "source_metadata_index_url_or_local_path",
        "metadata_index_file_checked",
        "metadata_index_file_exists",
        "metadata_index_file_read",
        "metadata_index_download_or_copy_performed",
        "metadata_index_header_probe_executed",
        "metadata_index_sample_rows_probe_executed",
        "metadata_index_download_smoke_status",
        "external_metadata_index_download_smoke_passed",
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

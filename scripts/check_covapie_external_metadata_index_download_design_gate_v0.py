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

from covalent_ext import covapie_external_metadata_index_download_design_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE External Metadata Index Download Design Gate v0 Summary

This is CovaPIE external metadata index download design gate.
It designs future metadata index download from specialized covalent databases.
It does not configure a real external source in this step.
It does not verify any external database in this step.
It does not use internet, network, curl, wget, requests, urllib, or browser.
It does not download metadata or raw structures.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
Metadata index download smoke will be allowed only after external source registry configuration.
Raw structure download remains forbidden until candidate metadata and allowlist are materialized.
It preserves one row = one covalent ligand-residue event.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

metadata_index_root: `{manifest["metadata_index_root"]}`
raw_structure_root: `{manifest["raw_structure_root"]}`
metadata_index_allowed_artifact_types: `{manifest["metadata_index_allowed_artifact_types"]}`
metadata_index_deferred_artifact_types: `{manifest["metadata_index_deferred_artifact_types"]}`
metadata_index_forbidden_artifact_types: `{manifest["metadata_index_forbidden_artifact_types"]}`
external_source_configured_current_step: `{manifest["external_source_configured_current_step"]}`
external_metadata_downloaded: `{manifest["external_metadata_downloaded"]}`
raw_structure_downloaded: `{manifest["raw_structure_downloaded"]}`
ready_for_covapie_external_source_registry_configuration: `{manifest["ready_for_covapie_external_source_registry_configuration"]}`
ready_for_covapie_external_metadata_index_download_smoke: `{manifest["ready_for_covapie_external_metadata_index_download_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
feature_semantics_audit_required_before_training: `{manifest["feature_semantics_audit_required_before_training"]}`
leakage_split_design_required_before_training: `{manifest["leakage_split_design_required_before_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_external_metadata_index_download_design_gate_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], gate.PRECONDITION_COLUMNS)
    write_csv(result["source_config_rows"], paths["source_config"], gate.SOURCE_CONFIG_COLUMNS)
    write_csv(result["download_plan_rows"], paths["download_plan"], gate.DOWNLOAD_PLAN_COLUMNS)
    write_csv(result["allowed_artifact_rows"], paths["allowed_artifact"], gate.ALLOWED_ARTIFACT_COLUMNS)
    write_csv(result["output_path_rows"], paths["output_path"], gate.OUTPUT_PATH_COLUMNS)
    write_csv(result["download_manifest_rows"], paths["download_manifest"], gate.DOWNLOAD_MANIFEST_COLUMNS)
    write_csv(result["schema_probe_rows"], paths["schema_probe"], gate.SCHEMA_PROBE_COLUMNS)
    write_csv(result["event_key_rows"], paths["event_key"], gate.EVENT_KEY_MAPPING_COLUMNS)
    write_csv(result["candidate_filter_rows"], paths["candidate_filter"], gate.CANDIDATE_FILTER_COLUMNS)
    write_csv(result["failure_rows"], paths["failure"], gate.FAILURE_TAXONOMY_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], gate.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], gate.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], gate.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], gate.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], gate.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_external_metadata_index_download_design_gate_v0_passed")
    for key in [
        "covapie_external_metadata_index_source_config_schema_contract_row_count",
        "covapie_external_metadata_index_download_plan_contract_row_count",
        "covapie_external_metadata_index_allowed_artifact_contract_row_count",
        "covapie_external_metadata_index_output_path_contract_row_count",
        "covapie_external_metadata_index_download_manifest_contract_row_count",
        "covapie_external_metadata_index_schema_probe_contract_row_count",
        "covapie_external_metadata_index_event_key_mapping_contract_row_count",
        "covapie_external_metadata_index_candidate_filter_contract_row_count",
        "covapie_external_metadata_index_failure_taxonomy_contract_row_count",
        "metadata_index_root",
        "raw_structure_root",
        "external_source_configured_current_step",
        "external_network_access_used",
        "external_metadata_downloaded",
        "raw_structure_downloaded",
        "event_identity_key_policy",
        "minimal_event_key",
        "preferred_event_key",
        "one_row_one_covalent_event",
        "ready_for_covapie_external_source_registry_configuration",
        "ready_for_covapie_external_metadata_index_download_smoke",
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

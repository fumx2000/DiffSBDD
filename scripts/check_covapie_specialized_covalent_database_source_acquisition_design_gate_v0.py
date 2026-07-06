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

from covalent_ext import covapie_specialized_covalent_database_source_acquisition_design_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE Specialized Covalent Database Source Acquisition Design Gate v0 Summary

This is CovaPIE specialized covalent database source acquisition design gate.
It prioritizes specialized covalent protein-ligand databases over blind PDB-wide scanning.
It does not verify any external database in this step.
It does not use internet, network, curl, wget, requests, or urllib.
It does not download metadata or raw structures.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
One metadata row must correspond to one covalent ligand-residue event, not merely one PDB entry.
Joining by pdb_id alone is forbidden.
Minimal event key: `{manifest["minimal_event_key"]}`.
Preferred event key: `{manifest["preferred_event_key"]}`.
Next step is external metadata index download design gate.
It keeps feature semantics audit and leakage/split design required before training.

source_registry_contract_row_count: `{manifest["source_registry_contract_row_count"]}`
external_source_verified_current_step: `{manifest["external_source_verified_current_step"]}`
external_network_access_used: `{manifest["external_network_access_used"]}`
external_metadata_downloaded: `{manifest["external_metadata_downloaded"]}`
raw_structure_downloaded: `{manifest["raw_structure_downloaded"]}`
ready_for_covapie_external_metadata_index_download_design_gate: `{manifest["ready_for_covapie_external_metadata_index_download_design_gate"]}`
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
    result = gate.run_covapie_specialized_covalent_database_source_acquisition_design_gate_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], gate.PRECONDITION_COLUMNS)
    write_csv(result["source_registry_rows"], paths["source_registry"], gate.SOURCE_REGISTRY_COLUMNS)
    write_csv(result["field_availability_rows"], paths["field_availability"], gate.FIELD_AVAILABILITY_COLUMNS)
    write_csv(result["schema_mapping_rows"], paths["schema_mapping"], gate.SCHEMA_MAPPING_COLUMNS)
    write_csv(result["event_identity_rows"], paths["event_identity"], gate.EVENT_IDENTITY_KEY_COLUMNS)
    write_csv(result["acquisition_method_rows"], paths["acquisition_method"], gate.ACQUISITION_METHOD_COLUMNS)
    write_csv(result["download_boundary_rows"], paths["download_boundary"], gate.DOWNLOAD_BOUNDARY_COLUMNS)
    write_csv(result["provenance_license_rows"], paths["provenance_license"], gate.PROVENANCE_LICENSE_COLUMNS)
    write_csv(result["manual_review_rows"], paths["manual_review"], gate.MANUAL_REVIEW_COLUMNS)
    write_csv(result["candidate_selection_rows"], paths["candidate_selection"], gate.CANDIDATE_SELECTION_COLUMNS)
    write_csv(result["failure_taxonomy_rows"], paths["failure_taxonomy"], gate.FAILURE_TAXONOMY_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], gate.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], gate.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], gate.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], gate.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], gate.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_specialized_covalent_database_source_acquisition_design_gate_v0_passed")
    for key in [
        "source_registry_contract_row_count",
        "external_source_verified_current_step",
        "external_network_access_used",
        "external_metadata_downloaded",
        "raw_structure_downloaded",
        "covapie_covalent_db_field_availability_contract_row_count",
        "covapie_covalent_db_allowlist_schema_mapping_contract_row_count",
        "covapie_covalent_event_identity_key_contract_row_count",
        "minimal_event_key",
        "preferred_event_key",
        "one_row_one_covalent_event",
        "covapie_covalent_db_acquisition_method_contract_row_count",
        "covapie_covalent_db_download_boundary_contract_row_count",
        "covapie_covalent_db_provenance_license_contract_row_count",
        "covapie_covalent_db_manual_review_contract_row_count",
        "covapie_covalent_db_candidate_selection_contract_row_count",
        "covapie_covalent_db_failure_taxonomy_contract_row_count",
        "covapie_covalent_db_execution_boundary_audit_row_count",
        "covapie_covalent_db_git_safety_audit_row_count",
        "covapie_covalent_db_mask_scope_audit_row_count",
        "covapie_covalent_db_feature_semantics_audit_row_count",
        "covapie_covalent_db_leakage_split_audit_row_count",
        "network_access_used",
        "raw_data_read",
        "candidate_metadata_materialized",
        "candidate_allowlist_materialized",
        "ready_for_covapie_external_metadata_index_download_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

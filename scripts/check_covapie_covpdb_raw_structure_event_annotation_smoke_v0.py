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

from covalent_ext import covapie_covpdb_raw_structure_event_annotation_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE CovPDB Raw Structure Event Annotation Smoke v0 Summary

This is a controlled first-five raw structure event annotation smoke.
It downloads only the first five allowed RCSB raw structure files from the Step 13AU contract.
It prefers mmCIF and uses PDB only as fallback if mmCIF download fails.
Raw files are stored under `{manifest["raw_storage_root"]}` and must remain untracked.
It does not download ligand SDF, archives, validation reports, assemblies, or any non-contracted URL.
It does not copy raw files or full coordinate tables into `data/derived`.
It does not use RDKit/Bio.PDB/gemmi/gzip/torch.
It does not materialize candidate metadata or allowlists.
It does not train.

attempted_structure_count: `{manifest["attempted_structure_count"]}`
raw_structure_download_succeeded_count: `{manifest["raw_structure_download_succeeded_count"]}`
raw_structure_download_failed_count: `{manifest["raw_structure_download_failed_count"]}`
selected_raw_formats: `{manifest["selected_raw_formats"]}`
struct_conn_loop_found_count: `{manifest["struct_conn_loop_found_count"]}`
atom_site_loop_found_count: `{manifest["atom_site_loop_found_count"]}`
pdb_link_record_found_count: `{manifest["pdb_link_record_found_count"]}`
pdb_conect_record_found_count: `{manifest["pdb_conect_record_found_count"]}`
raw_resolves_preferred_event_key_count: `{manifest["raw_resolves_preferred_event_key_count"]}`
raw_resolves_minimal_event_key_count: `{manifest["raw_resolves_minimal_event_key_count"]}`
raw_partial_event_key_only_count: `{manifest["raw_partial_event_key_only_count"]}`
raw_no_connectivity_records_found_count: `{manifest["raw_no_connectivity_records_found_count"]}`
raw_multiple_candidate_links_count: `{manifest["raw_multiple_candidate_links_count"]}`
raw_ligand_het_code_not_found_count: `{manifest["raw_ligand_het_code_not_found_count"]}`
raw_protein_partner_not_found_count: `{manifest["raw_protein_partner_not_found_count"]}`
raw_parse_failed_count: `{manifest["raw_parse_failed_count"]}`
future_candidate_metadata_possible_count: `{manifest["future_candidate_metadata_possible_count"]}`
future_automatic_allowlist_possible_count: `{manifest["future_automatic_allowlist_possible_count"]}`
candidate_metadata_materialized: `{manifest["candidate_metadata_materialized"]}`
candidate_allowlist_materialized: `{manifest["candidate_allowlist_materialized"]}`
ready_for_covapie_covpdb_raw_structure_event_annotation_qa_gate: `{manifest["ready_for_covapie_covpdb_raw_structure_event_annotation_qa_gate"]}`
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
    result = smoke.run_covapie_covpdb_raw_structure_event_annotation_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["download_plan_rows"], smoke.DOWNLOAD_PLAN_CSV, smoke.DOWNLOAD_PLAN_COLUMNS)
    write_csv(result["download_audit_rows"], smoke.DOWNLOAD_AUDIT_CSV, smoke.DOWNLOAD_AUDIT_COLUMNS)
    write_csv(result["storage_rows"], smoke.STORAGE_SAFETY_AUDIT_CSV, smoke.STORAGE_COLUMNS)
    write_csv(result["format_rows"], smoke.FORMAT_INVENTORY_CSV, smoke.FORMAT_COLUMNS)
    write_csv(result["struct_conn_rows"], smoke.MMCIF_STRUCT_CONN_INVENTORY_CSV, smoke.STRUCT_CONN_COLUMNS)
    write_csv(result["atom_site_rows"], smoke.MMCIF_ATOM_SITE_VALIDATION_AUDIT_CSV, smoke.ATOM_SITE_COLUMNS)
    write_csv(result["pdb_inventory_rows"], smoke.PDB_LINK_CONECT_INVENTORY_CSV, smoke.PDB_LINK_COLUMNS)
    write_csv(result["candidate_rows"], smoke.EVENT_CANDIDATE_ANNOTATION_CSV, smoke.EVENT_CANDIDATE_COLUMNS)
    write_csv(result["resolution_rows"], smoke.EVENT_KEY_RESOLUTION_AUDIT_CSV, smoke.RESOLUTION_COLUMNS)
    write_csv(result["failure_rows"], smoke.OBSERVED_FAILURE_TAXONOMY_CSV, smoke.FAILURE_COLUMNS)
    write_csv(result["materialization_rows"], smoke.MATERIALIZATION_BOUNDARY_AUDIT_CSV, smoke.MATERIALIZATION_COLUMNS)
    write_csv(result["execution_rows"], smoke.EXECUTION_BOUNDARY_AUDIT_CSV, smoke.EXECUTION_COLUMNS)
    write_csv(result["git_safety_rows"], smoke.GIT_SAFETY_AUDIT_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], smoke.MASK_SCOPE_AUDIT_CSV, smoke.MASK_COLUMNS)
    write_csv(result["feature_rows"], smoke.FEATURE_SEMANTICS_AUDIT_CSV, smoke.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], smoke.LEAKAGE_SPLIT_AUDIT_CSV, smoke.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), smoke.REPORT_CSV, smoke.REPORT_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_covpdb_raw_structure_event_annotation_smoke_v0_passed")
    else:
        print("covapie_covpdb_raw_structure_event_annotation_smoke_v0_blocked")
    for key in [
        "attempted_structure_count",
        "raw_structure_download_succeeded_count",
        "raw_structure_download_failed_count",
        "selected_raw_formats",
        "struct_conn_loop_found_count",
        "atom_site_loop_found_count",
        "pdb_link_record_found_count",
        "pdb_conect_record_found_count",
        "raw_resolves_preferred_event_key_count",
        "raw_resolves_minimal_event_key_count",
        "raw_partial_event_key_only_count",
        "raw_no_connectivity_records_found_count",
        "raw_multiple_candidate_links_count",
        "raw_ligand_het_code_not_found_count",
        "raw_protein_partner_not_found_count",
        "raw_parse_failed_count",
        "future_candidate_metadata_possible_count",
        "future_automatic_allowlist_possible_count",
        "ready_for_covapie_covpdb_raw_structure_event_annotation_qa_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())


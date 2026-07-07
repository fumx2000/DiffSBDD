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

from covalent_ext import covapie_covpdb_raw_structure_event_annotation_design_gate as gate  # noqa: E402


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
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE CovPDB Raw Structure Event Annotation Design Gate v0 Summary

This is a design gate for a future controlled raw structure event annotation smoke.
It does not access the network.
It does not download raw structures.
It does not read raw PDB/mmCIF/SDF/gzip content.
It does not create `.pdb`, `.cif`, or `.mmcif` files.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

The next smoke is designed to use the first five committed CovPDB metadata rows only.
Preferred raw format is mmCIF, using RCSB `{{pdb_id}}.cif` URLs.
PDB format is a fallback, using RCSB `{{pdb_id}}.pdb` URLs.
Raw files must be written only under `{manifest["raw_storage_root"]}` and must remain untracked.

first5_pdb_ids: `{manifest["first5_pdb_ids"]}`
first5_ligand_het_codes: `{manifest["first5_ligand_het_codes"]}`
preferred_raw_format: `{manifest["preferred_raw_format"]}`
fallback_raw_format: `{manifest["fallback_raw_format"]}`
raw_download_executed: `{manifest["raw_download_executed"]}`
raw_file_created: `{manifest["raw_file_created"]}`
ready_for_covapie_covpdb_raw_structure_event_annotation_smoke: `{manifest["ready_for_covapie_covpdb_raw_structure_event_annotation_smoke"]}`
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
    result = gate.run_covapie_covpdb_raw_structure_event_annotation_design_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["download_scope_rows"], gate.DOWNLOAD_SCOPE_CONTRACT_CSV, gate.DOWNLOAD_SCOPE_COLUMNS)
    write_csv(result["source_url_rows"], gate.SOURCE_URL_CONTRACT_CSV, gate.SOURCE_URL_COLUMNS)
    write_csv(result["storage_rows"], gate.STORAGE_CONTRACT_CSV, gate.STORAGE_COLUMNS)
    write_csv(result["parser_priority_rows"], gate.PARSER_PRIORITY_CONTRACT_CSV, gate.PARSER_PRIORITY_COLUMNS)
    write_csv(result["mmcif_rows"], gate.MMCIF_MAPPING_CONTRACT_CSV, gate.MAPPING_COLUMNS)
    write_csv(result["pdb_rows"], gate.PDB_LINK_MAPPING_CONTRACT_CSV, gate.MAPPING_COLUMNS)
    write_csv(result["event_key_rows"], gate.EVENT_KEY_RESOLUTION_CONTRACT_CSV, gate.EVENT_KEY_COLUMNS)
    write_csv(result["failure_rows"], gate.FAILURE_TAXONOMY_CSV, gate.FAILURE_COLUMNS)
    write_csv(result["materialization_rows"], gate.MATERIALIZATION_BOUNDARY_AUDIT_CSV, gate.MATERIALIZATION_COLUMNS)
    write_csv(result["execution_rows"], gate.EXECUTION_BOUNDARY_AUDIT_CSV, gate.EXECUTION_COLUMNS)
    write_csv(result["git_safety_rows"], gate.GIT_SAFETY_AUDIT_CSV, gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], gate.MASK_SCOPE_AUDIT_CSV, gate.MASK_COLUMNS)
    write_csv(result["feature_rows"], gate.FEATURE_SEMANTICS_AUDIT_CSV, gate.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], gate.LEAKAGE_SPLIT_AUDIT_CSV, gate.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), gate.REPORT_CSV, gate.REPORT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_covpdb_raw_structure_event_annotation_design_gate_v0_passed")
    else:
        print("covapie_covpdb_raw_structure_event_annotation_design_gate_v0_blocked")
    for key in [
        "first5_pdb_ids",
        "first5_ligand_het_codes",
        "preferred_raw_format",
        "fallback_raw_format",
        "raw_download_executed",
        "raw_file_created",
        "ready_for_covapie_covpdb_raw_structure_event_annotation_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

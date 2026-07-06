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

from covalent_ext import covapie_batch_scale_data_preparation_design_gate as gate  # noqa: E402


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
    blockers = _list_text(manifest["blocking_reasons"])
    rows: list[dict[str, str]] = []
    for section, evidence in result["report_sections"].items():
        rows.append(
            {
                "stage": gate.STAGE,
                "previous_stage": gate.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "CovaPIE batch-scale data preparation design gate passed"
                if manifest["all_checks_passed"]
                else "CovaPIE batch-scale data preparation design gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Batch-Scale Data Preparation Design Gate v0 Summary

This is a CovaPIE batch-scale data preparation design gate.
It does not run batch-scale preparation.
It designs future 10-30 sample smoke only.
It preserves current CYS/SG-only scope.
It preserves five canonical mask tasks including scaffold_only/B3.
It defines candidate selection, sharding, failure taxonomy, provenance, output artifact, git safety, feature semantics, leakage/split placeholders, and execution boundary contracts.
It does not read raw data, SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize new samples, write sample index, split assignment, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
It keeps feature semantics audit and leakage/split design required before training.
It allows CovaPIE batch-scale data preparation smoke next, not training.

batch_scale_initial_min_candidate_count: `{manifest["batch_scale_initial_min_candidate_count"]}`
batch_scale_initial_max_candidate_count: `{manifest["batch_scale_initial_max_candidate_count"]}`
batch_scale_initial_shard_size: `{manifest["batch_scale_initial_shard_size"]}`
current_reactive_residue_scope: `{manifest["current_reactive_residue_scope"]}`
covapie_batch_scale_precondition_audit_row_count: `{manifest["covapie_batch_scale_precondition_audit_row_count"]}`
covapie_batch_scale_input_source_contract_row_count: `{manifest["covapie_batch_scale_input_source_contract_row_count"]}`
covapie_batch_scale_candidate_selection_contract_row_count: `{manifest["covapie_batch_scale_candidate_selection_contract_row_count"]}`
covapie_batch_scale_sharding_contract_row_count: `{manifest["covapie_batch_scale_sharding_contract_row_count"]}`
covapie_batch_scale_failure_taxonomy_contract_row_count: `{manifest["covapie_batch_scale_failure_taxonomy_contract_row_count"]}`
covapie_batch_scale_provenance_contract_row_count: `{manifest["covapie_batch_scale_provenance_contract_row_count"]}`
covapie_batch_scale_output_artifact_contract_row_count: `{manifest["covapie_batch_scale_output_artifact_contract_row_count"]}`
covapie_batch_scale_git_safety_contract_row_count: `{manifest["covapie_batch_scale_git_safety_contract_row_count"]}`
covapie_batch_scale_mask_scope_contract_row_count: `{manifest["covapie_batch_scale_mask_scope_contract_row_count"]}`
covapie_batch_scale_feature_semantics_boundary_row_count: `{manifest["covapie_batch_scale_feature_semantics_boundary_row_count"]}`
covapie_batch_scale_leakage_split_placeholder_contract_row_count: `{manifest["covapie_batch_scale_leakage_split_placeholder_contract_row_count"]}`
covapie_batch_scale_execution_boundary_contract_row_count: `{manifest["covapie_batch_scale_execution_boundary_contract_row_count"]}`
batch_scale_design_gate_passed: `{manifest["batch_scale_design_gate_passed"]}`
ready_for_covapie_batch_scale_data_preparation_smoke: `{manifest["ready_for_covapie_batch_scale_data_preparation_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_batch_scale_data_preparation_design_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_AUDIT_COLUMNS)
    write_csv(result["input_source_rows"], gate.INPUT_SOURCE_CONTRACT_CSV, gate.INPUT_SOURCE_COLUMNS)
    write_csv(result["candidate_selection_rows"], gate.CANDIDATE_SELECTION_CONTRACT_CSV, gate.CANDIDATE_SELECTION_COLUMNS)
    write_csv(result["sharding_rows"], gate.SHARDING_CONTRACT_CSV, gate.SHARDING_COLUMNS)
    write_csv(result["failure_taxonomy_rows"], gate.FAILURE_TAXONOMY_CONTRACT_CSV, gate.FAILURE_TAXONOMY_COLUMNS)
    write_csv(result["provenance_rows"], gate.PROVENANCE_CONTRACT_CSV, gate.PROVENANCE_COLUMNS)
    write_csv(result["output_artifact_rows"], gate.OUTPUT_ARTIFACT_CONTRACT_CSV, gate.OUTPUT_ARTIFACT_COLUMNS)
    write_csv(result["git_safety_rows"], gate.GIT_SAFETY_CONTRACT_CSV, gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_scope_rows"], gate.MASK_SCOPE_CONTRACT_CSV, gate.MASK_SCOPE_COLUMNS)
    write_csv(result["feature_semantics_rows"], gate.FEATURE_SEMANTICS_BOUNDARY_CSV, gate.FEATURE_SEMANTICS_COLUMNS)
    write_csv(result["leakage_split_rows"], gate.LEAKAGE_SPLIT_PLACEHOLDER_CONTRACT_CSV, gate.LEAKAGE_SPLIT_COLUMNS)
    write_csv(result["execution_boundary_rows"], gate.EXECUTION_BOUNDARY_CONTRACT_CSV, gate.EXECUTION_BOUNDARY_COLUMNS)
    write_csv(build_report_rows(result), gate.REPORT_CSV, gate.REPORT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print(
        "covapie_batch_scale_data_preparation_design_gate_v0_passed"
        if manifest["all_checks_passed"]
        else "covapie_batch_scale_data_preparation_design_gate_v0_blocked"
    )
    for key in [
        "covapie_batch_scale_precondition_audit_row_count",
        "covapie_batch_scale_input_source_contract_row_count",
        "covapie_batch_scale_candidate_selection_contract_row_count",
        "covapie_batch_scale_sharding_contract_row_count",
        "covapie_batch_scale_failure_taxonomy_contract_row_count",
        "covapie_batch_scale_provenance_contract_row_count",
        "covapie_batch_scale_output_artifact_contract_row_count",
        "covapie_batch_scale_git_safety_contract_row_count",
        "covapie_batch_scale_mask_scope_contract_row_count",
        "covapie_batch_scale_feature_semantics_boundary_row_count",
        "covapie_batch_scale_leakage_split_placeholder_contract_row_count",
        "covapie_batch_scale_execution_boundary_contract_row_count",
        "batch_scale_initial_min_candidate_count",
        "batch_scale_initial_max_candidate_count",
        "batch_scale_initial_shard_size",
        "current_reactive_residue_scope",
        "batch_scale_design_gate_passed",
        "ready_for_covapie_batch_scale_data_preparation_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

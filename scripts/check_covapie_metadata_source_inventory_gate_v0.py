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

from covalent_ext import covapie_metadata_source_inventory_gate as gate  # noqa: E402


OUTPUT_PATHS = [
    gate.PRECONDITION_AUDIT_CSV,
    gate.SCANNED_ARTIFACT_AUDIT_CSV,
    gate.FORBIDDEN_ARTIFACT_AUDIT_CSV,
    gate.FIELD_COVERAGE_MATRIX_CSV,
    gate.GAP_AUDIT_CSV,
    gate.CANDIDATE_COUNT_ESTIMATE_CSV,
    gate.EXECUTION_BOUNDARY_AUDIT_CSV,
    gate.GIT_SAFETY_AUDIT_CSV,
    gate.MASK_SCOPE_AUDIT_CSV,
    gate.FEATURE_SEMANTICS_AUDIT_CSV,
    gate.LEAKAGE_SPLIT_AUDIT_CSV,
    gate.REPORT_CSV,
    gate.MANIFEST_JSON,
    gate.SUMMARY_MD,
]


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


def _read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _existing_outputs_available() -> bool:
    return all(path.is_file() for path in OUTPUT_PATHS)


def _validate_existing_outputs_read_only() -> dict[str, Any]:
    manifest = json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))
    expected_counts = {
        "covapie_metadata_inventory_precondition_audit_row_count": (gate.PRECONDITION_AUDIT_CSV, 7),
        "covapie_metadata_inventory_scanned_artifact_audit_row_count": (
            gate.SCANNED_ARTIFACT_AUDIT_CSV,
            manifest["scanned_artifact_count"],
        ),
        "covapie_metadata_inventory_forbidden_artifact_audit_row_count": (gate.FORBIDDEN_ARTIFACT_AUDIT_CSV, 15),
        "covapie_allowlist_field_source_coverage_matrix_row_count": (gate.FIELD_COVERAGE_MATRIX_CSV, 15),
        "covapie_candidate_metadata_assembly_gap_audit_row_count": (gate.GAP_AUDIT_CSV, 15),
        "covapie_metadata_inventory_candidate_count_estimate_row_count": (gate.CANDIDATE_COUNT_ESTIMATE_CSV, 1),
        "covapie_metadata_inventory_execution_boundary_audit_row_count": (gate.EXECUTION_BOUNDARY_AUDIT_CSV, 24),
        "covapie_metadata_inventory_git_safety_audit_row_count": (gate.GIT_SAFETY_AUDIT_CSV, 10),
        "covapie_metadata_inventory_mask_scope_audit_row_count": (gate.MASK_SCOPE_AUDIT_CSV, 5),
        "covapie_metadata_inventory_feature_semantics_audit_row_count": (gate.FEATURE_SEMANTICS_AUDIT_CSV, 12),
        "covapie_metadata_inventory_leakage_split_audit_row_count": (gate.LEAKAGE_SPLIT_AUDIT_CSV, 12),
    }
    blockers: list[str] = []
    for key, (path, expected) in expected_counts.items():
        rows = _read_csv_rows(path)
        if manifest.get(key) != len(rows) or len(rows) != expected:
            blockers.append(f"{key}_mismatch")
    if manifest.get("stage") != gate.STAGE:
        blockers.append("stage_mismatch")
    if manifest.get("previous_stage") != gate.PREVIOUS_STAGE:
        blockers.append("previous_stage_mismatch")
    if manifest.get("project_name") != "CovaPIE":
        blockers.append("project_name_mismatch")
    if manifest.get("all_checks_passed") is not True:
        blockers.append("all_checks_passed_not_true")
    if manifest.get("blocking_reasons") != []:
        blockers.append("blocking_reasons_not_empty")
    if manifest.get("canonical_mask_task_names") != gate.CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names_mismatch")
    if manifest.get("canonical_mask_task_aliases") != gate.CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases_mismatch")
    for key in [
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "torch_imported",
        "torch_tensor_created",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
    ]:
        if manifest.get(key) is not False:
            blockers.append(f"{key}_not_false")
    if blockers:
        raise ValueError("Existing Step 13AI outputs failed read-only validation: " + ";".join(blockers))
    return manifest


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
    text = f"""# CovaPIE Metadata Source Inventory Gate v0 Summary

This is CovaPIE metadata source inventory gate.
It only scans existing `data/derived/covalent_small` CSV/JSON/MD artifacts.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
It reports coverage of the 15 required allowlist columns.
It reports whether existing derived artifacts are enough for 10-30 candidate materialization.
It keeps feature semantics audit and leakage/split design required before training.

scanned_artifact_count: `{manifest["scanned_artifact_count"]}`
possible_metadata_source_artifact_count: `{manifest["possible_metadata_source_artifact_count"]}`
directly_available_column_count: `{manifest["directly_available_column_count"]}`
derivable_column_count: `{manifest["derivable_column_count"]}`
missing_required_column_count: `{manifest["missing_required_column_count"]}`
fully_covered_allowlist_candidate_count_estimate: `{manifest["fully_covered_allowlist_candidate_count_estimate"]}`
enough_for_10_to_30_materialization: `{manifest["enough_for_10_to_30_materialization"]}`
ready_for_covapie_candidate_metadata_assembly_design_gate: `{manifest["ready_for_covapie_candidate_metadata_assembly_design_gate"]}`
ready_for_user_or_pipeline_metadata: `{manifest["ready_for_user_or_pipeline_metadata"]}`
ready_for_covapie_batch_scale_raw_read_smoke: `{manifest["ready_for_covapie_batch_scale_raw_read_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
feature_semantics_audit_required_before_training: `{manifest["feature_semantics_audit_required_before_training"]}`
leakage_split_design_required_before_training: `{manifest["leakage_split_design_required_before_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def print_manifest_summary(manifest: dict[str, Any]) -> None:
    print("covapie_metadata_source_inventory_gate_v0_passed")
    for key in [
        "scanned_artifact_count",
        "possible_metadata_source_artifact_count",
        "directly_available_column_count",
        "derivable_column_count",
        "missing_required_column_count",
        "fully_covered_allowlist_candidate_count_estimate",
        "enough_for_10_to_30_materialization",
        "covapie_metadata_inventory_precondition_audit_row_count",
        "covapie_metadata_inventory_scanned_artifact_audit_row_count",
        "covapie_metadata_inventory_forbidden_artifact_audit_row_count",
        "covapie_allowlist_field_source_coverage_matrix_row_count",
        "covapie_candidate_metadata_assembly_gap_audit_row_count",
        "covapie_metadata_inventory_candidate_count_estimate_row_count",
        "covapie_metadata_inventory_execution_boundary_audit_row_count",
        "covapie_metadata_inventory_git_safety_audit_row_count",
        "covapie_metadata_inventory_mask_scope_audit_row_count",
        "covapie_metadata_inventory_feature_semantics_audit_row_count",
        "covapie_metadata_inventory_leakage_split_audit_row_count",
        "metadata_source_inventory_gate_passed",
        "ready_for_covapie_candidate_metadata_assembly_design_gate",
        "ready_for_user_or_pipeline_metadata",
        "ready_for_covapie_candidate_allowlist_materialization_smoke",
        "ready_for_covapie_batch_scale_raw_read_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")


def run() -> int:
    if _existing_outputs_available():
        manifest = _validate_existing_outputs_read_only()
        print_manifest_summary(manifest)
        return 0

    result = gate.run_covapie_metadata_source_inventory_gate_v0()
    paths = result["paths"]
    write_csv(result["precondition_rows"], paths["precondition"], gate.PRECONDITION_COLUMNS)
    write_csv(result["scanned_rows"], paths["scanned"], gate.SCANNED_COLUMNS)
    write_csv(result["forbidden_rows"], paths["forbidden"], gate.FORBIDDEN_COLUMNS)
    write_csv(result["coverage_rows"], paths["coverage"], gate.COVERAGE_COLUMNS)
    write_csv(result["gap_rows"], paths["gap"], gate.GAP_COLUMNS)
    write_csv(result["count_rows"], paths["count"], gate.COUNT_ESTIMATE_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], gate.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], gate.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], gate.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], gate.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], gate.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print_manifest_summary(manifest)
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

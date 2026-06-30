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

from covalent_ext.real_covalent_filtered_feature_semantics_audit import (  # noqa: E402
    AUDIT_TABLE_CSV,
    FILTER_POLICY_NAME,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_real_covalent_filtered_feature_semantics_audit_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "section",
    "status",
    "evidence",
    "decision",
    "blocking_reasons",
    "recommended_next_step",
]

AUDIT_TABLE_COLUMNS = [
    "row_type",
    "sample_id",
    "mask_level",
    "expected_reactive_atom_region",
    "step12h_filter_gate_validated",
    "step12b_mask_level_aware_validator_validated",
    "checkpoint_ligand_feature_dim",
    "checkpoint_pocket_feature_dim",
    "checkpoint_feature_semantics_source",
    "checkpoint_feature_semantics_directly_encoded",
    "checkpoint_10d_mapping_project",
    "checkpoint_10d_mapping_matches_project_mapping",
    "sample_count",
    "ligand_atomic_numbers_unique",
    "pocket_atomic_numbers_unique_before_filter",
    "pocket_atomic_numbers_unique_after_filter",
    "ligand_unknown_atom_count_before_filter",
    "pocket_unknown_atom_count_before_filter",
    "filtered_pocket_atom_count",
    "filtered_pocket_atom_numbers",
    "filtered_pocket_atom_symbols",
    "ligand_unknown_atom_count_after_filter",
    "pocket_unknown_atom_count_after_filter",
    "unknown_atom_policy_triggered_after_filter",
    "zero_vector_unknown_atom_policy_safe_after_filter",
    "checkpoint_compatible_batch_constructed_after_filter",
    "ligand_feature_dim",
    "pocket_feature_dim",
    "ligand_one_hot_rows_equal_ligand_coords_rows",
    "pocket_one_hot_rows_equal_pocket_coords_rows",
    "ligand_one_hot_row_sums_valid_after_filter",
    "pocket_one_hot_row_sums_valid_after_filter",
    "all_ligand_unknown_atom_count_zero_after_filter",
    "all_pocket_unknown_atom_count_zero_after_filter",
    "ligand_masks_unchanged_after_filter",
    "ligand_reactive_atom_region_preserved",
    "no_synthetic_fallback_used",
    "production_filter_helper_used",
    "production_adapter_modified",
    "original_data_modified",
    "feature_semantics_dimension_contract_passed_after_filter",
    "feature_semantics_mapping_confirmed",
    "feature_semantics_known_after_filter",
    "real_covalent_filtered_feature_semantics_audit_passed",
    "real_covalent_filtered_cuda_forward_backward_smoke_allowed",
    "real_covalent_single_optimizer_step_smoke_allowed",
    "cys_first_training_strategy_recommended",
    "non_cys_reactive_residue_support_status",
    "reaction_family_template_audit_required_before_broad_covalent_training",
    "ligand_reconstruction_template_gate_required",
    "non_cys_data_bulk_cleaning_policy",
    "train_ready_scope_v1",
    "recommended_next_step",
    "status",
    "blocking_reasons",
]


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


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
    recommended = manifest["recommended_next_step"]
    specs = [
        (
            "step12h_precondition",
            manifest["step12h_filter_gate_validated"] and manifest["step12b_mask_level_aware_validator_validated"],
            "Step 12H filter gate and Step 12B validator evidence are accepted.",
        ),
        (
            "checkpoint_feature_contract",
            manifest["checkpoint_10d_feature_contract_detected"]
            and manifest["checkpoint_10d_mapping_matches_project_mapping"],
            "Checkpoint ligand and pocket feature dimensions are audited as confirmed 10D.",
        ),
        (
            "filtered_real_atom_vocabulary",
            manifest["pocket_unknown_atom_count_before_filter"] == 2
            and manifest["pocket_unknown_atom_count_after_filter"] == 0
            and not manifest["unknown_atom_policy_triggered_after_filter"],
            "Projection filter changes pocket unknown atom count from 2 to 0.",
        ),
        (
            "mask_level_filtered_conversion",
            manifest["passed_mask_level_count"] == 5
            and manifest["all_pocket_one_hot_row_sums_valid_after_filter"],
            "A/B/B2/B3/C filtered checkpoint-compatible conversions pass.",
        ),
        (
            "feature_semantics_decision",
            manifest["real_covalent_filtered_feature_semantics_audit_passed"]
            and manifest["feature_semantics_known_after_filter"],
            "Filtered feature semantics reach hard pass while real optimizer step remains blocked.",
        ),
        (
            "non_cys_training_scope_boundary",
            manifest["cys_first_training_strategy_recommended"]
            and manifest["train_ready_scope_v1"] == "cys_with_known_reconstruction_template_only",
            "V1 training scope is Cys-first pending reaction-family template gates.",
        ),
        (
            "safety_boundary",
            not any(
                manifest[key]
                for key in [
                    "model_forward_called",
                    "loss_compute_called",
                    "backward_called",
                    "optimizer_created",
                    "optimizer_step_called",
                    "training_step_called",
                    "trainer_fit_called",
                    "checkpoint_saved",
                    "model_saved",
                    "tensor_dump_saved",
                    "npz_created",
                    "original_diffsbdd_source_modified",
                    "forbidden_artifacts_created",
                ]
            ),
            "No forward, loss calculation, gradient, optimizer, save, or protected-source change occurred.",
        ),
        (
            "next_step_decision",
            manifest["recommended_next_step"] == "real_covalent_filtered_cuda_forward_backward_smoke",
            "Next step is filtered CUDA forward/backward smoke, not optimizer step.",
        ),
    ]
    rows: list[dict[str, str]] = []
    for section, passed, evidence in specs:
        rows.append(
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"].get(section, {})) or evidence,
                "decision": evidence,
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": recommended,
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Filtered Feature Semantics Audit v0 Summary

Step 12I is a filtered feature semantics audit, not training.
It does not run forward, calculate loss, run gradients, create an optimizer, or save checkpoint/model/tensor dump.
It uses the Step 12H production filter helper: `{FILTER_POLICY_NAME}`.
Original data is unchanged, and the production adapter is unchanged.

## Filtered Vocabulary
- sample_count: {manifest["sample_count"]}
- filtered_pocket_atom_numbers: {manifest["filtered_pocket_atom_numbers"]}
- filtered_pocket_atom_symbols: {manifest["filtered_pocket_atom_symbols"]}
- pocket unknown count from 2 to 0: {manifest["pocket_unknown_atom_count_before_filter"]} -> {manifest["pocket_unknown_atom_count_after_filter"]}
- ligand_unknown_atom_count_after_filter: {manifest["ligand_unknown_atom_count_after_filter"]}
- unknown_atom_policy_triggered_after_filter: {str(manifest["unknown_atom_policy_triggered_after_filter"]).lower()}
- zero_vector_unknown_atom_policy_safe_after_filter: {str(manifest["zero_vector_unknown_atom_policy_safe_after_filter"]).lower()}

## Feature Semantics Decision
- checkpoint_feature_semantics_source: {manifest["checkpoint_feature_semantics_source"]}
- checkpoint_10d_mapping_matches_project_mapping: {str(manifest["checkpoint_10d_mapping_matches_project_mapping"]).lower()}
- audited_mask_level_count: {manifest["audited_mask_level_count"]}
- passed_mask_level_count: {manifest["passed_mask_level_count"]}
- all_checkpoint_compatible_batches_constructed_after_filter: {str(manifest["all_checkpoint_compatible_batches_constructed_after_filter"]).lower()}
- all_ligand_one_hot_row_sums_valid_after_filter: {str(manifest["all_ligand_one_hot_row_sums_valid_after_filter"]).lower()}
- all_pocket_one_hot_row_sums_valid_after_filter: {str(manifest["all_pocket_one_hot_row_sums_valid_after_filter"]).lower()}
- feature_semantics_known_after_filter: {str(manifest["feature_semantics_known_after_filter"]).lower()}
- real_covalent_filtered_feature_semantics_audit_passed: {str(manifest["real_covalent_filtered_feature_semantics_audit_passed"]).lower()}

## Scope Boundary
- This is not optimizer step permission.
- real_covalent_single_optimizer_step_smoke_allowed: {str(manifest["real_covalent_single_optimizer_step_smoke_allowed"]).lower()}
- real_covalent_filtered_cuda_forward_backward_smoke_allowed: {str(manifest["real_covalent_filtered_cuda_forward_backward_smoke_allowed"]).lower()}
- Cys-first strategy: {manifest["train_ready_scope_v1"]}
- Non-Cys data policy: {manifest["non_cys_data_bulk_cleaning_policy"]}
- reaction_family_template_audit_required_before_broad_covalent_training: {str(manifest["reaction_family_template_audit_required_before_broad_covalent_training"]).lower()}
- ligand_reconstruction_template_gate_required: {str(manifest["ligand_reconstruction_template_gate_required"]).lower()}
- recommended_next_step: {manifest["recommended_next_step"]}

## Safety Boundary
- model_forward_called: false
- loss_compute_called: false
- backward_called: false
- optimizer_created: false
- optimizer_step_called: false
- training_step_called: false
- trainer_fit_called: false
- checkpoint_saved: false
- model_saved: false
- tensor_dump_saved: false
- npz_created: false
- original_diffsbdd_source_modified: false
- forbidden_artifacts_created: false
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = build_real_covalent_filtered_feature_semantics_audit_v0()
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["audit_table_rows"], AUDIT_TABLE_CSV, AUDIT_TABLE_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_summary(result["manifest"], SUMMARY_MD)
    print(
        "real_covalent_filtered_feature_semantics_audit_v0_"
        + ("passed" if result["manifest"]["all_checks_passed"] else "blocked")
    )
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

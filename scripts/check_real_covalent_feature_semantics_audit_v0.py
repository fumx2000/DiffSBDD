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

from covalent_ext.real_covalent_feature_semantics_audit import (  # noqa: E402
    AUDIT_TABLE_CSV,
    CANONICAL_MASK_LEVELS,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_real_covalent_feature_semantics_audit_v0,
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
    "mask_level",
    "expected_reactive_atom_region",
    "checkpoint_ligand_feature_dim",
    "checkpoint_pocket_feature_dim",
    "checkpoint_feature_semantics_source",
    "checkpoint_feature_semantics_directly_encoded",
    "checkpoint_10d_mapping_project",
    "checkpoint_10d_mapping_matches_project_mapping",
    "sample_count",
    "ligand_atomic_numbers_unique",
    "protein_atomic_numbers_unique",
    "ligand_unknown_atom_count",
    "protein_unknown_atom_count",
    "unknown_atom_policy_triggered",
    "zero_vector_unknown_atom_policy_safe",
    "checkpoint_compatible_batch_constructed",
    "ligand_feature_dim",
    "pocket_feature_dim",
    "ligand_one_hot_rows_equal_ligand_coords_rows",
    "pocket_one_hot_rows_equal_pocket_coords_rows",
    "ligand_one_hot_row_sums_valid",
    "pocket_one_hot_row_sums_valid",
    "pocket_unknown_atom_count",
    "no_synthetic_fallback_used",
    "feature_semantics_dimension_contract_passed",
    "feature_semantics_mapping_confirmed",
    "feature_semantics_known_after_audit",
    "real_covalent_single_optimizer_step_smoke_allowed",
    "recommended_next_step",
    "status",
    "blocking_reasons",
]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


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
    sections = result["report_sections"]
    blockers = _list_text(manifest["blocking_reasons"])
    recommended = manifest["recommended_next_step"]
    specs = [
        (
            "step12e_precondition",
            manifest["step12e_validated"] and manifest["step12b_mask_level_aware_validator_validated"],
            "Step 12E backward smoke and Step 12B validator evidence are accepted.",
        ),
        (
            "checkpoint_feature_contract",
            manifest["checkpoint_10d_feature_contract_detected"],
            "Checkpoint-compatible ligand and pocket feature dimensions are audited as 10D.",
        ),
        (
            "real_atom_vocabulary",
            manifest["all_ligand_atoms_in_checkpoint_10d_vocab"]
            and manifest["all_protein_atoms_in_checkpoint_10d_vocab"],
            "All real covalent ligand/protein atomic numbers are checked against the 10D vocabulary.",
        ),
        (
            "mask_level_conversion_semantics",
            manifest["all_checkpoint_compatible_batches_constructed"]
            and manifest["all_ligand_one_hot_row_sums_valid"]
            and manifest["all_pocket_one_hot_row_sums_valid"],
            "A/B/B2/B3/C checkpoint-compatible conversions have valid 10D one-hot rows.",
        ),
        (
            "unknown_atom_policy",
            not manifest["unknown_atom_policy_triggered"] and manifest["zero_vector_unknown_atom_policy_safe"],
            "The zero-vector unknown atom policy is confirmed not to trigger on real covalent samples.",
        ),
        (
            "feature_semantics_decision",
            manifest["real_covalent_feature_semantics_audit_passed"],
            "Feature semantics readiness is decided before any real optimizer step.",
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
            "No forward, loss, backward, optimizer, persistence, forbidden artifact, or protected source edit occurred.",
        ),
        (
            "next_step_decision",
            manifest["all_checks_passed"],
            "The next step follows the feature semantics audit decision.",
        ),
    ]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": section,
            "status": "passed" if passed else "blocked",
            "evidence": _json_text(sections[section]),
            "decision": decision,
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        }
        for section, passed, decision in specs
    ]


def write_summary(result: dict[str, Any], path: str | Path) -> None:
    manifest = result["manifest"]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Real Covalent Feature Semantics Audit v0 Summary",
        "",
        "Step 12F is a feature semantics audit, not training.",
        "It does not run model forward, compute loss, run backward, create an optimizer, or save checkpoint/model/tensor dump.",
        "This audit exists because Step 12D/12E recorded UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False during smoke validation.",
        "",
        "## Preconditions",
        f"- step12e_validated: {str(manifest['step12e_validated']).lower()}",
        f"- step12b_mask_level_aware_validator_validated: {str(manifest['step12b_mask_level_aware_validator_validated']).lower()}",
        f"- input_source: {manifest['input_source']}",
        f"- selected_sample_index: {manifest['selected_sample_index']}",
        f"- selected_artifact_is_real_covalent: {str(manifest['selected_artifact_is_real_covalent']).lower()}",
        f"- selected_artifact_is_synthetic_only: {str(manifest['selected_artifact_is_synthetic_only']).lower()}",
        "",
        "## Checkpoint 10D Feature Contract",
        f"- checkpoint_path: {manifest['checkpoint_path']}",
        f"- checkpoint_ligand_feature_dim: {manifest['checkpoint_ligand_feature_dim']}",
        f"- checkpoint_pocket_feature_dim: {manifest['checkpoint_pocket_feature_dim']}",
        f"- checkpoint_feature_semantics_source: {manifest['checkpoint_feature_semantics_source']}",
        f"- checkpoint_feature_semantics_directly_encoded: {str(manifest['checkpoint_feature_semantics_directly_encoded']).lower()}",
        f"- checkpoint_10d_mapping_matches_project_mapping: {str(manifest['checkpoint_10d_mapping_matches_project_mapping']).lower()}",
        f"- checkpoint_10d_mapping_project: {json.dumps(manifest['checkpoint_10d_mapping_project'], sort_keys=True)}",
        "",
        "## Real Atom Vocabulary",
        f"- sample_count: {manifest['sample_count']}",
        f"- sample_ids: {', '.join(manifest['sample_ids'])}",
        f"- ligand_atom_count_total: {manifest['ligand_atom_count_total']}",
        f"- protein_atom_count_total: {manifest['protein_atom_count_total']}",
        f"- ligand_atomic_numbers_unique: {manifest['ligand_atomic_numbers_unique']}",
        f"- protein_atomic_numbers_unique: {manifest['protein_atomic_numbers_unique']}",
        f"- ligand_unknown_atom_numbers: {manifest['ligand_unknown_atom_numbers']}",
        f"- protein_unknown_atom_numbers: {manifest['protein_unknown_atom_numbers']}",
        f"- ligand_unknown_atom_count: {manifest['ligand_unknown_atom_count']}",
        f"- protein_unknown_atom_count: {manifest['protein_unknown_atom_count']}",
        f"- unknown_atom_policy_triggered: {str(manifest['unknown_atom_policy_triggered']).lower()}",
        f"- zero_vector_unknown_atom_policy_safe: {str(manifest['zero_vector_unknown_atom_policy_safe']).lower()}",
        "",
        "## Conversion Semantics",
        f"- canonical_mask_levels: {', '.join(CANONICAL_MASK_LEVELS)}",
        f"- audited_mask_level_count: {manifest['audited_mask_level_count']}",
        f"- passed_mask_level_count: {manifest['passed_mask_level_count']}",
        f"- failed_mask_level_count: {manifest['failed_mask_level_count']}",
        f"- all_checkpoint_compatible_batches_constructed: {str(manifest['all_checkpoint_compatible_batches_constructed']).lower()}",
        f"- all_ligand_one_hot_row_sums_valid: {str(manifest['all_ligand_one_hot_row_sums_valid']).lower()}",
        f"- all_pocket_one_hot_row_sums_valid: {str(manifest['all_pocket_one_hot_row_sums_valid']).lower()}",
        f"- all_ligand_unknown_atom_count_zero: {str(manifest['all_ligand_unknown_atom_count_zero']).lower()}",
        f"- all_pocket_unknown_atom_count_zero: {str(manifest['all_pocket_unknown_atom_count_zero']).lower()}",
        f"- no_synthetic_fallback_used: {str(manifest['no_synthetic_fallback_used']).lower()}",
        "",
        "## Decision",
        f"- feature_semantics_dimension_contract_passed: {str(manifest['feature_semantics_dimension_contract_passed']).lower()}",
        f"- feature_semantics_mapping_confirmed: {str(manifest['feature_semantics_mapping_confirmed']).lower()}",
        f"- feature_semantics_known_after_audit: {str(manifest['feature_semantics_known_after_audit']).lower()}",
        "- feature_semantics_mapping_source_needs_confirmation: "
        f"{str(manifest['feature_semantics_mapping_source_needs_confirmation']).lower()}",
        f"- real_covalent_feature_semantics_audit_passed: {str(manifest['real_covalent_feature_semantics_audit_passed']).lower()}",
        f"- real_covalent_cuda_forward_backward_smoke_allowed: {str(manifest['real_covalent_cuda_forward_backward_smoke_allowed']).lower()}",
        "- real_covalent_single_optimizer_step_smoke_allowed: "
        f"{str(manifest['real_covalent_single_optimizer_step_smoke_allowed']).lower()}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
        "",
        "## Safety Boundary",
        f"- model_forward_called: {str(manifest['model_forward_called']).lower()}",
        f"- loss_compute_called: {str(manifest['loss_compute_called']).lower()}",
        f"- backward_called: {str(manifest['backward_called']).lower()}",
        f"- optimizer_created: {str(manifest['optimizer_created']).lower()}",
        f"- optimizer_step_called: {str(manifest['optimizer_step_called']).lower()}",
        f"- training_step_called: {str(manifest['training_step_called']).lower()}",
        f"- trainer_fit_called: {str(manifest['trainer_fit_called']).lower()}",
        f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
        f"- model_saved: {str(manifest['model_saved']).lower()}",
        f"- tensor_dump_saved: {str(manifest['tensor_dump_saved']).lower()}",
        f"- npz_created: {str(manifest['npz_created']).lower()}",
        f"- original_diffsbdd_source_modified: {str(manifest['original_diffsbdd_source_modified']).lower()}",
        f"- forbidden_artifacts_created: {str(manifest['forbidden_artifacts_created']).lower()}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    result = build_real_covalent_feature_semantics_audit_v0()
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["audit_table_rows"], AUDIT_TABLE_CSV, AUDIT_TABLE_COLUMNS)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_summary(result, SUMMARY_MD)
    if result["manifest"]["all_checks_passed"]:
        print("real_covalent_feature_semantics_audit_v0_passed")
        return 0
    print("real_covalent_feature_semantics_audit_v0_blocked")
    print(json.dumps(result["manifest"]["blocking_reasons"], indent=2, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(run())

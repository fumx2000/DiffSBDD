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

from covalent_ext.real_covalent_noncheckpoint_pocket_atom_filter_gate import (  # noqa: E402
    FILTER_POLICY_NAME,
    FILTER_TABLE_CSV,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_real_covalent_noncheckpoint_pocket_atom_filter_gate_v0,
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

FILTER_TABLE_COLUMNS = [
    "row_type",
    "sample_id",
    "sample_index",
    "mask_level",
    "expected_reactive_atom_region",
    "filter_policy_name",
    "allowed_filtered_atomic_numbers_for_this_gate",
    "allowed_filtered_atom_symbols_for_this_gate",
    "direct_ligand_contact_distance_a",
    "ligand_reactive_contact_distance_a",
    "production_filter_helper_created",
    "production_adapter_modified",
    "original_data_modified",
    "original_pocket_atom_count",
    "filtered_pocket_atom_count",
    "removed_pocket_atom_count",
    "removed_pocket_atom_numbers",
    "removed_pocket_atom_symbols",
    "removed_pocket_atom_indices",
    "removed_pocket_atom_min_ligand_distances",
    "removed_pocket_atom_ligand_reactive_distances",
    "ligand_atom_count",
    "ligand_atom_count_changed",
    "post_filter_pocket_unknown_atom_count",
    "post_filter_ligand_unknown_atom_count",
    "all_remaining_pocket_atoms_in_checkpoint_10d_vocab",
    "all_ligand_atoms_in_checkpoint_10d_vocab",
    "checkpoint_compatible_batch_constructed_after_filter",
    "ligand_feature_dim",
    "pocket_feature_dim",
    "ligand_one_hot_row_sums_valid_after_filter",
    "pocket_one_hot_row_sums_valid_after_filter",
    "ligand_unknown_atom_count_after_filter",
    "pocket_unknown_atom_count_after_filter",
    "filtered_pocket_atom_numbers",
    "filtered_pocket_atom_symbols",
    "no_synthetic_fallback_used",
    "ligand_masks_unchanged_after_filter",
    "ligand_reactive_atom_region_preserved",
    "non_cys_reactive_residue_support_status",
    "reaction_family_template_audit_required_before_broad_covalent_training",
    "ligand_reconstruction_template_gate_required",
    "real_covalent_noncheckpoint_pocket_atom_filter_gate_passed",
    "real_covalent_filtered_feature_semantics_audit_allowed",
    "real_covalent_single_optimizer_step_smoke_allowed",
    "recommended_next_step",
    "step12g_filter_policy_debug_validated",
    "step12b_mask_level_aware_validator_validated",
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
    sections = result["report_sections"]
    blockers = _list_text(manifest["blocking_reasons"])
    recommended = manifest["recommended_next_step"]
    specs = [
        (
            "step12g_precondition",
            manifest["step12g_filter_policy_debug_validated"] and manifest["step12b_mask_level_aware_validator_validated"],
            "Step 12G debug evidence and Step 12B validator behavior are accepted.",
        ),
        (
            "filter_policy_contract",
            manifest["production_filter_helper_created"] and not manifest["production_adapter_modified"],
            "A reusable projection-level pocket filter helper is defined without replacing existing adapters.",
        ),
        (
            "sample_filter_projection",
            manifest["post_filter_pocket_unknown_atom_count"] == 0
            and manifest["post_filter_ligand_unknown_atom_count"] == 0,
            "All real samples pass sample-level pocket filtering checks.",
        ),
        (
            "mask_level_filtered_conversion",
            manifest["passed_mask_level_count"] == 5
            and manifest["all_pocket_one_hot_row_sums_valid_after_filter"],
            "A/B/B2/B3/C filtered checkpoint-compatible conversions pass.",
        ),
        (
            "ligand_integrity",
            manifest["all_ligand_atoms_in_checkpoint_10d_vocab"]
            and manifest["ligand_masks_unchanged_after_filter"]
            and manifest["ligand_reactive_atom_region_preserved"],
            "Ligand atoms, ligand masks, and reactive atom region remain unchanged.",
        ),
        (
            "non_cys_reaction_scope_boundary",
            manifest["reaction_family_template_audit_required_before_broad_covalent_training"]
            and manifest["ligand_reconstruction_template_gate_required"],
            "Schema can represent non-Cys families, but template audit remains required before broad training.",
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
                    "production_adapter_modified",
                    "original_diffsbdd_source_modified",
                    "forbidden_artifacts_created",
                ]
            ),
            "No forward, loss calculation, gradient call, optimizer, persistence, forbidden artifact, source edit, or adapter replacement occurred.",
        ),
        (
            "next_step_decision",
            manifest["real_covalent_filtered_feature_semantics_audit_allowed"],
            "The next step is filtered feature semantics audit, not optimizer step.",
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
        "# Real Covalent Noncheckpoint Pocket Atom Filter Gate v0 Summary",
        "",
        "Step 12H is a formal noncheckpoint pocket atom filter gate, not training.",
        "It does not run forward, calculate loss, run gradients, create an optimizer, or save checkpoint/model/tensor dump.",
        "Original data is unchanged and production adapters are not modified in this step.",
        "",
        "## Projection-Level Filter Policy",
        "This section records the projection-level filter policy.",
        f"- filter_policy_name: {FILTER_POLICY_NAME}",
        "- ligand unknown atoms are not filtered; they block.",
        "- protein/pocket unknown atoms can be filtered only when distance, reactive atom, and reactive residue checks pass.",
        "- checkpoint vocabulary is not expanded to 11D and Mg is not encoded as zero-vector.",
        f"- allowed_filtered_atomic_numbers_for_this_gate: {manifest['allowed_filtered_atomic_numbers_for_this_gate']}",
        f"- allowed_filtered_atom_symbols_for_this_gate: {manifest['allowed_filtered_atom_symbols_for_this_gate']}",
        f"- filtered_pocket_atom_numbers: {manifest['filtered_pocket_atom_numbers']}",
        f"- total_filtered_pocket_atom_count: {manifest['total_filtered_pocket_atom_count']}",
        "",
        "## Filtered Conversion Evidence",
        f"- sample_count: {manifest['sample_count']}",
        f"- pre_filter_pocket_unknown_atom_count: {manifest['pre_filter_pocket_unknown_atom_count']}",
        f"- post_filter_pocket_unknown_atom_count: {manifest['post_filter_pocket_unknown_atom_count']}",
        f"- post_filter_ligand_unknown_atom_count: {manifest['post_filter_ligand_unknown_atom_count']}",
        f"- audited_mask_level_count: {manifest['audited_mask_level_count']}",
        f"- passed_mask_level_count: {manifest['passed_mask_level_count']}",
        "- all_checkpoint_compatible_batches_constructed_after_filter: "
        f"{str(manifest['all_checkpoint_compatible_batches_constructed_after_filter']).lower()}",
        "- all_pocket_one_hot_row_sums_valid_after_filter: "
        f"{str(manifest['all_pocket_one_hot_row_sums_valid_after_filter']).lower()}",
        "- ligand_masks_unchanged_after_filter: "
        f"{str(manifest['ligand_masks_unchanged_after_filter']).lower()}",
        "- ligand_reactive_atom_region_preserved: "
        f"{str(manifest['ligand_reactive_atom_region_preserved']).lower()}",
        "",
        "## Non-Cys Reaction Boundary",
        f"- non_cys_reactive_residue_support_status: {manifest['non_cys_reactive_residue_support_status']}",
        "- reaction_family_template_audit_required_before_broad_covalent_training: "
        f"{str(manifest['reaction_family_template_audit_required_before_broad_covalent_training']).lower()}",
        "- ligand_reconstruction_template_gate_required: "
        f"{str(manifest['ligand_reconstruction_template_gate_required']).lower()}",
        "- Non-Cys covalent reaction schemas can be expressed, but reaction-family template audit is pending.",
        "",
        "## Decision",
        f"- real_covalent_noncheckpoint_pocket_atom_filter_gate_passed: {str(manifest['real_covalent_noncheckpoint_pocket_atom_filter_gate_passed']).lower()}",
        "- real_covalent_filtered_feature_semantics_audit_allowed: "
        f"{str(manifest['real_covalent_filtered_feature_semantics_audit_allowed']).lower()}",
        "- real_covalent_single_optimizer_step_smoke_allowed: "
        f"{str(manifest['real_covalent_single_optimizer_step_smoke_allowed']).lower()}",
        "- This is not optimizer step permission.",
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
    result = build_real_covalent_noncheckpoint_pocket_atom_filter_gate_v0()
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["filter_table_rows"], FILTER_TABLE_CSV, FILTER_TABLE_COLUMNS)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_summary(result, SUMMARY_MD)
    if result["manifest"]["all_checks_passed"]:
        print("real_covalent_noncheckpoint_pocket_atom_filter_gate_v0_passed")
        return 0
    print("real_covalent_noncheckpoint_pocket_atom_filter_gate_v0_blocked")
    print(json.dumps(result["manifest"]["blocking_reasons"], indent=2, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(run())

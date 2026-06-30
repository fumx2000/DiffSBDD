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

from covalent_ext.real_covalent_feature_semantics_audit_debug import (  # noqa: E402
    DEBUG_TABLE_CSV,
    FILTER_POLICY_NAME,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_real_covalent_feature_semantics_audit_debug_v0,
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

DEBUG_TABLE_COLUMNS = [
    "row_type",
    "sample_id",
    "sample_index",
    "mask_level",
    "expected_reactive_atom_region",
    "protein_atom_local_index",
    "atomic_number",
    "atom_symbol",
    "protein_coord_x",
    "protein_coord_y",
    "protein_coord_z",
    "ligand_atom_count",
    "protein_atom_count",
    "ligand_reactive_atom_index",
    "ligand_reactive_atom_distance",
    "min_distance_to_any_ligand_atom",
    "nearest_ligand_atom_index",
    "nearest_ligand_atomic_number",
    "nearest_ligand_atom_symbol",
    "distance_to_ligand_centroid",
    "protein_reactive_residue_atom_distance_min",
    "nearest_protein_reactive_atom_index",
    "direct_ligand_contact_candidate",
    "close_to_ligand_candidate",
    "likely_metal_cofactor_or_crystal_ion",
    "metadata_available",
    "metadata_fields_available",
    "chain_id",
    "residue_name",
    "residue_id",
    "residue_number",
    "resseq",
    "insertion_code",
    "atom_name",
    "hetero_flag",
    "original_protein_atom_count",
    "filtered_protein_atom_count",
    "removed_protein_atom_count",
    "removed_atomic_numbers",
    "removed_atom_symbols",
    "removed_atom_indices",
    "ligand_atom_count_changed",
    "all_remaining_protein_atoms_in_checkpoint_10d_vocab",
    "all_ligand_atoms_in_checkpoint_10d_vocab",
    "post_filter_unknown_protein_atom_count",
    "post_filter_unknown_ligand_atom_count",
    "checkpoint_compatible_batch_constructed_after_filter",
    "ligand_feature_dim",
    "pocket_feature_dim",
    "ligand_one_hot_rows_equal_ligand_coords_rows",
    "pocket_one_hot_rows_equal_pocket_coords_rows",
    "ligand_one_hot_row_sums_valid_after_filter",
    "pocket_one_hot_row_sums_valid_after_filter",
    "ligand_unknown_atom_count_after_filter",
    "pocket_unknown_atom_count_after_filter",
    "removed_pocket_atom_count",
    "removed_pocket_atom_numbers",
    "removed_pocket_atom_symbols",
    "removed_pocket_atom_indices",
    "no_synthetic_fallback_used",
    "ligand_masks_unchanged_after_filter",
    "ligand_reactive_atom_region_preserved",
    "filter_policy_name",
    "noncheckpoint_pocket_atom_filter_policy_recommended",
    "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed",
    "real_covalent_single_optimizer_step_smoke_allowed",
    "recommended_next_step",
    "step12f_clean_block_validated",
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
            "step12f_precondition",
            manifest["step12f_clean_block_validated"] and manifest["step12b_mask_level_aware_validator_validated"],
            "Step 12F clean block and Step 12B validator behavior are accepted.",
        ),
        (
            "unknown_protein_atom_localization",
            manifest["unknown_protein_atom_localization_passed"],
            "Unknown protein Mg atoms are localized with coordinates and sample ids.",
        ),
        (
            "mg_ligand_distance_assessment",
            not manifest["mg_direct_ligand_contact_detected"],
            "Mg distance to ligand and ligand reactive atom is assessed before recommending filtering.",
        ),
        (
            "sample_filter_projection",
            manifest["post_filter_protein_unknown_atom_count"] == 0
            and manifest["post_filter_ligand_unknown_atom_count"] == 0,
            "All real samples are checked under read-only in-memory pocket filtering.",
        ),
        (
            "mask_level_filter_projection",
            manifest["all_pocket_one_hot_row_sums_valid_after_filter"]
            and manifest["all_ligand_one_hot_row_sums_valid_after_filter"],
            "A/B/B2/B3/C checkpoint-compatible projection row sums recover after filtering.",
        ),
        (
            "filter_policy_decision",
            manifest["noncheckpoint_pocket_atom_filter_policy_recommended"],
            "Projection-level non-checkpoint pocket atom filtering is recommended for the next formal gate.",
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
            "No forward, loss calculation, gradient call, optimizer, persistence, forbidden artifact, or protected source edit occurred.",
        ),
        (
            "next_step_decision",
            manifest["real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed"],
            "The next step is a formal non-checkpoint pocket atom filter gate, not an optimizer step.",
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
    mg_rows = [row for row in result["debug_table_rows"] if row.get("row_type") == "unknown_protein_atom"]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Real Covalent Feature Semantics Audit Debug v0 Summary",
        "",
        "Step 12G is an audit debug and projection policy design step, not training.",
        "It does not run forward, calculate loss, run gradients, create an optimizer, or save checkpoint/model/tensor dump.",
        "Step 12F clean block was caused by protein Mg / atomic_number=12 triggering the UNKNOWN_ATOM_FEATURE_POLICY path.",
        "",
        "## Mg Localization",
        f"- mg_atom_count: {manifest['mg_atom_count']}",
        f"- mg_sample_ids: {', '.join(manifest['mg_sample_ids'])}",
    ]
    for row in mg_rows:
        lines.append(
            "- Mg "
            f"{row['sample_id']} protein_atom_local_index={row['protein_atom_local_index']} "
            f"coord=({row['protein_coord_x']:.4f}, {row['protein_coord_y']:.4f}, {row['protein_coord_z']:.4f}) "
            f"min_ligand_distance={row['min_distance_to_any_ligand_atom']:.4f} "
            f"ligand_reactive_distance={row['ligand_reactive_atom_distance']:.4f}"
        )
    lines.extend(
        [
            f"- mg_min_distance_to_ligand: {manifest['mg_min_distance_to_ligand']}",
            f"- mg_max_distance_to_ligand: {manifest['mg_max_distance_to_ligand']}",
            f"- mg_min_distance_to_ligand_reactive_atom: {manifest['mg_min_distance_to_ligand_reactive_atom']}",
            f"- mg_direct_ligand_contact_detected: {str(manifest['mg_direct_ligand_contact_detected']).lower()}",
            f"- mg_close_to_ligand_detected: {str(manifest['mg_close_to_ligand_detected']).lower()}",
            "",
            "## Projection-Level Filter Debug",
            f"- filter_policy_name: {FILTER_POLICY_NAME}",
            "- projection_filter_only_debug: true",
            "- production_adapter_modified: false",
            "- original_data_modified: false",
            f"- filtered_atom_numbers: {manifest['filtered_atom_numbers']}",
            f"- filtered_atom_symbols: {manifest['filtered_atom_symbols']}",
            f"- total_removed_pocket_atom_count: {manifest['total_removed_pocket_atom_count']}",
            f"- post_filter_protein_unknown_atom_count: {manifest['post_filter_protein_unknown_atom_count']}",
            f"- post_filter_ligand_unknown_atom_count: {manifest['post_filter_ligand_unknown_atom_count']}",
            f"- audited_mask_level_count: {manifest['audited_mask_level_count']}",
            f"- passed_mask_level_count: {manifest['passed_mask_level_count']}",
            f"- failed_mask_level_count: {manifest['failed_mask_level_count']}",
            "- all_pocket_one_hot_row_sums_valid_after_filter: "
            f"{str(manifest['all_pocket_one_hot_row_sums_valid_after_filter']).lower()}",
            "- ligand_masks_unchanged_after_filter: "
            f"{str(manifest['ligand_masks_unchanged_after_filter']).lower()}",
            "- ligand_reactive_atom_region_preserved: "
            f"{str(manifest['ligand_reactive_atom_region_preserved']).lower()}",
            "",
            "## Decision",
            "- This step recommends a formal projection-level filter gate only if Mg is not in direct ligand contact.",
            "- The next step is a filter gate, not an optimizer step.",
            "- It does not allow a real covalent optimizer step.",
            f"- noncheckpoint_pocket_atom_filter_policy_recommended: {str(manifest['noncheckpoint_pocket_atom_filter_policy_recommended']).lower()}",
            "- real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed: "
            f"{str(manifest['real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed']).lower()}",
            "- real_covalent_single_optimizer_step_smoke_allowed: "
            f"{str(manifest['real_covalent_single_optimizer_step_smoke_allowed']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
            "If a future structure review finds Mg directly participates in ligand binding geometry, the next step should be manual structure review rather than filtering.",
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
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    result = build_real_covalent_feature_semantics_audit_debug_v0()
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["debug_table_rows"], DEBUG_TABLE_CSV, DEBUG_TABLE_COLUMNS)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_summary(result, SUMMARY_MD)
    if result["manifest"]["all_checks_passed"]:
        print("real_covalent_feature_semantics_audit_debug_v0_passed")
        return 0
    print("real_covalent_feature_semantics_audit_debug_v0_blocked")
    print(json.dumps(result["manifest"]["blocking_reasons"], indent=2, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(run())

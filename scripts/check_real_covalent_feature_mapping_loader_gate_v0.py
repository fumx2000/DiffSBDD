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

from covalent_ext.real_covalent_feature_mapping_loader_gate import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    SAMPLE_TABLE_CSV,
    STAGE,
    SUMMARY_MD,
    build_real_covalent_feature_mapping_loader_gate_v0,
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

SAMPLE_TABLE_COLUMNS = [
    "sample_id",
    "npz_path",
    "selected_artifact_is_real_covalent",
    "selected_artifact_is_synthetic_only",
    "ligand_atom_count",
    "protein_atom_count",
    "ligand_coords_shape",
    "protein_coords_shape",
    "ligand_feature_source",
    "ligand_feature_dim",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "masks_disjoint",
    "masks_cover_assigned_ligand_atoms",
    "ligand_reactive_atom_index",
    "reactive_atom_in_range",
    "reactive_atom_in_warhead",
    "coords_finite",
    "features_finite",
    "all_five_level_masks_available",
    "real_b3_target_is_scaffold",
    "real_b3_context_is_linker_warhead",
    "real_b3_reactive_atom_in_context",
    "real_b3_reactive_atom_in_target",
    "real_b2_b3_contrast_passed",
    "mask_derivation_status",
    "status",
    "blocking_reasons",
    "mask_derivation_blocking_reasons",
]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


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
    sections = result["report_sections"]
    blockers = _list_text(manifest["blocking_reasons"])
    recommended = manifest["recommended_next_step"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11r_precondition",
            "status": "passed" if manifest["step11r_validated"] else "blocked",
            "evidence": _json_text(sections["step11r_precondition"]),
            "decision": "Step 11R cleanup-compatible optimizer smoke evidence is accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "artifact_discovery",
            "status": "passed" if manifest["selected_artifact_is_real_covalent"] else "blocked",
            "evidence": _json_text(sections["artifact_discovery"]),
            "decision": "Existing real covalent tensor/loader artifact discovery is read-only.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "selected_artifact_gate",
            "status": "passed"
            if manifest["selected_artifact_is_real_covalent"] and not manifest["selected_artifact_is_synthetic_only"]
            else "blocked",
            "evidence": _json_text(sections["selected_artifact_gate"]),
            "decision": "Selected artifact must be real covalent data, not synthetic-only data.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "real_sample_field_audit",
            "status": "passed" if manifest["real_covalent_sample_field_contract_proven"] else "blocked",
            "evidence": _json_text(sections["real_sample_field_audit"]),
            "decision": "Real sample field contract is audited without modifying source artifacts.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "five_level_mask_derivation",
            "status": "passed" if manifest["real_five_level_mask_contract_proven"] else "blocked",
            "evidence": _json_text(sections["five_level_mask_derivation"]),
            "decision": "A/B/B2/B3/C long-form masks are derived from real scaffold/linker/warhead masks.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b3_real_contract",
            "status": "passed" if manifest["real_b3_loader_contract_proven"] else "blocked",
            "evidence": _json_text(sections["b3_real_contract"]),
            "decision": "Real B3 target/context and B2/B3 contrast are preserved.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "batch_adapter_gate",
            "status": "passed" if manifest["real_batch_adapter_gate_passed"] else "blocked",
            "evidence": _json_text(sections["batch_adapter_gate"]),
            "decision": "Read-only Dataset/DataLoader and adapted batch gate passed.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "model_input_mapping_gate",
            "status": "passed" if manifest["real_model_input_mapping_gate_passed"] else "blocked",
            "evidence": _json_text(sections["model_input_mapping_gate"]),
            "decision": "Real covalent model-input-like mapping gate passed without model forward.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No model forward, backward, optimizer, checkpoint/model/tensor dump, or protected source edit occurred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(result: dict[str, Any], path: str | Path) -> None:
    manifest = result["manifest"]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Real Covalent Feature Mapping Loader Gate v0 Summary",
        "",
        "Step 12A is a real covalent feature mapping / loader gate, not training.",
        "It does not run model forward, backward, optimizer, training_step, or trainer.fit.",
        "It reads existing real covalent artifacts and writes only CSV/JSON/MD gate evidence.",
        "",
        "## Artifact",
        f"- discovered_artifact_count: {manifest['discovered_artifact_count']}",
        f"- discovered_manifest_count: {manifest['discovered_manifest_count']}",
        f"- discovered_npz_count: {manifest['discovered_npz_count']}",
        f"- selected_real_data_root: {manifest['selected_real_data_root']}",
        f"- selected_loader_or_tensor_artifact: {manifest['selected_loader_or_tensor_artifact']}",
        f"- selected_artifact_is_real_covalent: {str(manifest['selected_artifact_is_real_covalent']).lower()}",
        f"- selected_artifact_is_synthetic_only: {str(manifest['selected_artifact_is_synthetic_only']).lower()}",
        "",
        "## Real Sample Contract",
        f"- audited_real_sample_count: {manifest['audited_real_sample_count']}",
        f"- passed_real_sample_count: {manifest['passed_real_sample_count']}",
        f"- failed_real_sample_count: {manifest['failed_real_sample_count']}",
        f"- canonical_mask_levels: {', '.join(CANONICAL_MASK_LEVELS)}",
        f"- all_five_level_masks_available: {str(manifest['all_five_level_masks_available']).lower()}",
        f"- real_five_level_mask_contract_proven: {str(manifest['real_five_level_mask_contract_proven']).lower()}",
        f"- real_b3_target_is_scaffold: {str(manifest['real_b3_target_is_scaffold']).lower()}",
        f"- real_b3_context_is_linker_warhead: {str(manifest['real_b3_context_is_linker_warhead']).lower()}",
        f"- real_b3_reactive_atom_in_context: {str(manifest['real_b3_reactive_atom_in_context']).lower()}",
        f"- real_b3_reactive_atom_in_target: {str(manifest['real_b3_reactive_atom_in_target']).lower()}",
        f"- real_b2_b3_contrast_passed: {str(manifest['real_b2_b3_contrast_passed']).lower()}",
        "",
        "## Loader And Mapping",
        f"- dataset_created: {str(manifest['dataset_created']).lower()}",
        f"- dataloader_created: {str(manifest['dataloader_created']).lower()}",
        f"- batch_size: {manifest['batch_size']}",
        f"- real_batch_adapter_gate_passed: {str(manifest['real_batch_adapter_gate_passed']).lower()}",
        f"- real_model_input_mapping_gate_passed: {str(manifest['real_model_input_mapping_gate_passed']).lower()}",
        f"- real_covalent_feature_mapping_loader_gate_passed: {str(manifest['real_covalent_feature_mapping_loader_gate_passed']).lower()}",
        f"- real_covalent_pretraining_smoke_allowed: {str(manifest['real_covalent_pretraining_smoke_allowed']).lower()}",
        "",
        "## Safety Boundary",
        f"- model_forward_called: {str(manifest['model_forward_called']).lower()}",
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
        "## Decision",
        f"- all_checks_passed: {str(manifest['all_checks_passed']).lower()}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    result = build_real_covalent_feature_mapping_loader_gate_v0()
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["sample_table_rows"], SAMPLE_TABLE_CSV, SAMPLE_TABLE_COLUMNS)
    write_summary(result, SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())

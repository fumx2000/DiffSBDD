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

from covalent_ext.real_covalent_pretraining_smoke_design import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    MANIFEST_JSON,
    PLAN_TABLE_CSV,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_real_covalent_pretraining_smoke_design_v0,
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

PLAN_TABLE_COLUMNS = [
    "planned_stage",
    "mask_level",
    "expected_reactive_atom_region",
    "planned_batch_size",
    "planned_allow_model_forward",
    "planned_allow_loss_compute",
    "planned_allow_backward",
    "planned_allow_optimizer",
    "planned_allow_optimizer_step",
    "planned_use_synthetic_fallback",
    "status",
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
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step12a_precondition",
            "status": "passed" if manifest["step12a_validated"] else "blocked",
            "evidence": _json_text(sections["step12a_precondition"]),
            "decision": "Step 12A real covalent loader gate evidence is accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step12b_validator_contract",
            "status": "passed" if manifest["step12b_mask_level_aware_validator_validated"] else "blocked",
            "evidence": _json_text(sections["step12b_validator_contract"]),
            "decision": "Mask-level-aware reactive atom validation is required for the next smoke.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "selected_real_artifact",
            "status": "passed"
            if manifest["selected_artifact_is_real_covalent"] and not manifest["selected_artifact_is_synthetic_only"]
            else "blocked",
            "evidence": _json_text(sections["selected_real_artifact"]),
            "decision": "The planned next smoke must use the real covalent sample index, not synthetic fallback.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "planned_mask_levels",
            "status": "passed" if manifest["planned_mask_levels"] == CANONICAL_MASK_LEVELS else "blocked",
            "evidence": _json_text(sections["planned_mask_levels"]),
            "decision": "The next smoke covers A/B/B2/B3/C canonical long-form masks.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "planned_forward_loss_smoke_scope",
            "status": "passed"
            if manifest["planned_allow_model_forward"] and manifest["planned_allow_loss_compute"]
            else "blocked",
            "evidence": _json_text(sections["planned_forward_loss_smoke_scope"]),
            "decision": "The next stage may run forward and loss on real covalent batches.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "planned_safety_boundary",
            "status": "passed"
            if not any(
                manifest[key]
                for key in [
                    "planned_allow_backward",
                    "planned_allow_optimizer",
                    "planned_allow_optimizer_step",
                    "planned_allow_training_step",
                    "planned_allow_trainer_fit",
                    "planned_allow_checkpoint_save",
                    "planned_allow_model_save",
                    "planned_allow_tensor_dump",
                ]
            )
            else "blocked",
            "evidence": _json_text(sections["planned_safety_boundary"]),
            "decision": "The next smoke remains forward/loss only; training and persistence stay disallowed.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "decision",
            "status": "passed" if manifest["real_covalent_pretraining_smoke_design_passed"] else "blocked",
            "evidence": _json_text(sections["decision"]),
            "decision": "The real covalent pretrained forward/loss smoke plan is ready.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "artifact_safety",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["artifact_safety"]),
            "decision": "No protected source change or forbidden artifact was produced by this design step.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(result: dict[str, Any], path: str | Path) -> None:
    manifest = result["manifest"]
    plan = result["plan"]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    expected_regions = {
        row["mask_level"]: row["expected_reactive_atom_region"] for row in result["plan_table_rows"]
    }
    lines = [
        "# Real Covalent Pretraining Smoke Design v0 Summary",
        "",
        "Step 12C is design only, not training.",
        "It does not run model forward, backward, optimizer, training_step, or trainer.fit.",
        "It designs the next real covalent pretrained forward/loss smoke using existing real artifacts.",
        "",
        "## Preconditions",
        f"- step12a_validated: {str(manifest['step12a_validated']).lower()}",
        f"- step12b_mask_level_aware_validator_validated: {str(manifest['step12b_mask_level_aware_validator_validated']).lower()}",
        f"- selected_real_data_root: {manifest['selected_real_data_root']}",
        f"- selected_sample_index: {manifest['selected_sample_index']}",
        f"- selected_artifact_is_real_covalent: {str(manifest['selected_artifact_is_real_covalent']).lower()}",
        f"- selected_artifact_is_synthetic_only: {str(manifest['selected_artifact_is_synthetic_only']).lower()}",
        "",
        "## Planned Next Smoke",
        f"- planned_next_stage: {manifest['planned_next_stage']}",
        f"- planned_checkpoint_path: {manifest['planned_checkpoint_path']}",
        f"- planned_batch_size: {manifest['planned_batch_size']}",
        f"- planned_num_workers: {manifest['planned_num_workers']}",
        f"- planned_mask_levels: {', '.join(manifest['planned_mask_levels'])}",
        f"- planned_use_mask_level_aware_validator: {str(manifest['planned_use_mask_level_aware_validator']).lower()}",
        f"- planned_use_synthetic_fallback: {str(manifest['planned_use_synthetic_fallback']).lower()}",
        f"- planned_allow_model_forward: {str(manifest['planned_allow_model_forward']).lower()}",
        f"- planned_allow_loss_compute: {str(manifest['planned_allow_loss_compute']).lower()}",
        f"- planned_allow_backward: {str(manifest['planned_allow_backward']).lower()}",
        f"- planned_allow_optimizer: {str(manifest['planned_allow_optimizer']).lower()}",
        f"- planned_allow_optimizer_step: {str(manifest['planned_allow_optimizer_step']).lower()}",
        f"- planned_allow_training_step: {str(manifest['planned_allow_training_step']).lower()}",
        f"- planned_allow_trainer_fit: {str(manifest['planned_allow_trainer_fit']).lower()}",
        f"- planned_allow_checkpoint_save: {str(manifest['planned_allow_checkpoint_save']).lower()}",
        f"- planned_allow_model_save: {str(manifest['planned_allow_model_save']).lower()}",
        f"- planned_allow_tensor_dump: {str(manifest['planned_allow_tensor_dump']).lower()}",
        "",
        "## Reactive Atom Regions",
        f"- A_warhead_only: {expected_regions['A_warhead_only']}",
        f"- B_linker_warhead: {expected_regions['B_linker_warhead']}",
        f"- B2_scaffold_warhead: {expected_regions['B2_scaffold_warhead']}",
        f"- B3_scaffold_only: {expected_regions['B3_scaffold_only']}",
        f"- C_scaffold_linker_warhead: {expected_regions['C_scaffold_linker_warhead']}",
        "",
        "## Blocking Policy",
        "If the real batch cannot be converted into checkpoint-compatible model input, the next stage must cleanly block.",
        "Synthetic 10D shape contracts may be referenced for shape comparison only; they are not an input source.",
        f"- planned_success_criteria_count: {len(plan['planned_success_criteria'])}",
        f"- planned_blocking_criteria_count: {len(plan['planned_blocking_criteria'])}",
        "",
        "## Current Step Safety",
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
        f"- real_covalent_pretraining_smoke_design_passed: {str(manifest['real_covalent_pretraining_smoke_design_passed']).lower()}",
        f"- real_covalent_forward_loss_smoke_plan_ready: {str(manifest['real_covalent_forward_loss_smoke_plan_ready']).lower()}",
        f"- real_covalent_forward_loss_smoke_allowed: {str(manifest['real_covalent_forward_loss_smoke_allowed']).lower()}",
        f"- all_checks_passed: {str(manifest['all_checks_passed']).lower()}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    result = build_real_covalent_pretraining_smoke_design_v0()
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["plan_table_rows"], PLAN_TABLE_CSV, PLAN_TABLE_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_summary(result, SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

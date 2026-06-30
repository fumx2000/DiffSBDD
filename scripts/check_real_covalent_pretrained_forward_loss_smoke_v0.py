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

from covalent_ext.real_covalent_pretrained_forward_loss_smoke import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    LOSS_TABLE_CSV,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_real_covalent_pretrained_forward_loss_smoke_v0,
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

LOSS_TABLE_COLUMNS = [
    "mask_level",
    "expected_reactive_atom_region",
    "sample_ids",
    "batch_size",
    "adapted_valid",
    "model_input_valid",
    "diffsbdd_like_valid",
    "checkpoint_compatible_real_batch_constructed",
    "no_synthetic_fallback_used",
    "model_forward_called",
    "forward_call_count",
    "loss_computed",
    "selected_loss_key",
    "selected_loss_value",
    "loss_requires_grad",
    "loss_finite",
    "target_atom_count",
    "context_atom_count",
    "ligand_feature_dim",
    "pocket_feature_dim",
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
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step12c_precondition",
            "status": "passed" if manifest["step12c_validated"] else "blocked",
            "evidence": _json_text(sections["step12c_precondition"]),
            "decision": "Step 12C design evidence and Step 12B validator behavior are accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "real_batch_loading",
            "status": "passed" if manifest["selected_artifact_is_real_covalent"] else "blocked",
            "evidence": _json_text(sections["real_batch_loading"]),
            "decision": "Read-only real covalent Dataset/DataLoader supplies the smoke batch.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "mask_level_aware_model_input",
            "status": "passed" if manifest["all_model_inputs_valid"] else "blocked",
            "evidence": _json_text(sections["mask_level_aware_model_input"]),
            "decision": "A/B/B2/B3/C model inputs validate with mask-level-aware reactive atom rules.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_compatible_real_batch",
            "status": "passed" if manifest["all_checkpoint_compatible_real_batches_constructed"] else "blocked",
            "evidence": _json_text(sections["checkpoint_compatible_real_batch"]),
            "decision": "Real covalent batches are converted to checkpoint-compatible 10D model inputs.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_strict_load",
            "status": "passed" if manifest["strict_load_success"] else "blocked",
            "evidence": _json_text(sections["pretrained_strict_load"]),
            "decision": "A fresh checkpoint-compatible pretrained model is strict-loaded once.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "forward_loss_by_mask_level",
            "status": "passed" if manifest["all_losses_finite"] and manifest["all_losses_require_grad"] else "blocked",
            "evidence": _json_text(sections["forward_loss_by_mask_level"]),
            "decision": "Each canonical mask level runs exactly one forward and finite differentiable masked loss.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "aggregate_loss_decision",
            "status": "passed" if manifest["real_covalent_forward_loss_contract_proven"] else "blocked",
            "evidence": _json_text(sections["aggregate_loss_decision"]),
            "decision": "Aggregate selected loss statistics are finite across all mask levels.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed"
            if not any(
                manifest[key]
                for key in [
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
            )
            else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No backward, optimizer, training API, persistence, forbidden artifact, or protected source edit occurred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "next_step_decision",
            "status": "passed" if manifest["real_covalent_backward_smoke_allowed"] else "blocked",
            "evidence": _json_text(sections["next_step_decision"]),
            "decision": "The next allowed stage is real covalent backward smoke if all checks pass.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(result: dict[str, Any], path: str | Path) -> None:
    manifest = result["manifest"]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    by_level = {row["mask_level"]: row for row in result["loss_table_rows"]}
    lines = [
        "# Real Covalent Pretrained Forward/Loss Smoke v0 Summary",
        "",
        "Step 12D is a real covalent pretrained forward/loss smoke, not training.",
        "It uses the real covalent sample_index and does not use synthetic fallback.",
        "It does not run backward, create an optimizer, call training_step, call trainer.fit, or save checkpoint/model/tensor dump.",
        "",
        "## Inputs",
        f"- input_source: {manifest['input_source']}",
        f"- selected_sample_index: {manifest['selected_sample_index']}",
        f"- checkpoint_path: {manifest['checkpoint_path']}",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- batch_size: {manifest['batch_size']}",
        f"- num_workers: {manifest['num_workers']}",
        "",
        "## Mask Levels",
        f"- canonical_mask_levels: {', '.join(CANONICAL_MASK_LEVELS)}",
        "- A_warhead_only expected reactive atom region: target",
        "- B_linker_warhead expected reactive atom region: target",
        "- B2_scaffold_warhead expected reactive atom region: target",
        "- B3_scaffold_only expected reactive atom region: context",
        "- C_scaffold_linker_warhead expected reactive atom region: target",
        "",
        "## Pretrained Model",
        f"- model_instantiated: {str(manifest['model_instantiated']).lower()}",
        f"- strict_load_success: {str(manifest['strict_load_success']).lower()}",
        f"- pretrained_weights_loaded: {str(manifest['pretrained_weights_loaded']).lower()}",
        f"- pretrained_base_integration_proven: {str(manifest['pretrained_base_integration_proven']).lower()}",
        f"- model_strict_loaded_once: {str(manifest['model_strict_loaded_once']).lower()}",
        "",
        "## Forward/Loss Results",
        f"- model_forward_called: {str(manifest['model_forward_called']).lower()}",
        f"- model_forward_call_count: {manifest['model_forward_call_count']}",
        f"- all_level_forward_call_count_exactly_one: {str(manifest['all_level_forward_call_count_exactly_one']).lower()}",
        f"- all_losses_computed: {str(manifest['all_losses_computed']).lower()}",
        f"- all_losses_finite: {str(manifest['all_losses_finite']).lower()}",
        f"- all_losses_require_grad: {str(manifest['all_losses_require_grad']).lower()}",
        f"- selected_loss_key: {manifest['selected_loss_key']}",
        f"- min_selected_loss_value: {manifest['min_selected_loss_value']}",
        f"- max_selected_loss_value: {manifest['max_selected_loss_value']}",
        f"- mean_selected_loss_value: {manifest['mean_selected_loss_value']}",
        "",
        "## Per-Level Loss Table",
        "| mask_level | selected_loss_value | loss_finite | loss_requires_grad |",
        "| --- | ---: | --- | --- |",
    ]
    for level in CANONICAL_MASK_LEVELS:
        row = by_level[level]
        lines.append(
            f"| {level} | {row['selected_loss_value']} | "
            f"{str(row['loss_finite']).lower()} | {str(row['loss_requires_grad']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
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
            f"- real_covalent_pretrained_forward_loss_smoke_passed: {str(manifest['real_covalent_pretrained_forward_loss_smoke_passed']).lower()}",
            f"- real_covalent_forward_loss_contract_proven: {str(manifest['real_covalent_forward_loss_contract_proven']).lower()}",
            f"- real_covalent_all_mask_levels_forward_loss_proven: {str(manifest['real_covalent_all_mask_levels_forward_loss_proven']).lower()}",
            f"- real_covalent_backward_smoke_allowed: {str(manifest['real_covalent_backward_smoke_allowed']).lower()}",
            f"- all_checks_passed: {str(manifest['all_checks_passed']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    result = build_real_covalent_pretrained_forward_loss_smoke_v0()
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["loss_table_rows"], LOSS_TABLE_CSV, LOSS_TABLE_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_summary(result, SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

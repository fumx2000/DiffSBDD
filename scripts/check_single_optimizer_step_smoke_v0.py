#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.single_optimizer_step_smoke import (  # noqa: E402
    DELTA_TABLE_CSV,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_single_optimizer_step_smoke_v0,
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
DELTA_COLUMNS = [
    "stage",
    "selected_mask_level",
    "optimizer_class",
    "optimizer_lr",
    "selected_loss_key",
    "selected_loss_value",
    "backward_call_count",
    "optimizer_step_call_count",
    "sampled_parameter_count",
    "changed_parameter_count",
    "unchanged_parameter_count",
    "parameter_delta_l2_total",
    "parameter_delta_max_abs",
    "parameter_delta_mean_abs",
    "finite_parameter_delta",
    "delta_nan_count",
    "delta_inf_count",
    "status",
    "blocking_reasons",
]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(values: Any) -> str:
    if isinstance(values, list):
        return ";".join(str(value) for value in values)
    return "" if values is None else str(values)


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    sections = result["report_sections"]
    recommended = manifest["recommended_next_step"]
    blockers = _list_text(manifest["blocking_reasons"])
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11i_precondition",
            "status": "passed" if manifest["step11i_validated"] else "blocked",
            "evidence": _json_text(sections["step11i_precondition"]),
            "decision": "Step 11I optimizer smoke design evidence is accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_model_and_optimizer",
            "status": "passed" if manifest["optimizer_created"] and manifest["strict_load_success"] else "blocked",
            "evidence": _json_text(sections["pretrained_model_and_optimizer"]),
            "decision": "A fresh strict-loaded pretrained model and one AdamW optimizer were created in memory.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "loss_and_backward",
            "status": "passed" if manifest["backward_success"] and manifest["backward_call_count"] == 1 else "blocked",
            "evidence": _json_text(sections["loss_and_backward"]),
            "decision": "The differentiable masked loss was finite and received exactly one reverse pass.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "optimizer_step",
            "status": "passed" if manifest["optimizer_step_success"] and manifest["optimizer_step_call_count"] == 1 else "blocked",
            "evidence": _json_text(sections["optimizer_step"]),
            "decision": "The optimizer step was executed exactly once.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "parameter_delta",
            "status": "passed" if manifest["finite_parameter_delta"] and manifest["changed_parameter_count"] > 0 else "blocked",
            "evidence": _json_text(sections["parameter_delta"]),
            "decision": "At least one sampled parameter changed with finite positive delta summary.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "decision",
            "status": "passed" if manifest["single_optimizer_step_smoke_passed"] else "blocked",
            "evidence": _json_text(sections["decision"]),
            "decision": "Optimizer plumbing is proven for this synthetic shape-only single-step smoke.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No trainer, training_step, checkpoint save, model save, tensor dump, or source modification occurred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], delta_rows: list[dict[str, Any]], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    row = delta_rows[0] if delta_rows else {}
    lines = [
        "# Single Optimizer Step Smoke v0 Summary",
        "",
        "Step 11J is a single optimizer step smoke, not formal training.",
        "It uses one fresh strict-loaded pretrained model, one A_warhead_only synthetic 10D microbatch, one reverse pass, and one optimizer step.",
        "It does not save checkpoint, model, optimizer, full tensor, or parameter-delta tensor artifacts.",
        "",
        "## Optimizer",
        f"- optimizer_class: {manifest['optimizer_class']}",
        f"- optimizer_lr: {manifest['optimizer_lr']}",
        f"- optimizer_weight_decay: {manifest['optimizer_weight_decay']}",
        f"- selected_mask_level: {manifest['selected_mask_level']}",
        "",
        "## Loss And Gradient",
        f"- selected_loss_key: {manifest['selected_loss_key']}",
        f"- selected_loss_value: {manifest['selected_loss_value']}",
        f"- loss_requires_grad: {str(manifest['loss_requires_grad']).lower()}",
        f"- loss_finite: {str(manifest['loss_finite']).lower()}",
        f"- backward_call_count: {manifest['backward_call_count']}",
        f"- total_grad_norm: {manifest['total_grad_norm']}",
        f"- max_abs_grad: {manifest['max_abs_grad']}",
        f"- grad_nan_count: {manifest['grad_nan_count']}",
        f"- grad_inf_count: {manifest['grad_inf_count']}",
        "",
        "## Optimizer Step Delta",
        f"- optimizer_step_call_count: {manifest['optimizer_step_call_count']}",
        f"- sampled_parameter_count: {row.get('sampled_parameter_count', manifest['sampled_parameter_count'])}",
        f"- changed_parameter_count: {manifest['changed_parameter_count']}",
        f"- unchanged_parameter_count: {manifest['unchanged_parameter_count']}",
        f"- parameter_delta_l2_total: {manifest['parameter_delta_l2_total']}",
        f"- parameter_delta_max_abs: {manifest['parameter_delta_max_abs']}",
        f"- parameter_delta_mean_abs: {manifest['parameter_delta_mean_abs']}",
        f"- finite_parameter_delta: {str(manifest['finite_parameter_delta']).lower()}",
        f"- delta_nan_count: {manifest['delta_nan_count']}",
        f"- delta_inf_count: {manifest['delta_inf_count']}",
        "",
        "## Boundary",
        f"- single_optimizer_step_smoke_passed: {str(manifest['single_optimizer_step_smoke_passed']).lower()}",
        f"- optimizer_plumbing_proven: {str(manifest['optimizer_plumbing_proven']).lower()}",
        f"- tiny_training_dry_run_design_allowed: {str(manifest['tiny_training_dry_run_design_allowed']).lower()}",
        f"- training_allowed: {str(manifest['training_allowed']).lower()}",
        f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
        f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
        f"- training_step_called: {str(manifest['training_step_called']).lower()}",
        f"- trainer_fit_called: {str(manifest['trainer_fit_called']).lower()}",
        f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
        f"- model_saved: {str(manifest['model_saved']).lower()}",
        f"- tensor_dump_saved: {str(manifest['tensor_dump_saved']).lower()}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
        "",
        "This smoke does not prove loss decrease, generation quality, or real covalent data-loader training readiness.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(device: str = "cpu") -> int:
    result = build_single_optimizer_step_smoke_v0(device=device)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["delta_table_rows"], DELTA_TABLE_CSV, DELTA_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_summary(result["manifest"], result["delta_table_rows"], SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Step 11J single optimizer step smoke.")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    return run(device=args.device)


if __name__ == "__main__":
    raise SystemExit(main())

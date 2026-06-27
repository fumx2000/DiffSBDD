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

from covalent_ext.tiny_training_dry_run import (  # noqa: E402
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    STEP_TABLE_CSV,
    SUMMARY_MD,
    build_tiny_training_dry_run_v0,
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

STEP_TABLE_COLUMNS = [
    "stage",
    "step_index",
    "selected_mask_level",
    "loss_value",
    "loss_requires_grad",
    "loss_finite",
    "backward_called",
    "backward_call_count",
    "backward_success",
    "optimizer_step_called",
    "optimizer_step_call_count",
    "optimizer_step_success",
    "grad_nan_count",
    "grad_inf_count",
    "total_grad_norm",
    "max_abs_grad",
    "finite_nonzero_grad_exists",
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
    tiny_steps = sections["tiny_steps"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11k_precondition",
            "status": "passed" if manifest["step11k_validated"] else "blocked",
            "evidence": _json_text(sections["step11k_precondition"]),
            "decision": "Step 11K design evidence is accepted for the tiny dry run.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_model_and_optimizer",
            "status": "passed"
            if manifest["model_instantiated"] and manifest["strict_load_success"] and manifest["optimizer_created"]
            else "blocked",
            "evidence": _json_text(sections["pretrained_model_and_optimizer"]),
            "decision": "A fresh strict-loaded pretrained model and one AdamW optimizer were created in memory.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        *[
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": f"tiny_step_{row['step_index']}",
                "status": row["status"],
                "evidence": _json_text(row),
                "decision": "One finite synthetic A_warhead_only loss/backward/optimizer step completed.",
                "blocking_reasons": row.get("blocking_reasons", ""),
                "recommended_next_step": recommended,
            }
            for row in tiny_steps
        ],
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "decision",
            "status": "passed" if manifest["tiny_training_dry_run_passed"] else "blocked",
            "evidence": _json_text(sections["decision"]),
            "decision": "The three-step synthetic loop plumbing is ready for the next scoped design gate.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No checkpoint, model, tensor dump, trainer, or source modification was produced.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], step_rows: list[dict[str, Any]], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Tiny Training Dry Run v0 Summary",
        "",
        "Step 11L is a three-step tiny training dry run, not formal training or fine-tuning.",
        "It uses the synthetic 10D shape contract from the previous optimizer smoke path, not a real covalent loader.",
        "It uses only A_warhead_only and does not claim B/B2/C readiness.",
        "",
        "## Execution",
        f"- previous_stage: {manifest['previous_stage']}",
        f"- step11k_validated: {str(manifest['step11k_validated']).lower()}",
        f"- input_source: {manifest['input_source']}",
        f"- selected_mask_levels: {', '.join(manifest['selected_mask_levels'])}",
        f"- checkpoint_path: {manifest['checkpoint_path']}",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- model_instantiated: {str(manifest['model_instantiated']).lower()}",
        f"- strict_load_success: {str(manifest['strict_load_success']).lower()}",
        f"- pretrained_weights_loaded: {str(manifest['pretrained_weights_loaded']).lower()}",
        f"- optimizer_class: {manifest['optimizer_class']}",
        f"- optimizer_lr: {manifest['optimizer_lr']}",
        f"- optimizer_weight_decay: {manifest['optimizer_weight_decay']}",
        f"- reuse_optimizer_across_steps: {str(manifest['reuse_optimizer_across_steps']).lower()}",
        f"- step_count: {manifest['step_count']}",
        "",
        "## Step Results",
        "| step | mask_level | loss_value | backward | optimizer_step | grad_norm | parameter_delta_l2 | status |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for row in step_rows:
        lines.append(
            "| {step_index} | {selected_mask_level} | {loss_value} | {backward_success} | "
            "{optimizer_step_success} | {total_grad_norm} | {parameter_delta_l2_total} | {status} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Loss Trajectory",
            f"- loss_values: {manifest['loss_values']}",
            f"- initial_loss_value: {manifest['initial_loss_value']}",
            f"- final_loss_value: {manifest['final_loss_value']}",
            f"- finite_loss_all_steps: {str(manifest['finite_loss_all_steps']).lower()}",
            f"- loss_decrease_required: {str(manifest['loss_decrease_required']).lower()}",
            f"- loss_decreased_optional: {str(manifest['loss_decreased_optional']).lower()}",
            f"- loss_increased_warning: {str(manifest['loss_increased_warning']).lower()}",
            "",
            "## Safety Boundary",
            f"- backward_call_count_total: {manifest['backward_call_count_total']}",
            f"- optimizer_step_call_count_total: {manifest['optimizer_step_call_count_total']}",
            f"- training_allowed: {str(manifest['training_allowed']).lower()}",
            f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
            f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
            f"- quality_claim_allowed: {str(manifest['quality_claim_allowed']).lower()}",
            f"- training_step_called: {str(manifest['training_step_called']).lower()}",
            f"- trainer_fit_called: {str(manifest['trainer_fit_called']).lower()}",
            f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
            f"- model_saved: {str(manifest['model_saved']).lower()}",
            f"- tensor_dump_saved: {str(manifest['tensor_dump_saved']).lower()}",
            f"- original_source_files_modified: {str(manifest['original_source_files_modified']).lower()}",
            f"- forbidden_artifacts_created: {str(manifest['forbidden_artifacts_created']).lower()}",
            "",
            "## Decision",
            f"- tiny_training_dry_run_status: {manifest['tiny_training_dry_run_status']}",
            f"- tiny_training_dry_run_passed: {str(manifest['tiny_training_dry_run_passed']).lower()}",
            f"- tiny_training_loop_plumbing_proven: {str(manifest['tiny_training_loop_plumbing_proven']).lower()}",
            f"- real_covalent_loader_gate_allowed: {str(manifest['real_covalent_loader_gate_allowed']).lower()}",
            f"- b3_scaffold_only_mask_design_allowed: {str(manifest['b3_scaffold_only_mask_design_allowed']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
            "This dry run proves only in-memory loop plumbing on synthetic A_warhead_only inputs. It does not prove convergence, generation quality, real covalent data-loader readiness, or full mask-level training readiness.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step 11L tiny training dry run v0.")
    parser.add_argument("--device", default="cpu", help="Device for the tiny dry run. Default: cpu")
    return parser.parse_args()


def run(device: str = "cpu") -> int:
    result = build_tiny_training_dry_run_v0(device=device)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["step_table_rows"], STEP_TABLE_CSV, STEP_TABLE_COLUMNS)
    write_summary(result["manifest"], result["step_table_rows"], SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    return run(device=args.device)


if __name__ == "__main__":
    raise SystemExit(main())

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

from covalent_ext.few_step_training_dry_run import (  # noqa: E402
    BATCH_SIZE,
    DEFAULT_LR,
    DEFAULT_ROOT,
    DEFAULT_WEIGHT_DECAY,
    LOOP_NAME,
    MASK_ORDER,
    MAX_STEPS,
    OPTIMIZER_CLASS,
    PREVIOUS_STAGE,
    SEED,
    SHUFFLE,
    STAGE,
    run_few_step_training_dry_run_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10p_training_loop_design_passed",
    "loop_name",
    "step",
    "mask_level",
    "sample_ids",
    "target_atom_count",
    "context_atom_count",
    "ligand_atom_count",
    "loss_original",
    "loss_masked_x",
    "loss_masked_h",
    "loss_total",
    "loss_finite",
    "loss_total_requires_grad",
    "backward_called",
    "backward_success",
    "optimizer_class",
    "learning_rate",
    "optimizer_step_executed",
    "optimizer_step_success",
    "grad_norm",
    "max_grad_abs",
    "finite_gradients",
    "nonzero_gradients",
    "grad_nan_count",
    "grad_inf_count",
    "param_delta_norm",
    "max_param_delta_abs",
    "finite_parameter_delta",
    "nonzero_parameter_delta",
    "post_step_param_nan_count",
    "post_step_param_inf_count",
    "cuda_device",
    "elapsed_seconds",
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "trainer_fit_called",
    "checkpoint_written",
    "archive_created",
    "model_saved",
    "formal_training_executed",
    "real_finetune_executed",
    "original_source_files_modified",
    "stop_triggered",
    "stop_reason",
    "step_status",
    "blocking_reasons",
]


def _bool(value: Any) -> str:
    return str(bool(value)).lower()


def _list_text(values: list[Any]) -> str:
    return ";".join(str(value) for value in values)


def write_csv(rows: list[dict[str, str]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def report_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10p_training_loop_design_passed": "true",
        "loop_name": LOOP_NAME,
        "step": str(row["step"]),
        "mask_level": str(row["mask_level"]),
        "sample_ids": _list_text(row["sample_ids"]),
        "target_atom_count": str(row["target_atom_count"]),
        "context_atom_count": str(row["context_atom_count"]),
        "ligand_atom_count": str(row["ligand_atom_count"]),
        "loss_original": str(row["loss_original"]),
        "loss_masked_x": str(row["loss_masked_x"]),
        "loss_masked_h": str(row["loss_masked_h"]),
        "loss_total": str(row["loss_total"]),
        "loss_finite": _bool(row["loss_finite"]),
        "loss_total_requires_grad": _bool(row["loss_total_requires_grad"]),
        "backward_called": _bool(row["backward_called"]),
        "backward_success": _bool(row["backward_success"]),
        "optimizer_class": str(row["optimizer_class"]),
        "learning_rate": str(row["learning_rate"]),
        "optimizer_step_executed": _bool(row["optimizer_step_executed"]),
        "optimizer_step_success": _bool(row["optimizer_step_success"]),
        "grad_norm": str(row["grad_norm"]),
        "max_grad_abs": str(row["max_grad_abs"]),
        "finite_gradients": _bool(row["finite_gradients"]),
        "nonzero_gradients": _bool(row["nonzero_gradients"]),
        "grad_nan_count": str(row["grad_nan_count"]),
        "grad_inf_count": str(row["grad_inf_count"]),
        "param_delta_norm": str(row["param_delta_norm"]),
        "max_param_delta_abs": str(row["max_param_delta_abs"]),
        "finite_parameter_delta": _bool(row["finite_parameter_delta"]),
        "nonzero_parameter_delta": _bool(row["nonzero_parameter_delta"]),
        "post_step_param_nan_count": str(row["post_step_param_nan_count"]),
        "post_step_param_inf_count": str(row["post_step_param_inf_count"]),
        "cuda_device": str(row["cuda_device"]),
        "elapsed_seconds": str(row["elapsed_seconds"]),
        "checkpoint_loaded": _bool(row["checkpoint_loaded"]),
        "checkpoint_saved": _bool(row["checkpoint_saved"]),
        "training_step_called": _bool(row["training_step_called"]),
        "trainer_fit_called": _bool(row["trainer_fit_called"]),
        "checkpoint_written": _bool(row["checkpoint_written"]),
        "archive_created": _bool(row["archive_created"]),
        "model_saved": _bool(row["model_saved"]),
        "formal_training_executed": _bool(row["formal_training_executed"]),
        "real_finetune_executed": _bool(row["real_finetune_executed"]),
        "original_source_files_modified": _bool(row["original_source_files_modified"]),
        "stop_triggered": _bool(row["stop_triggered"]),
        "stop_reason": str(row["stop_reason"]),
        "step_status": str(row["step_status"]),
        "blocking_reasons": _list_text(row["blocking_reasons"]),
    }


def write_summary(rows: list[dict[str, Any]], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Few-Step Training Dry Run v0 Summary",
        "",
        "This step runs a tightly capped four-step dry run for the masked covalent training loop.",
        "It instantiates an in-memory DiffSBDD model, builds one AdamW optimizer, computes masked loss, calls backward, and executes optimizer.step for each fixed mask level.",
        "It does not call training_step or trainer.fit.",
        "It does not load or save checkpoints.",
        "It does not save a model.",
        "It does not run formal training or fine-tuning.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## Run Boundary",
        f"- stage: {manifest['stage']}",
        f"- previous_stage: {manifest['previous_stage']}",
        f"- loop_name: {manifest['loop_name']}",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- cuda_available: {manifest['cuda_available']}",
        f"- cuda_device_name: {manifest['cuda_device_name']}",
        f"- optimizer_class: {manifest['optimizer_class']}",
        f"- optimizer_lr: {manifest['optimizer_lr']}",
        f"- optimizer_weight_decay: {manifest['optimizer_weight_decay']}",
        f"- max_steps: {manifest['max_steps']}",
        f"- executed_steps: {manifest['executed_steps']}",
        f"- mask_order: {', '.join(manifest['mask_order'])}",
        f"- mask_levels_seen: {', '.join(manifest['mask_levels_seen'])}",
        f"- batch_size: {manifest['batch_size']}",
        f"- shuffle: {manifest['shuffle']}",
        f"- seed: {manifest['seed']}",
        "",
        "## Step Results",
        "| step | mask_level | target | context | loss_total | backward | optimizer_step | grad_norm | max_grad_abs | param_delta_norm | max_param_delta_abs | status |",
        "| ---: | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {step} | {mask} | {target} | {context} | {loss:.6f} | {backward} | {opt} | {grad:.6f} | {max_grad:.6f} | {delta:.8f} | {max_delta:.8f} | {status} |".format(
                step=row["step"],
                mask=row["mask_level"],
                target=row["target_atom_count"],
                context=row["context_atom_count"],
                loss=float(row["loss_total"]),
                backward=row["backward_success"],
                opt=row["optimizer_step_success"],
                grad=float(row["grad_norm"]),
                max_grad=float(row["max_grad_abs"]),
                delta=float(row["param_delta_norm"]),
                max_delta=float(row["max_param_delta_abs"]),
                status=row["step_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Global Result",
            f"- all_steps_passed: {manifest['all_steps_passed']}",
            f"- all_losses_finite: {manifest['all_losses_finite']}",
            f"- all_loss_total_requires_grad: {manifest['all_loss_total_requires_grad']}",
            f"- all_backward_success: {manifest['all_backward_success']}",
            f"- all_optimizer_steps_success: {manifest['all_optimizer_steps_success']}",
            f"- all_gradients_finite: {manifest['all_gradients_finite']}",
            f"- all_gradients_nonzero: {manifest['all_gradients_nonzero']}",
            f"- all_parameter_updates_finite: {manifest['all_parameter_updates_finite']}",
            f"- all_parameter_updates_nonzero: {manifest['all_parameter_updates_nonzero']}",
            f"- all_post_step_params_finite: {manifest['all_post_step_params_finite']}",
            f"- stop_triggered: {manifest['stop_triggered']}",
            f"- stop_reason: {manifest['stop_reason']}",
            f"- checkpoint_loaded: {manifest['checkpoint_loaded']}",
            f"- checkpoint_saved: {manifest['checkpoint_saved']}",
            f"- training_step_called: {manifest['training_step_called']}",
            f"- trainer_fit_called: {manifest['trainer_fit_called']}",
            f"- checkpoint_written: {manifest['checkpoint_written']}",
            f"- archive_created: {manifest['archive_created']}",
            f"- model_saved: {manifest['model_saved']}",
            f"- formal_training_executed: {manifest['formal_training_executed']}",
            f"- real_finetune_executed: {manifest['real_finetune_executed']}",
            f"- original_source_files_modified: {manifest['original_source_files_modified']}",
            f"- forbidden_artifacts_created: {manifest['forbidden_artifacts_created']}",
            f"- all_checks_passed: {manifest['all_checks_passed']}",
            "",
            "## Recommendation",
            f"- {manifest['recommended_next_step']}",
            "",
            "This is still a bounded dry run, not formal training. The next step should review the dry-run evidence and training boundary before any longer run or checkpoint policy is considered.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run few-step masked covalent training dry run without checkpoint.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR)
    parser.add_argument("--max_steps", type=int, default=MAX_STEPS)
    return parser.parse_args()


def run(device: str = "auto", lr: float = DEFAULT_LR, max_steps: int = MAX_STEPS) -> int:
    result = run_few_step_training_dry_run_v0(device=device, lr=lr, max_steps=max_steps)
    rows = result["rows"]
    manifest = result["summary"]
    write_csv(
        [report_row(row) for row in rows],
        DEFAULT_ROOT / "few_step_training_dry_run_report.csv",
        REPORT_COLUMNS,
    )
    write_json(manifest, DEFAULT_ROOT / "few_step_training_dry_run_preview_manifest.json")
    write_summary(rows, manifest, "docs/few_step_training_dry_run_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device, lr=args.lr, max_steps=args.max_steps)
    print("few_step_training_dry_run_v0_passed" if code == 0 else "few_step_training_dry_run_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

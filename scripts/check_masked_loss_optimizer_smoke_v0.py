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

from covalent_ext.masked_loss_optimizer_smoke import (  # noqa: E402
    DEFAULT_LR,
    DEFAULT_ROOT,
    DEFAULT_WEIGHT_DECAY,
    OPTIMIZER_CLASS,
    PREVIOUS_STAGE,
    SAFETY_FALSE_FIELDS,
    STAGE,
    run_masked_loss_optimizer_smoke_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10n_backward_smoke_passed",
    "requested_device",
    "resolved_device",
    "cuda_available",
    "cuda_device_name",
    "mask_level",
    "target_atom_count",
    "context_atom_count",
    "ligand_atom_count",
    "loss_original_scalar",
    "loss_masked_x_scalar",
    "loss_masked_h_scalar",
    "loss_total_dry_scalar",
    "loss_total_dry_finite",
    "loss_total_dry_requires_grad",
    "backward_called",
    "backward_success",
    "optimizer_class",
    "optimizer_lr",
    "optimizer_weight_decay",
    "optimizer_step_executed",
    "optimizer_step_success",
    "parameter_count",
    "trainable_parameter_count",
    "parameters_with_grad",
    "trainable_parameters_with_grad",
    "total_grad_norm",
    "max_grad_abs",
    "finite_gradients",
    "nonzero_gradients",
    "grad_nan_count",
    "grad_inf_count",
    "parameters_compared",
    "trainable_parameters_compared",
    "parameters_changed",
    "trainable_parameters_changed",
    "total_param_delta_norm",
    "max_param_delta_abs",
    "finite_parameter_delta",
    "nonzero_parameter_delta",
    "post_step_param_nan_count",
    "post_step_param_inf_count",
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "checkpoint_written",
    "archive_created",
    "model_saved",
    "original_source_files_modified",
    "smoke_status",
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


def report_row(result: dict[str, Any]) -> dict[str, str]:
    row = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10n_backward_smoke_passed": "true",
        "requested_device": str(result["requested_device"]),
        "resolved_device": str(result["resolved_device"]),
        "cuda_available": _bool(result["cuda_available"]),
        "cuda_device_name": str(result["cuda_device_name"]),
        "mask_level": str(result["mask_level"]),
        "target_atom_count": str(result["target_atom_count"]),
        "context_atom_count": str(result["context_atom_count"]),
        "ligand_atom_count": str(result["ligand_atom_count"]),
        "loss_original_scalar": str(result["loss_original_scalar"]),
        "loss_masked_x_scalar": str(result["loss_masked_x_scalar"]),
        "loss_masked_h_scalar": str(result["loss_masked_h_scalar"]),
        "loss_total_dry_scalar": str(result["loss_total_dry_scalar"]),
        "loss_total_dry_finite": _bool(result["loss_total_dry_finite"]),
        "loss_total_dry_requires_grad": _bool(result["loss_total_dry_requires_grad"]),
        "backward_called": _bool(result["backward_called"]),
        "backward_success": _bool(result["backward_success"]),
        "optimizer_class": str(result["optimizer_class"]),
        "optimizer_lr": str(result["optimizer_lr"]),
        "optimizer_weight_decay": str(result["optimizer_weight_decay"]),
        "optimizer_step_executed": _bool(result["optimizer_step_executed"]),
        "optimizer_step_success": _bool(result["optimizer_step_success"]),
        "parameter_count": str(result["parameter_count"]),
        "trainable_parameter_count": str(result["trainable_parameter_count"]),
        "parameters_with_grad": str(result["parameters_with_grad"]),
        "trainable_parameters_with_grad": str(result["trainable_parameters_with_grad"]),
        "total_grad_norm": str(result["total_grad_norm"]),
        "max_grad_abs": str(result["max_grad_abs"]),
        "finite_gradients": _bool(result["finite_gradients"]),
        "nonzero_gradients": _bool(result["nonzero_gradients"]),
        "grad_nan_count": str(result["grad_nan_count"]),
        "grad_inf_count": str(result["grad_inf_count"]),
        "parameters_compared": str(result["parameters_compared"]),
        "trainable_parameters_compared": str(result["trainable_parameters_compared"]),
        "parameters_changed": str(result["parameters_changed"]),
        "trainable_parameters_changed": str(result["trainable_parameters_changed"]),
        "total_param_delta_norm": str(result["total_param_delta_norm"]),
        "max_param_delta_abs": str(result["max_param_delta_abs"]),
        "finite_parameter_delta": _bool(result["finite_parameter_delta"]),
        "nonzero_parameter_delta": _bool(result["nonzero_parameter_delta"]),
        "post_step_param_nan_count": str(result["post_step_param_nan_count"]),
        "post_step_param_inf_count": str(result["post_step_param_inf_count"]),
        "original_source_files_modified": _bool(result["original_source_files_modified"]),
        "smoke_status": str(result["smoke_status"]),
        "blocking_reasons": _list_text(result["blocking_reasons"]),
    }
    for field_name in SAFETY_FALSE_FIELDS:
        row[field_name] = "false"
    return row


def write_summary(rows: list[dict[str, Any]], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Masked Loss Optimizer Smoke v0 Summary",
        "",
        "This step runs the first one-step optimizer smoke for the masked covalent loss.",
        "It runs forward, computes masked loss, calls backward, and executes one optimizer.step().",
        "It does not call training_step or trainer.fit.",
        "It does not load or save checkpoints.",
        "It does not save a model.",
        "It does not run formal training or fine-tuning.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## Device And Optimizer",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- cuda_available: {manifest['cuda_available']}",
        f"- cuda_device_name: {manifest['cuda_device_name']}",
        f"- optimizer_class: {manifest['optimizer_class']}",
        f"- optimizer_lr: {manifest['optimizer_lr']}",
        f"- optimizer_weight_decay: {manifest['optimizer_weight_decay']}",
        "",
        "## One-Step Results",
        "| mask_level | target | context | loss_total_dry | backward | optimizer_step | parameters_changed | trainable_parameters_changed | total_param_delta_norm | max_param_delta_abs | finite_delta | nonzero_delta |",
        "| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {mask} | {target} | {context} | {loss:.6f} | {backward} | {opt} | {changed} | {train_changed} | {delta:.8f} | {max_delta:.8f} | {finite} | {nonzero} |".format(
                mask=row["mask_level"],
                target=row["target_atom_count"],
                context=row["context_atom_count"],
                loss=float(row["loss_total_dry_scalar"]),
                backward=row["backward_success"],
                opt=row["optimizer_step_success"],
                changed=row["parameters_changed"],
                train_changed=row["trainable_parameters_changed"],
                delta=float(row["total_param_delta_norm"]),
                max_delta=float(row["max_param_delta_abs"]),
                finite=row["finite_parameter_delta"],
                nonzero=row["nonzero_parameter_delta"],
            )
        )
    lines.extend(
        [
            "",
            "## Global Result",
            f"- all_mask_levels_passed: {manifest['all_mask_levels_passed']}",
            f"- all_backward_success: {manifest['all_backward_success']}",
            f"- all_optimizer_steps_success: {manifest['all_optimizer_steps_success']}",
            f"- all_gradients_finite: {manifest['all_gradients_finite']}",
            f"- all_gradients_nonzero: {manifest['all_gradients_nonzero']}",
            f"- all_parameter_updates_finite: {manifest['all_parameter_updates_finite']}",
            f"- all_parameter_updates_nonzero: {manifest['all_parameter_updates_nonzero']}",
            f"- all_post_step_params_finite: {manifest['all_post_step_params_finite']}",
            f"- checkpoint_loaded: {manifest['checkpoint_loaded']}",
            f"- checkpoint_saved: {manifest['checkpoint_saved']}",
            f"- model_saved: {manifest['model_saved']}",
            f"- training_executed: {manifest['training_executed']}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
            "The next step is training loop design without checkpoint, not formal training.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run masked loss optimizer one-step smoke without checkpoint.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR)
    return parser.parse_args()


def run(device: str = "auto", lr: float = DEFAULT_LR) -> int:
    result = run_masked_loss_optimizer_smoke_v0(device=device, lr=lr)
    rows = result["rows"]
    manifest = result["summary"]
    write_csv(
        [report_row(row) for row in rows],
        DEFAULT_ROOT / "masked_loss_optimizer_smoke_report.csv",
        REPORT_COLUMNS,
    )
    write_json(manifest, DEFAULT_ROOT / "masked_loss_optimizer_smoke_preview_manifest.json")
    write_summary(rows, manifest, "docs/masked_loss_optimizer_smoke_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device, lr=args.lr)
    print("masked_loss_optimizer_smoke_v0_passed" if code == 0 else "masked_loss_optimizer_smoke_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

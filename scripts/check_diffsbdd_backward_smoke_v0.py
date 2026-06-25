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

from covalent_ext.diffsbdd_backward_smoke import DEFAULT_ROOT, STAGE, run_real_diffsbdd_backward_smoke_v0  # noqa: E402


REPORT_COLUMNS = [
    "stage",
    "requested_device",
    "resolved_device",
    "cuda_available",
    "cuda_device_count",
    "cuda_device_name",
    "mask_level",
    "batch_size",
    "model_class_name",
    "model_initialized",
    "model_mode",
    "parameter_count",
    "trainable_parameter_count",
    "forward_called",
    "forward_success",
    "output0_shape",
    "output0_is_loss_like",
    "loss_reduction",
    "scalar_loss",
    "scalar_loss_finite",
    "backward_called",
    "backward_success",
    "parameters_with_grad",
    "trainable_parameters_with_grad",
    "total_grad_norm",
    "max_grad_abs",
    "finite_gradients",
    "nonzero_gradients",
    "grad_nan_count",
    "grad_inf_count",
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "optimizer_step_executed",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "checkpoint_written",
    "smoke_status",
    "blocking_reasons",
]


def _bool(value: bool) -> str:
    return str(bool(value)).lower()


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
    return {
        "stage": STAGE,
        "requested_device": result["requested_device"],
        "resolved_device": result["resolved_device"],
        "cuda_available": _bool(result["cuda_available"]),
        "cuda_device_count": str(result["cuda_device_count"]),
        "cuda_device_name": result["cuda_device_name"],
        "mask_level": result["mask_level"],
        "batch_size": str(result["batch_size"]),
        "model_class_name": result["model_class_name"],
        "model_initialized": _bool(result["model_initialized"]),
        "model_mode": result["model_mode"],
        "parameter_count": str(result["parameter_count"]),
        "trainable_parameter_count": str(result["trainable_parameter_count"]),
        "forward_called": _bool(result["forward_called"]),
        "forward_success": _bool(result["forward_success"]),
        "output0_shape": str(result["output0_shape"]),
        "output0_is_loss_like": _bool(result["output0_is_loss_like"]),
        "loss_reduction": result["loss_reduction"],
        "scalar_loss": str(result["scalar_loss"]),
        "scalar_loss_finite": _bool(result["scalar_loss_finite"]),
        "backward_called": _bool(result["backward_called"]),
        "backward_success": _bool(result["backward_success"]),
        "parameters_with_grad": str(result["parameters_with_grad"]),
        "trainable_parameters_with_grad": str(result["trainable_parameters_with_grad"]),
        "total_grad_norm": str(result["total_grad_norm"]),
        "max_grad_abs": str(result["max_grad_abs"]),
        "finite_gradients": _bool(result["finite_gradients"]),
        "nonzero_gradients": _bool(result["nonzero_gradients"]),
        "grad_nan_count": str(result["grad_nan_count"]),
        "grad_inf_count": str(result["grad_inf_count"]),
        "checkpoint_loaded": _bool(result["checkpoint_loaded"]),
        "checkpoint_saved": _bool(result["checkpoint_saved"]),
        "training_step_called": _bool(result["training_step_called"]),
        "optimizer_step_executed": _bool(result["optimizer_step_executed"]),
        "trainer_fit_called": _bool(result["trainer_fit_called"]),
        "training_executed": _bool(result["training_executed"]),
        "real_finetune_executed": _bool(result["real_finetune_executed"]),
        "checkpoint_written": _bool(result["checkpoint_written"]),
        "smoke_status": result["smoke_status"],
        "blocking_reasons": ";".join(result["blocking_reasons"]),
    }


def preview_manifest(result: dict[str, Any]) -> dict[str, Any]:
    passed = result["smoke_status"] == "passed"
    return {
        "stage": STAGE,
        "previous_stage": "diffsbdd_forward_loss_semantics_review_without_backward_v0",
        "step10g_loss_semantics_passed": True,
        "requested_device": result["requested_device"],
        "resolved_device": result["resolved_device"],
        "cuda_available": result["cuda_available"],
        "cuda_device_count": result["cuda_device_count"],
        "cuda_device_name": result["cuda_device_name"],
        "mask_level": result["mask_level"],
        "batch_size": result["batch_size"],
        "model_class_name": result["model_class_name"],
        "model_initialized": result["model_initialized"],
        "model_mode": result["model_mode"],
        "parameter_count": result["parameter_count"],
        "trainable_parameter_count": result["trainable_parameter_count"],
        "forward_called": result["forward_called"],
        "forward_success": result["forward_success"],
        "output0_shape": result["output0_shape"],
        "loss_reduction": result["loss_reduction"],
        "scalar_loss_finite": result["scalar_loss_finite"],
        "backward_called": result["backward_called"],
        "backward_success": result["backward_success"],
        "parameters_with_grad": result["parameters_with_grad"],
        "trainable_parameters_with_grad": result["trainable_parameters_with_grad"],
        "total_grad_norm": result["total_grad_norm"],
        "max_grad_abs": result["max_grad_abs"],
        "finite_gradients": result["finite_gradients"],
        "nonzero_gradients": result["nonzero_gradients"],
        "grad_nan_count": result["grad_nan_count"],
        "grad_inf_count": result["grad_inf_count"],
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "checkpoint_written": False,
        "archive_created": False,
        "all_checks_passed": passed,
        "important_limitation": "original DiffSBDD loss is full-ligand objective; mask-aware covalent loss is not implemented yet",
        "recommended_next_step": "masked_loss_adapter_design_without_diffsbdd_modification" if passed else "manual_backward_smoke_review",
    }


def write_summary(result: dict[str, Any], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Backward Smoke v0 Summary",
        "",
        "This step is the first real DiffSBDD loss.backward smoke on the covalent batch.",
        "It does not load checkpoints.",
        "It does not call training_step.",
        "It does not run an optimizer step.",
        "It does not call trainer.fit.",
        "It does not save a model.",
        "It does not train or fine-tune.",
        "It does not modify DiffSBDD or equivariant_diffusion.",
        "",
        f"- requested_device: {result['requested_device']}",
        f"- resolved_device: {result['resolved_device']}",
        f"- cuda_available: {result['cuda_available']}",
        f"- cuda_device_name: {result['cuda_device_name']}",
        f"- mask_level: {result['mask_level']}",
        f"- model_mode: {result['model_mode']}",
        f"- loss_reduction: {result['loss_reduction']}",
        f"- scalar_loss_finite: {result['scalar_loss_finite']}",
        f"- backward_success: {result['backward_success']}",
        f"- finite_gradients: {result['finite_gradients']}",
        f"- nonzero_gradients: {result['nonzero_gradients']}",
        f"- parameters_with_grad: {result['parameters_with_grad']}",
        f"- trainable_parameters_with_grad: {result['trainable_parameters_with_grad']}",
        f"- total_grad_norm: {result['total_grad_norm']}",
        f"- max_grad_abs: {result['max_grad_abs']}",
        f"- grad_nan_count: {result['grad_nan_count']}",
        f"- grad_inf_count: {result['grad_inf_count']}",
        "",
        "Limitation: this only proves the original DiffSBDD full-ligand loss can backpropagate.",
        "It does not prove that masked covalent loss is implemented.",
        "A masked loss adapter is still required.",
        "",
        f"- recommended_next_step: {preview['recommended_next_step']}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    result = run_real_diffsbdd_backward_smoke_v0(device=args.device, mask_level=args.mask_level)
    preview = preview_manifest(result)
    write_csv([report_row(result)], args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(result, preview, args.output_md)
    return 0 if result["smoke_status"] == "passed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real DiffSBDD backward smoke without checkpoint.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--mask_level", default="A_warhead_only")
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_backward_smoke_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "diffsbdd_backward_smoke_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/diffsbdd_backward_smoke_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code = run(args)
    print("diffsbdd_backward_smoke_v0_passed" if code == 0 else "diffsbdd_backward_smoke_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

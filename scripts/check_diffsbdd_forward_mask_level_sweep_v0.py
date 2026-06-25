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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.diffsbdd_forward_mask_sweep import DEFAULT_ROOT, STAGE, run_diffsbdd_forward_mask_level_sweep_v0  # noqa: E402


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
    "parameter_count",
    "trainable_parameter_count",
    "selected_forward_call_style",
    "ligand_x_shape",
    "ligand_one_hot_shape",
    "pocket_x_shape",
    "pocket_one_hot_shape",
    "ligand_mask_shape",
    "pocket_mask_shape",
    "target_atom_count",
    "context_atom_count",
    "forward_called",
    "forward_success",
    "output_type",
    "output_keys",
    "tensor_output_shapes",
    "finite_tensor_outputs",
    "scalar_loss_like_output_finite",
    "forward_exception_type",
    "forward_exception_message",
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "backward_called",
    "optimizer_step_executed",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "smoke_status",
    "blocking_reasons",
]


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


def _bool(value: bool) -> str:
    return str(bool(value)).lower()


def _list_text(values: list[str]) -> str:
    return ";".join(str(value) for value in values)


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
        "parameter_count": str(result["parameter_count"]),
        "trainable_parameter_count": str(result["trainable_parameter_count"]),
        "selected_forward_call_style": result["selected_forward_call_style"],
        "ligand_x_shape": str(result["ligand_x_shape"]),
        "ligand_one_hot_shape": str(result["ligand_one_hot_shape"]),
        "pocket_x_shape": str(result["pocket_x_shape"]),
        "pocket_one_hot_shape": str(result["pocket_one_hot_shape"]),
        "ligand_mask_shape": str(result["ligand_mask_shape"]),
        "pocket_mask_shape": str(result["pocket_mask_shape"]),
        "target_atom_count": str(result["target_atom_count"]),
        "context_atom_count": str(result["context_atom_count"]),
        "forward_called": _bool(result["forward_called"]),
        "forward_success": _bool(result["forward_success"]),
        "output_type": result["output_type"],
        "output_keys": _list_text(result["output_keys"]),
        "tensor_output_shapes": json.dumps(result["tensor_output_shapes"], sort_keys=True),
        "finite_tensor_outputs": _bool(result["finite_tensor_outputs"]),
        "scalar_loss_like_output_finite": _bool(result["scalar_loss_like_output_finite"]),
        "forward_exception_type": result["forward_exception_type"],
        "forward_exception_message": result["forward_exception_message"],
        "checkpoint_loaded": _bool(result["checkpoint_loaded"]),
        "checkpoint_saved": _bool(result["checkpoint_saved"]),
        "training_step_called": _bool(result["training_step_called"]),
        "backward_called": _bool(result["backward_called"]),
        "optimizer_step_executed": _bool(result["optimizer_step_executed"]),
        "trainer_fit_called": _bool(result["trainer_fit_called"]),
        "training_executed": _bool(result["training_executed"]),
        "real_finetune_executed": _bool(result["real_finetune_executed"]),
        "smoke_status": result["smoke_status"],
        "blocking_reasons": _list_text(result["blocking_reasons"]),
    }


def preview_manifest(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": result["stage"],
        "previous_stage": result["previous_stage"],
        "step10e_single_forward_passed": result["step10e_single_forward_passed"],
        "requested_device": result["requested_device"],
        "resolved_device": result["resolved_device"],
        "cuda_available": result["cuda_available"],
        "cuda_device_count": result["cuda_device_count"],
        "cuda_device_name": result["cuda_device_name"],
        "model_class_name": result["model_class_name"],
        "selected_forward_call_style": result["selected_forward_call_style"],
        "mask_levels_checked": result["mask_levels_checked"],
        "report_row_count": result["report_row_count"],
        "all_mask_levels_passed": result["all_mask_levels_passed"],
        "target_atom_count_by_mask_level": result["target_atom_count_by_mask_level"],
        "context_atom_count_by_mask_level": result["context_atom_count_by_mask_level"],
        "forward_success_by_mask_level": result["forward_success_by_mask_level"],
        "finite_tensor_outputs_by_mask_level": result["finite_tensor_outputs_by_mask_level"],
        "scalar_loss_like_output_finite_by_mask_level": result["scalar_loss_like_output_finite_by_mask_level"],
        "output_type_by_mask_level": result["output_type_by_mask_level"],
        "tensor_output_shapes_by_mask_level": result["tensor_output_shapes_by_mask_level"],
        "checkpoint_loaded": result["checkpoint_loaded"],
        "checkpoint_saved": result["checkpoint_saved"],
        "training_step_called": result["training_step_called"],
        "backward_called": result["backward_called"],
        "optimizer_step_executed": result["optimizer_step_executed"],
        "trainer_fit_called": result["trainer_fit_called"],
        "training_executed": result["training_executed"],
        "real_finetune_executed": result["real_finetune_executed"],
        "archive_created": result["archive_created"],
        "all_checks_passed": result["all_checks_passed"],
        "recommended_next_step": result["recommended_next_step"],
    }


def write_summary(report_rows: list[dict[str, str]], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Forward Mask-level Sweep v0 Summary",
        "",
        "This step calls the real DiffSBDD forward path for all four mask levels: A, B, B2, and C.",
        "It does not load a checkpoint.",
        "It does not call training_step.",
        "It does not run backward.",
        "It does not run an optimizer step.",
        "It does not call trainer.fit.",
        "It does not train or fine-tune.",
        "It does not save a model.",
        "It does not modify DiffSBDD or equivariant_diffusion.",
        "This is still not training; it is a forward sweep only.",
        "",
        f"- requested_device: {preview['requested_device']}",
        f"- resolved_device: {preview['resolved_device']}",
        f"- cuda_available: {preview['cuda_available']}",
        f"- cuda_device_name: {preview['cuda_device_name']}",
        f"- all_mask_levels_passed: {preview['all_mask_levels_passed']}",
        "",
        "| mask_level | target_atom_count | context_atom_count | forward_success | output_type | finite_tensor_outputs |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            f"| {row['mask_level']} | {row['target_atom_count']} | {row['context_atom_count']} | "
            f"{row['forward_success']} | {row['output_type']} | {row['finite_tensor_outputs']} |"
        )
    lines.extend(
        [
            "",
            f"- checkpoint_loaded: {preview['checkpoint_loaded']}",
            f"- checkpoint_saved: {preview['checkpoint_saved']}",
            f"- training_step_called: {preview['training_step_called']}",
            f"- backward_called: {preview['backward_called']}",
            f"- optimizer_step_executed: {preview['optimizer_step_executed']}",
            f"- trainer_fit_called: {preview['trainer_fit_called']}",
            f"- training_executed: {preview['training_executed']}",
            f"- real_finetune_executed: {preview['real_finetune_executed']}",
            f"- recommended_next_step: {preview['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    result = run_diffsbdd_forward_mask_level_sweep_v0(device=args.device)
    rows = [report_row(row) for row in result["rows"]]
    preview = preview_manifest(result)
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(rows, preview, args.output_md)
    return 0 if result["all_mask_levels_passed"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DiffSBDD forward mask-level sweep without checkpoint.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_forward_mask_level_sweep_report.csv"))
    parser.add_argument(
        "--output_manifest_json",
        default=str(DEFAULT_ROOT / "diffsbdd_forward_mask_level_sweep_preview_manifest.json"),
    )
    parser.add_argument("--output_md", default="docs/diffsbdd_forward_mask_level_sweep_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code = run(args)
    print("diffsbdd_forward_mask_level_sweep_v0_passed" if code == 0 else "diffsbdd_forward_mask_level_sweep_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

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

from covalent_ext.diffsbdd_forward_shape_smoke import DEFAULT_ROOT, run_diffsbdd_single_batch_forward_shape_smoke_v0  # noqa: E402


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


def rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_step10d_inputs(report_csv: Path, manifest_json: Path) -> bool:
    rows = rows_from_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    if len(rows) != 1 or rows[0].get("smoke_status") != "passed":
        raise ValueError("Step 10D model instantiation report is not passed")
    expected = {
        "model_initialized": True,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "forward_called": False,
        "training_step_called": False,
        "training_executed": False,
    }
    for key, value in expected.items():
        if manifest.get(key) is not value:
            raise ValueError(f"Step 10D manifest invalid for {key}: {manifest.get(key)!r}")
    if manifest.get("recommended_next_step") != "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint":
        raise ValueError("Step 10D recommended next step is not single-batch forward shape smoke")
    return True


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
        "stage": "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint_v0",
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


def preview_manifest(result: dict[str, Any], step10d_passed: bool) -> dict[str, Any]:
    passed = result["smoke_status"] == "passed"
    return {
        "stage": "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint_v0",
        "previous_stage": "diffsbdd_model_instantiation_dry_run_without_checkpoint_v0",
        "step10d_instantiation_passed": step10d_passed,
        "requested_device": result["requested_device"],
        "resolved_device": result["resolved_device"],
        "cuda_available": result["cuda_available"],
        "cuda_device_count": result["cuda_device_count"],
        "cuda_device_name": result["cuda_device_name"],
        "mask_level": result["mask_level"],
        "batch_size": result["batch_size"],
        "model_class_name": result["model_class_name"],
        "model_initialized": result["model_initialized"],
        "parameter_count": result["parameter_count"],
        "trainable_parameter_count": result["trainable_parameter_count"],
        "forward_called": result["forward_called"],
        "forward_success": result["forward_success"],
        "selected_forward_call_style": result["selected_forward_call_style"],
        "output_type": result["output_type"],
        "output_keys": result["output_keys"],
        "tensor_output_shapes": result["tensor_output_shapes"],
        "finite_tensor_outputs": result["finite_tensor_outputs"],
        "scalar_loss_like_output_finite": result["scalar_loss_like_output_finite"],
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": False,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "archive_created": False,
        "all_checks_passed": passed,
        "recommended_next_step": "diffsbdd_forward_mask_level_sweep_without_checkpoint" if passed else "manual_forward_interface_review",
    }


def write_summary(result: dict[str, Any], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Single-batch Forward Shape Smoke v0 Summary",
        "",
        "This step calls the real DiffSBDD forward path for the first time, without loading a checkpoint.",
        "It is a single-batch shape smoke only.",
        "It does not call training_step.",
        "It does not run backward.",
        "It does not run an optimizer step.",
        "It does not call trainer.fit.",
        "It does not save a model.",
        "It does not modify DiffSBDD or equivariant_diffusion.",
        "",
        f"- requested_device: {result['requested_device']}",
        f"- resolved_device: {result['resolved_device']}",
        f"- cuda_available: {result['cuda_available']}",
        f"- cuda_device_name: {result['cuda_device_name']}",
        f"- mask_level: {result['mask_level']}",
        f"- model_initialized: {result['model_initialized']}",
        f"- forward_called: {result['forward_called']}",
        f"- forward_success: {result['forward_success']}",
        f"- selected_forward_call_style: {result['selected_forward_call_style']}",
        f"- output_type: {result['output_type']}",
        f"- output_keys: {result['output_keys']}",
        f"- tensor_output_shapes: {result['tensor_output_shapes']}",
        f"- finite_tensor_outputs: {result['finite_tensor_outputs']}",
        f"- scalar_loss_like_output_finite: {result['scalar_loss_like_output_finite']}",
    ]
    if result["forward_exception_type"]:
        lines.extend(
            [
                "",
                "## Forward Exception",
                f"- type: {result['forward_exception_type']}",
                f"- message: {result['forward_exception_message']}",
                f"- blocking_reasons: {result['blocking_reasons']}",
            ]
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
    step10d_passed = validate_step10d_inputs(Path(args.instantiation_report_csv), Path(args.instantiation_manifest_json))
    result = run_diffsbdd_single_batch_forward_shape_smoke_v0(device=args.device, mask_level=args.mask_level)
    preview = preview_manifest(result, step10d_passed)
    write_csv([report_row(result)], args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(result, preview, args.output_md)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DiffSBDD single-batch forward shape smoke without checkpoint.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--mask_level", default="A_warhead_only")
    parser.add_argument("--instantiation_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_model_instantiation_dry_run_report.csv"))
    parser.add_argument("--instantiation_manifest_json", default=str(DEFAULT_ROOT / "diffsbdd_model_instantiation_dry_run_preview_manifest.json"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_single_batch_forward_shape_smoke_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "diffsbdd_single_batch_forward_shape_smoke_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/diffsbdd_single_batch_forward_shape_smoke_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code = run(args)
    report = rows_from_csv(args.output_report_csv)[0]
    print("diffsbdd_single_batch_forward_shape_smoke_v0_passed" if report["smoke_status"] == "passed" else "diffsbdd_single_batch_forward_shape_smoke_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

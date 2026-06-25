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

from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import (  # noqa: E402
    DEFAULT_ROOT,
    PREVIOUS_STAGE,
    SAFETY_FALSE_FIELDS,
    STAGE,
    run_atomwise_loss_hook_prototype_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10j_hook_design_passed",
    "requested_device",
    "resolved_device",
    "cuda_available",
    "cuda_device_name",
    "mask_level",
    "model_initialized",
    "model_mode",
    "forward_no_probe_called",
    "forward_probe_called",
    "forward_no_probe_success",
    "forward_probe_success",
    "default_behavior_preserved",
    "output0_allclose",
    "output1_scalar_allclose",
    "eps_t_lig_captured",
    "net_out_lig_captured",
    "ligand_mask_flat_available",
    "eps_t_lig_shape",
    "net_out_lig_shape",
    "ligand_mask_flat_shape",
    "net_out_lig_requires_grad",
    "tensor_first_dim_matches_ligand_atoms",
    "target_mask_nonempty",
    "target_mask_matches_ligand_atoms",
    "residual_shape",
    "residual_x_shape",
    "residual_h_shape",
    "residual_x_finite",
    "residual_h_finite",
    "can_compute_masked_x_loss_later",
    "can_compute_masked_h_loss_later",
    "original_methods_restored",
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "backward_called",
    "optimizer_step_executed",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "checkpoint_written",
    "archive_created",
    "smoke_status",
    "blocking_reasons",
]


def _bool(value: Any) -> str:
    return str(bool(value)).lower()


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


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
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10j_hook_design_passed": _bool(not result.get("forward_exception_type")),
        "requested_device": str(result["requested_device"]),
        "resolved_device": str(result["resolved_device"]),
        "cuda_available": _bool(result["cuda_available"]),
        "cuda_device_name": str(result["cuda_device_name"]),
        "mask_level": str(result["mask_level"]),
        "model_initialized": _bool(result["model_initialized"]),
        "model_mode": str(result["model_mode"]),
        "forward_no_probe_called": _bool(result["forward_no_probe_called"]),
        "forward_probe_called": _bool(result["forward_probe_called"]),
        "forward_no_probe_success": _bool(result["forward_no_probe_success"]),
        "forward_probe_success": _bool(result["forward_probe_success"]),
        "default_behavior_preserved": _bool(result["default_behavior_preserved"]),
        "output0_allclose": _bool(result["output0_allclose"]),
        "output1_scalar_allclose": _bool(result["output1_scalar_allclose"]),
        "eps_t_lig_captured": _bool(result["eps_t_lig_captured"]),
        "net_out_lig_captured": _bool(result["net_out_lig_captured"]),
        "ligand_mask_flat_available": _bool(result["ligand_mask_flat_available"]),
        "eps_t_lig_shape": _json_text(result["eps_t_lig_shape"]),
        "net_out_lig_shape": _json_text(result["net_out_lig_shape"]),
        "ligand_mask_flat_shape": _json_text(result["ligand_mask_flat_shape"]),
        "net_out_lig_requires_grad": _bool(result["net_out_lig_requires_grad"]),
        "tensor_first_dim_matches_ligand_atoms": _bool(result["tensor_first_dim_matches_ligand_atoms"]),
        "target_mask_nonempty": _bool(result["target_mask_nonempty"]),
        "target_mask_matches_ligand_atoms": _bool(result["target_mask_matches_ligand_atoms"]),
        "residual_shape": _json_text(result["residual_shape"]),
        "residual_x_shape": _json_text(result["residual_x_shape"]),
        "residual_h_shape": _json_text(result["residual_h_shape"]),
        "residual_x_finite": _bool(result["residual_x_finite"]),
        "residual_h_finite": _bool(result["residual_h_finite"]),
        "can_compute_masked_x_loss_later": _bool(result["can_compute_masked_x_loss_later"]),
        "can_compute_masked_h_loss_later": _bool(result["can_compute_masked_h_loss_later"]),
        "original_methods_restored": _bool(result["original_methods_restored"]),
        "checkpoint_loaded": "false",
        "checkpoint_saved": "false",
        "training_step_called": "false",
        "backward_called": "false",
        "optimizer_step_executed": "false",
        "trainer_fit_called": "false",
        "training_executed": "false",
        "real_finetune_executed": "false",
        "checkpoint_written": "false",
        "archive_created": "false",
        "smoke_status": str(result["smoke_status"]),
        "blocking_reasons": _list_text(result["blocking_reasons"]),
    }


def preview_manifest(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10j_hook_design_passed": not bool(result.get("forward_exception_type")),
        "requested_device": result["requested_device"],
        "resolved_device": result["resolved_device"],
        "cuda_available": result["cuda_available"],
        "cuda_device_name": result["cuda_device_name"],
        "mask_level": result["mask_level"],
        "model_initialized": result["model_initialized"],
        "model_mode": result["model_mode"],
        "default_behavior_preserved": result["default_behavior_preserved"],
        "output0_allclose": result["output0_allclose"],
        "output1_scalar_allclose": result["output1_scalar_allclose"],
        "captured_tensor_contract": {
            "required": ["eps_t_lig", "net_out_lig", "ligand_mask_flat"],
            "adapter_supplied": ["ligand_target_mask_flat", "ligand_context_mask_flat", "generation_mask_flat"],
        },
        "eps_t_lig_shape": result["eps_t_lig_shape"],
        "net_out_lig_shape": result["net_out_lig_shape"],
        "ligand_mask_flat_shape": result["ligand_mask_flat_shape"],
        "net_out_lig_requires_grad": result["net_out_lig_requires_grad"],
        "tensor_first_dim_matches_ligand_atoms": result["tensor_first_dim_matches_ligand_atoms"],
        "target_mask_nonempty": result["target_mask_nonempty"],
        "target_mask_matches_ligand_atoms": result["target_mask_matches_ligand_atoms"],
        "residual_shape": result["residual_shape"],
        "residual_x_shape": result["residual_x_shape"],
        "residual_h_shape": result["residual_h_shape"],
        "residual_x_finite": result["residual_x_finite"],
        "residual_h_finite": result["residual_h_finite"],
        "can_compute_masked_x_loss_later": result["can_compute_masked_x_loss_later"],
        "can_compute_masked_h_loss_later": result["can_compute_masked_h_loss_later"],
        "original_methods_restored": result["original_methods_restored"],
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": False,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "checkpoint_written": False,
        "archive_created": False,
        "original_source_files_modified": result["original_source_files_modified"],
        "all_checks_passed": result["smoke_status"] == "passed",
        "recommended_next_step": (
            "atomwise_loss_hook_shape_sweep_without_backward"
            if result["smoke_status"] == "passed"
            else "manual_atomwise_hook_prototype_review"
        ),
    }


def write_summary(result: dict[str, Any], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Atomwise Loss Hook Prototype v0 Summary",
        "",
        "This step implements a runtime hook/probe prototype.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "It does not load or save checkpoints.",
        "It does not call training_step, backward, optimizer, trainer.fit, training, or fine-tuning.",
        "",
        "## Device",
        f"- requested_device: {result['requested_device']}",
        f"- resolved_device: {result['resolved_device']}",
        f"- cuda_available: {result['cuda_available']}",
        f"- cuda_device_name: {result['cuda_device_name']}",
        "",
        "## Forward Behavior",
        f"- mask_level: {result['mask_level']}",
        f"- model_initialized: {result['model_initialized']}",
        f"- model_mode: {result['model_mode']}",
        f"- forward_no_probe_success: {result['forward_no_probe_success']}",
        f"- forward_probe_success: {result['forward_probe_success']}",
        f"- default_behavior_preserved: {result['default_behavior_preserved']}",
        f"- output0_allclose: {result['output0_allclose']}",
        f"- output1_scalar_allclose: {result['output1_scalar_allclose']}",
        "",
        "## Captured Tensors",
        f"- eps_t_lig_shape: {result['eps_t_lig_shape']}",
        f"- net_out_lig_shape: {result['net_out_lig_shape']}",
        f"- ligand_mask_flat_shape: {result['ligand_mask_flat_shape']}",
        f"- net_out_lig_requires_grad: {result['net_out_lig_requires_grad']}",
        f"- tensor_first_dim_matches_ligand_atoms: {result['tensor_first_dim_matches_ligand_atoms']}",
        f"- target_mask_nonempty: {result['target_mask_nonempty']}",
        f"- residual_x_shape: {result['residual_x_shape']}",
        f"- residual_h_shape: {result['residual_h_shape']}",
        f"- residual_x_finite: {result['residual_x_finite']}",
        f"- residual_h_finite: {result['residual_h_finite']}",
        f"- can_compute_masked_x_loss_later: {result['can_compute_masked_x_loss_later']}",
        f"- can_compute_masked_h_loss_later: {result['can_compute_masked_h_loss_later']}",
        "",
        "## Safety",
    ]
    lines.extend(f"- {field_name}: false" for field_name in SAFETY_FALSE_FIELDS)
    lines.extend(
        [
            f"- original_methods_restored: {result['original_methods_restored']}",
            f"- original_source_files_modified: {result['original_source_files_modified']}",
            "",
            "## Conclusion",
            f"- smoke_status: {result['smoke_status']}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--mask_level", default="A_warhead_only")
    return parser.parse_args()


def run(device: str = "auto", mask_level: str = "A_warhead_only") -> int:
    result = run_atomwise_loss_hook_prototype_v0(device=device, mask_level=mask_level)
    row = report_row(result)
    manifest = preview_manifest(result)
    write_csv([row], DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_prototype_report.csv", REPORT_COLUMNS)
    write_json(manifest, DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_prototype_preview_manifest.json")
    write_summary(result, manifest, "docs/diffsbdd_atomwise_loss_hook_prototype_v0_summary.md")
    return 0 if result["smoke_status"] == "passed" else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device, mask_level=args.mask_level)
    print("diffsbdd_atomwise_loss_hook_prototype_v0_passed" if code == 0 else "diffsbdd_atomwise_loss_hook_prototype_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

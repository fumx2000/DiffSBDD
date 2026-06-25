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

from covalent_ext.diffsbdd_atomwise_loss_hook_shape_sweep import (  # noqa: E402
    DEFAULT_ROOT,
    PREVIOUS_STAGE,
    SAFETY_FALSE_FIELDS,
    STAGE,
    run_atomwise_loss_hook_shape_sweep_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10k_hook_prototype_passed",
    "requested_device",
    "resolved_device",
    "cuda_available",
    "cuda_device_name",
    "mask_level",
    "target_atom_count",
    "context_atom_count",
    "ligand_atom_count",
    "model_initialized",
    "model_mode",
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
    "original_source_files_modified",
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
    row = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10k_hook_prototype_passed": "true",
        "requested_device": str(result["requested_device"]),
        "resolved_device": str(result["resolved_device"]),
        "cuda_available": _bool(result["cuda_available"]),
        "cuda_device_name": str(result["cuda_device_name"]),
        "mask_level": str(result["mask_level"]),
        "target_atom_count": str(result["target_atom_count"]),
        "context_atom_count": str(result["context_atom_count"]),
        "ligand_atom_count": str(result["ligand_atom_count"]),
        "model_initialized": _bool(result["model_initialized"]),
        "model_mode": str(result["model_mode"]),
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
        "# DiffSBDD Atomwise Loss Hook Shape Sweep v0 Summary",
        "",
        "This step extends the Step 10K atomwise runtime probe from A to A/B/B2/C mask levels.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "It does not load or save checkpoints.",
        "It does not call training_step, backward, optimizer, trainer.fit, training, or fine-tuning.",
        "It still does not compute a masked loss scalar; that is reserved for the next dry run.",
        "",
        "## Device",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- cuda_available: {manifest['cuda_available']}",
        f"- cuda_device_name: {manifest['cuda_device_name']}",
        "",
        "## Mask Sweep",
        "| mask_level | target_atoms | context_atoms | behavior_preserved | captured | residual_x | residual_h | can_masked_x | can_masked_h |",
        "| --- | ---: | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        captured = row["eps_t_lig_captured"] and row["net_out_lig_captured"] and row["ligand_mask_flat_available"]
        lines.append(
            "| {mask} | {target} | {context} | {behavior} | {captured} | {rx} | {rh} | {mx} | {mh} |".format(
                mask=row["mask_level"],
                target=row["target_atom_count"],
                context=row["context_atom_count"],
                behavior=row["default_behavior_preserved"],
                captured=captured,
                rx=row["residual_x_shape"],
                rh=row["residual_h_shape"],
                mx=row["can_compute_masked_x_loss_later"],
                mh=row["can_compute_masked_h_loss_later"],
            )
        )
    lines.extend(
        [
            "",
            "## Global Result",
            f"- all_mask_levels_passed: {manifest['all_mask_levels_passed']}",
            f"- all_default_behavior_preserved: {manifest['all_default_behavior_preserved']}",
            f"- all_atomwise_tensors_captured: {manifest['all_atomwise_tensors_captured']}",
            f"- all_residuals_finite: {manifest['all_residuals_finite']}",
            f"- all_targets_nonempty: {manifest['all_targets_nonempty']}",
            f"- all_methods_restored: {manifest['all_methods_restored']}",
            f"- all_sources_unmodified: {manifest['all_sources_unmodified']}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="auto")
    return parser.parse_args()


def run(device: str = "auto") -> int:
    result = run_atomwise_loss_hook_shape_sweep_v0(device=device)
    rows = result["rows"]
    manifest = result["summary"]
    write_csv(
        [report_row(row) for row in rows],
        DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_shape_sweep_report.csv",
        REPORT_COLUMNS,
    )
    write_json(manifest, DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_shape_sweep_preview_manifest.json")
    write_summary(rows, manifest, "docs/diffsbdd_atomwise_loss_hook_shape_sweep_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device)
    print("diffsbdd_atomwise_loss_hook_shape_sweep_v0_passed" if code == 0 else "diffsbdd_atomwise_loss_hook_shape_sweep_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

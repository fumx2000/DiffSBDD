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

from covalent_ext.masked_loss_dry_run import (  # noqa: E402
    DEFAULT_ROOT,
    PREVIOUS_STAGE,
    SAFETY_FALSE_FIELDS,
    STAGE,
    run_masked_loss_dry_run_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10l_hook_shape_sweep_passed",
    "requested_device",
    "resolved_device",
    "cuda_available",
    "cuda_device_name",
    "mask_level",
    "target_atom_count",
    "context_atom_count",
    "ligand_atom_count",
    "eps_t_lig_shape",
    "net_out_lig_shape",
    "residual_x_shape",
    "residual_h_shape",
    "loss_original_scalar",
    "loss_masked_x_scalar",
    "loss_masked_h_scalar",
    "loss_total_dry_scalar",
    "loss_original_finite",
    "loss_masked_x_finite",
    "loss_masked_h_finite",
    "loss_total_dry_finite",
    "loss_masked_x_requires_grad",
    "loss_masked_h_requires_grad",
    "loss_total_dry_requires_grad",
    "target_mask_nonempty",
    "target_mask_matches_ligand_atoms",
    "used_target_mask_not_full_ligand",
    "c_level_full_ligand_target_expected",
    "dry_run_status",
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
    "original_source_files_modified",
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
        "step10l_hook_shape_sweep_passed": "true",
        "requested_device": str(result["requested_device"]),
        "resolved_device": str(result["resolved_device"]),
        "cuda_available": _bool(result["cuda_available"]),
        "cuda_device_name": str(result["cuda_device_name"]),
        "mask_level": str(result["mask_level"]),
        "target_atom_count": str(result["target_atom_count"]),
        "context_atom_count": str(result["context_atom_count"]),
        "ligand_atom_count": str(result["ligand_atom_count"]),
        "eps_t_lig_shape": _json_text(result["eps_t_lig_shape"]),
        "net_out_lig_shape": _json_text(result["net_out_lig_shape"]),
        "residual_x_shape": _json_text(result["residual_x_shape"]),
        "residual_h_shape": _json_text(result["residual_h_shape"]),
        "loss_original_scalar": str(result["loss_original_scalar"]),
        "loss_masked_x_scalar": str(result["loss_masked_x_scalar"]),
        "loss_masked_h_scalar": str(result["loss_masked_h_scalar"]),
        "loss_total_dry_scalar": str(result["loss_total_dry_scalar"]),
        "loss_original_finite": _bool(result["loss_original_finite"]),
        "loss_masked_x_finite": _bool(result["loss_masked_x_finite"]),
        "loss_masked_h_finite": _bool(result["loss_masked_h_finite"]),
        "loss_total_dry_finite": _bool(result["loss_total_dry_finite"]),
        "loss_masked_x_requires_grad": _bool(result["loss_masked_x_requires_grad"]),
        "loss_masked_h_requires_grad": _bool(result["loss_masked_h_requires_grad"]),
        "loss_total_dry_requires_grad": _bool(result["loss_total_dry_requires_grad"]),
        "target_mask_nonempty": _bool(result["target_mask_nonempty"]),
        "target_mask_matches_ligand_atoms": _bool(result["target_mask_matches_ligand_atoms"]),
        "used_target_mask_not_full_ligand": _bool(result["used_target_mask_not_full_ligand"]),
        "c_level_full_ligand_target_expected": _bool(result["c_level_full_ligand_target_expected"]),
        "dry_run_status": str(result["dry_run_status"]),
        "original_source_files_modified": _bool(result["original_source_files_modified"]),
        "blocking_reasons": _list_text(result["blocking_reasons"]),
    }
    for field_name in SAFETY_FALSE_FIELDS:
        row[field_name] = "false"
    return row


def write_summary(rows: list[dict[str, Any]], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Masked Loss Dry Run v0 Summary",
        "",
        "This step computes masked covalent loss scalars for the first time.",
        "It does not call backward, optimizer, trainer.fit, training, or fine-tuning.",
        "It does not load or save checkpoints.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## Device",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- cuda_available: {manifest['cuda_available']}",
        f"- cuda_device_name: {manifest['cuda_device_name']}",
        "",
        "## Masked Losses",
        "| mask_level | target | context | loss_original | loss_masked_x | loss_masked_h | loss_total_dry | finite | requires_grad |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        finite = (
            row["loss_original_finite"]
            and row["loss_masked_x_finite"]
            and row["loss_masked_h_finite"]
            and row["loss_total_dry_finite"]
        )
        lines.append(
            "| {mask} | {target} | {context} | {lo:.6f} | {lx:.6f} | {lh:.6f} | {lt:.6f} | {finite} | {grad} |".format(
                mask=row["mask_level"],
                target=row["target_atom_count"],
                context=row["context_atom_count"],
                lo=float(row["loss_original_scalar"]),
                lx=float(row["loss_masked_x_scalar"]),
                lh=float(row["loss_masked_h_scalar"]),
                lt=float(row["loss_total_dry_scalar"]),
                finite=finite,
                grad=row["loss_total_dry_requires_grad"],
            )
        )
    lines.extend(
        [
            "",
            "A/B/B2 use target subsets. C is a full-ligand target by design.",
            "",
            "## Global Result",
            f"- all_mask_levels_passed: {manifest['all_mask_levels_passed']}",
            f"- all_loss_scalars_finite: {manifest['all_loss_scalars_finite']}",
            f"- all_loss_total_requires_grad: {manifest['all_loss_total_requires_grad']}",
            f"- all_target_masks_nonempty: {manifest['all_target_masks_nonempty']}",
            f"- all_expected_target_counts: {manifest['all_expected_target_counts']}",
            f"- all_expected_context_counts: {manifest['all_expected_context_counts']}",
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
    result = run_masked_loss_dry_run_v0(device=device)
    rows = result["rows"]
    manifest = result["summary"]
    write_csv([report_row(row) for row in rows], DEFAULT_ROOT / "masked_loss_dry_run_report.csv", REPORT_COLUMNS)
    write_json(manifest, DEFAULT_ROOT / "masked_loss_dry_run_preview_manifest.json")
    write_summary(rows, manifest, "docs/masked_loss_dry_run_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device)
    print("masked_loss_dry_run_v0_passed" if code == 0 else "masked_loss_dry_run_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

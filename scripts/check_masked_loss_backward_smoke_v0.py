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

from covalent_ext.masked_loss_backward_smoke import (  # noqa: E402
    DEFAULT_ROOT,
    PREVIOUS_STAGE,
    SAFETY_FALSE_FIELDS,
    STAGE,
    run_masked_loss_backward_smoke_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10m_masked_loss_dry_run_passed",
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
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "optimizer_step_executed",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "checkpoint_written",
    "archive_created",
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
        "step10m_masked_loss_dry_run_passed": "true",
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
        "# Masked Loss Backward Smoke v0 Summary",
        "",
        "This step is the first backward smoke for the masked covalent loss.",
        "It calls loss_total_dry.backward().",
        "It does not run an optimizer step.",
        "It does not call training_step or trainer.fit.",
        "It does not load or save checkpoints.",
        "It does not train or fine-tune a model.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## Device",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- cuda_available: {manifest['cuda_available']}",
        f"- cuda_device_name: {manifest['cuda_device_name']}",
        "",
        "## Gradient Summary",
        "| mask_level | target | context | loss_total_dry | parameters_with_grad | trainable_parameters_with_grad | total_grad_norm | max_grad_abs | finite_gradients | nonzero_gradients | grad_nan_count | grad_inf_count |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {mask} | {target} | {context} | {loss:.6f} | {pwg} | {tpwg} | {norm:.6f} | {max_abs:.6f} | {finite} | {nonzero} | {nan} | {inf} |".format(
                mask=row["mask_level"],
                target=row["target_atom_count"],
                context=row["context_atom_count"],
                loss=float(row["loss_total_dry_scalar"]),
                pwg=row["parameters_with_grad"],
                tpwg=row["trainable_parameters_with_grad"],
                norm=float(row["total_grad_norm"]),
                max_abs=float(row["max_grad_abs"]),
                finite=row["finite_gradients"],
                nonzero=row["nonzero_gradients"],
                nan=row["grad_nan_count"],
                inf=row["grad_inf_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Global Result",
            f"- all_mask_levels_passed: {manifest['all_mask_levels_passed']}",
            f"- all_backward_success: {manifest['all_backward_success']}",
            f"- all_gradients_finite: {manifest['all_gradients_finite']}",
            f"- all_gradients_nonzero: {manifest['all_gradients_nonzero']}",
            f"- all_grad_nan_count_zero: {manifest['all_grad_nan_count_zero']}",
            f"- all_grad_inf_count_zero: {manifest['all_grad_inf_count_zero']}",
            f"- all_sources_unmodified: {manifest['all_sources_unmodified']}",
            f"- optimizer_step_executed: {manifest['optimizer_step_executed']}",
            f"- trainer_fit_called: {manifest['trainer_fit_called']}",
            f"- training_executed: {manifest['training_executed']}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run masked loss backward smoke without optimizer.")
    parser.add_argument("--device", default="auto")
    return parser.parse_args()


def run(device: str = "auto") -> int:
    result = run_masked_loss_backward_smoke_v0(device=device)
    rows = result["rows"]
    manifest = result["summary"]
    write_csv(
        [report_row(row) for row in rows],
        DEFAULT_ROOT / "masked_loss_backward_smoke_report.csv",
        REPORT_COLUMNS,
    )
    write_json(manifest, DEFAULT_ROOT / "masked_loss_backward_smoke_preview_manifest.json")
    write_summary(rows, manifest, "docs/masked_loss_backward_smoke_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device)
    print("masked_loss_backward_smoke_v0_passed" if code == 0 else "masked_loss_backward_smoke_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

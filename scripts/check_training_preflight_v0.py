#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0  # noqa: E402
from covalent_ext.model_input_adapter import build_covalent_model_input_v0, validate_covalent_model_input_v0  # noqa: E402
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn  # noqa: E402
from covalent_ext.training_preflight import (  # noqa: E402
    move_model_input_to_device_v0,
    run_mock_training_preflight_step_v0,
    summarize_model_input_for_preflight_v0,
)


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
REPORT_COLUMNS = [
    "mask_level",
    "batch_size",
    "sample_count",
    "protein_x_shape",
    "ligand_x_shape",
    "ligand_context_x_shape",
    "ligand_target_x_shape",
    "coordinate_center_shape",
    "target_atom_count_total",
    "context_atom_count_total",
    "reactive_atom_in_target_mask_all",
    "context_target_no_overlap_all",
    "finite_coords_all",
    "no_nan",
    "no_inf",
    "mock_x_mse_on_target",
    "mock_h_mse_on_target",
    "mock_total_loss",
    "mock_total_loss_finite",
    "device",
    "checkpoint_loaded",
    "model_initialized",
    "training_executed",
    "preflight_status",
    "blocking_reasons",
]


def rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def shape_text(shape: list[int]) -> str:
    return str(shape)


def _bool(value: bool) -> str:
    return str(bool(value)).lower()


def validate_inputs(
    manifest_json: Path,
    sanity_report_csv: Path,
    dataloader_report_csv: Path,
    adapter_report_csv: Path,
    model_input_mapping_report_csv: Path,
    model_input_mapping_manifest_json: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    model_input_manifest = json.loads(model_input_mapping_manifest_json.read_text(encoding="utf-8"))
    sanity_rows = rows_from_csv(sanity_report_csv)
    dataloader_rows = rows_from_csv(dataloader_report_csv)
    adapter_rows = rows_from_csv(adapter_report_csv)
    model_input_rows = rows_from_csv(model_input_mapping_report_csv)
    if manifest.get("row_count") != 3 or len(sanity_rows) != 3 or len(dataloader_rows) != 3:
        raise ValueError("Step 9A/9B input counts are invalid")
    if len(adapter_rows) != 12 or len(model_input_rows) != 12:
        raise ValueError("Step 9C/9D input counts are invalid")
    if any(row.get("sanity_status") != "passed" for row in sanity_rows):
        raise ValueError("Step 9A sanity_report has non-passed rows")
    if any(row.get("dataloader_sanity_status") != "passed" for row in dataloader_rows):
        raise ValueError("Step 9B dataloader_sanity_report has non-passed rows")
    if any(row.get("adapter_sanity_status") != "passed" for row in adapter_rows):
        raise ValueError("Step 9C batch_adapter_sanity_report has non-passed rows")
    if any(row.get("model_input_mapping_status") != "passed" for row in model_input_rows):
        raise ValueError("Step 9D model_input_mapping_sanity_report has non-passed rows")
    if model_input_manifest.get("stage") != "covalent_model_input_mapping_mock_loss_v0":
        raise ValueError("Step 9D model input mapping manifest stage is invalid")
    if model_input_manifest.get("report_row_count") != 12 or model_input_manifest.get("all_mask_levels_passed") is not True:
        raise ValueError("Step 9D model input mapping manifest is not fully passed")
    if model_input_manifest.get("checkpoint_loaded") is not False:
        raise ValueError("Step 9D manifest indicates checkpoint_loaded")
    if model_input_manifest.get("model_initialized") is not False:
        raise ValueError("Step 9D manifest indicates model_initialized")
    if model_input_manifest.get("training_executed") is not False:
        raise ValueError("Step 9D manifest indicates training_executed")
    return manifest


def report_row_for_mask_level(
    model_input: dict[str, Any],
    validation_ok: bool,
    validation_reasons: list[str],
    summary: dict[str, Any],
    preflight: dict[str, Any],
) -> dict[str, str]:
    checks = {
        "reactive_atom_in_target_mask_all": bool(summary["reactive_atom_in_target_mask_all"]),
        "context_target_no_overlap_all": bool(summary["context_target_no_overlap_all"]),
        "finite_coords_all": bool(summary["finite_coords_all"]),
        "no_nan": bool(summary["no_nan"]),
        "no_inf": bool(summary["no_inf"]),
        "mock_total_loss_finite": bool(preflight["mock_total_loss_finite"]),
        "target_atom_count_positive": bool(preflight["target_atom_count_positive"]),
        "checkpoint_loaded": bool(preflight["checkpoint_loaded"]),
        "model_initialized": bool(preflight["model_initialized"]),
        "training_executed": bool(preflight["training_executed"]),
    }
    blockers = []
    if not validation_ok:
        blockers.extend(validation_reasons)
    for key in [
        "reactive_atom_in_target_mask_all",
        "context_target_no_overlap_all",
        "finite_coords_all",
        "no_nan",
        "no_inf",
        "mock_total_loss_finite",
        "target_atom_count_positive",
    ]:
        if not checks[key]:
            blockers.append(key)
    if model_input.get("device_transfer_error"):
        blockers.append(str(model_input["device_transfer_error"]))
    for key in ["checkpoint_loaded", "model_initialized", "training_executed"]:
        if checks[key]:
            blockers.append(key)
    return {
        "mask_level": summary["mask_level"],
        "batch_size": str(summary["batch_size"]),
        "sample_count": str(summary["sample_count"]),
        "protein_x_shape": shape_text(summary["protein_x_shape"]),
        "ligand_x_shape": shape_text(summary["ligand_x_shape"]),
        "ligand_context_x_shape": shape_text(summary["ligand_context_x_shape"]),
        "ligand_target_x_shape": shape_text(summary["ligand_target_x_shape"]),
        "coordinate_center_shape": shape_text(summary["coordinate_center_shape"]),
        "target_atom_count_total": str(summary["target_atom_count_total"]),
        "context_atom_count_total": str(summary["context_atom_count_total"]),
        "reactive_atom_in_target_mask_all": _bool(checks["reactive_atom_in_target_mask_all"]),
        "context_target_no_overlap_all": _bool(checks["context_target_no_overlap_all"]),
        "finite_coords_all": _bool(checks["finite_coords_all"]),
        "no_nan": _bool(checks["no_nan"]),
        "no_inf": _bool(checks["no_inf"]),
        "mock_x_mse_on_target": f"{preflight['x_mse_on_target']:.8g}",
        "mock_h_mse_on_target": f"{preflight['h_mse_on_target']:.8g}",
        "mock_total_loss": f"{preflight['mock_total_loss']:.8g}",
        "mock_total_loss_finite": _bool(checks["mock_total_loss_finite"]),
        "device": model_input.get("device", "cpu"),
        "checkpoint_loaded": _bool(checks["checkpoint_loaded"]),
        "model_initialized": _bool(checks["model_initialized"]),
        "training_executed": _bool(checks["training_executed"]),
        "preflight_status": "passed" if not blockers else "blocked",
        "blocking_reasons": ";".join(sorted(set(blockers))),
    }


def write_summary(report_rows: list[dict[str, str]], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Training Preflight v0 Summary",
        "",
        "This step performs a final training preflight dry-run from NPZ artifacts to model-input-like tensors.",
        "It checks data loading, batching, covalent batch adaptation, model input mapping, device transfer, and mock loss aggregation.",
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not call DiffSBDD.",
        "It does not train or fine-tune.",
        "It does not modify DiffSBDD model code.",
        "",
        f"- dataset_len: {preview['dataset_len']}",
        f"- batch_size: {preview['batch_size']}",
        f"- device: {preview['device']}",
        f"- protein_x_shape: {preview['protein_x_shape']}",
        f"- ligand_x_shape: {preview['ligand_x_shape']}",
        f"- ligand_context_x_shape: {preview['ligand_context_x_shape']}",
        f"- ligand_target_x_shape: {preview['ligand_target_x_shape']}",
        f"- mock_total_loss_all_finite: {preview['mock_total_loss_all_finite']}",
        "",
        "| mask_level | target_atom_count_total | mock_total_loss | preflight_status |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in report_rows:
        lines.append(
            f"| {row['mask_level']} | {row['target_atom_count_total']} | {row['mock_total_loss']} | {row['preflight_status']} |"
        )
    lines.extend(
        [
            "",
            "Conclusion: if all rows are passed, the next step is DiffSBDD adapter or tiny model smoke test, not another gate.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    manifest = validate_inputs(
        Path(args.manifest_json),
        Path(args.sanity_report_csv),
        Path(args.dataloader_report_csv),
        Path(args.adapter_report_csv),
        Path(args.model_input_mapping_report_csv),
        Path(args.model_input_mapping_manifest_json),
    )
    dataset = CovalentNPZDataset(args.sample_index_csv)
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    report_rows: list[dict[str, str]] = []
    preview_shapes: dict[str, list[int]] = {}
    target_counts: dict[str, int] = {}
    mock_losses: dict[str, float] = {}
    mock_loss_finite: list[bool] = []
    for mask_level in MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        model_input = build_covalent_model_input_v0(adapted)
        validation_ok, validation_reasons = validate_covalent_model_input_v0(model_input)
        model_input = move_model_input_to_device_v0(model_input, device="cpu")
        summary = summarize_model_input_for_preflight_v0(model_input)
        preflight = run_mock_training_preflight_step_v0(model_input)
        report_rows.append(report_row_for_mask_level(model_input, validation_ok, validation_reasons, summary, preflight))
        target_counts[mask_level] = int(summary["target_atom_count_total"])
        mock_losses[mask_level] = float(preflight["mock_total_loss"])
        mock_loss_finite.append(bool(preflight["mock_total_loss_finite"]))
        if not preview_shapes:
            preview_shapes = {
                "protein_x_shape": summary["protein_x_shape"],
                "ligand_x_shape": summary["ligand_x_shape"],
                "ligand_context_x_shape": summary["ligand_context_x_shape"],
                "ligand_target_x_shape": summary["ligand_target_x_shape"],
                "coordinate_center_shape": summary["coordinate_center_shape"],
            }
    all_passed = all(row["preflight_status"] == "passed" for row in report_rows)
    preview = {
        "stage": "covalent_training_preflight_dry_run_v0",
        "dataset_name": manifest.get("dataset_name"),
        "dataset_len": len(dataset),
        "batch_size": 3,
        "mask_levels_checked": len(MASK_LEVELS),
        "report_row_count": len(report_rows),
        "all_mask_levels_passed": all_passed,
        "device": "cpu",
        **preview_shapes,
        "target_atom_count_total_by_mask_level": target_counts,
        "mock_total_loss_by_mask_level": mock_losses,
        "mock_total_loss_all_finite": all(mock_loss_finite),
        "checkpoint_loaded": False,
        "model_initialized": False,
        "training_executed": False,
        "archive_created": False,
        "recommended_next_step": "diffSBDD_adapter_or_tiny_model_smoke_test",
    }
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(report_rows, preview, args.output_md)
    return 0 if all_passed and all(mock_loss_finite) else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run training preflight dry-run without loading a real model.")
    parser.add_argument("--manifest_json", default=str(DEFAULT_ROOT / "manifest.json"))
    parser.add_argument("--sample_index_csv", default=str(DEFAULT_ROOT / "sample_index.csv"))
    parser.add_argument("--sanity_report_csv", default=str(DEFAULT_ROOT / "sanity_report.csv"))
    parser.add_argument("--dataloader_report_csv", default=str(DEFAULT_ROOT / "dataloader_sanity_report.csv"))
    parser.add_argument("--adapter_report_csv", default=str(DEFAULT_ROOT / "batch_adapter_sanity_report.csv"))
    parser.add_argument("--model_input_mapping_report_csv", default=str(DEFAULT_ROOT / "model_input_mapping_sanity_report.csv"))
    parser.add_argument("--model_input_mapping_manifest_json", default=str(DEFAULT_ROOT / "model_input_mapping_preview_manifest.json"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "training_preflight_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "training_preflight_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/training_preflight_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("training_preflight_v0_passed" if code == 0 else "training_preflight_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

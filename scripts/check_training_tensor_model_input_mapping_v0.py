#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0  # noqa: E402
from covalent_ext.model_input_adapter import (  # noqa: E402
    build_covalent_model_input_v0,
    compute_mock_reconstruction_loss_v0,
    validate_covalent_model_input_v0,
)
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn  # noqa: E402


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
REPORT_COLUMNS = [
    "sample_id",
    "mask_level",
    "protein_x_shape",
    "ligand_x_shape",
    "ligand_context_x_shape",
    "ligand_target_x_shape",
    "target_atom_count",
    "reactive_atom_in_target_mask",
    "context_target_no_overlap",
    "model_input_shapes_valid",
    "centered_coords_finite",
    "mock_loss_computed",
    "mock_loss_finite",
    "checkpoint_loaded",
    "model_initialized",
    "training_executed",
    "model_input_mapping_status",
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


def shape_text(tensor: torch.Tensor) -> str:
    return str(list(tensor.shape))


def _bool(value: bool) -> str:
    return str(bool(value)).lower()


def validate_inputs(manifest_json: Path, sanity_report_csv: Path, dataloader_report_csv: Path, adapter_report_csv: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    sanity_rows = rows_from_csv(sanity_report_csv)
    dataloader_rows = rows_from_csv(dataloader_report_csv)
    adapter_rows = rows_from_csv(adapter_report_csv)
    if manifest.get("row_count") != 3 or len(sanity_rows) != 3 or len(dataloader_rows) != 3 or len(adapter_rows) != 12:
        raise ValueError("Step 9A/9B/9C input counts are invalid")
    if any(row.get("sanity_status") != "passed" for row in sanity_rows):
        raise ValueError("Step 9A sanity_report has non-passed rows")
    if any(row.get("dataloader_sanity_status") != "passed" for row in dataloader_rows):
        raise ValueError("Step 9B dataloader_sanity_report has non-passed rows")
    if any(row.get("adapter_sanity_status") != "passed" for row in adapter_rows):
        raise ValueError("Step 9C batch_adapter_sanity_report has non-passed rows")
    return manifest


def per_sample_rows(model_input: dict[str, Any], validation_ok: bool, validation_reasons: list[str], mock_loss: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    target_mask = model_input["ligand_target_mask"]
    context_mask = model_input["ligand_context_mask"]
    ligand_mask = model_input["ligand_mask"]
    protein_mask = model_input["protein_mask"]
    for idx, sample_id in enumerate(model_input["sample_id"]):
        reactive_idx = int(model_input["ligand_reactive_atom_index"][idx].item())
        valid_ligand = model_input["ligand_x"][idx][ligand_mask[idx]]
        valid_protein = model_input["protein_x"][idx][protein_mask[idx]]
        checks = {
            "reactive_atom_in_target_mask": bool(target_mask[idx, reactive_idx].item()),
            "context_target_no_overlap": not bool((context_mask[idx] & target_mask[idx]).any().item()),
            "model_input_shapes_valid": validation_ok,
            "centered_coords_finite": bool(torch.isfinite(valid_ligand).all().item() and torch.isfinite(valid_protein).all().item()),
            "mock_loss_computed": bool(mock_loss["mock_loss_computed"]),
            "mock_loss_finite": bool(mock_loss["mock_loss_finite"]),
            "checkpoint_loaded": bool(model_input["checkpoint_loaded"]),
            "model_initialized": bool(model_input["model_initialized"]),
            "training_executed": bool(model_input["training_executed"]),
        }
        blockers = [key for key in ["reactive_atom_in_target_mask", "context_target_no_overlap", "model_input_shapes_valid", "centered_coords_finite", "mock_loss_computed", "mock_loss_finite"] if not checks[key]]
        if validation_reasons:
            blockers.extend(validation_reasons)
        if checks["checkpoint_loaded"]:
            blockers.append("checkpoint_loaded")
        if checks["model_initialized"]:
            blockers.append("model_initialized")
        if checks["training_executed"]:
            blockers.append("training_executed")
        rows.append(
            {
                "sample_id": sample_id,
                "mask_level": model_input["mask_level"],
                "protein_x_shape": shape_text(model_input["protein_x"]),
                "ligand_x_shape": shape_text(model_input["ligand_x"]),
                "ligand_context_x_shape": shape_text(model_input["ligand_context_x"]),
                "ligand_target_x_shape": shape_text(model_input["ligand_target_x"]),
                "target_atom_count": str(int(target_mask[idx].sum().item())),
                "reactive_atom_in_target_mask": _bool(checks["reactive_atom_in_target_mask"]),
                "context_target_no_overlap": _bool(checks["context_target_no_overlap"]),
                "model_input_shapes_valid": _bool(checks["model_input_shapes_valid"]),
                "centered_coords_finite": _bool(checks["centered_coords_finite"]),
                "mock_loss_computed": _bool(checks["mock_loss_computed"]),
                "mock_loss_finite": _bool(checks["mock_loss_finite"]),
                "checkpoint_loaded": _bool(checks["checkpoint_loaded"]),
                "model_initialized": _bool(checks["model_initialized"]),
                "training_executed": _bool(checks["training_executed"]),
                "model_input_mapping_status": "passed" if not blockers else "blocked",
                "blocking_reasons": ";".join(sorted(set(blockers))),
            }
        )
    return rows


def write_summary(report_rows: list[dict[str, str]], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    levels = sorted({row["mask_level"] for row in report_rows})
    lines = [
        "# Training Tensor Model Input Mapping v0 Summary",
        "",
        "This step maps adapted covalent batch into model-input-like tensors.",
        "It computes mock reconstruction losses without loading any model.",
        "It does not load checkpoint.",
        "It does not initialize model.",
        "It does not train/fine-tune.",
        "It does not modify DiffSBDD model code.",
        "",
        f"- protein_x_shape: {preview['protein_x_shape']}",
        f"- ligand_x_shape: {preview['ligand_x_shape']}",
        f"- ligand_context_x_shape: {preview['ligand_context_x_shape']}",
        f"- ligand_target_x_shape: {preview['ligand_target_x_shape']}",
        f"- coordinate_center_shape: {preview['coordinate_center_shape']}",
        f"- mock_loss_all_finite: {preview['mock_loss_all_finite']}",
        "",
        "| mask_level | rows | all_passed |",
        "| --- | --- | --- |",
    ]
    for level in levels:
        level_rows = [row for row in report_rows if row["mask_level"] == level]
        lines.append(f"| {level} | {len(level_rows)} | {all(row['model_input_mapping_status'] == 'passed' for row in level_rows)} |")
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    manifest = validate_inputs(Path(args.manifest_json), Path(args.sanity_report_csv), Path(args.dataloader_report_csv), Path(args.adapter_report_csv))
    dataset = CovalentNPZDataset(args.sample_index_csv)
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    report_rows: list[dict[str, str]] = []
    preview_shapes: dict[str, list[int]] = {}
    mock_loss_finite: list[bool] = []
    for mask_level in MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        model_input = build_covalent_model_input_v0(adapted)
        ok, reasons = validate_covalent_model_input_v0(model_input)
        mock_loss = compute_mock_reconstruction_loss_v0(model_input)
        mock_loss_finite.append(bool(mock_loss["mock_loss_finite"]))
        report_rows.extend(per_sample_rows(model_input, ok, reasons, mock_loss))
        if not preview_shapes:
            preview_shapes = {
                "protein_x_shape": list(model_input["protein_x"].shape),
                "ligand_x_shape": list(model_input["ligand_x"].shape),
                "ligand_context_x_shape": list(model_input["ligand_context_x"].shape),
                "ligand_target_x_shape": list(model_input["ligand_target_x"].shape),
                "coordinate_center_shape": list(model_input["coordinate_center"].shape),
            }
    all_passed = all(row["model_input_mapping_status"] == "passed" for row in report_rows)
    preview = {
        "stage": "covalent_model_input_mapping_mock_loss_v0",
        "dataset_name": manifest.get("dataset_name"),
        "dataset_len": len(dataset),
        "batch_size": 3,
        "mask_levels_checked": len(MASK_LEVELS),
        "report_row_count": len(report_rows),
        **preview_shapes,
        "all_mask_levels_passed": all_passed,
        "mock_loss_all_finite": all(mock_loss_finite),
        "checkpoint_loaded": False,
        "model_initialized": False,
        "training_executed": False,
        "archive_created": False,
    }
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(report_rows, preview, args.output_md)
    return 0 if all_passed and all(mock_loss_finite) else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check model-input-like mapping and mock loss sanity.")
    parser.add_argument("--manifest_json", default=str(DEFAULT_ROOT / "manifest.json"))
    parser.add_argument("--sample_index_csv", default=str(DEFAULT_ROOT / "sample_index.csv"))
    parser.add_argument("--sanity_report_csv", default=str(DEFAULT_ROOT / "sanity_report.csv"))
    parser.add_argument("--dataloader_report_csv", default=str(DEFAULT_ROOT / "dataloader_sanity_report.csv"))
    parser.add_argument("--adapter_report_csv", default=str(DEFAULT_ROOT / "batch_adapter_sanity_report.csv"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "model_input_mapping_sanity_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "model_input_mapping_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/training_tensor_model_input_mapping_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("model_input_mapping_v0_passed" if code == 0 else "model_input_mapping_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

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

from covalent_ext.batch_adapter import (  # noqa: E402
    MASK_LEVEL_TO_BATCH_KEY,
    adapt_covalent_batch_for_model_v0,
    validate_adapted_covalent_batch_v0,
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
    "ligand_atom_count",
    "protein_atom_count",
    "generation_mask_count",
    "fixed_ligand_atom_count",
    "reactive_atom_in_ligand_mask",
    "reactive_atom_in_generation_mask",
    "generation_mask_subset_ligand_mask",
    "fixed_mask_subset_ligand_mask",
    "generation_fixed_no_overlap",
    "context_mask_equals_fixed_mask",
    "target_mask_equals_generation_mask",
    "coordinate_center_finite",
    "centered_ligand_coords_finite",
    "centered_protein_coords_finite",
    "no_nan",
    "no_inf",
    "checkpoint_loaded",
    "model_initialized",
    "training_executed",
    "adapter_sanity_status",
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


def _bool(value: bool) -> str:
    return str(bool(value)).lower()


def validate_inputs(manifest_json: Path, sanity_report_csv: Path, dataloader_report_csv: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    sanity_rows = rows_from_csv(sanity_report_csv)
    dataloader_rows = rows_from_csv(dataloader_report_csv)
    if manifest.get("row_count") != 3 or len(sanity_rows) != 3 or len(dataloader_rows) != 3:
        raise ValueError("Step 9A/9B input counts are invalid")
    if any(row.get("sanity_status") != "passed" for row in sanity_rows):
        raise ValueError("Step 9A sanity_report has non-passed rows")
    if any(row.get("dataloader_sanity_status") != "passed" for row in dataloader_rows):
        raise ValueError("Step 9B dataloader_sanity_report has non-passed rows")
    return manifest


def per_sample_rows(adapted: dict[str, Any], validation_ok: bool, validation_reasons: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    ligand_mask = adapted["ligand_atom_mask"]
    protein_mask = adapted["protein_atom_mask"]
    generation_mask = adapted["generation_mask"]
    fixed_mask = adapted["fixed_ligand_atom_mask"]
    context_mask = adapted["ligand_context_mask"]
    target_mask = adapted["ligand_target_mask"]
    for idx, sample_id in enumerate(adapted["sample_id"]):
        reactive_idx = int(adapted["ligand_reactive_atom_index"][idx].item())
        valid_ligand_centered = adapted["ligand_coords_centered"][idx][ligand_mask[idx]]
        valid_protein_centered = adapted["protein_coords_centered"][idx][protein_mask[idx]]
        checks = {
            "reactive_atom_in_ligand_mask": bool(ligand_mask[idx, reactive_idx].item()),
            "reactive_atom_in_generation_mask": bool(generation_mask[idx, reactive_idx].item()),
            "generation_mask_subset_ligand_mask": not bool((generation_mask[idx] & ~ligand_mask[idx]).any().item()),
            "fixed_mask_subset_ligand_mask": not bool((fixed_mask[idx] & ~ligand_mask[idx]).any().item()),
            "generation_fixed_no_overlap": not bool((generation_mask[idx] & fixed_mask[idx]).any().item()),
            "context_mask_equals_fixed_mask": bool(torch.equal(context_mask[idx], fixed_mask[idx])),
            "target_mask_equals_generation_mask": bool(torch.equal(target_mask[idx], generation_mask[idx])),
            "coordinate_center_finite": bool(torch.isfinite(adapted["coordinate_center"][idx]).all().item()),
            "centered_ligand_coords_finite": bool(torch.isfinite(valid_ligand_centered).all().item()),
            "centered_protein_coords_finite": bool(torch.isfinite(valid_protein_centered).all().item()),
            "no_nan": not bool(torch.isnan(valid_ligand_centered).any().item() or torch.isnan(valid_protein_centered).any().item()),
            "no_inf": not bool(torch.isinf(valid_ligand_centered).any().item() or torch.isinf(valid_protein_centered).any().item()),
        }
        blockers = [key for key, value in checks.items() if not value]
        if not validation_ok:
            blockers.extend(validation_reasons)
        rows.append(
            {
                "sample_id": sample_id,
                "mask_level": adapted["mask_level"],
                "ligand_atom_count": str(int(ligand_mask[idx].sum().item())),
                "protein_atom_count": str(int(protein_mask[idx].sum().item())),
                "generation_mask_count": str(int(generation_mask[idx].sum().item())),
                "fixed_ligand_atom_count": str(int(fixed_mask[idx].sum().item())),
                **{key: _bool(value) for key, value in checks.items()},
                "checkpoint_loaded": _bool(adapted["checkpoint_loaded"]),
                "model_initialized": _bool(adapted["model_initialized"]),
                "training_executed": _bool(adapted["training_executed"]),
                "adapter_sanity_status": "passed" if not blockers else "blocked",
                "blocking_reasons": ";".join(sorted(set(blockers))),
            }
        )
    return rows


def write_summary(report_rows: list[dict[str, str]], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    levels = sorted({row["mask_level"] for row in report_rows})
    lines = [
        "# Training Tensor Batch Adapter v0 Summary",
        "",
        "This step adapts one DataLoader batch into a model-input-like covalent batch dictionary.",
        "It checks A/B/B2/C mask levels.",
        "It checks coordinate centering, generation/fixed masks, reactive atom inclusion, and shape consistency.",
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not train or fine-tune.",
        "It does not modify DiffSBDD model code.",
        "",
        f"- ligand_atom_coords_shape: {preview['ligand_atom_coords_shape']}",
        f"- protein_atom_coords_shape: {preview['protein_atom_coords_shape']}",
        f"- adapted_ligand_coords_shape: {preview['adapted_ligand_coords_shape']}",
        f"- adapted_protein_coords_shape: {preview['adapted_protein_coords_shape']}",
        f"- coordinate_center_shape: {preview['coordinate_center_shape']}",
        f"- all_mask_levels_passed: {preview['all_mask_levels_passed']}",
        "",
        "| mask_level | rows | all_passed |",
        "| --- | --- | --- |",
    ]
    for level in levels:
        level_rows = [row for row in report_rows if row["mask_level"] == level]
        lines.append(f"| {level} | {len(level_rows)} | {all(row['adapter_sanity_status'] == 'passed' for row in level_rows)} |")
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    manifest = validate_inputs(Path(args.manifest_json), Path(args.sanity_report_csv), Path(args.dataloader_report_csv))
    dataset = CovalentNPZDataset(args.sample_index_csv)
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    report_rows: list[dict[str, str]] = []
    adapted_shapes: dict[str, list[int]] = {}
    for mask_level in MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        ok, reasons = validate_adapted_covalent_batch_v0(adapted)
        report_rows.extend(per_sample_rows(adapted, ok, reasons))
        if not adapted_shapes:
            adapted_shapes = {
                "adapted_ligand_coords_shape": list(adapted["ligand_coords"].shape),
                "adapted_protein_coords_shape": list(adapted["protein_coords"].shape),
                "coordinate_center_shape": list(adapted["coordinate_center"].shape),
            }
    all_passed = all(row["adapter_sanity_status"] == "passed" for row in report_rows)
    preview = {
        "dataset_name": manifest.get("dataset_name"),
        "stage": "covalent_batch_adapter_sanity_v0",
        "dataset_len": len(dataset),
        "batch_size": 3,
        "mask_levels_checked": len(MASK_LEVELS),
        "report_row_count": len(report_rows),
        "sample_ids": batch["sample_id"],
        "ligand_atom_coords_shape": list(batch["ligand_atom_coords"].shape),
        "protein_atom_coords_shape": list(batch["protein_atom_coords"].shape),
        **adapted_shapes,
        "ligand_padded_length": int(batch["ligand_atom_coords"].shape[1]),
        "protein_padded_length": int(batch["protein_atom_coords"].shape[1]),
        "all_mask_levels_passed": all_passed,
        "checkpoint_loaded": False,
        "model_initialized": False,
        "training_executed": False,
        "archive_created": False,
    }
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(report_rows, preview, args.output_md)
    return 0 if all_passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check covalent batch adapter sanity for the Step 9B DataLoader batch.")
    parser.add_argument("--manifest_json", default=str(DEFAULT_ROOT / "manifest.json"))
    parser.add_argument("--sample_index_csv", default=str(DEFAULT_ROOT / "sample_index.csv"))
    parser.add_argument("--sanity_report_csv", default=str(DEFAULT_ROOT / "sanity_report.csv"))
    parser.add_argument("--dataloader_report_csv", default=str(DEFAULT_ROOT / "dataloader_sanity_report.csv"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "batch_adapter_sanity_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "batch_adapter_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/training_tensor_batch_adapter_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("batch_adapter_sanity_v0_passed" if code == 0 else "batch_adapter_sanity_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

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

from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn  # noqa: E402


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
REPORT_COLUMNS = [
    "sample_id",
    "ligand_atom_count",
    "protein_atom_count",
    "ligand_padded_length",
    "protein_padded_length",
    "ligand_atom_mask_sum_matches",
    "protein_atom_mask_sum_matches",
    "reactive_atom_in_range",
    "reactive_atom_in_warhead_mask",
    "generation_masks_shape_valid",
    "padding_masks_valid",
    "coords_finite",
    "no_nan",
    "no_inf",
    "dataloader_sanity_status",
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


def validate_inputs(manifest_path: Path, sample_index_path: Path, sanity_report_path: Path) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sample_rows = rows_from_csv(sample_index_path)
    sanity_rows = rows_from_csv(sanity_report_path)
    if manifest.get("row_count") != 3 or len(sample_rows) != 3 or len(sanity_rows) != 3:
        raise ValueError("Step 9A manifest/sample_index/sanity_report counts are not all 3")
    if any(row.get("sanity_status") != "passed" for row in sanity_rows):
        raise ValueError("Step 9A sanity_report has non-passed rows")
    return manifest, sample_rows, sanity_rows


def batch_sanity_rows(batch: dict[str, Any], sample_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    sample_by_id = {row["sample_id"]: row for row in sample_rows}
    ligand_lmax = int(batch["ligand_atom_coords"].shape[1])
    protein_pmax = int(batch["protein_atom_coords"].shape[1])
    generation_keys = [
        "generation_mask_A_warhead_only",
        "generation_mask_B_linker_warhead",
        "generation_mask_B2_scaffold_warhead",
        "generation_mask_C_scaffold_linker_warhead",
    ]
    rows: list[dict[str, str]] = []
    for idx, sample_id in enumerate(batch["sample_id"]):
        expected = sample_by_id[sample_id]
        ligand_count = int(expected["ligand_atom_count"])
        protein_count = int(expected["protein_atom_count"])
        reactive_idx = int(batch["ligand_reactive_atom_index"][idx].item())
        ligand_mask = batch["ligand_atom_mask"][idx]
        protein_mask = batch["protein_atom_mask"][idx]
        generation_shape_valid = all(batch[key].shape == batch["ligand_atom_mask"].shape for key in generation_keys)
        ligand_padding_valid = not ligand_mask[ligand_count:].any().item() if ligand_count < ligand_lmax else True
        protein_padding_valid = not protein_mask[protein_count:].any().item() if protein_count < protein_pmax else True
        coords = torch.cat(
            [
                batch["ligand_atom_coords"][idx, :ligand_count].reshape(-1),
                batch["protein_atom_coords"][idx, :protein_count].reshape(-1),
            ]
        )
        checks = {
            "ligand_atom_mask_sum_matches": int(ligand_mask.sum().item()) == ligand_count,
            "protein_atom_mask_sum_matches": int(protein_mask.sum().item()) == protein_count,
            "reactive_atom_in_range": 0 <= reactive_idx < ligand_count,
            "reactive_atom_in_warhead_mask": bool(batch["warhead_atom_mask"][idx, reactive_idx].item()),
            "generation_masks_shape_valid": generation_shape_valid,
            "padding_masks_valid": ligand_padding_valid and protein_padding_valid,
            "coords_finite": bool(torch.isfinite(coords).all().item()),
            "no_nan": not bool(torch.isnan(coords).any().item()),
            "no_inf": not bool(torch.isinf(coords).any().item()),
        }
        rows.append(
            {
                "sample_id": sample_id,
                "ligand_atom_count": str(ligand_count),
                "protein_atom_count": str(protein_count),
                "ligand_padded_length": str(ligand_lmax),
                "protein_padded_length": str(protein_pmax),
                **{key: _bool(value) for key, value in checks.items()},
                "dataloader_sanity_status": "passed" if all(checks.values()) else "blocked",
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], report_rows: list[dict[str, str]], batch: dict[str, Any], output_md: str | Path) -> None:
    path = Path(output_md)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Training Tensor NPZ DataLoader v0 Summary",
        "",
        "This step builds a minimal PyTorch Dataset and DataLoader from Step 9A `.npz` artifacts.",
        "It checks one batch with batch_size=3.",
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not train or fine-tune.",
        "It does not modify DiffSBDD model code.",
        "",
        f"- dataset_name: {manifest.get('dataset_name')}",
        f"- ligand_atom_coords_shape: {list(batch['ligand_atom_coords'].shape)}",
        f"- protein_atom_coords_shape: {list(batch['protein_atom_coords'].shape)}",
        f"- sanity_passed: {all(row['dataloader_sanity_status'] == 'passed' for row in report_rows)}",
        "",
        "| sample_id | ligand_atom_count | protein_atom_count | dataloader_sanity_status |",
        "| --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(f"| {row['sample_id']} | {row['ligand_atom_count']} | {row['protein_atom_count']} | {row['dataloader_sanity_status']} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest_json)
    sample_index_path = Path(args.sample_index_csv)
    sanity_report_path = Path(args.sanity_report_csv)
    manifest, sample_rows, _sanity_rows = validate_inputs(manifest_path, sample_index_path, sanity_report_path)
    dataset = CovalentNPZDataset(sample_index_path)
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    report_rows = batch_sanity_rows(batch, sample_rows)
    preview = {
        "dataset_name": manifest.get("dataset_name"),
        "stage": "torch_dataset_dataloader_batch_sanity_v0",
        "dataset_len": len(dataset),
        "batch_size": 3,
        "batch_count_checked": 1,
        "sample_ids": batch["sample_id"],
        "ligand_atom_coords_shape": list(batch["ligand_atom_coords"].shape),
        "protein_atom_coords_shape": list(batch["protein_atom_coords"].shape),
        "ligand_atom_mask_shape": list(batch["ligand_atom_mask"].shape),
        "protein_atom_mask_shape": list(batch["protein_atom_mask"].shape),
        "ligand_padded_length": int(batch["ligand_atom_coords"].shape[1]),
        "protein_padded_length": int(batch["protein_atom_coords"].shape[1]),
        "dataloader_created": True,
        "dataset_created": True,
        "checkpoint_loaded": False,
        "model_initialized": False,
        "training_executed": False,
        "archive_created": False,
        "sanity_passed": all(row["dataloader_sanity_status"] == "passed" for row in report_rows),
    }
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(manifest, report_rows, batch, args.output_md)
    return 0 if preview["sanity_passed"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check minimal PyTorch DataLoader batch sanity for Step 9A NPZ files.")
    parser.add_argument("--manifest_json", default=str(DEFAULT_ROOT / "manifest.json"))
    parser.add_argument("--sample_index_csv", default=str(DEFAULT_ROOT / "sample_index.csv"))
    parser.add_argument("--sanity_report_csv", default=str(DEFAULT_ROOT / "sanity_report.csv"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "dataloader_sanity_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "batch_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/training_tensor_npz_dataloader_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("dataloader_sanity_v0_passed" if code == 0 else "dataloader_sanity_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

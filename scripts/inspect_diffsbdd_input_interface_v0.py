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
from covalent_ext.diffsbdd_input_adapter import (  # noqa: E402
    DIRECT_MAPPING_FIELDS,
    MISSING_OR_UNCERTAIN_FIELDS,
    PREVIEW_DIFFSBDD_KEYS,
    build_diffsbdd_like_input_from_covalent_v0,
    validate_diffsbdd_like_input_v0,
)
from covalent_ext.model_input_adapter import (  # noqa: E402
    REQUIRED_MODEL_INPUT_KEYS,
    build_covalent_model_input_v0,
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
SOURCE_FILES_TO_INSPECT = [
    "dataset.py",
    "lightning_modules.py",
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/dynamics.py",
    "equivariant_diffusion/conditional_model.py",
    "generate_ligands.py",
    "optimize.py",
]
DETECTED_DIFFSBDD_ENTRYPOINTS = [
    "dataset.ProcessedLigandPocketDataset.collate_fn",
    "lightning_modules.LigandPocketDDPM.get_ligand_and_pocket",
    "lightning_modules.LigandPocketDDPM.forward",
    "lightning_modules.LigandPocketDDPM.training_step",
    "equivariant_diffusion.en_diffusion.EnVariationalDiffusion.forward",
    "equivariant_diffusion.dynamics.EGNNDynamics.forward",
    "equivariant_diffusion.dynamics.EGNNDynamics.get_edges",
    "equivariant_diffusion.conditional_model.ConditionalDDPM.sample_given_pocket",
    "equivariant_diffusion.conditional_model.ConditionalDDPM.inpaint",
    "generate_ligands.main",
    "optimize.main",
]
DETECTED_EXPECTED_INPUT_FIELDS = [
    "data.lig_coords",
    "data.lig_one_hot",
    "data.lig_mask",
    "data.num_lig_atoms",
    "data.pocket_coords",
    "data.pocket_one_hot",
    "data.pocket_mask",
    "data.num_pocket_nodes",
    "ligand.x",
    "ligand.one_hot",
    "ligand.size",
    "ligand.mask",
    "pocket.x",
    "pocket.one_hot",
    "pocket.size",
    "pocket.mask",
    "lig_fixed",
]
REPORT_COLUMNS = [
    "mask_level",
    "batch_size",
    "ligand_x_shape",
    "protein_x_shape",
    "ligand_mask_shape",
    "protein_mask_shape",
    "generation_mask_shape",
    "target_atom_count",
    "context_atom_count",
    "diffsbdd_like_keys_present",
    "required_covalent_keys_present",
    "direct_mapping_field_count",
    "missing_or_uncertain_field_count",
    "shape_sanity_passed",
    "mask_sanity_passed",
    "checkpoint_loaded",
    "diffsbdd_model_initialized",
    "diffsbdd_model_called",
    "training_executed",
    "adapter_status",
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


def shape_text(value: torch.Tensor) -> str:
    return str(list(value.shape))


def validate_tiny_smoke_inputs(report_csv: Path, manifest_json: Path) -> dict[str, Any]:
    rows = rows_from_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    if len(rows) != 4:
        raise ValueError("Step 10A tiny smoke report row count is invalid")
    if any(row.get("smoke_status") != "passed" for row in rows):
        raise ValueError("Step 10A tiny smoke report has non-passed rows")
    if manifest.get("stage") != "tiny_covalent_model_training_smoke_v0":
        raise ValueError("Step 10A tiny smoke manifest stage is invalid")
    if manifest.get("report_row_count") != 4 or manifest.get("all_mask_levels_passed") is not True:
        raise ValueError("Step 10A tiny smoke manifest is not fully passed")
    for key in ["checkpoint_loaded", "checkpoint_saved", "diffsbdd_model_initialized", "real_training_executed"]:
        if manifest.get(key) is not False:
            raise ValueError(f"Step 10A manifest indicates {key}")
    return manifest


def source_interface_summary() -> dict[str, list[str]]:
    inspected = []
    for relative in SOURCE_FILES_TO_INSPECT:
        path = REPO_ROOT / relative
        if path.is_file():
            path.read_text(encoding="utf-8", errors="replace")
            inspected.append(relative)
    return {
        "source_files_inspected": inspected,
        "detected_diffsbdd_entrypoints": list(DETECTED_DIFFSBDD_ENTRYPOINTS),
        "detected_expected_input_fields": list(DETECTED_EXPECTED_INPUT_FIELDS),
    }


def row_for_mask_level(
    mask_level: str,
    model_input: dict[str, Any],
    diffsbdd_like: dict[str, Any],
    model_input_ok: bool,
    model_input_reasons: list[str],
    diffsbdd_ok: bool,
    diffsbdd_reasons: list[str],
) -> dict[str, str]:
    required_covalent_keys_present = REQUIRED_MODEL_INPUT_KEYS.issubset(model_input)
    diffsbdd_like_keys_present = PREVIEW_DIFFSBDD_KEYS.issubset(diffsbdd_like)
    ligand = diffsbdd_like["ligand"]
    pocket = diffsbdd_like["pocket"]
    ligand_mask = diffsbdd_like["ligand_mask"]
    protein_mask = diffsbdd_like["protein_mask"]
    generation_mask = diffsbdd_like["generation_mask"]
    context_mask = diffsbdd_like["ligand_context_mask"]
    target_mask = diffsbdd_like["ligand_target_mask"]
    shape_sanity = (
        ligand["x"].ndim == 2
        and ligand["x"].shape[1] == 3
        and pocket["x"].ndim == 2
        and pocket["x"].shape[1] == 3
        and ligand["one_hot"].shape[0] == ligand["x"].shape[0]
        and pocket["one_hot"].shape[0] == pocket["x"].shape[0]
        and ligand["mask"].shape[0] == ligand["x"].shape[0]
        and pocket["mask"].shape[0] == pocket["x"].shape[0]
        and diffsbdd_like["lig_fixed"].shape == (ligand["x"].shape[0], 1)
        and diffsbdd_like["xh_ligand"].shape[0] == ligand["x"].shape[0]
        and diffsbdd_like["xh_pocket"].shape[0] == pocket["x"].shape[0]
    )
    mask_sanity = (
        bool((generation_mask & ~ligand_mask).any().item()) is False
        and bool((context_mask & target_mask).any().item()) is False
        and bool(torch.equal(generation_mask, target_mask))
        and int(target_mask.sum().item()) > 0
        and bool(torch.equal(ligand["size"], ligand_mask.sum(dim=1).to(dtype=torch.long)))
        and bool(torch.equal(pocket["size"], protein_mask.sum(dim=1).to(dtype=torch.long)))
    )
    blockers: list[str] = []
    if not model_input_ok:
        blockers.extend(model_input_reasons)
    if not diffsbdd_ok:
        blockers.extend(diffsbdd_reasons)
    for name, value in [
        ("required_covalent_keys_missing", required_covalent_keys_present),
        ("diffsbdd_like_keys_missing", diffsbdd_like_keys_present),
        ("shape_sanity_failed", shape_sanity),
        ("mask_sanity_failed", mask_sanity),
    ]:
        if not value:
            blockers.append(name)
    for key in ["checkpoint_loaded", "diffsbdd_model_initialized", "diffsbdd_model_called", "training_executed"]:
        if diffsbdd_like[key] is not False:
            blockers.append(key)
    return {
        "mask_level": mask_level,
        "batch_size": str(int(model_input["batch_size"])),
        "ligand_x_shape": shape_text(diffsbdd_like["ligand_x"]),
        "protein_x_shape": shape_text(diffsbdd_like["protein_x"]),
        "ligand_mask_shape": shape_text(diffsbdd_like["ligand_mask"]),
        "protein_mask_shape": shape_text(diffsbdd_like["protein_mask"]),
        "generation_mask_shape": shape_text(diffsbdd_like["generation_mask"]),
        "target_atom_count": str(int(target_mask.sum().item())),
        "context_atom_count": str(int(context_mask.sum().item())),
        "diffsbdd_like_keys_present": _bool(diffsbdd_like_keys_present),
        "required_covalent_keys_present": _bool(required_covalent_keys_present),
        "direct_mapping_field_count": str(len(DIRECT_MAPPING_FIELDS)),
        "missing_or_uncertain_field_count": str(len(MISSING_OR_UNCERTAIN_FIELDS)),
        "shape_sanity_passed": _bool(shape_sanity),
        "mask_sanity_passed": _bool(mask_sanity),
        "checkpoint_loaded": _bool(diffsbdd_like["checkpoint_loaded"]),
        "diffsbdd_model_initialized": _bool(diffsbdd_like["diffsbdd_model_initialized"]),
        "diffsbdd_model_called": _bool(diffsbdd_like["diffsbdd_model_called"]),
        "training_executed": _bool(diffsbdd_like["training_executed"]),
        "adapter_status": "passed" if not blockers else "blocked",
        "blocking_reasons": ";".join(sorted(set(blockers))),
    }


def write_summary(report_rows: list[dict[str, str]], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Input Interface v0 Summary",
        "",
        "This step inspects the DiffSBDD input interface and builds a covalent-to-DiffSBDD-like adapter preview.",
        "It does not initialize or call a real DiffSBDD model.",
        "It does not load or save checkpoint.",
        "It does not train or fine-tune.",
        "It does not modify DiffSBDD model code or equivariant_diffusion.",
        "",
        "## Inspected Entry Points",
    ]
    for item in preview["detected_diffsbdd_entrypoints"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Expected Input Fields"])
    for item in preview["detected_expected_input_fields"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Direct Covalent Mapping Fields"])
    for item in preview["direct_mapping_fields"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Missing Or Uncertain Fields"])
    for item in preview["missing_or_uncertain_fields"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Mask Level Results",
            "",
            "| mask_level | target_atom_count | shape_sanity_passed | mask_sanity_passed | adapter_status |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for row in report_rows:
        lines.append(
            f"| {row['mask_level']} | {row['target_atom_count']} | {row['shape_sanity_passed']} | {row['mask_sanity_passed']} | {row['adapter_status']} |"
        )
    lines.extend(
        [
            "",
            f"- checkpoint_loaded: {preview['checkpoint_loaded']}",
            f"- diffsbdd_model_initialized: {preview['diffsbdd_model_initialized']}",
            f"- diffsbdd_model_called: {preview['diffsbdd_model_called']}",
            f"- training_executed: {preview['training_executed']}",
            f"- recommended_next_step: {preview['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    validate_tiny_smoke_inputs(Path(args.tiny_smoke_report_csv), Path(args.tiny_smoke_manifest_json))
    source_summary = source_interface_summary()
    dataset = CovalentNPZDataset(args.sample_index_csv)
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    report_rows: list[dict[str, str]] = []
    model_input_fields: list[str] = []
    for mask_level in MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        model_input = build_covalent_model_input_v0(adapted)
        model_input_ok, model_input_reasons = validate_covalent_model_input_v0(model_input)
        diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
        diffsbdd_ok, diffsbdd_reasons = validate_diffsbdd_like_input_v0(diffsbdd_like)
        if not model_input_fields:
            model_input_fields = sorted(model_input.keys())
        report_rows.append(
            row_for_mask_level(
                mask_level,
                model_input,
                diffsbdd_like,
                model_input_ok,
                model_input_reasons,
                diffsbdd_ok,
                diffsbdd_reasons,
            )
        )
    all_passed = all(row["adapter_status"] == "passed" for row in report_rows)
    recommended_next_step = "diffsbdd_adapter_shape_smoke_without_checkpoint" if all_passed else "manual_diffsbdd_interface_review"
    preview = {
        "stage": "diffsbdd_input_interface_inspection_adapter_v0",
        "dataset_len": len(dataset),
        "batch_size": 3,
        "mask_levels_checked": len(MASK_LEVELS),
        "report_row_count": len(report_rows),
        "all_mask_levels_passed": all_passed,
        "source_files_inspected": source_summary["source_files_inspected"],
        "detected_diffsbdd_entrypoints": source_summary["detected_diffsbdd_entrypoints"],
        "detected_expected_input_fields": source_summary["detected_expected_input_fields"],
        "covalent_model_input_fields": model_input_fields,
        "direct_mapping_fields": list(DIRECT_MAPPING_FIELDS),
        "missing_or_uncertain_fields": list(MISSING_OR_UNCERTAIN_FIELDS),
        "recommended_next_step": recommended_next_step,
        "checkpoint_loaded": False,
        "diffsbdd_model_initialized": False,
        "diffsbdd_model_called": False,
        "training_executed": False,
        "archive_created": False,
    }
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(report_rows, preview, args.output_md)
    return 0 if all_passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect DiffSBDD input interface and covalent adapter mapping.")
    parser.add_argument("--sample_index_csv", default=str(DEFAULT_ROOT / "sample_index.csv"))
    parser.add_argument("--tiny_smoke_report_csv", default=str(DEFAULT_ROOT / "tiny_training_smoke_report.csv"))
    parser.add_argument("--tiny_smoke_manifest_json", default=str(DEFAULT_ROOT / "tiny_training_smoke_preview_manifest.json"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_input_interface_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "diffsbdd_input_adapter_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/diffsbdd_input_interface_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("diffsbdd_input_interface_v0_passed" if code == 0 else "diffsbdd_input_interface_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

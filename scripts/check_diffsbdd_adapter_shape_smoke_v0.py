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
from covalent_ext.diffsbdd_input_adapter import (  # noqa: E402
    build_diffsbdd_like_input_from_covalent_v0,
    validate_diffsbdd_like_input_v0,
)
from covalent_ext.diffsbdd_shape_smoke import (  # noqa: E402
    EXPECTED_DIFFSBDD_BATCH_FIELDS,
    EXPECTED_LIGAND_DICT_FIELDS,
    EXPECTED_POCKET_DICT_FIELDS,
    build_diffsbdd_batch_fields_v0,
    build_ligand_pocket_dicts_for_diffsbdd_v0,
    summarize_diffsbdd_shape_smoke_v0,
    validate_diffsbdd_adapter_shape_smoke_v0,
)
from covalent_ext.model_input_adapter import build_covalent_model_input_v0, validate_covalent_model_input_v0  # noqa: E402
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn  # noqa: E402


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
    "ligand_atom_total",
    "pocket_atom_total",
    "ligand_feature_dim",
    "pocket_feature_dim",
    "num_lig_atoms",
    "num_pocket_nodes",
    "target_atom_count",
    "context_atom_count",
    "lig_fixed_count",
    "ligand_x_shape",
    "ligand_one_hot_shape",
    "ligand_mask_shape",
    "pocket_x_shape",
    "pocket_one_hot_shape",
    "pocket_mask_shape",
    "coordinate_center_shape",
    "generation_mask_flat_shape",
    "ligand_context_mask_flat_shape",
    "ligand_target_mask_flat_shape",
    "generation_equals_target",
    "context_target_no_overlap",
    "lig_fixed_matches_context",
    "flattened_ligand_count_matches_size",
    "flattened_pocket_count_matches_size",
    "coords_finite",
    "one_hot_finite",
    "checkpoint_loaded",
    "checkpoint_saved",
    "diffsbdd_model_initialized",
    "diffsbdd_model_called",
    "training_executed",
    "shape_smoke_status",
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


def _list_text(values: list[int]) -> str:
    return ";".join(str(value) for value in values)


def validate_interface_inputs(report_csv: Path, manifest_json: Path) -> dict[str, Any]:
    rows = rows_from_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    if len(rows) != 4:
        raise ValueError("Step 10B DiffSBDD input interface report row count is invalid")
    if any(row.get("adapter_status") != "passed" for row in rows):
        raise ValueError("Step 10B DiffSBDD input interface report has non-passed rows")
    if manifest.get("stage") != "diffsbdd_input_interface_inspection_adapter_v0":
        raise ValueError("Step 10B DiffSBDD input interface manifest stage is invalid")
    if manifest.get("recommended_next_step") != "diffsbdd_adapter_shape_smoke_without_checkpoint":
        raise ValueError("Step 10B recommended next step is not shape smoke")
    for key in ["checkpoint_loaded", "diffsbdd_model_initialized", "diffsbdd_model_called", "training_executed"]:
        if manifest.get(key) is not False:
            raise ValueError(f"Step 10B manifest indicates {key}")
    return manifest


def report_row(summary: dict[str, Any], shape_ok: bool, reasons: list[str], shape_smoke: dict[str, Any]) -> dict[str, str]:
    checks = [
        "generation_equals_target",
        "context_target_no_overlap",
        "lig_fixed_matches_context",
        "flattened_ligand_count_matches_size",
        "flattened_pocket_count_matches_size",
        "coords_finite",
        "one_hot_finite",
        "shape_sanity_passed",
        "mask_sanity_passed",
    ]
    blockers = list(reasons)
    for key in checks:
        if not summary[key]:
            blockers.append(key)
    for key in ["checkpoint_loaded", "checkpoint_saved", "diffsbdd_model_initialized", "diffsbdd_model_called", "training_executed"]:
        if shape_smoke[key] is not False:
            blockers.append(key)
    if int(summary["target_atom_count"]) <= 0:
        blockers.append("target_atom_count_zero")
    return {
        "mask_level": summary["mask_level"],
        "batch_size": str(summary["batch_size"]),
        "ligand_atom_total": str(summary["ligand_atom_total"]),
        "pocket_atom_total": str(summary["pocket_atom_total"]),
        "ligand_feature_dim": str(summary["ligand_feature_dim"]),
        "pocket_feature_dim": str(summary["pocket_feature_dim"]),
        "num_lig_atoms": _list_text(summary["num_lig_atoms"]),
        "num_pocket_nodes": _list_text(summary["num_pocket_nodes"]),
        "target_atom_count": str(summary["target_atom_count"]),
        "context_atom_count": str(summary["context_atom_count"]),
        "lig_fixed_count": str(summary["lig_fixed_count"]),
        "ligand_x_shape": str(summary["ligand_x_shape"]),
        "ligand_one_hot_shape": str(summary["ligand_one_hot_shape"]),
        "ligand_mask_shape": str(summary["ligand_mask_shape"]),
        "pocket_x_shape": str(summary["pocket_x_shape"]),
        "pocket_one_hot_shape": str(summary["pocket_one_hot_shape"]),
        "pocket_mask_shape": str(summary["pocket_mask_shape"]),
        "coordinate_center_shape": str(summary["coordinate_center_shape"]),
        "generation_mask_flat_shape": str(summary["generation_mask_flat_shape"]),
        "ligand_context_mask_flat_shape": str(summary["ligand_context_mask_flat_shape"]),
        "ligand_target_mask_flat_shape": str(summary["ligand_target_mask_flat_shape"]),
        "generation_equals_target": _bool(summary["generation_equals_target"]),
        "context_target_no_overlap": _bool(summary["context_target_no_overlap"]),
        "lig_fixed_matches_context": _bool(summary["lig_fixed_matches_context"]),
        "flattened_ligand_count_matches_size": _bool(summary["flattened_ligand_count_matches_size"]),
        "flattened_pocket_count_matches_size": _bool(summary["flattened_pocket_count_matches_size"]),
        "coords_finite": _bool(summary["coords_finite"]),
        "one_hot_finite": _bool(summary["one_hot_finite"]),
        "checkpoint_loaded": _bool(shape_smoke["checkpoint_loaded"]),
        "checkpoint_saved": _bool(shape_smoke["checkpoint_saved"]),
        "diffsbdd_model_initialized": _bool(shape_smoke["diffsbdd_model_initialized"]),
        "diffsbdd_model_called": _bool(shape_smoke["diffsbdd_model_called"]),
        "training_executed": _bool(shape_smoke["training_executed"]),
        "shape_smoke_status": "passed" if shape_ok and not blockers else "blocked",
        "blocking_reasons": ";".join(sorted(set(blockers))),
    }


def write_summary(report_rows: list[dict[str, str]], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Adapter Shape Smoke v0 Summary",
        "",
        "This step builds DiffSBDD-like flattened ligand/pocket batch fields from covalent model input.",
        "It validates shape/mask/one-hot/size consistency without initializing or calling DiffSBDD.",
        "It does not load or save checkpoint.",
        "It does not train or fine-tune.",
        "It does not modify DiffSBDD or equivariant_diffusion.",
        "It is still not equivalent to a real DiffSBDD forward pass.",
        "",
        "## Shape Smoke Results",
        "",
        "| mask_level | ligand_atom_total | pocket_atom_total | target_atom_count | shape_smoke_status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in report_rows:
        lines.append(
            f"| {row['mask_level']} | {row['ligand_atom_total']} | {row['pocket_atom_total']} | {row['target_atom_count']} | {row['shape_smoke_status']} |"
        )
    lines.extend(
        [
            "",
            f"- ligand_feature_dim: {preview['ligand_feature_dim']}",
            f"- pocket_feature_dim: {preview['pocket_feature_dim']}",
            f"- shape_sanity_all_passed: {preview['shape_sanity_all_passed']}",
            f"- mask_sanity_all_passed: {preview['mask_sanity_all_passed']}",
            f"- checkpoint_loaded: {preview['checkpoint_loaded']}",
            f"- checkpoint_saved: {preview['checkpoint_saved']}",
            f"- diffsbdd_model_initialized: {preview['diffsbdd_model_initialized']}",
            f"- diffsbdd_model_called: {preview['diffsbdd_model_called']}",
            f"- training_executed: {preview['training_executed']}",
            f"- recommended_next_step: {preview['recommended_next_step']}",
            "",
            "If all rows are passed, the next step can be DiffSBDD model instantiation dry-run without checkpoint.",
            "If fields remain uncertain, use manual interface review before touching any real model path.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    validate_interface_inputs(Path(args.diffsbdd_input_interface_report_csv), Path(args.diffsbdd_input_interface_manifest_json))
    dataset = CovalentNPZDataset(args.sample_index_csv)
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    report_rows: list[dict[str, str]] = []
    summaries: list[dict[str, Any]] = []
    for mask_level in MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        model_input = build_covalent_model_input_v0(adapted)
        model_ok, model_reasons = validate_covalent_model_input_v0(model_input)
        diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
        diffsbdd_ok, diffsbdd_reasons = validate_diffsbdd_like_input_v0(diffsbdd_like)
        batch_fields = build_diffsbdd_batch_fields_v0(diffsbdd_like)
        shape_smoke = build_ligand_pocket_dicts_for_diffsbdd_v0(batch_fields)
        shape_ok, shape_reasons = validate_diffsbdd_adapter_shape_smoke_v0(shape_smoke)
        summary = summarize_diffsbdd_shape_smoke_v0(shape_smoke)
        summaries.append(summary)
        all_reasons = []
        if not model_ok:
            all_reasons.extend(model_reasons)
        if not diffsbdd_ok:
            all_reasons.extend(diffsbdd_reasons)
        all_reasons.extend(shape_reasons)
        report_rows.append(report_row(summary, model_ok and diffsbdd_ok and shape_ok, all_reasons, shape_smoke))
    all_passed = all(row["shape_smoke_status"] == "passed" for row in report_rows)
    preview = {
        "stage": "diffsbdd_adapter_shape_smoke_without_checkpoint_v0",
        "dataset_len": len(dataset),
        "batch_size": 3,
        "mask_levels_checked": len(MASK_LEVELS),
        "report_row_count": len(report_rows),
        "all_mask_levels_passed": all_passed,
        "ligand_atom_total_by_mask_level": {summary["mask_level"]: summary["ligand_atom_total"] for summary in summaries},
        "pocket_atom_total_by_mask_level": {summary["mask_level"]: summary["pocket_atom_total"] for summary in summaries},
        "target_atom_count_by_mask_level": {summary["mask_level"]: summary["target_atom_count"] for summary in summaries},
        "context_atom_count_by_mask_level": {summary["mask_level"]: summary["context_atom_count"] for summary in summaries},
        "ligand_feature_dim": summaries[0]["ligand_feature_dim"],
        "pocket_feature_dim": summaries[0]["pocket_feature_dim"],
        "expected_diffsbdd_batch_fields": list(EXPECTED_DIFFSBDD_BATCH_FIELDS),
        "expected_ligand_dict_fields": list(EXPECTED_LIGAND_DICT_FIELDS),
        "expected_pocket_dict_fields": list(EXPECTED_POCKET_DICT_FIELDS),
        "shape_sanity_all_passed": all(summary["shape_sanity_passed"] for summary in summaries),
        "mask_sanity_all_passed": all(summary["mask_sanity_passed"] for summary in summaries),
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "diffsbdd_model_initialized": False,
        "diffsbdd_model_called": False,
        "training_executed": False,
        "archive_created": False,
        "recommended_next_step": "diffsbdd_model_instantiation_dry_run_without_checkpoint_or_manual_interface_review",
    }
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(report_rows, preview, args.output_md)
    return 0 if all_passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DiffSBDD adapter shape smoke without checkpoint.")
    parser.add_argument("--sample_index_csv", default=str(DEFAULT_ROOT / "sample_index.csv"))
    parser.add_argument("--diffsbdd_input_interface_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_input_interface_report.csv"))
    parser.add_argument("--diffsbdd_input_interface_manifest_json", default=str(DEFAULT_ROOT / "diffsbdd_input_adapter_preview_manifest.json"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_adapter_shape_smoke_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "diffsbdd_adapter_shape_smoke_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/diffsbdd_adapter_shape_smoke_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("diffsbdd_adapter_shape_smoke_v0_passed" if code == 0 else "diffsbdd_adapter_shape_smoke_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

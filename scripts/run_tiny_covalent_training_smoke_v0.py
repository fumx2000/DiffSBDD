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
from covalent_ext.tiny_covalent_model import run_tiny_training_step_v0  # noqa: E402


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
    "target_atom_count",
    "requested_device",
    "resolved_device",
    "cuda_available",
    "cuda_device_count",
    "cuda_device_name",
    "initial_total_loss",
    "post_step_total_loss",
    "initial_loss_finite",
    "post_step_loss_finite",
    "gradient_norm",
    "gradient_norm_finite",
    "any_gradient_nonzero",
    "optimizer_step_executed",
    "tiny_model_initialized",
    "diffsbdd_model_initialized",
    "checkpoint_loaded",
    "checkpoint_saved",
    "real_training_executed",
    "tiny_training_step_executed",
    "smoke_status",
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


def validate_preflight_inputs(report_csv: Path, manifest_json: Path) -> dict[str, Any]:
    rows = rows_from_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    if len(rows) != 4:
        raise ValueError("Step 9E training_preflight_report row count is invalid")
    if any(row.get("preflight_status") != "passed" for row in rows):
        raise ValueError("Step 9E training_preflight_report has non-passed rows")
    if manifest.get("stage") != "covalent_training_preflight_dry_run_v0":
        raise ValueError("Step 9E training preflight manifest stage is invalid")
    if manifest.get("report_row_count") != 4 or manifest.get("all_mask_levels_passed") is not True:
        raise ValueError("Step 9E training preflight manifest is not fully passed")
    if manifest.get("checkpoint_loaded") is not False:
        raise ValueError("Step 9E manifest indicates checkpoint_loaded")
    if manifest.get("model_initialized") is not False:
        raise ValueError("Step 9E manifest indicates model_initialized")
    if manifest.get("training_executed") is not False:
        raise ValueError("Step 9E manifest indicates training_executed")
    return manifest


def report_row_for_smoke(mask_level: str, batch_size: int, validation_ok: bool, validation_reasons: list[str], result: dict[str, Any]) -> dict[str, str]:
    checks = {
        "target_atom_count_positive": int(result["target_atom_count"]) > 0,
        "initial_loss_finite": bool(result["initial_loss_finite"]),
        "post_step_loss_finite": bool(result["post_step_loss_finite"]),
        "gradient_norm_finite": bool(result["gradient_norm_finite"]),
        "any_gradient_nonzero": bool(result["any_gradient_nonzero"]),
        "optimizer_step_executed": bool(result["optimizer_step_executed"]),
        "tiny_model_initialized": bool(result["tiny_model_initialized"]),
        "diffsbdd_model_initialized": bool(result["diffsbdd_model_initialized"]),
        "checkpoint_loaded": bool(result["checkpoint_loaded"]),
        "checkpoint_saved": bool(result["checkpoint_saved"]),
        "real_training_executed": bool(result["real_training_executed"]),
        "tiny_training_step_executed": bool(result["tiny_training_step_executed"]),
    }
    blockers = []
    if not validation_ok:
        blockers.extend(validation_reasons)
    for key in [
        "target_atom_count_positive",
        "initial_loss_finite",
        "post_step_loss_finite",
        "gradient_norm_finite",
        "any_gradient_nonzero",
        "optimizer_step_executed",
        "tiny_model_initialized",
        "tiny_training_step_executed",
    ]:
        if not checks[key]:
            blockers.append(key)
    for key in ["diffsbdd_model_initialized", "checkpoint_loaded", "checkpoint_saved", "real_training_executed"]:
        if checks[key]:
            blockers.append(key)
    if result["requested_device"] == "auto" and result["cuda_available"] and result["resolved_device"] != "cuda:0":
        blockers.append("auto_device_did_not_resolve_to_cuda0")
    return {
        "mask_level": mask_level,
        "batch_size": str(batch_size),
        "target_atom_count": str(int(result["target_atom_count"])),
        "requested_device": result["requested_device"],
        "resolved_device": result["resolved_device"],
        "cuda_available": _bool(result["cuda_available"]),
        "cuda_device_count": str(result["cuda_device_count"]),
        "cuda_device_name": result["cuda_device_name"],
        "initial_total_loss": f"{result['initial_total_loss']:.8g}",
        "post_step_total_loss": f"{result['post_step_total_loss']:.8g}",
        "initial_loss_finite": _bool(checks["initial_loss_finite"]),
        "post_step_loss_finite": _bool(checks["post_step_loss_finite"]),
        "gradient_norm": f"{result['gradient_norm']:.8g}",
        "gradient_norm_finite": _bool(checks["gradient_norm_finite"]),
        "any_gradient_nonzero": _bool(checks["any_gradient_nonzero"]),
        "optimizer_step_executed": _bool(checks["optimizer_step_executed"]),
        "tiny_model_initialized": _bool(checks["tiny_model_initialized"]),
        "diffsbdd_model_initialized": _bool(checks["diffsbdd_model_initialized"]),
        "checkpoint_loaded": _bool(checks["checkpoint_loaded"]),
        "checkpoint_saved": _bool(checks["checkpoint_saved"]),
        "real_training_executed": _bool(checks["real_training_executed"]),
        "tiny_training_step_executed": _bool(checks["tiny_training_step_executed"]),
        "smoke_status": "passed" if not blockers else "blocked",
        "blocking_reasons": ";".join(sorted(set(blockers))),
    }


def write_summary(report_rows: list[dict[str, str]], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Tiny Covalent Training Smoke v0 Summary",
        "",
        "This step runs a tiny toy covalent model training smoke test.",
        "It verifies that the current covalent batch supports forward, loss, backward, gradient, and optimizer step.",
        "It uses device=auto and prefers cuda:0 when available.",
        "It does not use DiffSBDD.",
        "It does not load checkpoint.",
        "It does not save checkpoint.",
        "It does not train or fine-tune a real model.",
        "It does not modify DiffSBDD model code.",
        "",
        f"- requested_device: {preview['requested_device']}",
        f"- resolved_device: {preview['resolved_device']}",
        f"- cuda_available: {preview['cuda_available']}",
        f"- cuda_device_count: {preview['cuda_device_count']}",
        f"- cuda_device_name: {preview['cuda_device_name']}",
        "",
        "| mask_level | target_atom_count | initial_total_loss | post_step_total_loss | gradient_norm | smoke_status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report_rows:
        lines.append(
            f"| {row['mask_level']} | {row['target_atom_count']} | {row['initial_total_loss']} | {row['post_step_total_loss']} | {row['gradient_norm']} | {row['smoke_status']} |"
        )
    lines.extend(
        [
            "",
            "Conclusion: if all rows are passed, the next step is DiffSBDD input interface inspection or adapter.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    preflight_manifest = validate_preflight_inputs(Path(args.training_preflight_report_csv), Path(args.training_preflight_manifest_json))
    dataset = CovalentNPZDataset(args.sample_index_csv)
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    report_rows: list[dict[str, str]] = []
    target_counts: dict[str, int] = {}
    initial_losses: dict[str, float] = {}
    post_losses: dict[str, float] = {}
    gradient_norms: dict[str, float] = {}
    raw_results: list[dict[str, Any]] = []
    for index, mask_level in enumerate(MASK_LEVELS):
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        model_input = build_covalent_model_input_v0(adapted)
        validation_ok, validation_reasons = validate_covalent_model_input_v0(model_input)
        result = run_tiny_training_step_v0(model_input, seed=args.seed + index, lr=args.lr, device=args.device)
        raw_results.append(result)
        report_rows.append(report_row_for_smoke(mask_level, int(model_input["batch_size"]), validation_ok, validation_reasons, result))
        target_counts[mask_level] = int(result["target_atom_count"])
        initial_losses[mask_level] = float(result["initial_total_loss"])
        post_losses[mask_level] = float(result["post_step_total_loss"])
        gradient_norms[mask_level] = float(result["gradient_norm"])
    all_passed = all(row["smoke_status"] == "passed" for row in report_rows)
    first = raw_results[0]
    preview = {
        "stage": "tiny_covalent_model_training_smoke_v0",
        "dataset_name": preflight_manifest.get("dataset_name"),
        "dataset_len": len(dataset),
        "batch_size": 3,
        "requested_device": first["requested_device"],
        "resolved_device": first["resolved_device"],
        "cuda_available": bool(first["cuda_available"]),
        "cuda_device_count": int(first["cuda_device_count"]),
        "cuda_device_name": first["cuda_device_name"],
        "mask_levels_checked": len(MASK_LEVELS),
        "report_row_count": len(report_rows),
        "all_mask_levels_passed": all_passed,
        "target_atom_count_total_by_mask_level": target_counts,
        "initial_total_loss_by_mask_level": initial_losses,
        "post_step_total_loss_by_mask_level": post_losses,
        "gradient_norm_by_mask_level": gradient_norms,
        "all_losses_finite": all(result["initial_loss_finite"] and result["post_step_loss_finite"] for result in raw_results),
        "all_gradients_finite": all(result["gradient_norm_finite"] for result in raw_results),
        "all_gradients_nonzero": all(result["any_gradient_nonzero"] for result in raw_results),
        "optimizer_step_executed": all(result["optimizer_step_executed"] for result in raw_results),
        "tiny_model_initialized": all(result["tiny_model_initialized"] for result in raw_results),
        "diffsbdd_model_initialized": False,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "real_training_executed": False,
        "archive_created": False,
        "recommended_next_step": "diffSBDD_input_interface_inspection_or_adapter",
    }
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(report_rows, preview, args.output_md)
    return 0 if all_passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run tiny covalent model training smoke test.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample_index_csv", default=str(DEFAULT_ROOT / "sample_index.csv"))
    parser.add_argument("--training_preflight_report_csv", default=str(DEFAULT_ROOT / "training_preflight_report.csv"))
    parser.add_argument("--training_preflight_manifest_json", default=str(DEFAULT_ROOT / "training_preflight_preview_manifest.json"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "tiny_training_smoke_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "tiny_training_smoke_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/tiny_covalent_training_smoke_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("tiny_covalent_training_smoke_v0_passed" if code == 0 else "tiny_covalent_training_smoke_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

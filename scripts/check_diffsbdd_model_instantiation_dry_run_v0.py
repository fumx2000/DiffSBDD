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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.diffsbdd_model_instantiation import (  # noqa: E402
    build_minimal_diffsbdd_instantiation_config_v0,
    inspect_diffsbdd_model_constructor_v0,
    try_instantiate_diffsbdd_model_without_checkpoint_v0,
)


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
REPORT_COLUMNS = [
    "stage",
    "device",
    "model_class_name",
    "model_class_imported",
    "constructor_signature_resolved",
    "config_status",
    "config_source",
    "dataset_info_source",
    "atom_encoder_source",
    "missing_or_uncertain_config_fields",
    "model_initialized",
    "parameter_count",
    "trainable_parameter_count",
    "module_count",
    "instantiation_exception_type",
    "instantiation_exception_message",
    "checkpoint_loaded",
    "checkpoint_saved",
    "forward_called",
    "diffsbdd_model_called",
    "training_step_called",
    "training_executed",
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


def _list_text(values: list[str]) -> str:
    return ";".join(values)


def validate_step10c_inputs(report_csv: Path, manifest_json: Path) -> bool:
    rows = rows_from_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    if len(rows) != 4:
        raise ValueError("Step 10C shape smoke report row count is invalid")
    if any(row.get("shape_smoke_status") != "passed" for row in rows):
        raise ValueError("Step 10C shape smoke report has non-passed rows")
    if manifest.get("stage") != "diffsbdd_adapter_shape_smoke_without_checkpoint_v0":
        raise ValueError("Step 10C shape smoke manifest stage is invalid")
    if manifest.get("shape_sanity_all_passed") is not True:
        raise ValueError("Step 10C shape sanity did not pass")
    if manifest.get("mask_sanity_all_passed") is not True:
        raise ValueError("Step 10C mask sanity did not pass")
    for key in ["checkpoint_loaded", "checkpoint_saved", "diffsbdd_model_initialized", "diffsbdd_model_called", "training_executed"]:
        if manifest.get(key) is not False:
            raise ValueError(f"Step 10C manifest indicates {key}")
    return True


def report_row(result: dict[str, Any]) -> dict[str, str]:
    return {
        "stage": "diffsbdd_model_instantiation_dry_run_without_checkpoint_v0",
        "device": result["device"],
        "model_class_name": result["model_class_name"],
        "model_class_imported": _bool(result["model_class_imported"]),
        "constructor_signature_resolved": _bool(result["constructor_signature_resolved"]),
        "config_status": result["config_status"],
        "config_source": result["config_source"],
        "dataset_info_source": result["dataset_info_source"],
        "atom_encoder_source": result["atom_encoder_source"],
        "missing_or_uncertain_config_fields": _list_text(result["missing_or_uncertain_config_fields"]),
        "model_initialized": _bool(result["model_initialized"]),
        "parameter_count": str(result["parameter_count"]),
        "trainable_parameter_count": str(result["trainable_parameter_count"]),
        "module_count": str(result["module_count"]),
        "instantiation_exception_type": result["instantiation_exception_type"],
        "instantiation_exception_message": result["instantiation_exception_message"],
        "checkpoint_loaded": _bool(result["checkpoint_loaded"]),
        "checkpoint_saved": _bool(result["checkpoint_saved"]),
        "forward_called": _bool(result["forward_called"]),
        "diffsbdd_model_called": _bool(result["diffsbdd_model_called"]),
        "training_step_called": _bool(result["training_step_called"]),
        "training_executed": _bool(result["training_executed"]),
        "smoke_status": result["smoke_status"],
        "blocking_reasons": _list_text(result["blocking_reasons"]),
    }


def write_summary(inspection: dict[str, Any], config: dict[str, Any], result: dict[str, Any], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Model Instantiation Dry-run v0 Summary",
        "",
        "This step imports the real DiffSBDD model class, inspects its constructor, and runs a constructor-only instantiation dry-run.",
        "It does not read checkpoint files.",
        "It does not call forward.",
        "It does not call training_step.",
        "It does not train or fine-tune.",
        "It does not save checkpoints.",
        "It does not modify DiffSBDD or equivariant_diffusion.",
        "",
        f"- model_class_name: {result['model_class_name']}",
        f"- constructor_signature_resolved: {result['constructor_signature_resolved']}",
        f"- config_status: {result['config_status']}",
        f"- config_source: {result['config_source']}",
        f"- dataset_info_source: {result['dataset_info_source']}",
        f"- atom_encoder_source: {result['atom_encoder_source']}",
        f"- model_initialized: {result['model_initialized']}",
        f"- parameter_count: {result['parameter_count']}",
        f"- trainable_parameter_count: {result['trainable_parameter_count']}",
        f"- module_count: {result['module_count']}",
        f"- smoke_status: {result['smoke_status']}",
        "",
        "## Inspected Source Files",
    ]
    for item in inspection["inspected_source_files"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Missing Or Uncertain Config Fields"])
    for item in config["missing_or_uncertain_config_fields"]:
        lines.append(f"- {item}")
    if result["blocking_reasons"]:
        lines.extend(["", "## Blocking Reasons"])
        for item in result["blocking_reasons"]:
            lines.append(f"- {item}")
    lines.extend(
        [
            "",
            f"- checkpoint_loaded: {preview['checkpoint_loaded']}",
            f"- checkpoint_saved: {preview['checkpoint_saved']}",
            f"- forward_called: {preview['forward_called']}",
            f"- diffsbdd_model_called: {preview['diffsbdd_model_called']}",
            f"- training_step_called: {preview['training_step_called']}",
            f"- training_executed: {preview['training_executed']}",
            f"- recommended_next_step: {preview['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    step10c_passed = validate_step10c_inputs(Path(args.shape_smoke_report_csv), Path(args.shape_smoke_manifest_json))
    inspection = inspect_diffsbdd_model_constructor_v0()
    config = build_minimal_diffsbdd_instantiation_config_v0()
    result = try_instantiate_diffsbdd_model_without_checkpoint_v0(device=args.device)
    all_checks_passed = step10c_passed and result["smoke_status"] == "passed"
    recommended_next_step = (
        "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint"
        if all_checks_passed
        else "manual_diffsbdd_instantiation_config_review"
    )
    preview = {
        "stage": "diffsbdd_model_instantiation_dry_run_without_checkpoint_v0",
        "previous_stage": "diffsbdd_adapter_shape_smoke_without_checkpoint_v0",
        "step10c_shape_smoke_passed": step10c_passed,
        "device": result["device"],
        "model_class_name": result["model_class_name"],
        "model_class_imported": result["model_class_imported"],
        "constructor_signature_resolved": result["constructor_signature_resolved"],
        "config_status": result["config_status"],
        "config_source": result["config_source"],
        "dataset_info_source": result["dataset_info_source"],
        "atom_encoder_source": result["atom_encoder_source"],
        "missing_or_uncertain_config_fields": result["missing_or_uncertain_config_fields"],
        "model_initialized": result["model_initialized"],
        "parameter_count": result["parameter_count"],
        "trainable_parameter_count": result["trainable_parameter_count"],
        "module_count": result["module_count"],
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "forward_called": False,
        "diffsbdd_model_called": False,
        "training_step_called": False,
        "training_executed": False,
        "archive_created": False,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": recommended_next_step,
    }
    write_csv([report_row(result)], args.output_report_csv, REPORT_COLUMNS)
    write_json(preview, args.output_manifest_json)
    write_summary(inspection, config, result, preview, args.output_md)
    return 0 if all_checks_passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DiffSBDD model instantiation dry-run without checkpoint.")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--shape_smoke_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_adapter_shape_smoke_report.csv"))
    parser.add_argument("--shape_smoke_manifest_json", default=str(DEFAULT_ROOT / "diffsbdd_adapter_shape_smoke_preview_manifest.json"))
    parser.add_argument("--output_report_csv", default=str(DEFAULT_ROOT / "diffsbdd_model_instantiation_dry_run_report.csv"))
    parser.add_argument("--output_manifest_json", default=str(DEFAULT_ROOT / "diffsbdd_model_instantiation_dry_run_preview_manifest.json"))
    parser.add_argument("--output_md", default="docs/diffsbdd_model_instantiation_dry_run_v0_summary.md")
    return parser.parse_args()


def main() -> int:
    code = run(parse_args())
    print("diffsbdd_model_instantiation_dry_run_v0_passed" if code == 0 else "diffsbdd_model_instantiation_dry_run_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

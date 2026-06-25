#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.masked_loss_adapter_design import (  # noqa: E402
    DEFAULT_ROOT,
    STAGE,
    build_masked_loss_adapter_design_v0,
    inspect_masked_loss_candidate_sources_v0,
    validate_step10h_outputs_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10h_backward_smoke_passed",
    "source_inspection_status",
    "design_status",
    "atomwise_loss_exposed_by_current_forward",
    "nodewise_noise_exposed_by_current_forward",
    "can_build_masked_loss_from_current_output_only",
    "current_forward_is_mask_aware",
    "current_forward_is_full_ligand_objective",
    "must_modify_loss_for_masked_training",
    "no_diffsbdd_modification_feasible",
    "minimal_required_hook_points",
    "proposed_loss_components",
    "recommended_path",
    "recommended_next_step",
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
    "blocking_reasons",
]


def _bool(value: bool) -> str:
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


def report_row(source_info: dict[str, Any], design: dict[str, Any], step10h_passed: bool) -> dict[str, str]:
    return {
        "stage": STAGE,
        "previous_stage": "diffsbdd_backward_smoke_without_checkpoint_v0",
        "step10h_backward_smoke_passed": _bool(step10h_passed),
        "source_inspection_status": "passed" if source_info["loss_construction_locations"] and source_info["ligand_error_locations"] else "blocked",
        "design_status": design["design_status"],
        "atomwise_loss_exposed_by_current_forward": _bool(source_info["atomwise_loss_exposed_by_current_forward"]),
        "nodewise_noise_exposed_by_current_forward": _bool(source_info["nodewise_noise_exposed_by_current_forward"]),
        "can_build_masked_loss_from_current_output_only": _bool(source_info["can_build_masked_loss_from_current_output_only"]),
        "current_forward_is_mask_aware": _bool(source_info["current_forward_is_mask_aware"]),
        "current_forward_is_full_ligand_objective": _bool(source_info["current_forward_is_full_ligand_objective"]),
        "must_modify_loss_for_masked_training": _bool(source_info["must_modify_loss_for_masked_training"]),
        "no_diffsbdd_modification_feasible": str(source_info["no_diffsbdd_modification_feasible"]),
        "minimal_required_hook_points": _list_text(source_info["minimal_required_hook_points"]),
        "proposed_loss_components": _list_text(design["proposed_loss_components"]),
        "recommended_path": design["recommended_path"],
        "recommended_next_step": design["recommended_next_step"],
        "checkpoint_loaded": "false",
        "checkpoint_saved": "false",
        "training_step_called": "false",
        "backward_called": "false",
        "optimizer_step_executed": "false",
        "trainer_fit_called": "false",
        "training_executed": "false",
        "real_finetune_executed": "false",
        "checkpoint_written": "false",
        "archive_created": "false",
        "blocking_reasons": _list_text(design["blocking_reasons"]),
    }


def preview_manifest(source_info: dict[str, Any], design: dict[str, Any], step10h_passed: bool) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "previous_stage": "diffsbdd_backward_smoke_without_checkpoint_v0",
        "step10h_backward_smoke_passed": step10h_passed,
        "design_status": design["design_status"],
        "atomwise_loss_exposed_by_current_forward": source_info["atomwise_loss_exposed_by_current_forward"],
        "nodewise_noise_exposed_by_current_forward": source_info["nodewise_noise_exposed_by_current_forward"],
        "can_build_masked_loss_from_current_output_only": source_info["can_build_masked_loss_from_current_output_only"],
        "current_forward_is_mask_aware": False,
        "current_forward_is_full_ligand_objective": True,
        "must_modify_loss_for_masked_training": True,
        "proposed_loss_components": design["proposed_loss_components"],
        "adapter_input_contract": design["adapter_input_contract"],
        "adapter_output_contract": design["adapter_output_contract"],
        "mask_level_loss_policy": design["mask_level_loss_policy"],
        "no_diffsbdd_modification_feasible": source_info["no_diffsbdd_modification_feasible"],
        "minimal_required_hook_points": source_info["minimal_required_hook_points"],
        "recommended_path": design["recommended_path"],
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": False,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "checkpoint_written": False,
        "archive_created": False,
        "all_checks_passed": step10h_passed and design["design_status"] in {"ready", "uncertain"},
        "recommended_next_step": design["recommended_next_step"],
    }


def write_summary(source_info: dict[str, Any], design: dict[str, Any], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Masked Loss Adapter Design v0 Summary",
        "",
        "Step 10G and Step 10H proved that the original DiffSBDD full-ligand loss can forward and backward on the covalent batch.",
        "The current original loss is a full-ligand objective.",
        "The current forward path does not consume covalent target/context masks.",
        "Therefore the current training path cannot be described as masked covalent training.",
        "Current output0 is a per-sample loss and cannot directly support atom-level masked loss.",
        "Current output1 is scalar diagnostics and cannot directly support target-atom masked loss.",
        "",
        "## Source Findings",
        f"- atomwise_loss_exposed_by_current_forward: {source_info['atomwise_loss_exposed_by_current_forward']}",
        f"- nodewise_noise_exposed_by_current_forward: {source_info['nodewise_noise_exposed_by_current_forward']}",
        f"- can_build_masked_loss_from_current_output_only: {source_info['can_build_masked_loss_from_current_output_only']}",
        f"- no_diffsbdd_modification_feasible: {source_info['no_diffsbdd_modification_feasible']}",
        "",
        "## Proposed Loss Components",
    ]
    lines.extend(f"- {component}" for component in design["proposed_loss_components"])
    lines.extend(
        [
            "",
            f"- formula: {design['proposed_loss_formula_text']}",
            "",
            "## Required Internal Signals",
        ]
    )
    lines.extend(f"- {signal}" for signal in design["required_model_signals"])
    lines.extend(
        [
            "",
            "## Adapter Input Contract",
        ]
    )
    lines.extend(f"- {item}" for item in design["adapter_input_contract"])
    lines.extend(
        [
            "",
            "## Adapter Output Contract",
        ]
    )
    lines.extend(f"- {item}" for item in design["adapter_output_contract"])
    lines.extend(
        [
            "",
            "## Mask-level Policy",
            "| mask_level | target | context | focus |",
            "| --- | --- | --- | --- |",
        ]
    )
    for mask_level, policy in design["mask_level_loss_policy"].items():
        lines.append(f"| {mask_level} | {policy['target']} | {policy['context']} | {policy['focus']} |")
    lines.extend(
        [
            "",
            "## Recommended Path",
            design["recommended_path"],
            "",
            "Minimal hook points:",
        ]
    )
    lines.extend(f"- {point}" for point in source_info["minimal_required_hook_points"])
    lines.extend(
        [
            "",
            f"- recommended_next_step: {preview['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    step10h_passed = validate_step10h_outputs_v0()
    source_info = inspect_masked_loss_candidate_sources_v0()
    design = build_masked_loss_adapter_design_v0(source_info)
    row = report_row(source_info, design, step10h_passed)
    manifest = preview_manifest(source_info, design, step10h_passed)
    write_csv([row], DEFAULT_ROOT / "masked_loss_adapter_design_report.csv", REPORT_COLUMNS)
    write_json(manifest, DEFAULT_ROOT / "masked_loss_adapter_design_preview_manifest.json")
    write_summary(source_info, design, manifest, "docs/masked_loss_adapter_design_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    code = run()
    print("masked_loss_adapter_design_v0_passed" if code == 0 else "masked_loss_adapter_design_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

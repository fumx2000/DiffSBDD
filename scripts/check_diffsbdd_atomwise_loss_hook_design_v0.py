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

from covalent_ext.diffsbdd_atomwise_loss_hook_design import (  # noqa: E402
    DEFAULT_ROOT,
    PREVIOUS_STAGE,
    STAGE,
    build_atomwise_loss_hook_design_v0,
    inspect_atomwise_hook_candidate_sources_v0,
    validate_step10i_outputs_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10i_masked_loss_design_passed",
    "source_inspection_status",
    "design_status",
    "eps_t_lig_found",
    "net_out_lig_found",
    "squared_error_found",
    "reduction_found",
    "preferred_hook_point",
    "recommended_hook_strategy",
    "original_forward_return_should_change",
    "checkpoint_compatibility_affected",
    "can_preserve_default_behavior",
    "can_capture_atomwise_noise_after_hook",
    "can_compute_masked_x_loss_after_hook",
    "can_compute_masked_h_loss_after_hook",
    "required_tensors",
    "tensor_shape_contract",
    "implementation_phases",
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


def _bool(value: Any) -> str:
    return str(bool(value)).lower()


def _list_text(values: list[Any]) -> str:
    return ";".join(str(value) for value in values)


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


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


def source_inspection_passed(source_info: dict[str, Any]) -> bool:
    return all(
        [
            source_info["eps_t_lig_locations"],
            source_info["net_out_lig_locations"],
            source_info["squared_error_locations"] or source_info["error_t_lig_locations"],
            source_info["reduction_locations"],
        ]
    )


def report_row(source_info: dict[str, Any], design: dict[str, Any], step10i_passed: bool) -> dict[str, str]:
    readiness = design["masked_loss_readiness_after_hook"]
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10i_masked_loss_design_passed": _bool(step10i_passed),
        "source_inspection_status": "passed" if source_inspection_passed(source_info) else "blocked",
        "design_status": design["design_status"],
        "eps_t_lig_found": _bool(source_info["eps_t_lig_locations"]),
        "net_out_lig_found": _bool(source_info["net_out_lig_locations"]),
        "squared_error_found": _bool(source_info["squared_error_locations"] or source_info["error_t_lig_locations"]),
        "reduction_found": _bool(source_info["reduction_locations"]),
        "preferred_hook_point": design["preferred_hook_point"],
        "recommended_hook_strategy": design["recommended_hook_strategy"],
        "original_forward_return_should_change": _bool(source_info["whether_original_forward_return_should_change"]),
        "checkpoint_compatibility_affected": _bool(
            source_info["whether_checkpoint_compatibility_should_be_affected"]
        ),
        "can_preserve_default_behavior": _bool(not source_info["whether_original_forward_return_should_change"]),
        "can_capture_atomwise_noise_after_hook": _bool(readiness["can_capture_atomwise_noise_after_hook"]),
        "can_compute_masked_x_loss_after_hook": _bool(readiness["can_compute_masked_x_loss_after_hook"]),
        "can_compute_masked_h_loss_after_hook": _bool(readiness["can_compute_masked_h_loss_after_hook"]),
        "required_tensors": _list_text(source_info["tensors_needed_for_masked_loss"]),
        "tensor_shape_contract": _json_text(source_info["tensor_shape_contract"]),
        "implementation_phases": _list_text(design["implementation_phases"]),
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


def preview_manifest(source_info: dict[str, Any], design: dict[str, Any], step10i_passed: bool) -> dict[str, Any]:
    readiness = design["masked_loss_readiness_after_hook"]
    all_checks_passed = step10i_passed and source_inspection_passed(source_info) and design["design_status"] == "ready"
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10i_masked_loss_design_passed": step10i_passed,
        "design_status": design["design_status"],
        "preferred_hook_point": design["preferred_hook_point"],
        "recommended_hook_strategy": design["recommended_hook_strategy"],
        "candidate_hook_points": source_info["candidate_hook_points"],
        "captured_tensor_contract": design["captured_tensor_contract"],
        "tensor_alignment_contract": design["tensor_alignment_contract"],
        "behavior_preservation_contract": design["behavior_preservation_contract"],
        "checkpoint_compatibility_contract": design["checkpoint_compatibility_contract"],
        "can_preserve_default_behavior": True,
        "original_forward_return_should_change": False,
        "checkpoint_compatibility_affected": False,
        "can_capture_atomwise_noise_after_hook": readiness["can_capture_atomwise_noise_after_hook"],
        "can_compute_masked_x_loss_after_hook": readiness["can_compute_masked_x_loss_after_hook"],
        "can_compute_masked_h_loss_after_hook": readiness["can_compute_masked_h_loss_after_hook"],
        "implementation_phases": design["implementation_phases"],
        "source_locations": {
            "eps_t_lig": source_info["eps_t_lig_locations"],
            "net_out_lig": source_info["net_out_lig_locations"],
            "squared_error": source_info["squared_error_locations"],
            "error_t_lig": source_info["error_t_lig_locations"],
            "reduction": source_info["reduction_locations"],
        },
        "hook_point_rankings": source_info["hook_point_rankings"],
        "hook_point_risks": source_info["hook_point_risks"],
        "required_tensors": source_info["tensors_needed_for_masked_loss"],
        "tensor_shape_contract": source_info["tensor_shape_contract"],
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
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": design["recommended_next_step"],
    }


def write_summary(source_info: dict[str, Any], design: dict[str, Any], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Atomwise Loss Hook Design v0 Summary",
        "",
        "This step is a source inspection and hook design only.",
        "It does not modify DiffSBDD or equivariant_diffusion code.",
        "It does not load or save checkpoints.",
        "It does not call training_step, backward, optimizer, trainer.fit, training, or fine-tuning.",
        "",
        "## Why a Hook Is Needed",
        "Step 10I showed that the current DiffSBDD forward output is not enough to build atom-level masked losses.",
        "output0 is a per-sample loss-like vector, and output1 contains reduced diagnostics.",
        "Neither output exposes ligand atom-wise target noise, predicted noise, or unreduced residuals.",
        "",
        "## Source Locations Found",
        f"- eps_t_lig locations: {len(source_info['eps_t_lig_locations'])}",
        f"- net_out_lig locations: {len(source_info['net_out_lig_locations'])}",
        f"- squared_error locations: {len(source_info['squared_error_locations'])}",
        f"- error_t_lig locations: {len(source_info['error_t_lig_locations'])}",
        f"- reduction locations: {len(source_info['reduction_locations'])}",
        "",
        "## Recommended Hook",
        f"- preferred_hook_point: {design['preferred_hook_point']}",
        f"- recommended_hook_strategy: {design['recommended_hook_strategy']}",
        "- The default forward return should not change.",
        "- The original loss value should not change when the probe is disabled.",
        "- Checkpoint compatibility should not be affected because no parameters, buffers, or state_dict keys are added.",
        "",
        "## Captured Tensor Contract",
    ]
    for group, values in design["captured_tensor_contract"].items():
        lines.append(f"- {group}: {', '.join(values)}")
    lines.extend(["", "## Tensor Alignment Contract"])
    lines.extend(f"- {item}" for item in design["tensor_alignment_contract"])
    lines.extend(
        [
            "",
            "## Masked Loss Readiness After Hook",
            f"- can_compute_masked_x_loss_after_hook: {manifest['can_compute_masked_x_loss_after_hook']}",
            f"- can_compute_masked_h_loss_after_hook: {manifest['can_compute_masked_h_loss_after_hook']}",
            "",
            "## Implementation Phases",
        ]
    )
    lines.extend(f"- {phase}" for phase in design["implementation_phases"])
    lines.extend(
        [
            "",
            "## Conclusion",
            f"- design_status: {design['design_status']}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "- Optimizer or training work should not begin before the hook prototype and masked-loss dry runs pass.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    step10i_passed = validate_step10i_outputs_v0()
    source_info = inspect_atomwise_hook_candidate_sources_v0()
    design = build_atomwise_loss_hook_design_v0(source_info)
    row = report_row(source_info, design, step10i_passed)
    manifest = preview_manifest(source_info, design, step10i_passed)
    write_csv([row], DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_design_report.csv", REPORT_COLUMNS)
    write_json(manifest, DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_design_preview_manifest.json")
    write_summary(source_info, design, manifest, "docs/diffsbdd_atomwise_loss_hook_design_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    code = run()
    print("diffsbdd_atomwise_loss_hook_design_v0_passed" if code == 0 else "diffsbdd_atomwise_loss_hook_design_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

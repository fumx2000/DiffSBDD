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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.diffsbdd_loss_semantics import (  # noqa: E402
    DEFAULT_ROOT,
    STAGE,
    PREVIOUS_STAGE,
    assess_forward_loss_training_readiness_v0,
    inspect_diffsbdd_loss_semantics_sources_v0,
    run_forward_output_semantics_probe_v0,
)


REPORT_COLUMNS = [
    "stage",
    "source_inspection_status",
    "probe_status",
    "forward_loss_semantics_status",
    "output0_is_loss_like",
    "output0_is_per_sample_vector",
    "output0_shape_by_mask_level",
    "output0_finite_by_mask_level",
    "output0_mean_by_mask_level",
    "output1_keys",
    "output1_all_finite",
    "training_step_uses_forward_output0",
    "recommended_loss_reduction",
    "output1_is_diagnostics",
    "mask_consumption_status",
    "lig_fixed_consumed_by_forward",
    "generation_mask_consumed_by_forward",
    "target_mask_consumed_by_forward",
    "current_forward_is_mask_aware",
    "current_forward_is_full_ligand_objective",
    "can_do_backward_smoke_next",
    "must_modify_loss_for_masked_training",
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "backward_called",
    "optimizer_step_executed",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "recommended_next_step",
    "blocking_reasons",
]


def _bool(value: bool) -> str:
    return str(bool(value)).lower()


def _json(value: Any) -> str:
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


def _output1_all_finite(probe_info: dict[str, Any]) -> bool:
    return all(all(values.values()) for values in probe_info["output1_finite_by_mask_level"].values())


def report_row(source_info: dict[str, Any], probe_info: dict[str, Any], assessment: dict[str, Any]) -> dict[str, str]:
    return {
        "stage": STAGE,
        "source_inspection_status": "passed" if source_info["forward_signature"] and source_info["training_step_signature"] else "blocked",
        "probe_status": probe_info["probe_status"],
        "forward_loss_semantics_status": assessment["forward_loss_semantics_status"],
        "output0_is_loss_like": _bool(assessment["output0_is_loss_like"]),
        "output0_is_per_sample_vector": _bool(assessment["output0_is_per_sample_vector"]),
        "output0_shape_by_mask_level": _json(probe_info["output0_shape_by_mask_level"]),
        "output0_finite_by_mask_level": _json(probe_info["output0_finite_by_mask_level"]),
        "output0_mean_by_mask_level": _json(probe_info["output0_mean_by_mask_level"]),
        "output1_keys": ";".join(assessment["output1_keys"]),
        "output1_all_finite": _bool(_output1_all_finite(probe_info)),
        "training_step_uses_forward_output0": _bool(assessment["training_step_uses_forward_output0"]),
        "recommended_loss_reduction": assessment["recommended_loss_reduction"],
        "output1_is_diagnostics": _bool(assessment["output1_is_diagnostics"]),
        "mask_consumption_status": assessment["mask_consumption_status"],
        "lig_fixed_consumed_by_forward": _bool(assessment["lig_fixed_consumed_by_forward"]),
        "generation_mask_consumed_by_forward": _bool(assessment["generation_mask_consumed_by_forward"]),
        "target_mask_consumed_by_forward": _bool(assessment["target_mask_consumed_by_forward"]),
        "current_forward_is_mask_aware": _bool(assessment["current_forward_is_mask_aware"]),
        "current_forward_is_full_ligand_objective": _bool(assessment["current_forward_is_full_ligand_objective"]),
        "can_do_backward_smoke_next": _bool(assessment["can_do_backward_smoke_next"]),
        "must_modify_loss_for_masked_training": _bool(assessment["must_modify_loss_for_masked_training"]),
        "checkpoint_loaded": _bool(probe_info["checkpoint_loaded"]),
        "checkpoint_saved": _bool(probe_info["checkpoint_saved"]),
        "training_step_called": _bool(probe_info["training_step_called"]),
        "backward_called": _bool(probe_info["backward_called"]),
        "optimizer_step_executed": _bool(probe_info["optimizer_step_executed"]),
        "trainer_fit_called": _bool(probe_info["trainer_fit_called"]),
        "training_executed": _bool(probe_info["training_executed"]),
        "real_finetune_executed": _bool(probe_info["real_finetune_executed"]),
        "recommended_next_step": assessment["recommended_next_step"],
        "blocking_reasons": ";".join(assessment["blocking_reasons"]),
    }


def preview_manifest(source_info: dict[str, Any], probe_info: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10f_forward_sweep_passed": probe_info["step10f_forward_sweep_passed"],
        "inspected_source_files": source_info["inspected_source_files"],
        "forward_loss_semantics_status": assessment["forward_loss_semantics_status"],
        "output0_is_loss_like": assessment["output0_is_loss_like"],
        "output0_is_per_sample_vector": assessment["output0_is_per_sample_vector"],
        "recommended_loss_reduction": assessment["recommended_loss_reduction"],
        "training_step_uses_forward_output0": assessment["training_step_uses_forward_output0"],
        "training_step_reduction_semantics": assessment["training_step_reduction_semantics"],
        "output1_is_diagnostics": assessment["output1_is_diagnostics"],
        "mask_consumption_status": assessment["mask_consumption_status"],
        "lig_fixed_consumed_by_forward": assessment["lig_fixed_consumed_by_forward"],
        "generation_mask_consumed_by_forward": assessment["generation_mask_consumed_by_forward"],
        "target_mask_consumed_by_forward": assessment["target_mask_consumed_by_forward"],
        "context_mask_consumed_by_forward": assessment["context_mask_consumed_by_forward"],
        "current_forward_is_mask_aware": assessment["current_forward_is_mask_aware"],
        "current_forward_is_full_ligand_objective": assessment["current_forward_is_full_ligand_objective"],
        "can_do_backward_smoke_next": assessment["can_do_backward_smoke_next"],
        "must_modify_loss_for_masked_training": assessment["must_modify_loss_for_masked_training"],
        "output0_shape_by_mask_level": probe_info["output0_shape_by_mask_level"],
        "output1_keys": assessment["output1_keys"],
        "requested_device": probe_info["requested_device"],
        "resolved_device": probe_info["resolved_device"],
        "cuda_available": probe_info["cuda_available"],
        "cuda_device_name": probe_info["cuda_device_name"],
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": False,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "archive_created": False,
        "all_checks_passed": assessment["forward_loss_semantics_status"] in {"ready", "uncertain"}
        and probe_info["probe_status"] == "passed"
        and assessment["can_do_backward_smoke_next"],
        "recommended_next_step": assessment["recommended_next_step"],
    }


def write_summary(source_info: dict[str, Any], probe_info: dict[str, Any], assessment: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DiffSBDD Forward Loss Semantics v0 Summary",
        "",
        "This step reviews DiffSBDD forward loss semantics without training.",
        "It does not load checkpoints.",
        "It does not save checkpoints.",
        "It does not call training_step.",
        "It does not run backward.",
        "It does not run an optimizer step.",
        "It does not call trainer.fit.",
        "It does not train or fine-tune.",
        "It does not modify DiffSBDD or equivariant_diffusion.",
        "",
        "## Output 0",
        f"- semantics: {source_info['output0_semantics_candidate']}",
        f"- output0_is_loss_like: {assessment['output0_is_loss_like']}",
        f"- output0_is_per_sample_vector: {assessment['output0_is_per_sample_vector']}",
        f"- recommended_loss_reduction: {assessment['recommended_loss_reduction']}",
        f"- training_step_reduction_semantics: {assessment['training_step_reduction_semantics']}",
        "",
        "## Output 1 Diagnostics",
        f"- output1_keys: {assessment['output1_keys']}",
        f"- output1_is_diagnostics: {assessment['output1_is_diagnostics']}",
        "",
        "## Mask Consumption",
        f"- mask_consumption_status: {assessment['mask_consumption_status']}",
        f"- lig_fixed_consumed_by_forward: {assessment['lig_fixed_consumed_by_forward']}",
        f"- generation_mask_consumed_by_forward: {assessment['generation_mask_consumed_by_forward']}",
        f"- target_mask_consumed_by_forward: {assessment['target_mask_consumed_by_forward']}",
        f"- current_forward_is_mask_aware: {assessment['current_forward_is_mask_aware']}",
        f"- current_forward_is_full_ligand_objective: {assessment['current_forward_is_full_ligand_objective']}",
        f"- must_modify_loss_for_masked_training: {assessment['must_modify_loss_for_masked_training']}",
        "",
        "The current forward sweep proves that the covalent batch can enter the real model.",
        "It does not prove that a masked covalent training objective is implemented, because the training forward path does not consume the covalent target/context masks.",
        "The next practical step can verify the original loss with a backward smoke, then design a masked loss adapter.",
        "",
        "## Probe Summary",
        f"- requested_device: {probe_info['requested_device']}",
        f"- resolved_device: {probe_info['resolved_device']}",
        f"- output0_shape_by_mask_level: {probe_info['output0_shape_by_mask_level']}",
        f"- output0_finite_by_mask_level: {probe_info['output0_finite_by_mask_level']}",
        f"- recommended_next_step: {assessment['recommended_next_step']}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    source_info = inspect_diffsbdd_loss_semantics_sources_v0()
    probe_info = run_forward_output_semantics_probe_v0(device="auto")
    assessment = assess_forward_loss_training_readiness_v0(source_info, probe_info)
    row = report_row(source_info, probe_info, assessment)
    manifest = preview_manifest(source_info, probe_info, assessment)
    write_csv([row], DEFAULT_ROOT / "diffsbdd_forward_loss_semantics_report.csv", REPORT_COLUMNS)
    write_json(manifest, DEFAULT_ROOT / "diffsbdd_forward_loss_semantics_preview_manifest.json")
    write_summary(source_info, probe_info, assessment, "docs/diffsbdd_forward_loss_semantics_v0_summary.md")
    return 0 if assessment["output0_is_loss_like"] and assessment["can_do_backward_smoke_next"] else 1


def main() -> int:
    code = run()
    print("diffsbdd_forward_loss_semantics_v0_passed" if code == 0 else "diffsbdd_forward_loss_semantics_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

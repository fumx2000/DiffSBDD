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

from covalent_ext.longer_no_checkpoint_training_dry_run_design import (  # noqa: E402
    DEFAULT_ROOT,
    LOSS_WEIGHTS,
    MAX_STEPS,
    PREVIOUS_STAGE,
    STAGE,
    build_longer_no_checkpoint_training_dry_run_design_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "row_type",
    "step",
    "cycle_index",
    "mask_level",
    "expected_target_atom_count",
    "expected_context_atom_count",
    "allowed",
    "forbidden",
    "stop_conditions",
    "checkpoint_allowed",
    "model_save_allowed",
    "trainer_fit_allowed",
    "training_step_allowed",
    "source_modification_allowed",
    "design_status",
    "blocking_reasons",
]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _join(values: list[Any]) -> str:
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


def _base_policy_fields(design: dict[str, Any]) -> dict[str, str]:
    contract = design["contract"]
    stop_policy = design["stop_policy"]
    checkpoint_policy = design["checkpoint_policy"]
    return {
        "allowed": _join(contract["allowed_actions"]),
        "forbidden": _join(contract["forbidden_actions"]),
        "stop_conditions": _join(stop_policy["hard_stop_conditions"]),
        "checkpoint_allowed": str(checkpoint_policy["next_12_step_dry_run_checkpoint_allowed"]).lower(),
        "model_save_allowed": str(checkpoint_policy["model_save_allowed"]).lower(),
        "trainer_fit_allowed": "false",
        "training_step_allowed": "false",
        "source_modification_allowed": "false",
        "design_status": "passed" if design["all_checks_passed"] else "blocked",
        "blocking_reasons": "",
    }


def report_rows(design: dict[str, Any]) -> list[dict[str, str]]:
    base = _base_policy_fields(design)
    rows: list[dict[str, str]] = []
    for schedule_row in design["schedule"]:
        rows.append(
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "row_type": "schedule",
                "step": str(schedule_row["step"]),
                "cycle_index": str(schedule_row["cycle_index"]),
                "mask_level": schedule_row["mask_level"],
                "expected_target_atom_count": str(schedule_row["expected_target_atom_count"]),
                "expected_context_atom_count": str(schedule_row["expected_context_atom_count"]),
                **base,
            }
        )
    policy_rows = [
        ("contract", design["contract"]),
        ("loss_policy", design["loss_policy"]),
        ("stop_policy", design["stop_policy"]),
        ("output_policy", design["output_policy"]),
        ("checkpoint_policy", design["checkpoint_policy"]),
        ("success_criteria", design["success_criteria"]),
        ("risk_register", design["risk_register"]),
    ]
    for row_type, payload in policy_rows:
        rows.append(
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "row_type": row_type,
                "step": "",
                "cycle_index": "",
                "mask_level": "",
                "expected_target_atom_count": "",
                "expected_context_atom_count": "",
                **base,
                "allowed": _json_text(payload),
                "forbidden": _join(design["contract"]["forbidden_actions"]),
            }
        )
    return rows


def preview_manifest(design: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10r_boundary_review_passed": design["step10r_boundary_review_passed"],
        "loop_name": design["loop_name"],
        "next_stage": design["next_stage"],
        "max_steps": design["max_steps"],
        "batch_size": design["batch_size"],
        "shuffle": design["shuffle"],
        "seed": design["seed"],
        "optimizer_class": design["optimizer_class"],
        "optimizer_lr": design["optimizer_lr"],
        "optimizer_weight_decay": design["optimizer_weight_decay"],
        "mask_schedule": design["mask_schedule_text"],
        "mask_schedule_values": design["mask_schedule"],
        "mask_schedule_length": design["mask_schedule_length"],
        "mask_counts": design["mask_counts"],
        "loss_weights": dict(LOSS_WEIGHTS),
        "loss_decrease_required": design["loss_policy"]["loss_decrease_required"],
        "quality_claim_allowed": design["loss_policy"]["quality_claim_allowed"],
        "checkpoint_allowed": design["checkpoint_policy"]["next_12_step_dry_run_checkpoint_allowed"],
        "model_save_allowed": design["checkpoint_policy"]["model_save_allowed"],
        "checkpoint_load_allowed": design["checkpoint_policy"]["checkpoint_load_allowed"],
        "checkpoint_save_allowed": design["checkpoint_policy"]["checkpoint_save_allowed"],
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "source_modification_allowed": False,
        "allowed_outputs": design["output_policy"]["allowed_outputs"],
        "forbidden_outputs": design["output_policy"]["forbidden_outputs"],
        "hard_stop_conditions": design["stop_policy"]["hard_stop_conditions"],
        "warning_thresholds": design["stop_policy"]["warning_thresholds"],
        "success_criteria": design["success_criteria"],
        "risk_register": design["risk_register"],
        "all_checks_passed": design["all_checks_passed"],
        "recommended_next_step": design["recommended_next_step"],
    }


def write_summary(design: dict[str, Any], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Longer No-Checkpoint Training Dry Run Design v0 Summary",
        "",
        "Step 10S is a design step, not training.",
        "It does not instantiate a model, run forward, call backward, execute optimizer step, call training step, call trainer fit, load or save checkpoints, save a model, or fine-tune.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## Purpose",
        "The 12-step dry run is intended to validate longer loop stability and boundary enforcement. It does not claim model quality or generation improvement.",
        "",
        "## Schedule",
        f"- max_steps: {manifest['max_steps']}",
        f"- batch_size: {manifest['batch_size']}",
        f"- shuffle: {manifest['shuffle']}",
        f"- seed: {manifest['seed']}",
        f"- mask_schedule: {manifest['mask_schedule']}",
        f"- mask_counts: {_json_text(manifest['mask_counts'])}",
        "",
        "## Loss Policy",
        f"- loss_weights: {_json_text(manifest['loss_weights'])}",
        f"- loss_decrease_required: {manifest['loss_decrease_required']}",
        f"- quality_claim_allowed: {manifest['quality_claim_allowed']}",
        "",
        "## Still Forbidden",
        f"- checkpoint_allowed: {manifest['checkpoint_allowed']}",
        f"- model_save_allowed: {manifest['model_save_allowed']}",
        f"- checkpoint_load_allowed: {manifest['checkpoint_load_allowed']}",
        f"- checkpoint_save_allowed: {manifest['checkpoint_save_allowed']}",
        f"- trainer_fit_allowed: {manifest['trainer_fit_allowed']}",
        f"- training_step_allowed: {manifest['training_step_allowed']}",
        f"- source_modification_allowed: {manifest['source_modification_allowed']}",
        "",
        "## Hard Stop Conditions",
    ]
    lines.extend(f"- {condition}" for condition in manifest["hard_stop_conditions"])
    lines.extend(
        [
            "",
            "## Checkpoint Boundary",
            "Checkpoint discussion remains deferred until the 12-step no-checkpoint dry run passes, output/checkpoint naming and retention policies are reviewed, and explicit user approval is given.",
            "",
            "## Recommended Next Step",
            f"- {manifest['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    design = build_longer_no_checkpoint_training_dry_run_design_v0()
    manifest = preview_manifest(design)
    write_csv(
        report_rows(design),
        DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_design_report.csv",
        REPORT_COLUMNS,
    )
    write_json(manifest, DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_design_preview_manifest.json")
    write_summary(design, manifest, "docs/longer_no_checkpoint_training_dry_run_design_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    code = run()
    print(
        "longer_no_checkpoint_training_dry_run_design_v0_passed"
        if code == 0
        else "longer_no_checkpoint_training_dry_run_design_v0_blocked"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())

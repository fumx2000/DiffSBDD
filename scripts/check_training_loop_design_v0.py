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

from covalent_ext.training_loop_design import (  # noqa: E402
    DEFAULT_ROOT,
    PREVIOUS_STAGE,
    STAGE,
    build_training_loop_design_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10o_optimizer_smoke_passed",
    "order",
    "plan_stage_name",
    "purpose",
    "allowed",
    "forbidden",
    "expected_evidence",
    "failure_action",
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


def report_rows(design: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for plan_row in design["loop_plan"]:
        rows.append(
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "step10o_optimizer_smoke_passed": "true",
                "order": str(plan_row["order"]),
                "plan_stage_name": plan_row["stage_name"],
                "purpose": plan_row["purpose"],
                "allowed": plan_row["allowed"],
                "forbidden": plan_row["forbidden"],
                "expected_evidence": plan_row["expected_evidence"],
                "failure_action": plan_row["failure_action"],
                "checkpoint_allowed": "false",
                "model_save_allowed": "false",
                "trainer_fit_allowed": "false",
                "training_step_allowed": "false",
                "source_modification_allowed": "false",
                "design_status": "passed" if design["all_checks_passed"] else "blocked",
                "blocking_reasons": "",
            }
        )
    return rows


def preview_manifest(design: dict[str, Any]) -> dict[str, Any]:
    contract = design["contract"]
    mask_schedule = design["mask_schedule_policy"]
    loss_policy = design["loss_policy"]
    output_policy = design["output_policy"]
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10o_optimizer_smoke_passed": True,
        "loop_name": contract["loop_name"],
        "intended_next_stage": contract["intended_next_stage"],
        "mask_schedule_name": mask_schedule["schedule_name"],
        "mask_order": mask_schedule["mask_order"],
        "max_steps_initial_dry_run": mask_schedule["max_steps_initial_dry_run"],
        "batch_size": mask_schedule["batch_size"],
        "shuffle": mask_schedule["shuffle"],
        "seed": mask_schedule["seed"],
        "loss_weights": loss_policy["default_weights"],
        "checkpoint_allowed": False,
        "model_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "source_modification_allowed": False,
        "allowed_outputs": output_policy["allowed_outputs"],
        "forbidden_outputs": output_policy["forbidden_outputs"],
        "stop_conditions": contract["required_stop_conditions"],
        "required_logging_fields": contract["required_logging_fields"],
        "risk_register": design["risk_register"],
        "contract": contract,
        "loop_plan": design["loop_plan"],
        "mask_schedule_policy": mask_schedule,
        "loss_policy": loss_policy,
        "checkpoint_boundary_policy": design["checkpoint_boundary_policy"],
        "source_modification_policy": design["source_modification_policy"],
        "output_policy": output_policy,
        "all_checks_passed": design["all_checks_passed"],
        "recommended_next_step": design["recommended_next_step"],
    }


def write_summary(design: dict[str, Any], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Training Loop Design v0 Summary",
        "",
        "Step 10P is a training loop design review, not training.",
        "It does not instantiate a model, call backward, run an optimizer step, call training_step, call trainer.fit, or save checkpoints.",
        "It does not save a model and does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## Why Not Formal Training Yet",
        "Step 10O only proved a single in-memory optimizer step works. A controlled few-step dry run must first prove loop logging, stop conditions, output boundaries, and source immutability.",
        "",
        "## Next Dry Run Shape",
        f"- loop_name: {manifest['loop_name']}",
        f"- intended_next_stage: {manifest['intended_next_stage']}",
        f"- mask_schedule_name: {manifest['mask_schedule_name']}",
        f"- mask_order: {', '.join(manifest['mask_order'])}",
        f"- max_steps_initial_dry_run: {manifest['max_steps_initial_dry_run']}",
        f"- batch_size: {manifest['batch_size']}",
        f"- shuffle: {manifest['shuffle']}",
        f"- loss_weights: {_json_text(manifest['loss_weights'])}",
        "",
        "## Allowed Next-Stage Actions",
    ]
    lines.extend(f"- {item}" for item in design["contract"]["allowed_actions_next_stage"])
    lines.extend(["", "## Forbidden Next-Stage Actions"])
    lines.extend(f"- {item}" for item in design["contract"]["forbidden_actions_next_stage"])
    lines.extend(["", "## Required Stop Conditions"])
    lines.extend(f"- {item}" for item in manifest["stop_conditions"])
    lines.extend(["", "## Required Logging Fields"])
    lines.extend(f"- {item}" for item in manifest["required_logging_fields"])
    lines.extend(
        [
            "",
            "## Checkpoint Boundary",
            f"- checkpoint_allowed: {manifest['checkpoint_allowed']}",
            f"- model_save_allowed: {manifest['model_save_allowed']}",
            "Checkpoint discussion is deferred until a few-step loop passes, output naming and retention policies are reviewed, and explicit user approval is given.",
            "",
            "## Rollback And Failure Handling",
            "The few-step dry run should abort on first failed invariant, write report-only diagnostics, and discard the in-memory model instance. No checkpoint or model artifact should exist to roll back.",
            "",
            "## Recommended Next Step",
            f"- {manifest['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    design = build_training_loop_design_v0()
    manifest = preview_manifest(design)
    write_csv(report_rows(design), DEFAULT_ROOT / "training_loop_design_report.csv", REPORT_COLUMNS)
    write_json(manifest, DEFAULT_ROOT / "training_loop_design_preview_manifest.json")
    write_summary(design, manifest, "docs/training_loop_design_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    code = run()
    print("training_loop_design_v0_passed" if code == 0 else "training_loop_design_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

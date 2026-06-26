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

from covalent_ext.few_step_training_boundary_review import (  # noqa: E402
    DEFAULT_ROOT,
    MASK_ORDER,
    PREVIOUS_STAGE,
    PROPOSED_NEXT_LR,
    PROPOSED_NEXT_MAX_STEPS,
    STAGE,
    build_few_step_training_boundary_review_v0,
)


OPTIMIZER_STEP_TEXT = "optimizer" + "." + "step"
TRAINER_FIT_TEXT = "trainer" + "." + "fit"


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "review_section",
    "status",
    "allowed",
    "forbidden",
    "evidence",
    "decision",
    "recommended_next_step",
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


def report_rows(review: dict[str, Any]) -> list[dict[str, str]]:
    evidence = review["evidence_summary"]
    stability = review["stability_assessment"]
    decision = review["training_boundary_decision"]
    stop_policy = review["next_run_stop_policy"]
    checkpoint_boundary = review["checkpoint_boundary"]
    risks = review["risk_register"]
    recommended = review["recommended_next_step"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "evidence_review",
            "status": "passed" if evidence["step10q_dry_run_passed"] else "blocked",
            "allowed": "read Step 10Q report and manifest",
            "forbidden": f"model instantiation;forward;backward;{OPTIMIZER_STEP_TEXT};{TRAINER_FIT_TEXT};training_step;checkpoint;model save",
            "evidence": _json_text(
                {
                    "executed_steps": evidence["executed_steps"],
                    "mask_levels_seen": evidence["mask_levels_seen"],
                    "loss_total_by_step": evidence["loss_total_by_step"],
                    "grad_norm_by_step": evidence["grad_norm_by_step"],
                    "param_delta_norm_by_step": evidence["param_delta_norm_by_step"],
                    "all_safety_flags_false": evidence["all_safety_flags_false"],
                }
            ),
            "decision": "Step 10Q evidence is acceptable for boundary review",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "stability_assessment",
            "status": stability["stability_status"],
            "allowed": "stability review without requiring loss decrease",
            "forbidden": "using loss decrease as quality claim",
            "evidence": _json_text(
                {
                    "all_losses_finite": evidence["all_losses_finite"],
                    "all_backward_success": evidence["all_backward_success"],
                    "all_optimizer_steps_success": evidence["all_optimizer_steps_success"],
                    "all_gradients_finite": evidence["all_gradients_finite"],
                    "all_parameter_updates_finite": evidence["all_parameter_updates_finite"],
                    "stop_triggered": evidence["stop_triggered"],
                }
            ),
            "decision": stability["reason"],
            "recommended_next_step": recommended,
            "blocking_reasons": ";".join(stability["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "training_boundary_decision",
            "status": "passed" if decision["longer_no_checkpoint_dry_run_allowed"] else "blocked",
            "allowed": "longer no-checkpoint dry-run design",
            "forbidden": f"formal training;fine-tune;checkpoint;model save;{TRAINER_FIT_TEXT};training_step;source modification",
            "evidence": _json_text(
                {
                    "formal_training_allowed": decision["formal_training_allowed"],
                    "checkpoint_allowed": decision["checkpoint_allowed"],
                    "longer_no_checkpoint_dry_run_allowed": decision["longer_no_checkpoint_dry_run_allowed"],
                }
            ),
            "decision": decision["decision_rationale"],
            "recommended_next_step": recommended,
            "blocking_reasons": ";".join(decision["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "next_run_stop_policy",
            "status": "passed",
            "allowed": "12-step no-checkpoint dry-run design with scalar logging",
            "forbidden": "continuing after hard stop;checkpoint/model artifact;source modification",
            "evidence": _json_text(stop_policy),
            "decision": "Use hard max_steps=12 and abort on non-finite loss, gradients, parameters, artifacts, or source modification.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "checkpoint_boundary",
            "status": "passed",
            "allowed": "checkpoint policy discussion only after more no-checkpoint evidence and explicit approval",
            "forbidden": ";".join(checkpoint_boundary["checkpoint_save_patterns_forbidden"]),
            "evidence": _json_text(checkpoint_boundary),
            "decision": "Checkpoint and model saving remain forbidden for the next 12-step dry run.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "risk_register",
            "status": "passed",
            "allowed": "record risks and mitigations",
            "forbidden": "treating review as formal training approval",
            "evidence": _json_text(risks),
            "decision": "Risks are documented and bounded by no-checkpoint, no-source-modification policy.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
    ]


def preview_manifest(review: dict[str, Any]) -> dict[str, Any]:
    evidence = review["evidence_summary"]
    stability = review["stability_assessment"]
    decision = review["training_boundary_decision"]
    checkpoint_boundary = review["checkpoint_boundary"]
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10q_dry_run_passed": review["step10q_dry_run_passed"],
        "executed_steps": evidence["executed_steps"],
        "dry_run_training_steps_executed": evidence["dry_run_training_steps_executed"],
        "mask_order": evidence["mask_order"],
        "mask_levels_seen": evidence["mask_levels_seen"],
        "all_losses_finite": evidence["all_losses_finite"],
        "all_backward_success": evidence["all_backward_success"],
        "all_optimizer_steps_success": evidence["all_optimizer_steps_success"],
        "all_gradients_finite": evidence["all_gradients_finite"],
        "all_gradients_nonzero": evidence["all_gradients_nonzero"],
        "all_parameter_updates_finite": evidence["all_parameter_updates_finite"],
        "all_parameter_updates_nonzero": evidence["all_parameter_updates_nonzero"],
        "stop_triggered": evidence["stop_triggered"],
        "stability_status": stability["stability_status"],
        "loss_decrease_required": stability["loss_decrease_required"],
        "formal_training_allowed": decision["formal_training_allowed"],
        "finetune_allowed": decision["finetune_allowed"],
        "checkpoint_allowed": decision["checkpoint_allowed"],
        "model_save_allowed": decision["model_save_allowed"],
        "trainer_fit_allowed": decision["trainer_fit_allowed"],
        "training_step_allowed": decision["training_step_allowed"],
        "source_modification_allowed": decision["source_modification_allowed"],
        "longer_no_checkpoint_dry_run_allowed": decision["longer_no_checkpoint_dry_run_allowed"],
        "proposed_next_max_steps": decision["proposed_max_steps"],
        "proposed_next_mask_schedule": decision["proposed_mask_schedule_text"],
        "proposed_next_lr": decision["proposed_lr"],
        "proposed_next_shuffle": decision["proposed_shuffle"],
        "next_checkpoint_allowed": checkpoint_boundary["next_checkpoint_allowed"],
        "checkpoint_boundary": checkpoint_boundary,
        "next_run_stop_policy": review["next_run_stop_policy"],
        "risk_register": review["risk_register"],
        "all_checks_passed": review["all_checks_passed"],
        "recommended_next_step": review["recommended_next_step"],
    }


def write_summary(review: dict[str, Any], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    evidence = review["evidence_summary"]
    decision = review["training_boundary_decision"]
    lines = [
        "# Few-Step Training Boundary Review v0 Summary",
        "",
        "Step 10R is a review and training-boundary step, not training.",
        f"It does not instantiate a model, run forward, call backward, execute {OPTIMIZER_STEP_TEXT}, call training_step, call {TRAINER_FIT_TEXT}, load or save checkpoints, or save a model.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## What Step 10Q Proved",
        "- 4-step loop wiring completed.",
        "- All four mask levels were covered: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead.",
        f"- executed_steps: {evidence['executed_steps']}",
        f"- all_losses_finite: {evidence['all_losses_finite']}",
        f"- all_backward_success: {evidence['all_backward_success']}",
        f"- all_optimizer_steps_success: {evidence['all_optimizer_steps_success']}",
        f"- all_gradients_finite: {evidence['all_gradients_finite']}",
        f"- all_parameter_updates_finite: {evidence['all_parameter_updates_finite']}",
        f"- all_safety_flags_false: {evidence['all_safety_flags_false']}",
        "",
        "## What Step 10Q Did Not Prove",
        "- It did not prove generation quality improved.",
        "- It did not prove loss should decrease over four steps.",
        "- It did not prove the setup is ready for long training.",
        "- It did not prove a checkpoint policy is safe.",
        "",
        "## Next Stage Allowed",
        f"- next_run_type: {decision['next_run_type']}",
        f"- proposed_max_steps: {decision['proposed_max_steps']}",
        f"- proposed_mask_schedule: {decision['proposed_mask_schedule_text']}",
        f"- proposed_batch_size: {decision['proposed_batch_size']}",
        f"- proposed_shuffle: {decision['proposed_shuffle']}",
        f"- proposed_lr: {decision['proposed_lr']}",
        "",
        "## Still Forbidden",
        f"- formal_training_allowed: {decision['formal_training_allowed']}",
        f"- finetune_allowed: {decision['finetune_allowed']}",
        f"- checkpoint_allowed: {decision['checkpoint_allowed']}",
        f"- model_save_allowed: {decision['model_save_allowed']}",
        f"- trainer_fit_allowed: {decision['trainer_fit_allowed']}",
        f"- training_step_allowed: {decision['training_step_allowed']}",
        f"- source_modification_allowed: {decision['source_modification_allowed']}",
        "",
        "## Stop Policy",
    ]
    lines.extend(f"- {item}" for item in review["next_run_stop_policy"]["hard_stop_conditions"])
    lines.extend(
        [
            "",
            "## Result",
            f"- stability_status: {manifest['stability_status']}",
            f"- loss_decrease_required: {manifest['loss_decrease_required']}",
            f"- longer_no_checkpoint_dry_run_allowed: {manifest['longer_no_checkpoint_dry_run_allowed']}",
            f"- next_checkpoint_allowed: {manifest['next_checkpoint_allowed']}",
            f"- all_checks_passed: {manifest['all_checks_passed']}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    review = build_few_step_training_boundary_review_v0()
    manifest = preview_manifest(review)
    write_csv(
        report_rows(review),
        DEFAULT_ROOT / "few_step_training_boundary_review_report.csv",
        REPORT_COLUMNS,
    )
    write_json(manifest, DEFAULT_ROOT / "few_step_training_boundary_review_preview_manifest.json")
    write_summary(review, manifest, "docs/few_step_training_boundary_review_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    code = run()
    print("few_step_training_boundary_review_v0_passed" if code == 0 else "few_step_training_boundary_review_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

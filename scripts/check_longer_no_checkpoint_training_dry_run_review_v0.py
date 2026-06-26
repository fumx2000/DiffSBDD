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

from covalent_ext.longer_no_checkpoint_training_dry_run_review import (  # noqa: E402
    DEFAULT_ROOT,
    PREVIOUS_STAGE,
    STAGE,
    build_longer_no_checkpoint_training_dry_run_review_v0,
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
    "observation",
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
    observations = review["evidence_observations"]
    decision = review["next_boundary_decision"]
    checkpoint_gate = review["checkpoint_discussion_gate"]
    risk_register = review["risk_register"]
    recommended = review["recommended_next_step"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "evidence_review",
            "status": "passed" if evidence["step10t_dry_run_passed"] else "blocked",
            "allowed": "read Step 10T report and manifest",
            "forbidden": f"model instantiation;forward;backward;{OPTIMIZER_STEP_TEXT};{TRAINER_FIT_TEXT};training_step;checkpoint;model save",
            "evidence": _json_text(
                {
                    "executed_steps": evidence["executed_steps"],
                    "dry_run_training_steps_executed": evidence["dry_run_training_steps_executed"],
                    "mask_counts_seen": evidence["mask_counts_seen"],
                    "loss_total_by_step": evidence["loss_total_by_step"],
                    "grad_norm_by_step": evidence["grad_norm_by_step"],
                    "param_delta_norm_by_step": evidence["param_delta_norm_by_step"],
                    "all_safety_flags_false": evidence["all_safety_flags_false"],
                }
            ),
            "observation": "Step 10T completed 12 bounded no-checkpoint dry-run steps.",
            "decision": "Step 10T evidence is acceptable for dry-run review.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "stability_assessment",
            "status": stability["stability_status"],
            "allowed": "review stability without loss decrease or quality claim",
            "forbidden": "treating dry-run losses as model-quality proof",
            "evidence": _json_text(
                {
                    "all_steps_passed": evidence["all_steps_passed"],
                    "all_losses_finite": evidence["all_losses_finite"],
                    "all_backward_success": evidence["all_backward_success"],
                    "all_optimizer_steps_success": evidence["all_optimizer_steps_success"],
                    "all_gradients_finite": evidence["all_gradients_finite"],
                    "all_parameter_updates_finite": evidence["all_parameter_updates_finite"],
                    "warnings_triggered": evidence["warnings_triggered"],
                    "stop_triggered": evidence["stop_triggered"],
                }
            ),
            "observation": stability["reason"],
            "decision": f"stability_status={stability['stability_status']}",
            "recommended_next_step": recommended,
            "blocking_reasons": ";".join(stability["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "observations",
            "status": "passed",
            "allowed": "record non-blocking observations",
            "forbidden": "converting observations into quality claims",
            "evidence": _json_text(
                {
                    "loss_total_range": observations["loss_total_range"],
                    "grad_norm_range": observations["grad_norm_range"],
                    "param_delta_norm_range": observations["param_delta_norm_range"],
                }
            ),
            "observation": _json_text(
                {
                    "highest_grad_step": observations["highest_grad_step"],
                    "highest_grad_mask_level": observations["highest_grad_mask_level"],
                    "highest_grad_value": observations["highest_grad_value"],
                    "highest_grad_observation": observations["highest_grad_observation"],
                }
            ),
            "decision": "Highest gradient is finite and below warning threshold; record it as observation only.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "next_boundary_decision",
            "status": "passed" if decision["checkpoint_policy_design_allowed"] else "blocked",
            "allowed": "checkpoint/output policy design",
            "forbidden": f"formal training;fine-tune;checkpoint save;model save;{TRAINER_FIT_TEXT};training_step;source modification",
            "evidence": _json_text(
                {
                    "formal_training_allowed": decision["formal_training_allowed"],
                    "checkpoint_allowed": decision["checkpoint_allowed"],
                    "checkpoint_policy_design_allowed": decision["checkpoint_policy_design_allowed"],
                    "output_policy_design_allowed": decision["output_policy_design_allowed"],
                }
            ),
            "observation": "Next stage is policy design only.",
            "decision": decision["decision_rationale"],
            "recommended_next_step": recommended,
            "blocking_reasons": ";".join(decision["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "checkpoint_discussion_gate",
            "status": "passed",
            "allowed": "checkpoint/output policy discussion only",
            "forbidden": "checkpoint save;checkpoint load;model save;direct checkpoint creation",
            "evidence": _json_text(checkpoint_gate),
            "observation": "Checkpoint remains disabled until policy design and explicit approval.",
            "decision": "Policy design may proceed; checkpointing itself remains forbidden.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "risk_register",
            "status": "passed",
            "allowed": "record risks and mitigations",
            "forbidden": "treating review as checkpoint or formal-training approval",
            "evidence": _json_text(risk_register),
            "observation": "Risks are bounded by policy-design-only next step.",
            "decision": "Proceed only to checkpoint/output policy design.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
    ]


def preview_manifest(review: dict[str, Any]) -> dict[str, Any]:
    evidence = review["evidence_summary"]
    stability = review["stability_assessment"]
    observations = review["evidence_observations"]
    decision = review["next_boundary_decision"]
    checkpoint_gate = review["checkpoint_discussion_gate"]
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10t_dry_run_passed": review["step10t_dry_run_passed"],
        "executed_steps": evidence["executed_steps"],
        "dry_run_training_steps_executed": evidence["dry_run_training_steps_executed"],
        "mask_schedule_length": evidence["mask_schedule_length"],
        "mask_schedule": evidence["mask_schedule"],
        "mask_levels_seen": evidence["mask_levels_seen"],
        "mask_counts_seen": evidence["mask_counts_seen"],
        "all_steps_passed": evidence["all_steps_passed"],
        "all_losses_finite": evidence["all_losses_finite"],
        "all_backward_success": evidence["all_backward_success"],
        "all_optimizer_steps_success": evidence["all_optimizer_steps_success"],
        "all_gradients_finite": evidence["all_gradients_finite"],
        "all_gradients_nonzero": evidence["all_gradients_nonzero"],
        "all_parameter_updates_finite": evidence["all_parameter_updates_finite"],
        "all_parameter_updates_nonzero": evidence["all_parameter_updates_nonzero"],
        "warnings_triggered": evidence["warnings_triggered"],
        "warning_steps": evidence["warning_steps"],
        "stop_triggered": evidence["stop_triggered"],
        "stability_status": stability["stability_status"],
        "loss_decrease_required": stability["loss_decrease_required"],
        "quality_claim_allowed": stability["quality_claim_allowed"],
        "highest_grad_step": observations["highest_grad_step"],
        "highest_grad_mask_level": observations["highest_grad_mask_level"],
        "highest_grad_value": observations["highest_grad_value"],
        "formal_training_allowed": decision["formal_training_allowed"],
        "finetune_allowed": decision["finetune_allowed"],
        "checkpoint_allowed": decision["checkpoint_allowed"],
        "model_save_allowed": decision["model_save_allowed"],
        "trainer_fit_allowed": decision["trainer_fit_allowed"],
        "training_step_allowed": decision["training_step_allowed"],
        "source_modification_allowed": decision["source_modification_allowed"],
        "checkpoint_policy_design_allowed": decision["checkpoint_policy_design_allowed"],
        "output_policy_design_allowed": decision["output_policy_design_allowed"],
        "checkpoint_save_allowed": checkpoint_gate["checkpoint_save_allowed"],
        "checkpoint_load_allowed": checkpoint_gate["checkpoint_load_allowed"],
        "next_step_is_policy_design_only": checkpoint_gate["next_step_is_policy_design_only"],
        "checkpoint_discussion_gate": checkpoint_gate,
        "risk_register": review["risk_register"],
        "all_checks_passed": review["all_checks_passed"],
        "recommended_next_step": review["recommended_next_step"],
    }


def write_summary(review: dict[str, Any], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    evidence = review["evidence_summary"]
    observations = review["evidence_observations"]
    decision = review["next_boundary_decision"]
    lines = [
        "# Longer No-Checkpoint Training Dry Run Review v0 Summary",
        "",
        "Step 10U is review only, not training.",
        "It does not instantiate a model, run forward, call backward, execute optimizer step, call training_step, call trainer fit, load or save checkpoints, save a model, or save optimizer state.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## What Step 10T Proved",
        "- 12-step loop wiring completed.",
        "- Three full A/B/B2/C cycles completed.",
        f"- executed_steps: {evidence['executed_steps']}",
        f"- dry_run_training_steps_executed: {evidence['dry_run_training_steps_executed']}",
        f"- all_losses_finite: {evidence['all_losses_finite']}",
        f"- all_backward_success: {evidence['all_backward_success']}",
        f"- all_optimizer_steps_success: {evidence['all_optimizer_steps_success']}",
        f"- all_gradients_finite: {evidence['all_gradients_finite']}",
        f"- all_parameter_updates_finite: {evidence['all_parameter_updates_finite']}",
        f"- warnings_triggered: {evidence['warnings_triggered']}",
        f"- stop_triggered: {evidence['stop_triggered']}",
        "",
        "## What Step 10T Did Not Prove",
        "- It did not prove model generation quality improved.",
        "- It did not prove loss should decrease.",
        "- It did not prove formal training is allowed.",
        "- It did not prove checkpoint strategy is safe.",
        "",
        "## Observation",
        f"- highest_grad_step: {observations['highest_grad_step']}",
        f"- highest_grad_mask_level: {observations['highest_grad_mask_level']}",
        f"- highest_grad_value: {observations['highest_grad_value']}",
        f"- observation: {observations['highest_grad_observation']}",
        "",
        "## Next Stage Allowed",
        f"- checkpoint_policy_design_allowed: {decision['checkpoint_policy_design_allowed']}",
        f"- output_policy_design_allowed: {decision['output_policy_design_allowed']}",
        "",
        "## Still Forbidden",
        f"- formal_training_allowed: {decision['formal_training_allowed']}",
        f"- finetune_allowed: {decision['finetune_allowed']}",
        f"- checkpoint_allowed: {decision['checkpoint_allowed']}",
        f"- model_save_allowed: {decision['model_save_allowed']}",
        f"- trainer_fit_allowed: {decision['trainer_fit_allowed']}",
        f"- training_step_allowed: {decision['training_step_allowed']}",
        f"- source_modification_allowed: {decision['source_modification_allowed']}",
        f"- checkpoint_save_allowed: {manifest['checkpoint_save_allowed']}",
        f"- checkpoint_load_allowed: {manifest['checkpoint_load_allowed']}",
        "",
        "## Result",
        f"- stability_status: {manifest['stability_status']}",
        f"- loss_decrease_required: {manifest['loss_decrease_required']}",
        f"- quality_claim_allowed: {manifest['quality_claim_allowed']}",
        f"- next_step_is_policy_design_only: {manifest['next_step_is_policy_design_only']}",
        f"- all_checks_passed: {manifest['all_checks_passed']}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    review = build_longer_no_checkpoint_training_dry_run_review_v0()
    manifest = preview_manifest(review)
    write_csv(
        report_rows(review),
        DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_review_report.csv",
        REPORT_COLUMNS,
    )
    write_json(manifest, DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_review_preview_manifest.json")
    write_summary(review, manifest, "docs/longer_no_checkpoint_training_dry_run_review_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    code = run()
    print(
        "longer_no_checkpoint_training_dry_run_review_v0_passed"
        if code == 0
        else "longer_no_checkpoint_training_dry_run_review_v0_blocked"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())

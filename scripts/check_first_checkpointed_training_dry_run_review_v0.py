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

from covalent_ext.first_checkpointed_training_dry_run_review import (  # noqa: E402
    CHECKPOINT_FILENAME,
    CHECKPOINT_PATH,
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_CHECKPOINT_SIZE_BYTES,
    LOCAL_CHECKPOINT_REVIEW_JSON,
    MASK_SCHEDULE,
    REVIEW_MANIFEST_JSON,
    REVIEW_REPORT_CSV,
    REVIEW_SUMMARY_MD,
    STAGE,
    PREVIOUS_STAGE,
    build_first_checkpointed_training_dry_run_review_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "review_section",
    "status",
    "evidence",
    "observation",
    "decision",
    "allowed_next",
    "forbidden_next",
    "recommended_next_step",
    "blocking_reasons",
]


def _bool(value: Any) -> str:
    return str(bool(value)).lower()


def _list_text(values: Any) -> str:
    if isinstance(values, list):
        return ";".join(str(value) for value in values)
    return "" if values is None else str(values)


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


def review_manifest(review: dict[str, Any]) -> dict[str, Any]:
    evidence = review["evidence"]
    artifact = review["local_checkpoint_artifact_review"]
    payload = review["payload_schema_review"]
    assessment = review["assessment"]
    observations = review["observations"]
    next_decision = review["next_boundary_decision"]
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10w_run_passed": evidence["step10w_run_passed"],
        "executed_steps": evidence["executed_steps"],
        "dry_run_training_steps_executed": evidence["dry_run_training_steps_executed"],
        "mask_schedule": evidence["mask_schedule"],
        "mask_counts_seen": evidence["mask_counts_seen"],
        "all_steps_passed": evidence["all_steps_passed"],
        "all_losses_finite": evidence["all_losses_finite"],
        "all_backward_success": evidence["all_backward_success"],
        "all_optimizer_steps_success": evidence["all_optimizer_steps_success"],
        "all_gradients_finite": evidence["all_gradients_finite"],
        "all_parameter_updates_finite": evidence["all_parameter_updates_finite"],
        "checkpoint_saved": evidence["checkpoint_saved"],
        "checkpoint_count": evidence["checkpoint_count"],
        "checkpoint_filename": evidence["checkpoint_filename"],
        "checkpoint_path": evidence["checkpoint_path"],
        "checkpoint_sha256": evidence["checkpoint_sha256"],
        "checkpoint_size_bytes": evidence["checkpoint_size_bytes"],
        "local_checkpoint_present": artifact["local_checkpoint_present"],
        "local_checkpoint_sha256_matches": artifact["local_checkpoint_sha256_matches"],
        "local_checkpoint_size_matches": artifact["local_checkpoint_size_matches"],
        "checkpoint_tracked_by_git": artifact["checkpoint_tracked_by_git"],
        "checkpoint_staged_by_git": artifact["checkpoint_staged_by_git"],
        "checkpoint_ignored_or_untracked": artifact["checkpoint_ignored_or_untracked"],
        "checkpoint_git_commit_allowed": artifact["checkpoint_git_commit_allowed"],
        "checkpoint_payload_schema_valid": evidence["checkpoint_payload_schema_valid"],
        "payload_schema_reviewed": payload["payload_schema_reviewed"],
        "payload_review_passed": payload["payload_review_passed"],
        "payload_load_used_weights_only": payload.get("payload_load_used_weights_only", False),
        "resume_smoke_passed": evidence["resume_smoke_passed"],
        "model_state_loaded": evidence["model_state_loaded"],
        "optimizer_state_loaded": evidence["optimizer_state_loaded"],
        "completed_steps_verified": evidence["completed_steps_verified"],
        "mask_schedule_verified": evidence["mask_schedule_verified"],
        "parameter_shapes_verified": evidence["parameter_shapes_verified"],
        "second_checkpoint_saved": evidence["second_checkpoint_saved"],
        "training_step_called": evidence["training_step_called"],
        "trainer_fit_called": evidence["trainer_fit_called"],
        "model_saved": evidence["model_saved"],
        "formal_training_executed": evidence["formal_training_executed"],
        "real_finetune_executed": evidence["real_finetune_executed"],
        "forbidden_artifacts_created": evidence["forbidden_artifacts_created"],
        "unexpected_checkpoint_files_created": evidence["unexpected_checkpoint_files_created"],
        "review_status": assessment["review_status"],
        "checkpoint_artifact_status": assessment["checkpoint_artifact_status"],
        "resume_smoke_status": assessment["resume_smoke_status"],
        "training_boundary_status": assessment["training_boundary_status"],
        "loss_decrease_required": assessment["loss_decrease_required"],
        "quality_claim_allowed": assessment["quality_claim_allowed"],
        "formal_training_allowed": assessment["formal_training_allowed"],
        "finetune_allowed": assessment["finetune_allowed"],
        "long_training_allowed": assessment["long_training_allowed"],
        "model_save_allowed": assessment["model_save_allowed"],
        "direct_long_training_allowed": next_decision["direct_long_training_allowed"],
        "future_clean_run_recommended": observations["future_clean_run_recommended"],
        "recommended_next_step": review["recommended_next_step"],
        "all_checks_passed": review["all_checks_passed"],
    }


def review_rows(review: dict[str, Any]) -> list[dict[str, str]]:
    evidence = review["evidence"]
    artifact = review["local_checkpoint_artifact_review"]
    payload = review["payload_schema_review"]
    assessment = review["assessment"]
    observations = review["observations"]
    next_decision = review["next_boundary_decision"]
    recommended = review["recommended_next_step"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "run_evidence_review",
            "status": "passed" if evidence["step10w_run_passed"] else "blocked",
            "evidence": _json_text(
                {
                    "executed_steps": evidence["executed_steps"],
                    "mask_schedule": evidence["mask_schedule"],
                    "mask_counts_seen": evidence["mask_counts_seen"],
                    "all_steps_passed": evidence["all_steps_passed"],
                    "all_losses_finite": evidence["all_losses_finite"],
                    "all_backward_success": evidence["all_backward_success"],
                    "all_optimizer_steps_success": evidence["all_optimizer_steps_success"],
                }
            ),
            "observation": "",
            "decision": "Step 10W run evidence is accepted for review.",
            "allowed_next": "clean checkpointed dry-run design",
            "forbidden_next": "direct long training;formal training;fine-tune",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "checkpoint_artifact_review",
            "status": assessment["checkpoint_artifact_status"],
            "evidence": _json_text(artifact),
            "observation": "checkpoint is a large local binary artifact and should stay outside normal Git history",
            "decision": "Keep checkpoint local; commit metadata and evidence only.",
            "allowed_next": "local artifact review",
            "forbidden_next": "checkpoint Git commit;additional checkpoint files",
            "recommended_next_step": recommended,
            "blocking_reasons": _list_text(assessment["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "payload_schema_review",
            "status": "passed" if payload["payload_review_passed"] else "blocked",
            "evidence": _json_text(payload),
            "observation": "",
            "decision": "Payload top-level schema is compatible with review evidence.",
            "allowed_next": "clean checkpointed dry-run design",
            "forbidden_next": "model instantiation during review;optimizer construction during review",
            "recommended_next_step": recommended,
            "blocking_reasons": _list_text(payload["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "resume_smoke_review",
            "status": assessment["resume_smoke_status"],
            "evidence": _json_text(
                {
                    "resume_smoke_passed": evidence["resume_smoke_passed"],
                    "model_state_loaded": evidence["model_state_loaded"],
                    "optimizer_state_loaded": evidence["optimizer_state_loaded"],
                    "completed_steps_verified": evidence["completed_steps_verified"],
                    "mask_schedule_verified": evidence["mask_schedule_verified"],
                    "parameter_shapes_verified": evidence["parameter_shapes_verified"],
                    "second_checkpoint_saved": evidence["second_checkpoint_saved"],
                }
            ),
            "observation": "",
            "decision": "Resume smoke evidence passed without a second checkpoint.",
            "allowed_next": "clean checkpointed dry-run design",
            "forbidden_next": "resume optimizer step;second checkpoint save",
            "recommended_next_step": recommended,
            "blocking_reasons": _list_text(assessment["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "safety_boundary_review",
            "status": assessment["training_boundary_status"],
            "evidence": _json_text(
                {
                    "training_step_called": evidence["training_step_called"],
                    "trainer_fit_called": evidence["trainer_fit_called"],
                    "model_saved": evidence["model_saved"],
                    "formal_training_executed": evidence["formal_training_executed"],
                    "real_finetune_executed": evidence["real_finetune_executed"],
                    "forbidden_artifacts_created": evidence["forbidden_artifacts_created"],
                }
            ),
            "observation": "",
            "decision": "Training boundary stayed inside the first checkpointed dry-run scope.",
            "allowed_next": "review-only boundary decision",
            "forbidden_next": "formal training;fine-tune;model save",
            "recommended_next_step": recommended,
            "blocking_reasons": _list_text(assessment["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "observations",
            "status": "passed",
            "evidence": "",
            "observation": _json_text(observations),
            "decision": "Non-clean git status during Step 10W is an observation, not a blocker.",
            "allowed_next": "clean committed-code rerun design",
            "forbidden_next": "quality claim;loss trend claim",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "next_boundary_decision",
            "status": "passed" if review["all_checks_passed"] else "blocked",
            "evidence": "",
            "observation": "",
            "decision": _json_text(next_decision),
            "allowed_next": "clean_checkpointed_dry_run_from_committed_code_design",
            "forbidden_next": "direct_long_training;direct_generation_quality_claim;checkpoint_git_commit",
            "recommended_next_step": recommended,
            "blocking_reasons": _list_text(assessment["blocking_reasons"]),
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "review_section": "risk_register",
            "status": "passed",
            "evidence": "",
            "observation": _json_text(
                [
                    "checkpoint remains local and intentionally untracked",
                    "Step 10W was run before Step 10W files were committed",
                    "clean committed-code rerun should precede longer training",
                ]
            ),
            "decision": "Keep formal training and checkpoint Git commit disallowed.",
            "allowed_next": "design next clean dry run",
            "forbidden_next": "long training;model save;fine-tune",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
    ]


def write_summary(review: dict[str, Any], output_md: str | Path) -> None:
    manifest = review_manifest(review)
    observations = review["observations"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First Checkpointed Training Dry Run Review v0 Summary",
        "",
        "Step 10X is a review step, not training.",
        "It reads Step 10W evidence and the local checkpoint artifact metadata.",
        "It does not instantiate a model, run forward, run backward, perform an optimizer step, or save a checkpoint.",
        "",
        "## What Step 10W Proved",
        f"- 12-step checkpointed dry run completed: {manifest['executed_steps'] == 12}",
        f"- exactly one checkpoint was saved at step 12: {manifest['checkpoint_count'] == 1}",
        f"- checkpoint hash verified: {manifest['checkpoint_sha256']}",
        f"- checkpoint size bytes verified: {manifest['checkpoint_size_bytes']}",
        f"- checkpoint payload schema valid: {manifest['checkpoint_payload_schema_valid']}",
        f"- resume smoke passed: {manifest['resume_smoke_passed']}",
        "",
        "## What Step 10W Did Not Prove",
        "- It did not prove generation quality improved.",
        "- It did not prove loss should decrease.",
        "- It did not prove long training is allowed.",
        "- It did not prove the checkpoint should be committed to normal Git history.",
        "",
        "## Checkpoint Policy",
        f"- checkpoint path: {manifest['checkpoint_path']}",
        f"- checkpoint filename: {CHECKPOINT_FILENAME}",
        f"- checkpoint kept as local artifact: {observations['checkpoint_kept_as_local_artifact']}",
        f"- checkpoint committed to Git: {manifest['checkpoint_tracked_by_git']}",
        f"- checkpoint Git commit allowed: {manifest['checkpoint_git_commit_allowed']}",
        "- metadata and evidence are committed separately from the binary checkpoint.",
        "",
        "## Observations",
        f"- git_status_clean_before_run: {observations['git_status_clean_before_run']}",
        f"- git_status_clean_after_run: {observations['git_status_clean_after_run']}",
        f"- observation reason: {observations['git_status_observation_reason']}",
        f"- future_clean_run_recommended: {observations['future_clean_run_recommended']}",
        f"- highest_grad_step: {observations['highest_grad_step']}",
        f"- highest_grad_mask_level: {observations['highest_grad_mask_level']}",
        f"- highest_grad_value: {observations['highest_grad_value']}",
        "",
        "## Boundary",
        f"- review_status: {manifest['review_status']}",
        f"- checkpoint_artifact_status: {manifest['checkpoint_artifact_status']}",
        f"- resume_smoke_status: {manifest['resume_smoke_status']}",
        f"- training_boundary_status: {manifest['training_boundary_status']}",
        f"- loss_decrease_required: {manifest['loss_decrease_required']}",
        f"- quality_claim_allowed: {manifest['quality_claim_allowed']}",
        f"- formal_training_allowed: {manifest['formal_training_allowed']}",
        f"- long_training_allowed: {manifest['long_training_allowed']}",
        "",
        "## Recommendation",
        f"- {manifest['recommended_next_step']}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review first checkpointed training dry-run evidence.")
    parser.add_argument("--require-local-checkpoint", action="store_true", default=True)
    parser.add_argument("--skip-payload-load", action="store_true", default=False)
    return parser.parse_args()


def run(require_local_checkpoint: bool = True, skip_payload_load: bool = False) -> int:
    review = build_first_checkpointed_training_dry_run_review_v0(
        require_local_checkpoint=require_local_checkpoint,
        skip_payload_load=skip_payload_load,
    )
    write_csv(review_rows(review), REVIEW_REPORT_CSV, REPORT_COLUMNS)
    write_json(review_manifest(review), REVIEW_MANIFEST_JSON)
    write_json(review["local_checkpoint_artifact_review"], LOCAL_CHECKPOINT_REVIEW_JSON)
    write_summary(review, REVIEW_SUMMARY_MD)
    return 0 if review["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(require_local_checkpoint=args.require_local_checkpoint, skip_payload_load=args.skip_payload_load)
    print(
        "first_checkpointed_training_dry_run_review_v0_passed"
        if code == 0
        else "first_checkpointed_training_dry_run_review_v0_blocked"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())

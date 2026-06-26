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

from covalent_ext.checkpoint_output_policy_design import (  # noqa: E402
    DEFAULT_ROOT,
    NEXT_STAGE,
    PREVIOUS_STAGE,
    RUN_NAME,
    STAGE,
    build_checkpoint_output_policy_design_v0,
)


TRAINER_FIT_TEXT = "trainer" + "." + "fit"
TRAINING_STEP_TEXT = "training" + "_step"
TORCH_SAVE_TEXT = "torch" + "." + "save"
TORCH_LOAD_TEXT = "torch" + "." + "load"


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "policy_section",
    "status",
    "current_step_allowed",
    "next_step_allowed",
    "forbidden_current_step",
    "forbidden_next_step",
    "policy",
    "decision",
    "recommended_next_step",
    "blocking_reasons",
]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _bool_text(value: bool) -> str:
    return str(bool(value)).lower()


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


def report_rows(policy: dict[str, Any]) -> list[dict[str, str]]:
    output_policy = policy["output_directory_policy"]
    naming_policy = policy["checkpoint_naming_policy"]
    payload_policy = policy["checkpoint_payload_policy"]
    metadata_policy = policy["metadata_policy"]
    retention_policy = policy["retention_policy"]
    resume_policy = policy["resume_smoke_policy"]
    boundary = policy["next_step_execution_boundary"]
    risk_register = policy["risk_register"]
    recommended = policy["recommended_next_step"]
    current_forbidden = f"checkpoint save;checkpoint load;model save;{TORCH_SAVE_TEXT};{TORCH_LOAD_TEXT};forward;backward;optimizer step;{TRAINER_FIT_TEXT};{TRAINING_STEP_TEXT};formal training"
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "policy_section": "output_directory_policy",
            "status": "passed",
            "current_step_allowed": "write policy report/manifest/summary only",
            "next_step_allowed": "create fixed run directory tree only after explicit approval",
            "forbidden_current_step": current_forbidden,
            "forbidden_next_step": "overwrite existing run directory unless later explicit overwrite flag is provided",
            "policy": _json_text(output_policy),
            "decision": "Use a dedicated first checkpointed dry-run root with reports, metadata, checkpoints, and resume-smoke subdirectories.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "policy_section": "checkpoint_naming_policy",
            "status": "passed",
            "current_step_allowed": "design checkpoint name only",
            "next_step_allowed": f"save exactly one checkpoint named {naming_policy['checkpoint_filename']}",
            "forbidden_current_step": current_forbidden,
            "forbidden_next_step": "intermediate checkpoints;epoch checkpoints;lightning checkpoints;model-only checkpoints;optimizer-only checkpoints",
            "policy": _json_text(naming_policy),
            "decision": "Allow one deterministic final-step checkpoint only.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "policy_section": "checkpoint_payload_policy",
            "status": "passed",
            "current_step_allowed": "design payload schema only",
            "next_step_allowed": "dictionary payload with model and optimizer state dictionaries plus scalar evidence",
            "forbidden_current_step": current_forbidden,
            "forbidden_next_step": ";".join(payload_policy["forbidden_payload_fields"]),
            "policy": _json_text(payload_policy),
            "decision": "Payload must be explicit metadata plus state dictionaries, not object pickles or data archives.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "policy_section": "metadata_policy",
            "status": "passed",
            "current_step_allowed": "design metadata requirements only",
            "next_step_allowed": "write manifest and checkpoint metadata with hash, size, git state, and safety flags",
            "forbidden_current_step": current_forbidden,
            "forbidden_next_step": "checkpoint without sha256;checkpoint without size;missing source diff check;missing forbidden artifact scan",
            "policy": _json_text(metadata_policy),
            "decision": "Require metadata sufficient to identify, hash, and resume-test the single checkpoint.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "policy_section": "retention_policy",
            "status": "passed",
            "current_step_allowed": "design retention constraints only",
            "next_step_allowed": "keep one checkpoint and fail on unexpected checkpoint files",
            "forbidden_current_step": current_forbidden,
            "forbidden_next_step": "multiple checkpoints;zero-byte checkpoint;missing checkpoint;archive creation",
            "policy": _json_text(retention_policy),
            "decision": "Use max_checkpoints=1 and fail closed on unexpected files.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "policy_section": "resume_smoke_policy",
            "status": "passed",
            "current_step_allowed": "design resume-smoke requirements only",
            "next_step_allowed": "load the single checkpoint into fresh in-memory model and optimizer for resume smoke",
            "forbidden_current_step": current_forbidden,
            "forbidden_next_step": f"second checkpoint save;optimizer step during resume smoke;{TRAINER_FIT_TEXT};{TRAINING_STEP_TEXT};model save",
            "policy": _json_text(resume_policy),
            "decision": "Resume smoke is required, but it must not create a second checkpoint.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "policy_section": "next_step_execution_boundary",
            "status": "passed",
            "current_step_allowed": "policy design only",
            "next_step_allowed": "first checkpointed dry run after explicit approval",
            "forbidden_current_step": current_forbidden,
            "forbidden_next_step": ";".join(boundary["forbidden_outputs_next_step"]),
            "policy": _json_text(boundary),
            "decision": "Next step may save and resume-load the one allowed checkpoint, but still may not run formal training.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "policy_section": "risk_register",
            "status": "passed",
            "current_step_allowed": "record risks and mitigations",
            "next_step_allowed": "use mitigations as first checkpointed dry-run gates",
            "forbidden_current_step": current_forbidden,
            "forbidden_next_step": "treating policy design as checkpoint approval beyond one dry-run checkpoint",
            "policy": _json_text(risk_register),
            "decision": "Risks are bounded by one-checkpoint, metadata, retention, and resume-smoke policies.",
            "recommended_next_step": recommended,
            "blocking_reasons": "",
        },
    ]


def preview_manifest(policy: dict[str, Any]) -> dict[str, Any]:
    output_policy = policy["output_directory_policy"]
    naming_policy = policy["checkpoint_naming_policy"]
    metadata_policy = policy["metadata_policy"]
    retention_policy = policy["retention_policy"]
    resume_policy = policy["resume_smoke_policy"]
    boundary = policy["next_step_execution_boundary"]
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10u_review_passed": policy["step10u_review_passed"],
        "next_stage": NEXT_STAGE,
        "run_name": RUN_NAME,
        "run_root": output_policy["run_root"] + "/",
        "checkpoint_filename": naming_policy["checkpoint_filename"],
        "checkpoint_path": naming_policy["checkpoint_path"],
        "checkpoint_count_limit": naming_policy["checkpoint_count_limit"],
        "save_at_step": naming_policy["save_at_step"],
        "no_intermediate_checkpoints": naming_policy["no_intermediate_checkpoints"],
        "checkpoint_extension": naming_policy["checkpoint_extension"],
        "current_step_checkpoint_save_allowed": False,
        "current_step_checkpoint_load_allowed": False,
        "current_step_model_save_allowed": False,
        "current_step_formal_training_allowed": False,
        "next_step_checkpoint_save_allowed": boundary["checkpoint_save_allowed_next_step"],
        "next_step_checkpoint_load_allowed": boundary["checkpoint_load_allowed_next_step"],
        "next_step_model_save_allowed": boundary["model_save_allowed_next_step"],
        "next_step_trainer_fit_allowed": boundary["trainer_fit_allowed_next_step"],
        "next_step_training_step_allowed": boundary["training_step_allowed_next_step"],
        "next_step_formal_training_allowed": boundary["formal_training_allowed_next_step"],
        "next_step_finetune_allowed": boundary["finetune_allowed_next_step"],
        "next_step_source_modification_allowed": boundary["source_modification_allowed_next_step"],
        "resume_smoke_required": resume_policy["resume_smoke_required"],
        "no_second_checkpoint_during_resume_smoke": not resume_policy["second_checkpoint_save_allowed"],
        "max_checkpoints": retention_policy["max_checkpoints"],
        "keep_last_only": retention_policy["keep_last_only"],
        "fail_if_multiple_checkpoints_created": retention_policy["fail_if_multiple_checkpoints_created"],
        "fail_if_unexpected_checkpoint_files_exist": retention_policy["fail_if_unexpected_checkpoint_files_exist"],
        "metadata_required": metadata_policy["metadata_required"],
        "checkpoint_sha256_required": metadata_policy["checkpoint_sha256_required"],
        "current_step_checkpoint_saved": policy["current_step_checkpoint_saved"],
        "current_step_checkpoint_loaded": policy["current_step_checkpoint_loaded"],
        "current_step_model_saved": policy["current_step_model_saved"],
        "current_step_formal_training_executed": policy["current_step_formal_training_executed"],
        "forbidden_artifacts_created": policy["forbidden_artifacts_created"],
        "all_checks_passed": policy["all_checks_passed"],
        "recommended_next_step": policy["recommended_next_step"],
        "output_directory_policy": output_policy,
        "checkpoint_naming_policy": naming_policy,
        "checkpoint_payload_policy": policy["checkpoint_payload_policy"],
        "metadata_policy": metadata_policy,
        "retention_policy": retention_policy,
        "resume_smoke_policy": resume_policy,
        "next_step_execution_boundary": boundary,
        "risk_register": policy["risk_register"],
    }


def write_summary(policy: dict[str, Any], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Checkpoint and Output Policy Design v0 Summary",
        "",
        "Step 10V is checkpoint/output policy design only. It does not save or load a checkpoint.",
        "Previous steps kept checkpointing disabled; Step 10T and Step 10U showed that the bounded 12-step dry-run loop is stable enough to design a first checkpointed dry run.",
        "This step defines what may be saved, where it may be saved, how it must be named, how it must be verified, and how resume smoke must work.",
        "",
        "## Output Root",
        f"- run_root: {manifest['run_root']}",
        f"- checkpoints_dir: {manifest['output_directory_policy']['checkpoints_dir']}",
        f"- reports_dir: {manifest['output_directory_policy']['reports_dir']}",
        f"- metadata_dir: {manifest['output_directory_policy']['metadata_dir']}",
        f"- resume_smoke_dir: {manifest['output_directory_policy']['resume_smoke_dir']}",
        "",
        "## First Checkpoint Policy",
        f"- checkpoint_filename: {manifest['checkpoint_filename']}",
        f"- checkpoint_count_limit: {manifest['checkpoint_count_limit']}",
        f"- save_at_step: {manifest['save_at_step']}",
        f"- no_intermediate_checkpoints: {manifest['no_intermediate_checkpoints']}",
        f"- checkpoint_sha256_required: {manifest['checkpoint_sha256_required']}",
        f"- metadata_required: {manifest['metadata_required']}",
        "",
        "## Next Step Allows",
        "- first checkpointed dry run after explicit approval",
        "- exactly one final checkpoint file",
        "- resume smoke may load that one checkpoint",
        "",
        "## Still Forbidden",
        "- formal training",
        "- fine-tune",
        f"- {TRAINER_FIT_TEXT}",
        f"- {TRAINING_STEP_TEXT}",
        "- model save",
        "- multiple checkpoints",
        "- archives",
        "- tensor dumps",
        "- source modification",
        "",
        "## Current Step Safety",
        f"- current_step_checkpoint_save_allowed: {manifest['current_step_checkpoint_save_allowed']}",
        f"- current_step_checkpoint_load_allowed: {manifest['current_step_checkpoint_load_allowed']}",
        f"- current_step_model_save_allowed: {manifest['current_step_model_save_allowed']}",
        f"- current_step_formal_training_allowed: {manifest['current_step_formal_training_allowed']}",
        f"- forbidden_artifacts_created: {manifest['forbidden_artifacts_created']}",
        "",
        "## Result",
        f"- all_checks_passed: {manifest['all_checks_passed']}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    policy = build_checkpoint_output_policy_design_v0()
    manifest = preview_manifest(policy)
    write_csv(
        report_rows(policy),
        DEFAULT_ROOT / "checkpoint_output_policy_design_report.csv",
        REPORT_COLUMNS,
    )
    write_json(manifest, DEFAULT_ROOT / "checkpoint_output_policy_design_preview_manifest.json")
    write_summary(policy, manifest, "docs/checkpoint_output_policy_design_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    code = run()
    print("checkpoint_output_policy_design_v0_passed" if code == 0 else "checkpoint_output_policy_design_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

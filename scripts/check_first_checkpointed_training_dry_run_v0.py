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

from covalent_ext.first_checkpointed_training_dry_run import (  # noqa: E402
    CHECKPOINT_FILENAME,
    CHECKPOINT_PATH,
    DEFAULT_LR,
    DEFAULT_WEIGHT_DECAY,
    LOSS_WEIGHTS,
    LOOP_NAME,
    MASK_SCHEDULE,
    MAX_STEPS,
    OPTIMIZER_CLASS,
    PREVIOUS_STAGE,
    RUN_NAME,
    RUN_ROOT,
    SEED,
    SHUFFLE,
    STAGE,
    run_first_checkpointed_training_dry_run_v0,
)


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "step10v_policy_passed",
    "run_name",
    "loop_name",
    "step",
    "cycle_index",
    "mask_level",
    "expected_mask_level",
    "expected_target_atom_count",
    "expected_context_atom_count",
    "target_atom_count",
    "context_atom_count",
    "ligand_atom_count",
    "sample_ids",
    "loss_original",
    "loss_masked_x",
    "loss_masked_h",
    "loss_total",
    "loss_finite",
    "loss_total_requires_grad",
    "loss_decrease_required",
    "quality_claim_allowed",
    "backward_called",
    "backward_success",
    "optimizer_class",
    "learning_rate",
    "optimizer_step_executed",
    "optimizer_step_success",
    "grad_norm",
    "max_grad_abs",
    "finite_gradients",
    "nonzero_gradients",
    "grad_nan_count",
    "grad_inf_count",
    "param_delta_norm",
    "max_param_delta_abs",
    "finite_parameter_delta",
    "nonzero_parameter_delta",
    "post_step_param_nan_count",
    "post_step_param_inf_count",
    "cuda_device",
    "elapsed_seconds",
    "warning_triggered",
    "warning_reasons",
    "stop_triggered",
    "stop_reason",
    "checkpoint_loaded",
    "checkpoint_saved",
    "checkpoint_written",
    "checkpoint_path",
    "checkpoint_sha256",
    "checkpoint_size_bytes",
    "resume_smoke_passed",
    "checkpoint_loaded_for_resume_smoke",
    "model_state_loaded",
    "optimizer_state_loaded",
    "second_checkpoint_saved",
    "training_step_called",
    "trainer_fit_called",
    "archive_created",
    "model_saved",
    "formal_training_executed",
    "real_finetune_executed",
    "original_source_files_modified",
    "forbidden_artifacts_created",
    "step_status",
    "blocking_reasons",
]
RESUME_COLUMNS = [
    "stage",
    "checkpoint_path",
    "checkpoint_loaded",
    "model_state_loaded",
    "optimizer_state_loaded",
    "completed_steps_verified",
    "mask_schedule_verified",
    "parameter_shapes_verified",
    "optimizer_step_during_resume_smoke",
    "second_checkpoint_saved",
    "trainer_fit_called",
    "training_step_called",
    "model_saved",
    "resume_smoke_passed",
    "blocking_reasons",
]


def _bool(value: Any) -> str:
    return str(bool(value)).lower()


def _list_text(values: Any) -> str:
    if values is None:
        return ""
    if isinstance(values, list):
        return ";".join(str(value) for value in values)
    return str(values)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_jsonable(child) for child in value]
    return value


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
    output.write_text(json.dumps(_jsonable(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def report_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10v_policy_passed": _bool(True),
        "run_name": RUN_NAME,
        "loop_name": LOOP_NAME,
        "step": str(row.get("step", "")),
        "cycle_index": str(row.get("cycle_index", "")),
        "mask_level": str(row.get("mask_level", "")),
        "expected_mask_level": str(row.get("expected_mask_level", "")),
        "expected_target_atom_count": str(row.get("expected_target_atom_count", "")),
        "expected_context_atom_count": str(row.get("expected_context_atom_count", "")),
        "target_atom_count": str(row.get("target_atom_count", "")),
        "context_atom_count": str(row.get("context_atom_count", "")),
        "ligand_atom_count": str(row.get("ligand_atom_count", "")),
        "sample_ids": _list_text(row.get("sample_ids", [])),
        "loss_original": str(row.get("loss_original", "")),
        "loss_masked_x": str(row.get("loss_masked_x", "")),
        "loss_masked_h": str(row.get("loss_masked_h", "")),
        "loss_total": str(row.get("loss_total", "")),
        "loss_finite": _bool(row.get("loss_finite", False)),
        "loss_total_requires_grad": _bool(row.get("loss_total_requires_grad", False)),
        "loss_decrease_required": _bool(row.get("loss_decrease_required", False)),
        "quality_claim_allowed": _bool(row.get("quality_claim_allowed", False)),
        "backward_called": _bool(row.get("backward_called", False)),
        "backward_success": _bool(row.get("backward_success", False)),
        "optimizer_class": str(row.get("optimizer_class", OPTIMIZER_CLASS)),
        "learning_rate": str(row.get("learning_rate", "")),
        "optimizer_step_executed": _bool(row.get("optimizer_step_executed", False)),
        "optimizer_step_success": _bool(row.get("optimizer_step_success", False)),
        "grad_norm": str(row.get("grad_norm", "")),
        "max_grad_abs": str(row.get("max_grad_abs", "")),
        "finite_gradients": _bool(row.get("finite_gradients", False)),
        "nonzero_gradients": _bool(row.get("nonzero_gradients", False)),
        "grad_nan_count": str(row.get("grad_nan_count", "")),
        "grad_inf_count": str(row.get("grad_inf_count", "")),
        "param_delta_norm": str(row.get("param_delta_norm", "")),
        "max_param_delta_abs": str(row.get("max_param_delta_abs", "")),
        "finite_parameter_delta": _bool(row.get("finite_parameter_delta", False)),
        "nonzero_parameter_delta": _bool(row.get("nonzero_parameter_delta", False)),
        "post_step_param_nan_count": str(row.get("post_step_param_nan_count", "")),
        "post_step_param_inf_count": str(row.get("post_step_param_inf_count", "")),
        "cuda_device": str(row.get("cuda_device", "")),
        "elapsed_seconds": str(row.get("elapsed_seconds", "")),
        "warning_triggered": _bool(row.get("warning_triggered", False)),
        "warning_reasons": _list_text(row.get("warning_reasons", [])),
        "stop_triggered": _bool(row.get("stop_triggered", False)),
        "stop_reason": str(row.get("stop_reason", "")),
        "checkpoint_loaded": _bool(row.get("checkpoint_loaded", False)),
        "checkpoint_saved": _bool(row.get("checkpoint_saved", False)),
        "checkpoint_written": _bool(row.get("checkpoint_written", False)),
        "checkpoint_path": str(row.get("checkpoint_path", "")),
        "checkpoint_sha256": str(row.get("checkpoint_sha256", "")),
        "checkpoint_size_bytes": str(row.get("checkpoint_size_bytes", "")),
        "resume_smoke_passed": _bool(row.get("resume_smoke_passed", False)),
        "checkpoint_loaded_for_resume_smoke": _bool(row.get("checkpoint_loaded_for_resume_smoke", False)),
        "model_state_loaded": _bool(row.get("model_state_loaded", False)),
        "optimizer_state_loaded": _bool(row.get("optimizer_state_loaded", False)),
        "second_checkpoint_saved": _bool(row.get("second_checkpoint_saved", False)),
        "training_step_called": _bool(row.get("training_step_called", False)),
        "trainer_fit_called": _bool(row.get("trainer_fit_called", False)),
        "archive_created": _bool(row.get("archive_created", False)),
        "model_saved": _bool(row.get("model_saved", False)),
        "formal_training_executed": _bool(row.get("formal_training_executed", False)),
        "real_finetune_executed": _bool(row.get("real_finetune_executed", False)),
        "original_source_files_modified": _bool(row.get("original_source_files_modified", False)),
        "forbidden_artifacts_created": _bool(row.get("forbidden_artifacts_created", False)),
        "step_status": str(row.get("step_status", "")),
        "blocking_reasons": _list_text(row.get("blocking_reasons", [])),
    }


def resume_row(resume: dict[str, Any]) -> dict[str, str]:
    return {
        "stage": STAGE,
        "checkpoint_path": str(resume.get("checkpoint_path", CHECKPOINT_PATH)),
        "checkpoint_loaded": _bool(resume.get("checkpoint_loaded", False)),
        "model_state_loaded": _bool(resume.get("model_state_loaded", False)),
        "optimizer_state_loaded": _bool(resume.get("optimizer_state_loaded", False)),
        "completed_steps_verified": _bool(resume.get("completed_steps_verified", False)),
        "mask_schedule_verified": _bool(resume.get("mask_schedule_verified", False)),
        "parameter_shapes_verified": _bool(resume.get("parameter_shapes_verified", False)),
        "optimizer_step_during_resume_smoke": _bool(resume.get("optimizer_step_during_resume_smoke", False)),
        "second_checkpoint_saved": _bool(resume.get("second_checkpoint_saved", False)),
        "trainer_fit_called": _bool(resume.get("trainer_fit_called", False)),
        "training_step_called": _bool(resume.get("training_step_called", False)),
        "model_saved": _bool(resume.get("model_saved", False)),
        "resume_smoke_passed": _bool(resume.get("resume_smoke_passed", False)),
        "blocking_reasons": _list_text(resume.get("blocking_reasons", [])),
    }


def checkpoint_metadata_json(summary: dict[str, Any], checkpoint_metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "run_name": RUN_NAME,
        "checkpoint_path": checkpoint_metadata.get("checkpoint_path", str(CHECKPOINT_PATH)),
        "checkpoint_filename": checkpoint_metadata.get("checkpoint_filename", CHECKPOINT_FILENAME),
        "checkpoint_sha256": checkpoint_metadata.get("checkpoint_sha256", ""),
        "checkpoint_size_bytes": checkpoint_metadata.get("checkpoint_size_bytes", 0),
        "checkpoint_count": checkpoint_metadata.get("checkpoint_count", 0),
        "checkpoint_saved": checkpoint_metadata.get("checkpoint_saved", False),
        "checkpoint_payload_schema_valid": checkpoint_metadata.get("checkpoint_payload_schema_valid", False),
        "repo_commit": checkpoint_metadata.get("repo_commit", summary.get("repo_commit", "")),
        "created_at_utc": checkpoint_metadata.get("created_at_utc", ""),
        "completed_steps": checkpoint_metadata.get("completed_steps", summary.get("executed_steps", 0)),
        "max_steps": checkpoint_metadata.get("max_steps", MAX_STEPS),
        "mask_schedule": list(MASK_SCHEDULE),
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": summary.get("optimizer_lr", DEFAULT_LR),
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "batch_size": summary.get("batch_size", 0),
        "shuffle": SHUFFLE,
        "seed": SEED,
        "source_modification_allowed": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
        "blocking_reasons": checkpoint_metadata.get("blocking_reasons", []),
    }


def write_summary(rows: list[dict[str, Any]], manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# First Checkpointed Training Dry Run v0 Summary",
        "",
        "This step runs a tightly bounded first checkpointed dry run, not formal training.",
        "It executes the approved 12-step masked covalent loop and saves exactly one final dictionary checkpoint.",
        "The checkpoint contains model_state_dict, optimizer_state_dict, scalar evidence, and run metadata.",
        "It does not call training_step, trainer fit, or save a model object.",
        "It does not fine-tune or claim model quality.",
        "It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.",
        "",
        "## Run",
        f"- stage: {manifest['stage']}",
        f"- previous_stage: {manifest['previous_stage']}",
        f"- run_name: {manifest['run_name']}",
        f"- run_root: {manifest['run_root']}",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- cuda_available: {manifest['cuda_available']}",
        f"- cuda_device_name: {manifest['cuda_device_name']}",
        f"- optimizer_class: {manifest['optimizer_class']}",
        f"- optimizer_lr: {manifest['optimizer_lr']}",
        f"- optimizer_weight_decay: {manifest['optimizer_weight_decay']}",
        f"- max_steps: {manifest['max_steps']}",
        f"- executed_steps: {manifest['executed_steps']}",
        f"- mask_schedule: {', '.join(manifest['mask_schedule'])}",
        f"- loss_weights: {json.dumps(manifest['loss_weights'], sort_keys=True)}",
        "",
        "## Step Evidence",
        "| step | mask_level | target | context | loss_total | grad_norm | param_delta_norm | checkpoint_saved | status |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {step} | {mask} | {target} | {context} | {loss:.6f} | {grad:.6f} | {delta:.8f} | {ckpt} | {status} |".format(
                step=row["step"],
                mask=row["mask_level"],
                target=row["target_atom_count"],
                context=row["context_atom_count"],
                loss=float(row["loss_total"]),
                grad=float(row["grad_norm"]),
                delta=float(row["param_delta_norm"]),
                ckpt=row.get("checkpoint_saved", False),
                status=row["step_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Checkpoint",
            f"- checkpoint_saved: {manifest['checkpoint_saved']}",
            f"- checkpoint_path: {manifest['checkpoint_path']}",
            f"- checkpoint_filename: {manifest['checkpoint_filename']}",
            f"- checkpoint_count: {manifest['checkpoint_count']}",
            f"- checkpoint_sha256: {manifest['checkpoint_sha256']}",
            f"- checkpoint_size_bytes: {manifest['checkpoint_size_bytes']}",
            f"- checkpoint_payload_schema_valid: {manifest['checkpoint_payload_schema_valid']}",
            f"- checkpoint_metadata_written: {manifest['checkpoint_metadata_written']}",
            "",
            "## Resume Smoke",
            f"- checkpoint_loaded_for_resume_smoke: {manifest['checkpoint_loaded_for_resume_smoke']}",
            f"- resume_smoke_passed: {manifest['resume_smoke_passed']}",
            f"- model_state_loaded: {manifest['model_state_loaded']}",
            f"- optimizer_state_loaded: {manifest['optimizer_state_loaded']}",
            f"- completed_steps_verified: {manifest['completed_steps_verified']}",
            f"- mask_schedule_verified: {manifest['mask_schedule_verified']}",
            f"- parameter_shapes_verified: {manifest['parameter_shapes_verified']}",
            f"- optimizer_step_during_resume_smoke: {manifest['optimizer_step_during_resume_smoke']}",
            f"- second_checkpoint_saved: {manifest['second_checkpoint_saved']}",
            "",
            "## Safety",
            f"- training_step_called: {manifest['training_step_called']}",
            f"- trainer_fit_called: {manifest['trainer_fit_called']}",
            f"- model_saved: {manifest['model_saved']}",
            f"- formal_training_executed: {manifest['formal_training_executed']}",
            f"- real_finetune_executed: {manifest['real_finetune_executed']}",
            f"- source_modification_allowed: {manifest['source_modification_allowed']}",
            f"- original_source_files_modified: {manifest['original_source_files_modified']}",
            f"- forbidden_artifacts_created: {manifest['forbidden_artifacts_created']}",
            f"- unexpected_checkpoint_files_created: {manifest['unexpected_checkpoint_files_created']}",
            f"- all_checks_passed: {manifest['all_checks_passed']}",
            "",
            "## Recommendation",
            f"- {manifest['recommended_next_step']}",
            "",
            "The next step is review of this first checkpointed dry-run evidence, not formal training.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run first checkpointed masked covalent training dry run.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR)
    parser.add_argument("--max_steps", type=int, default=MAX_STEPS)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def run(device: str = "auto", lr: float = DEFAULT_LR, max_steps: int = MAX_STEPS, overwrite: bool = False) -> int:
    result = run_first_checkpointed_training_dry_run_v0(
        device=device,
        lr=lr,
        max_steps=max_steps,
        overwrite=overwrite,
    )
    rows = result["rows"]
    manifest = result["summary"]
    checkpoint_metadata = checkpoint_metadata_json(manifest, result.get("checkpoint_metadata", {}))
    resume = result.get("resume_smoke", {})

    if RUN_ROOT.exists():
        write_csv(
            [report_row(row) for row in rows],
            RUN_ROOT / "reports" / "first_checkpointed_training_dry_run_report.csv",
            REPORT_COLUMNS,
        )
        write_json(manifest, RUN_ROOT / "metadata" / "first_checkpointed_training_dry_run_manifest.json")
        if checkpoint_metadata.get("checkpoint_saved"):
            write_json(checkpoint_metadata, RUN_ROOT / "metadata" / "checkpoint_metadata.json")
        if resume:
            write_csv([resume_row(resume)], RUN_ROOT / "resume_smoke" / "resume_smoke_report.csv", RESUME_COLUMNS)
            write_json(resume, RUN_ROOT / "resume_smoke" / "resume_smoke_manifest.json")
        if rows:
            write_summary(rows, manifest, "docs/first_checkpointed_training_dry_run_v0_summary.md")
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device, lr=args.lr, max_steps=args.max_steps, overwrite=args.overwrite)
    print(
        "first_checkpointed_training_dry_run_v0_passed"
        if code == 0
        else "first_checkpointed_training_dry_run_v0_blocked"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())

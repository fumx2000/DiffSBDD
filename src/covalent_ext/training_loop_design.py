from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
STAGE = "training_loop_design_without_checkpoint_v0"
PREVIOUS_STAGE = "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0"
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
EXPECTED_TARGET_COUNTS = {
    "A_warhead_only": 12,
    "B_linker_warhead": 30,
    "B2_scaffold_warhead": 86,
    "C_scaffold_linker_warhead": 104,
}
EXPECTED_CONTEXT_COUNTS = {
    "A_warhead_only": 92,
    "B_linker_warhead": 74,
    "B2_scaffold_warhead": 18,
    "C_scaffold_linker_warhead": 0,
}
LOSS_WEIGHTS = {
    "w_original": 1.0,
    "w_x": 1.0,
    "w_h": 0.2,
}
SAFETY_FALSE_FIELDS = [
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "checkpoint_written",
    "archive_created",
    "model_saved",
    "original_source_files_modified",
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_step10o_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "masked_loss_optimizer_smoke_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "masked_loss_optimizer_smoke_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10O masked loss optimizer smoke outputs are missing")

    rows = _rows_from_csv(report_path)
    if len(rows) != 4:
        raise ValueError(f"Step 10O report must contain exactly four rows, found {len(rows)}")
    if [row.get("mask_level") for row in rows] != MASK_LEVELS:
        raise ValueError("Step 10O report mask levels do not match expected order")
    for row in rows:
        mask_level = row["mask_level"]
        expected = {
            "stage": PREVIOUS_STAGE,
            "previous_stage": "masked_loss_backward_smoke_without_optimizer_v0",
            "step10n_backward_smoke_passed": "true",
            "target_atom_count": str(EXPECTED_TARGET_COUNTS[mask_level]),
            "context_atom_count": str(EXPECTED_CONTEXT_COUNTS[mask_level]),
            "ligand_atom_count": "104",
            "loss_total_dry_finite": "true",
            "loss_total_dry_requires_grad": "true",
            "backward_called": "true",
            "backward_success": "true",
            "optimizer_class": "AdamW",
            "optimizer_lr": "1e-06",
            "optimizer_weight_decay": "0.0",
            "optimizer_step_executed": "true",
            "optimizer_step_success": "true",
            "finite_gradients": "true",
            "nonzero_gradients": "true",
            "grad_nan_count": "0",
            "grad_inf_count": "0",
            "finite_parameter_delta": "true",
            "nonzero_parameter_delta": "true",
            "post_step_param_nan_count": "0",
            "post_step_param_inf_count": "0",
            "checkpoint_loaded": "false",
            "checkpoint_saved": "false",
            "training_step_called": "false",
            "trainer_fit_called": "false",
            "training_executed": "false",
            "real_finetune_executed": "false",
            "checkpoint_written": "false",
            "archive_created": "false",
            "model_saved": "false",
            "original_source_files_modified": "false",
            "smoke_status": "passed",
            "blocking_reasons": "",
        }
        for key, expected_value in expected.items():
            if row.get(key) != expected_value:
                raise ValueError(f"Step 10O report invalid for {mask_level} {key}: {row.get(key)!r}")
        for key in [
            "parameters_with_grad",
            "trainable_parameters_with_grad",
            "parameters_changed",
            "trainable_parameters_changed",
        ]:
            if int(row.get(key, "0")) <= 0:
                raise ValueError(f"Step 10O report invalid for {mask_level} {key}: {row.get(key)!r}")
        for key in ["total_grad_norm", "max_grad_abs", "total_param_delta_norm", "max_param_delta_abs"]:
            if float(row.get(key, "0")) <= 0:
                raise ValueError(f"Step 10O report invalid for {mask_level} {key}: {row.get(key)!r}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "masked_loss_backward_smoke_without_optimizer_v0",
        "step10n_backward_smoke_passed": True,
        "optimizer_class": "AdamW",
        "optimizer_lr": 1e-06,
        "optimizer_weight_decay": 0.0,
        "mask_levels_checked": 4,
        "mask_levels": MASK_LEVELS,
        "all_mask_levels_passed": True,
        "all_backward_success": True,
        "all_optimizer_steps_success": True,
        "all_gradients_finite": True,
        "all_gradients_nonzero": True,
        "all_parameter_updates_finite": True,
        "all_parameter_updates_nonzero": True,
        "all_post_step_params_finite": True,
        "all_expected_target_counts": True,
        "all_expected_context_counts": True,
        "all_sources_unmodified": True,
        "target_atom_count_by_mask_level": EXPECTED_TARGET_COUNTS,
        "context_atom_count_by_mask_level": EXPECTED_CONTEXT_COUNTS,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": True,
        "optimizer_step_executed": True,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "checkpoint_written": False,
        "archive_created": False,
        "model_saved": False,
        "original_source_files_modified": False,
        "all_checks_passed": True,
        "recommended_next_step": "training_loop_design_without_checkpoint",
    }
    for key, expected in expected_manifest_values.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Step 10O manifest invalid for {key}: {manifest.get(key)!r}")
    return True


def build_training_loop_contract_v0() -> dict[str, Any]:
    return {
        "loop_name": "masked_covalent_training_loop_v0",
        "intended_next_stage": "few_step_training_dry_run_no_checkpoint",
        "allowed_actions_next_stage": [
            "instantiate model",
            "build optimizer",
            "iterate over dataloader",
            "compute masked loss",
            "backward",
            "optimizer.step",
            "log scalar metrics",
        ],
        "forbidden_actions_next_stage": [
            "trainer.fit",
            "training_step",
            "checkpoint loading",
            "checkpoint saving",
            "torch.save",
            "model saving",
            "archive writing",
            "modifying DiffSBDD source files",
            "source modification",
        ],
        "required_stop_conditions": [
            "max_steps hard cap",
            "finite loss required",
            "finite gradients required",
            "finite parameters after step required",
            "no NaN/Inf in loss/grad/params",
            "abort on unexpected mask level",
            "abort on missing target mask",
        ],
        "required_logging_fields": [
            "step",
            "mask_level",
            "sample_ids",
            "loss_original",
            "loss_masked_x",
            "loss_masked_h",
            "loss_total",
            "target_atom_count",
            "context_atom_count",
            "grad_norm",
            "max_grad_abs",
            "param_delta_norm",
            "max_param_delta_abs",
            "learning_rate",
            "optimizer_class",
            "cuda_device",
            "elapsed_seconds",
        ],
        "allowed_outputs_next_stage": [
            "csv report",
            "json preview manifest",
            "markdown summary",
        ],
        "forbidden_outputs_next_stage": [
            ".pt",
            ".pkl",
            ".lmdb",
            ".tar",
            ".zip",
            ".tgz",
            "checkpoint files",
            "saved model files",
        ],
    }


def build_minimal_training_loop_plan_v0() -> list[dict[str, Any]]:
    stages = [
        (
            "preflight_validate_inputs",
            "Validate Step 10O reports, materialized inputs, mask levels, and source immutability.",
            "Read reports and manifests only.",
            "Proceeding with missing, stale, or blocked upstream evidence.",
            "Validated upstream manifest and source diff check.",
            "Abort before model construction.",
        ),
        (
            "instantiate_model_no_checkpoint",
            "Create a fresh in-memory DiffSBDD model instance for the dry run.",
            "Constructor-only initialization from reviewed config.",
            "Checkpoint loading or source edits.",
            "Model class, parameter count, and no-checkpoint flags.",
            "Abort and write blocked report.",
        ),
        (
            "build_optimizer",
            "Create a conservative optimizer for the in-memory model.",
            "AdamW with reviewed learning rate and no weight decay.",
            "Trainer, Lightning loop, saved optimizer state.",
            "Optimizer class, learning rate, and weight decay logged.",
            "Abort if optimizer configuration differs from policy.",
        ),
        (
            "prepare_mask_schedule",
            "Use a deterministic A/B/B2/C cycle so every mask level is covered.",
            "Fixed seed, no shuffle, tiny max step count.",
            "Random uncontrolled sampling for first dry run.",
            "Mask level per step and target/context counts.",
            "Abort on unexpected mask level or empty target mask.",
        ),
        (
            "run_few_step_dry_loop",
            "Run only the explicitly capped number of dry-run steps.",
            "Forward, masked loss, backward, optimizer step, metrics logging.",
            "Formal training, checkpoint writing, trainer.fit, training_step.",
            "One row per step with loss, gradient, and parameter delta metrics.",
            "Stop immediately on any failed invariant.",
        ),
        (
            "collect_loss_metrics",
            "Record original and masked loss components for audit.",
            "Scalar logging only.",
            "Tensor artifact persistence.",
            "Finite loss fields for every step.",
            "Abort on NaN or Inf.",
        ),
        (
            "collect_gradient_metrics",
            "Record gradient norm, max abs, finite checks, and NaN/Inf counts.",
            "Gradient inspection after backward.",
            "Optimizer step before gradient checks.",
            "Finite nonzero gradient metrics.",
            "Abort before optimizer step if gradients fail.",
        ),
        (
            "collect_parameter_update_metrics",
            "Record in-memory parameter delta after optimizer step.",
            "Lightweight before/after in-memory comparison.",
            "Saving model weights or optimizer state.",
            "Finite nonzero parameter delta and post-step finite parameters.",
            "Abort if update is zero or non-finite.",
        ),
        (
            "enforce_stop_conditions",
            "Apply hard stop conditions after every step.",
            "Abort-on-first-failure policy.",
            "Continuing after a failed invariant.",
            "Stop reason and last safe step.",
            "Stop loop and write blocked report.",
        ),
        (
            "write_report_only",
            "Write auditable review-only dry-run outputs.",
            "CSV report, JSON preview manifest, Markdown summary.",
            "Model files, checkpoint files, archives, tensor dumps.",
            "Only allowed files are present.",
            "Delete disallowed outputs and mark blocked.",
        ),
        (
            "verify_no_checkpoint_or_model_saved",
            "Confirm no checkpoint, model, tensor, or archive file was created.",
            "Filesystem scan of dry-run output root.",
            "Any .pt/.pkl/.lmdb/.tar/.zip/.tgz output.",
            "Empty forbidden artifact scan.",
            "Mark blocked and remove forbidden outputs if any were created.",
        ),
        (
            "verify_sources_unmodified",
            "Confirm DiffSBDD, equivariant_diffusion, and lightning_modules are unchanged.",
            "Source diff inspection.",
            "Source modification.",
            "No diff in protected source paths.",
            "Abort and require manual review.",
        ),
    ]
    return [
        {
            "order": index + 1,
            "stage_name": stage_name,
            "purpose": purpose,
            "allowed": allowed,
            "forbidden": forbidden,
            "expected_evidence": expected_evidence,
            "failure_action": failure_action,
        }
        for index, (stage_name, purpose, allowed, forbidden, expected_evidence, failure_action) in enumerate(stages)
    ]


def build_mask_schedule_policy_v0() -> dict[str, Any]:
    return {
        "schedule_name": "balanced_A_B_B2_C_cycle",
        "mask_order": list(MASK_LEVELS),
        "max_steps_initial_dry_run": 4,
        "batch_size": 3,
        "shuffle": False,
        "seed": 4401,
        "rationale": "Each mask level runs once first; this validates loop behavior and safety, not loss decrease.",
        "not_for_real_training": True,
    }


def build_loss_policy_v0() -> dict[str, Any]:
    return {
        "loss_original": "output0.mean()",
        "loss_masked_x": "target masked coordinate residual loss",
        "loss_masked_h": "target masked feature residual loss",
        "loss_total": "w_original*loss_original + w_x*loss_masked_x + w_h*loss_masked_h",
        "default_weights": dict(LOSS_WEIGHTS),
        "future_optional_losses": [
            "warhead type classification",
            "reactive atom pair prediction",
            "geometry/residue distance auxiliary loss",
        ],
        "current_step_auxiliary_losses_enabled": False,
    }


def build_checkpoint_boundary_policy_v0() -> dict[str, Any]:
    return {
        "current_stage_checkpoint_allowed": False,
        "next_few_step_dry_run_checkpoint_allowed": False,
        "first_checkpoint_may_only_be_considered_after": [
            "few-step loop passes",
            "source modification boundary is reviewed",
            "output directory naming is fixed",
            "checkpoint naming / retention / metadata policy is reviewed",
            "explicit user approval",
        ],
        "checkpoint_forbidden_patterns": [
            "torch.save",
            "trainer.save_checkpoint",
            "ModelCheckpoint",
            ".ckpt",
            ".pt",
            ".pth",
        ],
    }


def build_training_loop_design_v0() -> dict[str, Any]:
    validate_step10o_outputs_v0()
    contract = build_training_loop_contract_v0()
    loop_plan = build_minimal_training_loop_plan_v0()
    mask_schedule_policy = build_mask_schedule_policy_v0()
    loss_policy = build_loss_policy_v0()
    checkpoint_boundary_policy = build_checkpoint_boundary_policy_v0()
    source_modification_policy = {
        "source_modification_allowed": False,
        "protected_paths": [
            "equivariant_diffusion/en_diffusion.py",
            "equivariant_diffusion/conditional_model.py",
            "equivariant_diffusion/dynamics.py",
            "lightning_modules.py",
        ],
        "required_check": "git diff -- equivariant_diffusion/ lightning_modules.py must be empty",
    }
    output_policy = {
        "allowed_outputs": list(contract["allowed_outputs_next_stage"]),
        "forbidden_outputs": list(contract["forbidden_outputs_next_stage"]),
        "checkpoint_allowed": False,
        "model_save_allowed": False,
        "archive_allowed": False,
    }
    risk_register = [
        {
            "risk": "Dry-run loop accidentally becomes formal training.",
            "mitigation": "Use a hard max_steps cap and report-only outputs; require explicit approval before any broader run.",
        },
        {
            "risk": "Checkpoint or model artifact is written unintentionally.",
            "mitigation": "Scan output roots for forbidden suffixes and keep checkpoint/model saving disabled.",
        },
        {
            "risk": "Masked loss is unstable for one mask level.",
            "mitigation": "Abort on first non-finite loss, gradient, parameter, or missing target mask.",
        },
        {
            "risk": "Source-level behavior changes hide in the training loop step.",
            "mitigation": "Require protected source diff checks before and after the few-step dry run.",
        },
    ]
    all_checks_passed = True
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10o_optimizer_smoke_passed": True,
        "contract": contract,
        "loop_plan": loop_plan,
        "mask_schedule_policy": mask_schedule_policy,
        "loss_policy": loss_policy,
        "checkpoint_boundary_policy": checkpoint_boundary_policy,
        "source_modification_policy": source_modification_policy,
        "output_policy": output_policy,
        "risk_register": risk_register,
        "checkpoint_allowed": False,
        "model_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "source_modification_allowed": False,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "few_step_training_dry_run_no_checkpoint"
            if all_checks_passed
            else "manual_training_loop_design_review"
        ),
    }

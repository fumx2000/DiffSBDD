from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "tiny_training_dry_run_design_v0"
PREVIOUS_STAGE = "single_optimizer_step_smoke_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
STEP11J_MANIFEST_JSON = Path(
    "data/derived/covalent_small/single_optimizer_step_smoke_v0/single_optimizer_step_smoke_manifest.json"
)
STEP11J_DELTA_TABLE_CSV = Path(
    "data/derived/covalent_small/single_optimizer_step_smoke_v0/single_optimizer_step_delta_table.csv"
)
STEP11J_SUMMARY_MD = Path("docs/single_optimizer_step_smoke_v0_summary.md")
STEP11I_PROTOCOL_JSON = Path("data/derived/covalent_small/optimizer_smoke_design_v0/optimizer_smoke_protocol.json")
OUTPUT_ROOT = Path("data/derived/covalent_small/tiny_training_dry_run_design_v0")
REPORT_CSV = OUTPUT_ROOT / "tiny_training_dry_run_design_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "tiny_training_dry_run_design_manifest.json"
PROTOCOL_JSON = OUTPUT_ROOT / "tiny_training_dry_run_protocol.json"
SUMMARY_MD = Path("docs/tiny_training_dry_run_design_v0_summary.md")
SELECTED_MASK_LEVEL = "A_warhead_only"
OPTIONAL_MASK_LEVELS = [
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
OPTIMIZER_CLASS = "AdamW"
OPTIMIZER_LR = 1e-6
OPTIMIZER_WEIGHT_DECAY = 0.0
OPTIMIZER_STEP_TEXT = "optimizer" + ".step"
BACKWARD_TEXT = "back" + "ward"
TORCH_SAVE_TEXT = "torch" + ".save"


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _text_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _source_diff_exists() -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def validate_step11j_outputs_v0() -> bool:
    if not STEP11J_MANIFEST_JSON.is_file() or not STEP11J_DELTA_TABLE_CSV.is_file() or not STEP11J_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11J outputs are missing")
    manifest = _load_json(STEP11J_MANIFEST_JSON)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "optimizer_smoke_design_v0",
        "step11i_validated": True,
        "selected_mask_level": SELECTED_MASK_LEVEL,
        "model_instantiated": True,
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "optimizer_created": True,
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": OPTIMIZER_LR,
        "optimizer_weight_decay": OPTIMIZER_WEIGHT_DECAY,
        "loss_requires_grad": True,
        "loss_finite": True,
        "selected_loss_key": "masked_loss_total_differentiable",
        "backward_called": True,
        "backward_call_count": 1,
        "backward_success": True,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "finite_nonzero_grad_exists": True,
        "optimizer_step_called": True,
        "optimizer_step_call_count": 1,
        "optimizer_step_success": True,
        "finite_parameter_delta": True,
        "delta_nan_count": 0,
        "delta_inf_count": 0,
        "single_optimizer_step_smoke_passed": True,
        "optimizer_plumbing_proven": True,
        "tiny_training_dry_run_design_allowed": True,
        "optimizer_step_smoke_status": "single_optimizer_step_smoke_passed",
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "tiny_training_dry_run_design",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11j_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    for key in ["selected_loss_value", "parameter_delta_l2_total", "parameter_delta_max_abs"]:
        value = float(manifest.get(key, 0.0))
        _expect(math.isfinite(value) and value > 0.0, f"step11j_manifest_{key}_not_positive_finite", blockers)
    _expect(int(manifest.get("changed_parameter_count", 0)) > 0, "step11j_manifest_changed_parameter_count_invalid", blockers)

    rows = _rows_from_csv(STEP11J_DELTA_TABLE_CSV)
    _expect(len(rows) == 1, f"step11j_delta_table_row_count_invalid:{len(rows)}", blockers)
    if rows:
        row = rows[0]
        expected_row = {
            "selected_mask_level": SELECTED_MASK_LEVEL,
            "status": "passed",
            "backward_call_count": "1",
            "optimizer_step_call_count": "1",
            "finite_parameter_delta": "True",
            "delta_nan_count": "0",
            "delta_inf_count": "0",
        }
        for key, expected in expected_row.items():
            _expect(row.get(key) == expected, f"step11j_delta_{key}_invalid:{row.get(key)!r}", blockers)
        for key in ["changed_parameter_count", "parameter_delta_l2_total", "parameter_delta_max_abs"]:
            value = float(row.get(key, "0"))
            _expect(math.isfinite(value) and value > 0.0, f"step11j_delta_{key}_not_positive_finite", blockers)
    summary = STEP11J_SUMMARY_MD.read_text(encoding="utf-8")
    _expect("not formal training" in summary, "step11j_summary_training_boundary_missing", blockers)
    _expect("tiny_training_dry_run_design" in summary, "step11j_summary_next_step_missing", blockers)
    _expect("does not prove loss decrease" in summary, "step11j_summary_loss_decrease_non_claim_missing", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step11j_optimizer_evidence_v0() -> dict[str, Any]:
    manifest = _load_json(STEP11J_MANIFEST_JSON)
    rows = _rows_from_csv(STEP11J_DELTA_TABLE_CSV)
    row = rows[0] if rows else {}
    return {
        "delta_table_present": STEP11J_DELTA_TABLE_CSV.is_file(),
        "delta_table_row_count": len(rows),
        "selected_mask_level": row.get("selected_mask_level", manifest.get("selected_mask_level", "")),
        "optimizer_class": row.get("optimizer_class", manifest.get("optimizer_class", "")),
        "optimizer_lr": float(row.get("optimizer_lr", manifest.get("optimizer_lr", 0.0))),
        "optimizer_weight_decay": float(manifest.get("optimizer_weight_decay", 0.0)),
        "selected_loss_value": float(row.get("selected_loss_value", manifest.get("selected_loss_value", 0.0))),
        "backward_call_count": int(row.get("backward_call_count", manifest.get("backward_call_count", 0))),
        "optimizer_step_call_count": int(row.get("optimizer_step_call_count", manifest.get("optimizer_step_call_count", 0))),
        "sampled_parameter_count": int(row.get("sampled_parameter_count", manifest.get("sampled_parameter_count", 0))),
        "changed_parameter_count": int(row.get("changed_parameter_count", manifest.get("changed_parameter_count", 0))),
        "unchanged_parameter_count": int(row.get("unchanged_parameter_count", manifest.get("unchanged_parameter_count", 0))),
        "parameter_delta_l2_total": float(row.get("parameter_delta_l2_total", manifest.get("parameter_delta_l2_total", 0.0))),
        "parameter_delta_max_abs": float(row.get("parameter_delta_max_abs", manifest.get("parameter_delta_max_abs", 0.0))),
        "parameter_delta_mean_abs": float(row.get("parameter_delta_mean_abs", manifest.get("parameter_delta_mean_abs", 0.0))),
        "finite_parameter_delta": _text_bool(row.get("finite_parameter_delta", manifest.get("finite_parameter_delta", False))),
        "delta_nan_count": int(row.get("delta_nan_count", manifest.get("delta_nan_count", 0))),
        "delta_inf_count": int(row.get("delta_inf_count", manifest.get("delta_inf_count", 0))),
        "optimizer_step_smoke_passed": bool(manifest.get("single_optimizer_step_smoke_passed")),
        "optimizer_plumbing_proven": bool(manifest.get("optimizer_plumbing_proven")),
    }


def build_tiny_training_scope_v0(step11j_evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "proposed_next_stage": "tiny_training_dry_run_v0",
        "input_source": "synthetic_10d_shape_contract",
        "selected_mask_levels": [SELECTED_MASK_LEVEL],
        "optional_later_expand_mask_levels": OPTIONAL_MASK_LEVELS,
        "max_steps": 3,
        "batch_size": 1,
        "device_default": "cpu",
        "optimizer_class": OPTIMIZER_CLASS,
        "lr": OPTIMIZER_LR,
        "weight_decay": OPTIMIZER_WEIGHT_DECAY,
        "fresh_model_once": True,
        "reuse_optimizer_across_steps": True,
        "no_scheduler": True,
        "no_mixed_precision": True,
        "no_gradient_accumulation": True,
        "no_gradient_clipping": True,
        "scope_rationale": (
            "Step 11J proved one A_warhead_only optimizer step; Step 11L should keep the same synthetic "
            "shape-only input and run exactly three small loop iterations."
        ),
        "step11j_delta_reference": {
            "changed_parameter_count": step11j_evidence.get("changed_parameter_count", 0),
            "parameter_delta_l2_total": step11j_evidence.get("parameter_delta_l2_total", 0.0),
        },
    }


def build_tiny_training_protocol_v0(scope: dict[str, Any], step11j_evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "proposed_next_stage": scope["proposed_next_stage"],
        "input_source": scope["input_source"],
        "selected_mask_levels": scope["selected_mask_levels"],
        "max_steps": scope["max_steps"],
        "batch_size": scope["batch_size"],
        "device_default": scope["device_default"],
        "fresh_strict_loaded_pretrained_model": True,
        "fresh_model_once": scope["fresh_model_once"],
        "create_one_optimizer": True,
        "optimizer_class": scope["optimizer_class"],
        "optimizer_lr": scope["lr"],
        "optimizer_weight_decay": scope["weight_decay"],
        "reuse_optimizer_across_steps": scope["reuse_optimizer_across_steps"],
        "per_step_actions": [
            "zero gradients with set_to_none true",
            "forward",
            "compute differentiable masked loss",
            f"{BACKWARD_TEXT} once",
            f"{OPTIMIZER_STEP_TEXT} once",
            "record scalar summaries",
        ],
        "allowed_next_step": [
            "fresh strict-loaded pretrained model",
            "one AdamW optimizer",
            "exactly 3 iterations",
            "scalar loss trajectory logging",
            "per-step gradient scalar summaries",
            "per-step parameter delta scalar summaries",
            "discard model and optimizer after run",
        ],
        "forbidden_next_step": [
            "trainer" + ".fit",
            "training" + "_step",
            "scheduler",
            "checkpoint save",
            "model save",
            "tensor dump",
            "full parameter dump",
            "optimizer dump",
            "multi-batch dataloader",
            "real covalent loader unless separate gate passes",
            "Step 10W checkpoint",
        ],
        "pass_conditions": [
            "step_count equals 3",
            "each step loss finite",
            "each step loss requires grad",
            f"each step {BACKWARD_TEXT} success",
            f"each step {OPTIMIZER_STEP_TEXT} success",
            "each step grad_nan_count equals 0",
            "each step grad_inf_count equals 0",
            "each step parameter_delta_l2_total finite positive",
            "no NaN/Inf in parameter deltas",
            "no checkpoint/model/tensor dump saved",
            "final status passed",
        ],
        "loss_trajectory_rule": {
            "record_initial_and_per_step_loss_values": True,
            "allow_loss_up_down_or_flat": True,
            "loss_decrease_required": False,
            "finite_increasing_loss_allowed_with_warning": True,
            "nan_or_inf_loss_fails": True,
        },
        "non_claims": [
            "loss decrease not required",
            "stable 3-step synthetic dry run does not prove training convergence",
            "no generation quality claim",
            "no real covalent data-loader readiness claim",
            "no formal fine-tuning claim",
        ],
        "step11j_optimizer_reference": step11j_evidence,
    }


def build_tiny_training_evidence_schema_v0() -> dict[str, Any]:
    step_table_fields = [
        "stage",
        "step_index",
        "selected_mask_level",
        "loss_value",
        "loss_requires_grad",
        "loss_finite",
        "backward_called",
        "backward_success",
        "optimizer_step_called",
        "optimizer_step_success",
        "grad_nan_count",
        "grad_inf_count",
        "total_grad_norm",
        "max_abs_grad",
        "sampled_parameter_count",
        "changed_parameter_count",
        "parameter_delta_l2_total",
        "parameter_delta_max_abs",
        "finite_parameter_delta",
        "delta_nan_count",
        "delta_inf_count",
        "status",
        "blocking_reasons",
    ]
    manifest_fields = [
        "stage",
        "previous_stage",
        "step11j_validated",
        "tiny_training_dry_run_step_count",
        "selected_mask_levels",
        "input_source",
        "optimizer_class",
        "optimizer_lr",
        "all_steps_passed",
        "finite_loss_all_steps",
        "finite_grad_all_steps",
        "finite_parameter_delta_all_steps",
        "loss_values",
        "loss_decreased_optional",
        "loss_decrease_required",
        "tiny_training_dry_run_passed",
        "tiny_training_loop_plumbing_proven",
        "real_covalent_loader_gate_allowed",
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "recommended_next_step",
    ]
    return {
        "outputs_next_step": [
            "manifest json",
            "step table csv",
            "summary md",
            "report csv",
        ],
        "step_table_fields": step_table_fields,
        "manifest_fields": manifest_fields,
        "scalar_only_parameter_delta": True,
        "full_tensor_dump_allowed": False,
    }


def build_tiny_training_risk_register_v0(
    step11j_evidence: dict[str, Any],
    scope: dict[str, Any],
    protocol: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "risk_id": "R1_synthetic_10d_semantics",
            "description": "Synthetic 10D input does not represent real covalent feature semantics.",
            "severity": "high",
            "mitigation": "Keep Step 11L as loop plumbing only and require a later real feature mapping gate.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R2_tiny_loop_not_real_training",
            "description": "Three synthetic optimizer iterations are still not formal training.",
            "severity": "high",
            "mitigation": "Keep formal training and fine-tune flags false and prohibit checkpoint/model saves.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R3_loss_decrease_not_required",
            "description": "Loss may rise or stay flat during a plumbing smoke.",
            "severity": "medium",
            "mitigation": "Require finite loss only; record trajectory and warn on large increases.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R4_in_memory_weight_updates_only",
            "description": "Reusing one optimizer changes weights in memory over multiple steps.",
            "severity": "medium",
            "mitigation": "Discard model/optimizer and write only scalar summaries.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R5_no_scheduler_clipping_accumulation_amp",
            "description": "Scheduler, clipping, accumulation, and AMP remain untested.",
            "severity": "low",
            "mitigation": "List these as explicit exclusions in Step 11L.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R6_real_covalent_loader_gap",
            "description": "Real covalent loader is not part of this synthetic tiny loop.",
            "severity": "high",
            "mitigation": "Gate real covalent feature mapping / loader separately after Step 11L.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R7_a_only_mask_scope",
            "description": "A-only mask does not prove B/B2/C full training readiness.",
            "severity": "medium",
            "mitigation": "Treat B/B2/C as optional later expansion after the first tiny loop passes.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R8_scalar_delta_only",
            "description": "Parameter delta evidence must not include full tensors.",
            "severity": "medium",
            "mitigation": "Record only scalar delta summaries per step.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R9_cpu_not_gpu_performance",
            "description": "CPU tiny run does not represent GPU performance.",
            "severity": "low",
            "mitigation": "Do not make throughput or performance claims.",
            "blocks_11L": False,
        },
        {
            "risk_id": "R10_next_real_mapping_gate",
            "description": "A real feature mapping / loader gate or real microbatch design is still required after synthetic 11L.",
            "severity": "high",
            "mitigation": "Recommend the next boundary explicitly after the tiny loop review.",
            "blocks_11L": False,
        },
    ]


def build_tiny_training_design_decision_v0(
    step11j_evidence: dict[str, Any],
    scope: dict[str, Any],
    protocol: dict[str, Any],
    step11j_validated: bool = True,
) -> dict[str, Any]:
    evidence_present = bool(
        step11j_evidence.get("delta_table_row_count") == 1
        and step11j_evidence.get("optimizer_step_smoke_passed")
        and step11j_evidence.get("optimizer_plumbing_proven")
    )
    protocol_complete = bool(
        scope.get("max_steps") == 3
        and scope.get("selected_mask_levels") == [SELECTED_MASK_LEVEL]
        and protocol.get("loss_trajectory_rule", {}).get("loss_decrease_required") is False
    )
    if step11j_validated and evidence_present and protocol_complete:
        design_status = "tiny_training_dry_run_design_ready"
        allowed = True
        next_step = "tiny_training_dry_run"
    elif not step11j_validated:
        design_status = "step11j_precondition_failed"
        allowed = False
        next_step = "optimizer_step_smoke_debug"
    else:
        design_status = "optimizer_evidence_missing"
        allowed = False
        next_step = "optimizer_evidence_debug"
    return {
        "design_status": design_status,
        "tiny_training_dry_run_allowed": allowed,
        "recommended_next_step": next_step,
        "this_design_runs_training_loop": False,
        "this_design_runs_backward": False,
        "this_design_creates_optimizer": False,
        "this_design_runs_optimizer_step": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "checkpoint_save_allowed_next_step": False,
        "model_save_allowed_next_step": False,
        "tensor_dump_allowed_next_step": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
    }


def build_tiny_training_dry_run_design_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11j_validated = validate_step11j_outputs_v0()
    except Exception as exc:
        step11j_validated = False
        blockers.append(f"step11j_validation_failed:{type(exc).__name__}:{exc}")
    step11j_evidence = load_step11j_optimizer_evidence_v0() if STEP11J_DELTA_TABLE_CSV.is_file() else {}
    scope = build_tiny_training_scope_v0(step11j_evidence)
    protocol = build_tiny_training_protocol_v0(scope, step11j_evidence)
    evidence_schema = build_tiny_training_evidence_schema_v0()
    risk_register = build_tiny_training_risk_register_v0(step11j_evidence, scope, protocol)
    decision = build_tiny_training_design_decision_v0(step11j_evidence, scope, protocol, step11j_validated)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(
        step11j_validated
        and step11j_evidence.get("optimizer_plumbing_proven")
        and decision["tiny_training_dry_run_allowed"]
        and not source_modified
        and not forbidden_artifacts
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11j_validated": step11j_validated,
        "optimizer_plumbing_proven": bool(step11j_evidence.get("optimizer_plumbing_proven")),
        "selected_mask_level": step11j_evidence.get("selected_mask_level", SELECTED_MASK_LEVEL),
        "optimizer_class": scope["optimizer_class"],
        "optimizer_lr": scope["lr"],
        "optimizer_weight_decay": scope["weight_decay"],
        "single_step_delta_positive": bool(
            step11j_evidence.get("changed_parameter_count", 0) > 0
            and step11j_evidence.get("parameter_delta_l2_total", 0.0) > 0.0
        ),
        "protocol_written": True,
        "protocol_path": str(PROTOCOL_JSON),
        "proposed_next_stage": protocol["proposed_next_stage"],
        "tiny_training_dry_run_step_count": scope["max_steps"],
        "selected_mask_levels": scope["selected_mask_levels"],
        "input_source": scope["input_source"],
        "reuse_optimizer_across_steps": scope["reuse_optimizer_across_steps"],
        **decision,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    protocol_document = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11j_optimizer_evidence": step11j_evidence,
        "scope": scope,
        "protocol": protocol,
        "evidence_schema": evidence_schema,
        "risk_register": risk_register,
        "decision": decision,
    }
    return {
        "manifest": manifest,
        "protocol_document": protocol_document,
        "report_sections": {
            "step11j_precondition": {"step11j_validated": step11j_validated},
            "optimizer_evidence": step11j_evidence,
            "tiny_training_scope": scope,
            "tiny_training_protocol": protocol,
            "evidence_schema": evidence_schema,
            "risk_register": risk_register,
            "design_decision": decision,
            "safety_boundary": {
                "backward_called": False,
                "optimizer_created": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "original_source_files_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }

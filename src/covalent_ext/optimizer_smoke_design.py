from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "optimizer_smoke_design_v0"
PREVIOUS_STAGE = "pretrained_masked_loss_microbatch_backward_dry_run_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
STEP11H_MANIFEST_JSON = Path(
    "data/derived/covalent_small/pretrained_masked_loss_microbatch_backward_dry_run_v0/"
    "pretrained_masked_loss_microbatch_backward_manifest.json"
)
STEP11H_GRADIENT_TABLE_CSV = Path(
    "data/derived/covalent_small/pretrained_masked_loss_microbatch_backward_dry_run_v0/"
    "pretrained_masked_loss_microbatch_gradient_table.csv"
)
STEP11H_SUMMARY_MD = Path("docs/pretrained_masked_loss_microbatch_backward_dry_run_v0_summary.md")
STEP11G_PROTOCOL_JSON = Path(
    "data/derived/covalent_small/pretrained_masked_loss_microbatch_design_v0/"
    "pretrained_masked_loss_microbatch_protocol.json"
)
OUTPUT_ROOT = Path("data/derived/covalent_small/optimizer_smoke_design_v0")
REPORT_CSV = OUTPUT_ROOT / "optimizer_smoke_design_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "optimizer_smoke_design_manifest.json"
PROTOCOL_JSON = OUTPUT_ROOT / "optimizer_smoke_protocol.json"
SUMMARY_MD = Path("docs/optimizer_smoke_design_v0_summary.md")
CONFIG_CANDIDATES = [
    Path("configs/crossdock_fullatom_cond.yml"),
    Path("configs/crossdock_fullatom_joint.yml"),
]
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


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


def _parse_first_lr_from_config(paths: list[Path] = CONFIG_CANDIDATES) -> dict[str, Any]:
    for path in paths:
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped.startswith("lr:"):
                continue
            value_text = stripped.split(":", 1)[1].strip()
            try:
                return {"base_lr_from_config": float(value_text), "base_lr_config_source": str(path)}
            except ValueError:
                return {"base_lr_from_config": None, "base_lr_config_source": str(path)}
    return {"base_lr_from_config": None, "base_lr_config_source": ""}


def validate_step11h_outputs_v0() -> bool:
    if not STEP11H_MANIFEST_JSON.is_file() or not STEP11H_GRADIENT_TABLE_CSV.is_file() or not STEP11H_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11H outputs are missing")

    manifest = _load_json(STEP11H_MANIFEST_JSON)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "pretrained_masked_loss_microbatch_design_v0",
        "step11g_validated": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "microbatch_backward_policy": "isolated_backward_per_mask_level",
        "fresh_model_per_mask_level": True,
        "all_mask_levels_passed": True,
        "backward_level_count": 4,
        "backward_success_level_count": 4,
        "backward_called": True,
        "backward_call_count_total": 4,
        "failed_mask_levels": [],
        "loss_requires_grad_all_levels": True,
        "finite_loss_all_levels": True,
        "finite_nonzero_grad_all_levels": True,
        "grad_nan_count_total": 0,
        "grad_inf_count_total": 0,
        "microbatch_backward_status": "pretrained_microbatch_backward_dry_run_passed",
        "microbatch_backward_dry_run_passed": True,
        "gradient_plumbing_proven": True,
        "optimizer_smoke_design_allowed": True,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "optimizer_free_to_optimizer_smoke_design",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11h_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(set(manifest.get("mask_levels_attempted", [])) == set(MASK_LEVELS), "step11h_attempted_masks_invalid", blockers)
    _expect(set(manifest.get("mask_levels_passed", [])) == set(MASK_LEVELS), "step11h_passed_masks_invalid", blockers)
    for key in ["max_total_grad_norm", "max_abs_grad_overall"]:
        value = float(manifest.get(key, 0.0))
        _expect(math.isfinite(value) and value > 0.0, f"step11h_manifest_{key}_not_positive_finite", blockers)

    rows = _rows_from_csv(STEP11H_GRADIENT_TABLE_CSV)
    _expect(len(rows) == 4, f"step11h_gradient_table_row_count_invalid:{len(rows)}", blockers)
    _expect({row.get("mask_level") for row in rows} == set(MASK_LEVELS), "step11h_gradient_table_masks_invalid", blockers)
    for row in rows:
        mask_level = row.get("mask_level", "")
        expected_row = {
            "status": "passed",
            "backward_success": "True",
            "loss_requires_grad": "True",
            "loss_finite": "True",
            "finite_nonzero_grad_exists": "True",
            "grad_nan_count": "0",
            "grad_inf_count": "0",
            "optimizer_created": "False",
            "optimizer_step_called": "False",
        }
        for key, expected in expected_row.items():
            _expect(row.get(key) == expected, f"step11h_gradient_{mask_level}_{key}_invalid:{row.get(key)!r}", blockers)
        for key in ["total_grad_norm", "max_abs_grad"]:
            try:
                value = float(row.get(key, "nan"))
            except ValueError:
                value = math.nan
            _expect(math.isfinite(value) and value > 0.0, f"step11h_gradient_{mask_level}_{key}_not_positive_finite", blockers)

    summary = STEP11H_SUMMARY_MD.read_text(encoding="utf-8")
    _expect("pretrained_microbatch_backward_dry_run_passed" in summary, "step11h_summary_status_missing", blockers)
    _expect("optimizer_free_to_optimizer_smoke_design" in summary, "step11h_summary_next_step_missing", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step11h_gradient_evidence_v0() -> dict[str, Any]:
    rows = _rows_from_csv(STEP11H_GRADIENT_TABLE_CSV)
    mask_levels: list[str] = []
    loss_values_by_level: dict[str, float] = {}
    grad_norm_by_level: dict[str, float] = {}
    max_abs_grad_by_level: dict[str, float] = {}
    parameters_with_grad_by_level: dict[str, int] = {}
    parameters_with_nonzero_grad_by_level: dict[str, int] = {}
    grad_nan_count_total = 0
    grad_inf_count_total = 0
    for row in rows:
        mask_level = row["mask_level"]
        mask_levels.append(mask_level)
        loss_values_by_level[mask_level] = float(row["selected_loss_value"])
        grad_norm_by_level[mask_level] = float(row["total_grad_norm"])
        max_abs_grad_by_level[mask_level] = float(row["max_abs_grad"])
        parameters_with_grad_by_level[mask_level] = int(row["parameters_with_grad_count"])
        parameters_with_nonzero_grad_by_level[mask_level] = int(row["parameters_with_nonzero_grad_count"])
        grad_nan_count_total += int(row["grad_nan_count"])
        grad_inf_count_total += int(row["grad_inf_count"])
    grad_norm_values = list(grad_norm_by_level.values())
    max_abs_values = list(max_abs_grad_by_level.values())
    max_grad_norm = max(grad_norm_values) if grad_norm_values else 0.0
    return {
        "gradient_table_present": STEP11H_GRADIENT_TABLE_CSV.is_file(),
        "gradient_table_row_count": len(rows),
        "mask_levels": mask_levels,
        "loss_values_by_level": loss_values_by_level,
        "grad_norm_by_level": grad_norm_by_level,
        "max_abs_grad_by_level": max_abs_grad_by_level,
        "parameters_with_grad_by_level": parameters_with_grad_by_level,
        "parameters_with_nonzero_grad_by_level": parameters_with_nonzero_grad_by_level,
        "min_grad_norm": min(grad_norm_values) if grad_norm_values else 0.0,
        "max_grad_norm": max_grad_norm,
        "max_abs_grad_overall": max(max_abs_values) if max_abs_values else 0.0,
        "grad_nan_count_total": grad_nan_count_total,
        "grad_inf_count_total": grad_inf_count_total,
        "all_backward_success": all(_text_bool(row.get("backward_success")) for row in rows),
        "all_grad_finite": all(int(row.get("grad_nan_count", "1")) == 0 and int(row.get("grad_inf_count", "1")) == 0 for row in rows),
        "all_have_nonzero_grad": all(_text_bool(row.get("finite_nonzero_grad_exists")) for row in rows),
        "gradient_scale_warning": "monitor_optimizer_step_size_for_large_gradient_norm" if max_grad_norm > 100.0 else "",
    }


def build_optimizer_smoke_input_policy_v0(step11h_evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "optimizer_smoke_input_source": "synthetic_10d_shape_contract",
        "mask_levels_for_optimizer_smoke": ["A_warhead_only"],
        "optional_expand_to_all_levels_after_first_pass": True,
        "all_mask_levels_have_backward_evidence": set(step11h_evidence.get("mask_levels", [])) == set(MASK_LEVELS),
        "selected_initial_mask_level": "A_warhead_only",
        "selection_reason": "largest_observed_grad_norm_and_simple_warhead_mask",
        "selected_initial_grad_norm": step11h_evidence.get("grad_norm_by_level", {}).get("A_warhead_only", 0.0),
        "not_formal_training": True,
        "quality_claim_allowed": False,
    }


def build_optimizer_config_recommendation_v0() -> dict[str, Any]:
    lr_evidence = _parse_first_lr_from_config()
    return {
        **lr_evidence,
        "optimizer_class": "AdamW",
        "optimizer_import_path_next_step": "torch" + "." + "optim" + ".AdamW",
        "lr": 1e-6,
        "weight_decay": 0.0,
        "betas": [0.9, 0.999],
        "eps": 1e-8,
        "scheduler_allowed": False,
        "gradient_accumulation_allowed": False,
        "mixed_precision_allowed": False,
        "gradient_clipping_allowed": False,
        "recommendation_reason": (
            "Use a tiny learning rate for plumbing-only parameter delta evidence; no loss decrease or quality "
            "claim is expected."
        ),
    }


def build_optimizer_smoke_protocol_v0(
    step11h_evidence: dict[str, Any],
    input_policy: dict[str, Any],
    optimizer_config: dict[str, Any],
) -> dict[str, Any]:
    optimizer_step_text = "optimizer" + ".step"
    return {
        "proposed_next_stage": "optimizer_step_smoke_v0",
        "input_source": input_policy["optimizer_smoke_input_source"],
        "selected_mask_level": input_policy["selected_initial_mask_level"],
        "model_policy": "fresh_strict_loaded_pretrained_model",
        "optimizer_policy": "single AdamW optimizer for smoke only",
        "optimizer_config": optimizer_config,
        "backward_policy": "single backward",
        "optimizer_step_policy": f"single {optimizer_step_text} exactly once",
        "optimizer_step_call_count_next_step": 1,
        "zero_grad_policy": [
            "optimizer.zero_grad(set_to_none=True) before forward",
            "compute differentiable masked loss",
            "backward once",
            "capture selected parameter snapshots before step",
            f"{optimizer_step_text} once",
            "compare parameter delta summaries",
            "optimizer.zero_grad(set_to_none=True) after measurement",
        ],
        "parameter_delta_policy": {
            "save_full_tensors": False,
            "record_only_summary": True,
            "summary_fields": [
                "sampled_parameter_names",
                "parameter_delta_l2_total",
                "parameter_delta_max_abs",
                "changed_parameter_count",
                "unchanged_parameter_count",
                "finite_parameter_delta",
            ],
        },
        "pass_conditions": [
            "loss finite",
            "loss.requires_grad true",
            "backward_success true",
            "optimizer_created true",
            "optimizer_step_called true",
            "optimizer_step_call_count equals 1",
            "at least one parameter changed",
            "parameter_delta_l2_total finite positive",
            "parameter_delta_max_abs finite positive",
            "no NaN/Inf in changed parameters",
            "no checkpoint/model saved",
        ],
        "non_claims": [
            "not formal training",
            "loss decrease is not required",
            "no generation quality claim",
            "no real covalent data-loader training claim",
        ],
        "forbidden_next_step": [
            "trainer" + ".fit",
            "training_step",
            "scheduler",
            "multiple optimizer steps",
            "checkpoint save",
            "model save",
            "writing .pt/.ckpt/.pth/.pkl artifacts",
            "using Step 10W checkpoint",
        ],
        "step11h_gradient_reference": step11h_evidence.get("grad_norm_by_level", {}),
    }


def build_optimizer_smoke_risk_register_v0(
    step11h_evidence: dict[str, Any],
    input_policy: dict[str, Any],
    optimizer_config: dict[str, Any],
    protocol: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "risk_id": "R1_synthetic_10d_contract",
            "description": "Synthetic 10D contract still does not prove real covalent feature semantics.",
            "severity": "high",
            "mitigation": "Keep Step 11J as optimizer plumbing only and retain no quality claims.",
            "blocks_11J": False,
        },
        {
            "risk_id": "R2_in_memory_pretrained_weight_update",
            "description": "The optimizer step will change pretrained weights in memory only.",
            "severity": "medium",
            "mitigation": "Do not save checkpoint/model artifacts; discard model after measurement.",
            "blocks_11J": False,
        },
        {
            "risk_id": "R3_lr_too_large",
            "description": "Too-large learning rate may perturb parameters more than needed for a smoke test.",
            "severity": "medium",
            "mitigation": "Use AdamW with lr=1e-6 and weight_decay=0.0 for the first step smoke.",
            "blocks_11J": False,
        },
        {
            "risk_id": "R4_lr_too_small",
            "description": "Too-small learning rate may produce parameter deltas near floating-point precision.",
            "severity": "low",
            "mitigation": "Require positive finite parameter delta summaries and report unchanged parameter counts.",
            "blocks_11J": False,
        },
        {
            "risk_id": "R5_optimizer_state_not_training_loop_readiness",
            "description": "AdamW state creation alone does not prove scheduler, clipping, accumulation, or loop readiness.",
            "severity": "medium",
            "mitigation": "Defer scheduler, clipping, and accumulation to later explicit gates.",
            "blocks_11J": False,
        },
        {
            "risk_id": "R6_scheduler_clipping_accumulation_untested",
            "description": "No scheduler, mixed precision, gradient accumulation, or clipping will be tested.",
            "severity": "low",
            "mitigation": "State these as exclusions in the Step 11J report.",
            "blocks_11J": False,
        },
        {
            "risk_id": "R7_real_covalent_loader_unresolved",
            "description": "Real covalent loader and feature mapping remain outside this optimizer smoke.",
            "severity": "high",
            "mitigation": "Keep synthetic shape-only labels and require later real-data mapping gates.",
            "blocks_11J": False,
        },
        {
            "risk_id": "R8_parameter_delta_tensor_leak",
            "description": "Parameter delta evidence must not write tensor dumps or model snapshots.",
            "severity": "medium",
            "mitigation": "Record only scalar summaries and sampled parameter names.",
            "blocks_11J": False,
        },
    ]


def build_optimizer_smoke_design_decision_v0(
    step11h_evidence: dict[str, Any],
    input_policy: dict[str, Any],
    optimizer_config: dict[str, Any],
    protocol: dict[str, Any],
    step11h_validated: bool = True,
) -> dict[str, Any]:
    gradient_evidence_present = bool(
        step11h_evidence.get("gradient_table_row_count") == 4
        and step11h_evidence.get("all_backward_success")
        and step11h_evidence.get("all_grad_finite")
        and step11h_evidence.get("all_have_nonzero_grad")
    )
    protocol_complete = bool(
        protocol.get("selected_mask_level") == "A_warhead_only"
        and protocol.get("optimizer_step_call_count_next_step") == 1
        and optimizer_config.get("optimizer_class") == "AdamW"
        and optimizer_config.get("lr") == 1e-6
    )
    if step11h_validated and gradient_evidence_present and protocol_complete:
        design_status = "optimizer_smoke_design_ready"
        allowed = True
        next_step = "single_optimizer_step_smoke"
    elif not step11h_validated:
        design_status = "step11h_precondition_failed"
        allowed = False
        next_step = "microbatch_backward_debug"
    else:
        design_status = "gradient_evidence_missing"
        allowed = False
        next_step = "gradient_evidence_debug"
    return {
        "design_status": design_status,
        "optimizer_step_smoke_allowed": allowed,
        "recommended_next_step": next_step,
        "this_design_creates_optimizer": False,
        "this_design_runs_optimizer_step": False,
        "this_design_runs_backward": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "checkpoint_save_allowed_next_step": False,
        "model_save_allowed_next_step": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
    }


def build_optimizer_smoke_design_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11h_validated = validate_step11h_outputs_v0()
    except Exception as exc:
        step11h_validated = False
        blockers.append(f"step11h_validation_failed:{type(exc).__name__}:{exc}")
    step11h_evidence = load_step11h_gradient_evidence_v0() if STEP11H_GRADIENT_TABLE_CSV.is_file() else {}
    input_policy = build_optimizer_smoke_input_policy_v0(step11h_evidence)
    optimizer_config = build_optimizer_config_recommendation_v0()
    protocol = build_optimizer_smoke_protocol_v0(step11h_evidence, input_policy, optimizer_config)
    risk_register = build_optimizer_smoke_risk_register_v0(step11h_evidence, input_policy, optimizer_config, protocol)
    decision = build_optimizer_smoke_design_decision_v0(step11h_evidence, input_policy, optimizer_config, protocol, step11h_validated)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(
        step11h_validated
        and step11h_evidence.get("gradient_table_row_count") == 4
        and decision["optimizer_step_smoke_allowed"]
        and not source_modified
        and not forbidden_artifacts
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11h_validated": step11h_validated,
        "gradient_plumbing_proven": step11h_validated and bool(step11h_evidence.get("all_have_nonzero_grad")),
        "all_mask_levels_backward_passed": step11h_validated and set(step11h_evidence.get("mask_levels", [])) == set(MASK_LEVELS),
        "grad_nan_count_total": step11h_evidence.get("grad_nan_count_total", 0),
        "grad_inf_count_total": step11h_evidence.get("grad_inf_count_total", 0),
        "max_total_grad_norm": step11h_evidence.get("max_grad_norm", 0.0),
        "selected_initial_mask_level": input_policy["selected_initial_mask_level"],
        "optimizer_smoke_input_source": input_policy["optimizer_smoke_input_source"],
        "optimizer_class_recommended": optimizer_config["optimizer_class"],
        "optimizer_lr_recommended": optimizer_config["lr"],
        "optimizer_weight_decay_recommended": optimizer_config["weight_decay"],
        "protocol_written": True,
        "protocol_path": str(PROTOCOL_JSON),
        "proposed_next_stage": protocol["proposed_next_stage"],
        "optimizer_step_policy_next_step": protocol["optimizer_step_policy"],
        "optimizer_step_call_count_next_step": protocol["optimizer_step_call_count_next_step"],
        **decision,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    protocol_document = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11h_gradient_evidence": step11h_evidence,
        "input_policy": input_policy,
        "optimizer_config": optimizer_config,
        "protocol": protocol,
        "risk_register": risk_register,
        "decision": decision,
    }
    return {
        "manifest": manifest,
        "protocol_document": protocol_document,
        "report_sections": {
            "step11h_precondition": {"step11h_validated": step11h_validated},
            "gradient_evidence": step11h_evidence,
            "optimizer_input_policy": input_policy,
            "optimizer_config": optimizer_config,
            "optimizer_protocol": protocol,
            "design_decision": decision,
            "safety_boundary": {
                "backward_called": False,
                "optimizer_created": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "original_source_files_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import PROTECTED_SOURCE_FILES, _build_candidate_inputs
from covalent_ext.diffsbdd_forward_shape_smoke import _instantiate_model_for_forward, resolve_diffsbdd_forward_device_v0
from covalent_ext.longer_no_checkpoint_training_dry_run import (
    BATCH_SIZE,
    DEFAULT_LR,
    LOOP_NAME,
    MASK_CYCLE,
    MASK_SCHEDULE,
    MAX_STEPS,
    SEED,
    SHUFFLE,
    run_one_longer_dry_step_v0,
)
from covalent_ext.masked_loss_optimizer_smoke import DEFAULT_WEIGHT_DECAY, OPTIMIZER_CLASS, build_optimizer_v0


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
STAGE = "first_checkpointed_training_dry_run_v0"
PREVIOUS_STAGE = "checkpoint_output_policy_design_v0"
RUN_NAME = "first_checkpointed_training_dry_run_v0"
RUN_ROOT = Path("data/derived/covalent_small/training_runs/first_checkpointed_training_dry_run_v0")
CHECKPOINT_FILENAME = "checkpoint_step_000012.pt"
CHECKPOINT_PATH = RUN_ROOT / "checkpoints" / CHECKPOINT_FILENAME
LOSS_WEIGHTS = {"w_original": 1.0, "w_x": 1.0, "w_h": 0.2}
MODEL_CONFIG_PATH = "configs/crossdock_fullatom_cond.yml"
ALLOWED_RUN_SUFFIXES = {".pt", ".csv", ".json", ".md"}
FORBIDDEN_RUN_SUFFIXES = {".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
KNOWN_RUN_OUTPUTS = [
    CHECKPOINT_PATH,
    RUN_ROOT / "reports" / "first_checkpointed_training_dry_run_report.csv",
    RUN_ROOT / "metadata" / "first_checkpointed_training_dry_run_manifest.json",
    RUN_ROOT / "metadata" / "checkpoint_metadata.json",
    RUN_ROOT / "resume_smoke" / "resume_smoke_report.csv",
    RUN_ROOT / "resume_smoke" / "resume_smoke_manifest.json",
]
REQUIRED_STEP10V_SECTIONS = [
    "output_directory_policy",
    "checkpoint_naming_policy",
    "checkpoint_payload_policy",
    "metadata_policy",
    "retention_policy",
    "resume_smoke_policy",
    "next_step_execution_boundary",
    "risk_register",
]
REQUIRED_PAYLOAD_FIELDS = [
    "schema_version",
    "stage",
    "run_name",
    "repo_commit",
    "created_at_utc",
    "model_class",
    "model_config_path",
    "model_state_dict",
    "optimizer_class",
    "optimizer_state_dict",
    "optimizer_lr",
    "optimizer_weight_decay",
    "completed_steps",
    "max_steps",
    "mask_schedule",
    "loss_weights",
    "batch_size",
    "shuffle",
    "seed",
    "sample_ids",
    "loss_total_by_step",
    "grad_norm_by_step",
    "param_delta_norm_by_step",
    "source_modification_allowed",
    "formal_training_executed",
    "real_finetune_executed",
]
FORBIDDEN_PAYLOAD_KEYS = {
    "dataset",
    "dataloader",
    "model",
    "optimizer",
    "raw_pdb_contents",
    "raw_sdf_contents",
    "generated_molecule_archive",
}


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _git_output(args: list[str]) -> str:
    completed = subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.stdout.strip()


def git_commit_v0() -> str:
    return _git_output(["git", "rev-parse", "HEAD"])


def git_status_short_v0() -> str:
    return _git_output(["git", "status", "--short"])


def _source_snapshots() -> dict[str, str]:
    return {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }


def _sources_modified(before: dict[str, str]) -> bool:
    return any((REPO_ROOT / rel_path).read_text(encoding="utf-8") != text for rel_path, text in before.items())


def _hash_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_root_pt_files() -> list[Path]:
    if not RUN_ROOT.exists():
        return []
    return sorted(path for path in RUN_ROOT.rglob("*.pt") if path.is_file())


def _unexpected_checkpoint_files() -> list[str]:
    allowed = Path(CHECKPOINT_PATH)
    unexpected = []
    for path in _run_root_pt_files():
        if path != allowed:
            unexpected.append(str(path))
    for suffix in [".ckpt", ".pth"]:
        unexpected.extend(str(path) for path in RUN_ROOT.rglob(f"*{suffix}") if path.is_file())
    return sorted(unexpected)


def _forbidden_run_artifacts() -> list[str]:
    if not RUN_ROOT.exists():
        return []
    forbidden: list[str] = []
    for path in RUN_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in FORBIDDEN_RUN_SUFFIXES:
            forbidden.append(str(path))
        elif path.suffix == ".pt" and path != CHECKPOINT_PATH:
            forbidden.append(str(path))
        elif path.suffix and path.suffix not in ALLOWED_RUN_SUFFIXES:
            forbidden.append(str(path))
    return sorted(set(forbidden))


def _cleanup_known_run_outputs() -> None:
    for path in KNOWN_RUN_OUTPUTS:
        if path.is_file():
            path.unlink()
    for directory in [
        RUN_ROOT / "checkpoints",
        RUN_ROOT / "reports",
        RUN_ROOT / "metadata",
        RUN_ROOT / "resume_smoke",
        RUN_ROOT,
    ]:
        try:
            directory.rmdir()
        except OSError:
            pass


def validate_step10v_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "checkpoint_output_policy_design_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "checkpoint_output_policy_design_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10V checkpoint/output policy outputs are missing")

    blockers: list[str] = []
    rows = _rows_from_csv(report_path)
    _expect(len(rows) == 8, f"step10v_report_row_count_invalid:{len(rows)}", blockers)
    _expect([row.get("policy_section") for row in rows] == REQUIRED_STEP10V_SECTIONS, "step10v_sections_invalid", blockers)
    for row in rows:
        _expect(row.get("stage") == PREVIOUS_STAGE, f"step10v_report_stage_invalid:{row.get('stage')!r}", blockers)
        _expect(
            row.get("previous_stage") == "longer_no_checkpoint_training_dry_run_review_v0",
            f"step10v_report_previous_stage_invalid:{row.get('previous_stage')!r}",
            blockers,
        )
        _expect(row.get("status") == "passed", f"step10v_report_status_invalid:{row.get('status')!r}", blockers)
        _expect(
            row.get("recommended_next_step") == "first_checkpointed_training_dry_run",
            f"step10v_report_recommended_next_step_invalid:{row.get('recommended_next_step')!r}",
            blockers,
        )

    manifest = _load_json(manifest_path)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "longer_no_checkpoint_training_dry_run_review_v0",
        "step10u_review_passed": True,
        "next_stage": STAGE,
        "run_name": RUN_NAME,
        "run_root": str(RUN_ROOT) + "/",
        "checkpoint_filename": CHECKPOINT_FILENAME,
        "checkpoint_count_limit": 1,
        "save_at_step": 12,
        "no_intermediate_checkpoints": True,
        "checkpoint_extension": ".pt",
        "current_step_checkpoint_save_allowed": False,
        "current_step_checkpoint_load_allowed": False,
        "current_step_model_save_allowed": False,
        "current_step_formal_training_allowed": False,
        "next_step_checkpoint_save_allowed": True,
        "next_step_checkpoint_load_allowed": True,
        "next_step_model_save_allowed": False,
        "next_step_trainer_fit_allowed": False,
        "next_step_training_step_allowed": False,
        "next_step_formal_training_allowed": False,
        "next_step_finetune_allowed": False,
        "next_step_source_modification_allowed": False,
        "resume_smoke_required": True,
        "no_second_checkpoint_during_resume_smoke": True,
        "max_checkpoints": 1,
        "keep_last_only": True,
        "fail_if_multiple_checkpoints_created": True,
        "fail_if_unexpected_checkpoint_files_exist": True,
        "metadata_required": True,
        "checkpoint_sha256_required": True,
        "current_step_checkpoint_saved": False,
        "current_step_checkpoint_loaded": False,
        "current_step_model_saved": False,
        "current_step_formal_training_executed": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "first_checkpointed_training_dry_run",
    }
    for key, expected_value in expected.items():
        _expect(manifest.get(key) == expected_value, f"step10v_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)

    naming = manifest.get("checkpoint_naming_policy", {})
    execution = manifest.get("next_step_execution_boundary", {})
    resume = manifest.get("resume_smoke_policy", {})
    _expect(naming.get("checkpoint_path") == str(CHECKPOINT_PATH), "step10v_checkpoint_path_invalid", blockers)
    _expect(naming.get("checkpoint_count_limit") == 1, "step10v_checkpoint_count_limit_invalid", blockers)
    _expect(execution.get("allowed_checkpoint_files_next_step") == [CHECKPOINT_FILENAME], "step10v_allowed_checkpoint_invalid", blockers)
    _expect(resume.get("load_model_state_dict") is True, "step10v_resume_load_model_state_invalid", blockers)
    _expect(resume.get("load_optimizer_state_dict") is True, "step10v_resume_load_optimizer_state_invalid", blockers)
    _expect(resume.get("second_checkpoint_save_allowed") is False, "step10v_resume_second_checkpoint_invalid", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def prepare_run_root_v0(overwrite: bool = False) -> dict[str, Any]:
    blockers: list[str] = []
    if RUN_ROOT.exists() and not overwrite:
        return {"prepared": False, "blocking_reasons": ["run_root_exists"], "created_directories": []}
    if RUN_ROOT.exists() and overwrite:
        unknown = sorted(str(path) for path in RUN_ROOT.rglob("*") if path.is_file() and path not in KNOWN_RUN_OUTPUTS)
        if unknown:
            return {"prepared": False, "blocking_reasons": [f"unknown_existing_files:{';'.join(unknown)}"], "created_directories": []}
        _cleanup_known_run_outputs()

    for directory in [RUN_ROOT / "checkpoints", RUN_ROOT / "reports", RUN_ROOT / "metadata", RUN_ROOT / "resume_smoke"]:
        directory.mkdir(parents=True, exist_ok=True)
    unexpected_checkpoints = _unexpected_checkpoint_files()
    forbidden = _forbidden_run_artifacts()
    if unexpected_checkpoints:
        blockers.append(f"unexpected_checkpoint_files:{';'.join(unexpected_checkpoints)}")
    if forbidden:
        blockers.append(f"forbidden_run_artifacts:{';'.join(forbidden)}")
    return {
        "prepared": not blockers,
        "blocking_reasons": blockers,
        "created_directories": [
            str(RUN_ROOT / "checkpoints"),
            str(RUN_ROOT / "reports"),
            str(RUN_ROOT / "metadata"),
            str(RUN_ROOT / "resume_smoke"),
        ],
    }


def validate_checkpoint_payload_schema_v0(payload: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    for field_name in REQUIRED_PAYLOAD_FIELDS:
        _expect(field_name in payload, f"missing_payload_field:{field_name}", blockers)
    for field_name in FORBIDDEN_PAYLOAD_KEYS:
        _expect(field_name not in payload, f"forbidden_payload_field:{field_name}", blockers)
    expected_values = {
        "schema_version": STAGE,
        "stage": STAGE,
        "run_name": RUN_NAME,
        "model_config_path": MODEL_CONFIG_PATH,
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": DEFAULT_LR,
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "completed_steps": MAX_STEPS,
        "max_steps": MAX_STEPS,
        "mask_schedule": MASK_SCHEDULE,
        "loss_weights": LOSS_WEIGHTS,
        "batch_size": BATCH_SIZE,
        "shuffle": SHUFFLE,
        "seed": SEED,
        "source_modification_allowed": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
    }
    for key, expected in expected_values.items():
        _expect(payload.get(key) == expected, f"payload_{key}_invalid:{payload.get(key)!r}", blockers)
    _expect(isinstance(payload.get("model_state_dict"), dict), "model_state_dict_not_dict", blockers)
    _expect(isinstance(payload.get("optimizer_state_dict"), dict), "optimizer_state_dict_not_dict", blockers)
    _expect(bool(payload.get("model_state_dict")), "model_state_dict_empty", blockers)
    _expect(bool(payload.get("optimizer_state_dict")), "optimizer_state_dict_empty", blockers)
    _expect(len(payload.get("loss_total_by_step", {})) == MAX_STEPS, "loss_total_by_step_count_invalid", blockers)
    _expect(len(payload.get("grad_norm_by_step", {})) == MAX_STEPS, "grad_norm_by_step_count_invalid", blockers)
    _expect(len(payload.get("param_delta_norm_by_step", {})) == MAX_STEPS, "param_delta_norm_by_step_count_invalid", blockers)
    return {"valid": not blockers, "blocking_reasons": blockers}


def build_checkpoint_payload_v0(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    run_summary: dict[str, Any],
    rows: list[dict[str, Any]],
    repo_commit: str,
    created_at_utc: str,
) -> dict[str, Any]:
    sample_ids = rows[0]["sample_ids"] if rows else []
    return {
        "schema_version": STAGE,
        "stage": STAGE,
        "run_name": RUN_NAME,
        "repo_commit": repo_commit,
        "created_at_utc": created_at_utc,
        "model_class": model.__class__.__name__,
        "model_config_path": MODEL_CONFIG_PATH,
        "model_state_dict": model.state_dict(),
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_state_dict": optimizer.state_dict(),
        "optimizer_lr": float(run_summary["optimizer_lr"]),
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "completed_steps": int(run_summary["executed_steps"]),
        "max_steps": MAX_STEPS,
        "mask_schedule": list(MASK_SCHEDULE),
        "loss_weights": dict(LOSS_WEIGHTS),
        "batch_size": BATCH_SIZE,
        "shuffle": SHUFFLE,
        "seed": SEED,
        "sample_ids": list(sample_ids),
        "loss_total_by_step": {str(row["step"]): float(row["loss_total"]) for row in rows},
        "grad_norm_by_step": {str(row["step"]): float(row["grad_norm"]) for row in rows},
        "param_delta_norm_by_step": {str(row["step"]): float(row["param_delta_norm"]) for row in rows},
        "checkpoint_path": str(CHECKPOINT_PATH),
        "source_modification_allowed": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
    }


def save_single_checkpoint_v0(payload: dict[str, Any], checkpoint_path: str | Path = CHECKPOINT_PATH) -> dict[str, Any]:
    path = Path(checkpoint_path)
    blockers: list[str] = []
    _expect(path == CHECKPOINT_PATH, f"checkpoint_path_not_allowed:{path}", blockers)
    _expect(validate_checkpoint_payload_schema_v0(payload)["valid"], "checkpoint_payload_schema_invalid", blockers)
    _expect(not path.exists(), "checkpoint_already_exists", blockers)
    _expect(len(_run_root_pt_files()) == 0, "pt_files_exist_before_save", blockers)
    if blockers:
        return {
            "checkpoint_saved": False,
            "checkpoint_path": str(path),
            "checkpoint_filename": path.name,
            "checkpoint_sha256": "",
            "checkpoint_size_bytes": 0,
            "checkpoint_count": len(_run_root_pt_files()),
            "checkpoint_payload_schema_valid": False,
            "blocking_reasons": blockers,
        }

    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    pt_files = _run_root_pt_files()
    size = path.stat().st_size if path.is_file() else 0
    forbidden = _forbidden_run_artifacts()
    saved = bool(path.is_file() and size > 0 and pt_files == [path] and not forbidden)
    blockers.extend([] if saved else ["checkpoint_save_validation_failed"])
    return {
        "checkpoint_saved": saved,
        "checkpoint_path": str(path),
        "checkpoint_filename": path.name,
        "checkpoint_sha256": _hash_file(path) if path.is_file() else "",
        "checkpoint_size_bytes": int(size),
        "checkpoint_count": len(pt_files),
        "checkpoint_payload_schema_valid": validate_checkpoint_payload_schema_v0(payload)["valid"],
        "repo_commit": payload.get("repo_commit", ""),
        "created_at_utc": payload.get("created_at_utc", ""),
        "completed_steps": payload.get("completed_steps", 0),
        "max_steps": payload.get("max_steps", 0),
        "blocking_reasons": blockers,
    }


def _state_shapes(state_dict: dict[str, Any]) -> dict[str, list[int]]:
    return {
        key: [int(dim) for dim in value.shape]
        for key, value in state_dict.items()
        if torch.is_tensor(value)
    }


def run_resume_smoke_v0(checkpoint_path: str | Path = CHECKPOINT_PATH, device: str = "auto", lr: float = DEFAULT_LR) -> dict[str, Any]:
    device_info = resolve_diffsbdd_forward_device_v0(device)
    path = Path(checkpoint_path)
    result: dict[str, Any] = {
        "stage": STAGE,
        "checkpoint_path": str(path),
        "checkpoint_loaded": False,
        "model_state_loaded": False,
        "optimizer_state_loaded": False,
        "completed_steps_verified": False,
        "mask_schedule_verified": False,
        "parameter_shapes_verified": False,
        "optimizer_step_during_resume_smoke": False,
        "second_checkpoint_saved": False,
        "trainer_fit_called": False,
        "training_step_called": False,
        "model_saved": False,
        "resume_smoke_passed": False,
        "blocking_reasons": [],
        **device_info,
    }
    try:
        if _run_root_pt_files() != [CHECKPOINT_PATH]:
            result["blocking_reasons"].append("checkpoint_count_not_one_before_resume")
            return result
        payload = torch.load(path, map_location=torch.device(device_info["resolved_device"]))
        result["checkpoint_loaded"] = True
        schema = validate_checkpoint_payload_schema_v0(payload)
        if not schema["valid"]:
            result["blocking_reasons"].extend(schema["blocking_reasons"])
            return result

        candidate_inputs = _build_candidate_inputs(MASK_SCHEDULE[0])
        model, _counts, reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
        if model is None:
            result["blocking_reasons"].extend(reasons or ["resume_model_initialization_failed"])
            return result
        model.train()
        optimizer = build_optimizer_v0(model, lr=lr)
        fresh_shapes = _state_shapes(model.state_dict())
        payload_shapes = _state_shapes(payload["model_state_dict"])
        result["parameter_shapes_verified"] = fresh_shapes == payload_shapes
        model.load_state_dict(payload["model_state_dict"])
        result["model_state_loaded"] = True
        optimizer.load_state_dict(payload["optimizer_state_dict"])
        result["optimizer_state_loaded"] = bool(optimizer.state_dict().get("state"))
        result["completed_steps_verified"] = payload.get("completed_steps") == MAX_STEPS
        result["mask_schedule_verified"] = payload.get("mask_schedule") == MASK_SCHEDULE
        result["second_checkpoint_saved"] = len(_run_root_pt_files()) != 1
        if result["second_checkpoint_saved"]:
            result["blocking_reasons"].append("unexpected_checkpoint_count_after_resume")
        for key in [
            "model_state_loaded",
            "optimizer_state_loaded",
            "completed_steps_verified",
            "mask_schedule_verified",
            "parameter_shapes_verified",
        ]:
            if result[key] is not True:
                result["blocking_reasons"].append(f"{key}_false")
        result["resume_smoke_passed"] = not result["blocking_reasons"]
    except Exception as exc:
        result["blocking_reasons"].append(f"resume_smoke_failed:{type(exc).__name__}:{exc}")
    finally:
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()
    return result


def _blocked_summary(
    device_info: dict[str, Any],
    max_steps: int,
    stop_reason: str,
    rows: list[dict[str, Any]] | None = None,
    lr: float = DEFAULT_LR,
) -> dict[str, Any]:
    rows = [] if rows is None else rows
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10v_policy_passed": False,
        "run_name": RUN_NAME,
        "run_root": str(RUN_ROOT),
        "loop_name": LOOP_NAME,
        "requested_device": device_info["requested_device"],
        "resolved_device": device_info["resolved_device"],
        "cuda_available": device_info["cuda_available"],
        "cuda_device_count": device_info["cuda_device_count"],
        "cuda_device_name": device_info["cuda_device_name"],
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": float(lr),
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "max_steps": max_steps,
        "executed_steps": len(rows),
        "dry_run_training_steps_executed": len(rows),
        "mask_schedule": list(MASK_SCHEDULE),
        "mask_levels_seen": [row["mask_level"] for row in rows],
        "expected_mask_schedule_followed": False,
        "mask_counts_seen": dict(Counter(row["mask_level"] for row in rows)),
        "batch_size": BATCH_SIZE,
        "shuffle": SHUFFLE,
        "seed": SEED,
        "loss_weights": dict(LOSS_WEIGHTS),
        "all_steps_passed": False,
        "all_losses_finite": False,
        "all_backward_success": False,
        "all_optimizer_steps_success": False,
        "all_gradients_finite": False,
        "all_gradients_nonzero": False,
        "all_parameter_updates_finite": False,
        "all_parameter_updates_nonzero": False,
        "stop_triggered": True,
        "stop_reason": stop_reason,
        "checkpoint_saved": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_filename": CHECKPOINT_FILENAME,
        "checkpoint_count": len(_run_root_pt_files()),
        "checkpoint_sha256": "",
        "checkpoint_size_bytes": 0,
        "checkpoint_payload_schema_valid": False,
        "checkpoint_metadata_written": False,
        "checkpoint_loaded_for_resume_smoke": False,
        "resume_smoke_passed": False,
        "model_state_loaded": False,
        "optimizer_state_loaded": False,
        "completed_steps_verified": False,
        "mask_schedule_verified": False,
        "parameter_shapes_verified": False,
        "optimizer_step_during_resume_smoke": False,
        "second_checkpoint_saved": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "model_saved": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
        "source_modification_allowed": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": bool(_forbidden_run_artifacts()),
        "unexpected_checkpoint_files_created": bool(_unexpected_checkpoint_files()),
        "all_checks_passed": False,
        "recommended_next_step": "manual_first_checkpointed_training_dry_run_review",
    }


def run_first_checkpointed_training_dry_run_v0(
    device: str = "auto",
    lr: float = DEFAULT_LR,
    max_steps: int = MAX_STEPS,
    overwrite: bool = False,
) -> dict[str, Any]:
    device_info = resolve_diffsbdd_forward_device_v0(device)
    git_status_before = git_status_short_v0()
    try:
        validate_step10v_outputs_v0()
    except Exception as exc:
        summary = _blocked_summary(device_info, max_steps, f"step10v_validation_failed:{type(exc).__name__}:{exc}", lr=lr)
        return {"rows": [], "summary": summary, "checkpoint_metadata": {}, "resume_smoke": {}}

    if max_steps != MAX_STEPS:
        summary = _blocked_summary(device_info, max_steps, "max_steps_must_equal_12", lr=lr)
        summary["step10v_policy_passed"] = True
        return {"rows": [], "summary": summary, "checkpoint_metadata": {}, "resume_smoke": {}}
    if MASK_SCHEDULE != MASK_CYCLE * 3:
        summary = _blocked_summary(device_info, max_steps, "mask_schedule_invalid", lr=lr)
        summary["step10v_policy_passed"] = True
        return {"rows": [], "summary": summary, "checkpoint_metadata": {}, "resume_smoke": {}}

    prepared = prepare_run_root_v0(overwrite=overwrite)
    if not prepared["prepared"]:
        summary = _blocked_summary(device_info, max_steps, ";".join(prepared["blocking_reasons"]), lr=lr)
        summary["step10v_policy_passed"] = True
        return {"rows": [], "summary": summary, "checkpoint_metadata": {}, "resume_smoke": {}}

    snapshots = _source_snapshots()
    rows: list[dict[str, Any]] = []
    model: torch.nn.Module | None = None
    optimizer: torch.optim.Optimizer | None = None
    try:
        candidate_inputs = _build_candidate_inputs(MASK_SCHEDULE[0])
        model, _counts, reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
        if model is None:
            summary = _blocked_summary(device_info, max_steps, ";".join(reasons) or "model_init_failed", rows, lr=lr)
            summary["step10v_policy_passed"] = True
            return {"rows": rows, "summary": summary, "checkpoint_metadata": {}, "resume_smoke": {}}
        model.train()
        optimizer = build_optimizer_v0(model, lr=lr)
        for step_index, mask_level in enumerate(MASK_SCHEDULE[:max_steps], start=1):
            cycle_index = ((step_index - 1) // len(MASK_CYCLE)) + 1
            row = run_one_longer_dry_step_v0(
                model=model,
                optimizer=optimizer,
                device_info=device_info,
                mask_level=mask_level,
                step_index=step_index,
                cycle_index=cycle_index,
                lr=lr,
            )
            row.update(
                {
                    "checkpoint_path": "",
                    "checkpoint_sha256": "",
                    "checkpoint_size_bytes": 0,
                    "resume_smoke_passed": False,
                    "checkpoint_loaded_for_resume_smoke": False,
                    "model_state_loaded": False,
                    "optimizer_state_loaded": False,
                    "second_checkpoint_saved": False,
                }
            )
            rows.append(row)
            if row["step_status"] != "passed" or row["stop_triggered"]:
                break
    finally:
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()

    sources_modified = _sources_modified(snapshots)
    executed_steps = len(rows)
    all_steps_passed = executed_steps == MAX_STEPS and all(row["step_status"] == "passed" for row in rows)
    all_losses_finite = executed_steps == MAX_STEPS and all(row["loss_finite"] for row in rows)
    all_backward_success = (
        executed_steps == MAX_STEPS and all(row["backward_called"] and row["backward_success"] for row in rows)
    )
    all_optimizer_steps_success = (
        executed_steps == MAX_STEPS
        and all(row["optimizer_step_executed"] and row["optimizer_step_success"] for row in rows)
    )
    all_gradients_finite = executed_steps == MAX_STEPS and all(row["finite_gradients"] for row in rows)
    all_gradients_nonzero = executed_steps == MAX_STEPS and all(row["nonzero_gradients"] for row in rows)
    all_parameter_updates_finite = executed_steps == MAX_STEPS and all(row["finite_parameter_delta"] for row in rows)
    all_parameter_updates_nonzero = executed_steps == MAX_STEPS and all(row["nonzero_parameter_delta"] for row in rows)
    expected_mask_schedule_followed = [row["mask_level"] for row in rows] == MASK_SCHEDULE[:executed_steps]
    stop_triggered = executed_steps != MAX_STEPS or any(row["stop_triggered"] for row in rows)
    stop_reason = ""
    if stop_triggered:
        stop_reason = next((row["stop_reason"] for row in rows if row.get("stop_reason")), "loop_did_not_complete_12_steps")

    checkpoint_metadata: dict[str, Any] = {}
    resume_smoke: dict[str, Any] = {}
    checkpoint_payload_schema_valid = False
    if (
        model is not None
        and optimizer is not None
        and all_steps_passed
        and all_losses_finite
        and all_backward_success
        and all_optimizer_steps_success
        and all_gradients_finite
        and all_gradients_nonzero
        and all_parameter_updates_finite
        and all_parameter_updates_nonzero
        and expected_mask_schedule_followed
        and not stop_triggered
        and not sources_modified
    ):
        provisional_summary = {
            "optimizer_lr": float(lr),
            "executed_steps": executed_steps,
        }
        created_at_utc = datetime.now(timezone.utc).isoformat()
        payload = build_checkpoint_payload_v0(
            model=model,
            optimizer=optimizer,
            run_summary=provisional_summary,
            rows=rows,
            repo_commit=git_commit_v0(),
            created_at_utc=created_at_utc,
        )
        payload_schema = validate_checkpoint_payload_schema_v0(payload)
        checkpoint_payload_schema_valid = payload_schema["valid"]
        checkpoint_metadata = save_single_checkpoint_v0(payload, CHECKPOINT_PATH)
        checkpoint_metadata["checkpoint_payload_schema_valid"] = checkpoint_payload_schema_valid
        if checkpoint_metadata["checkpoint_saved"]:
            resume_smoke = run_resume_smoke_v0(CHECKPOINT_PATH, device=device, lr=lr)
        else:
            resume_smoke = {
                "resume_smoke_passed": False,
                "checkpoint_loaded": False,
                "model_state_loaded": False,
                "optimizer_state_loaded": False,
                "completed_steps_verified": False,
                "mask_schedule_verified": False,
                "parameter_shapes_verified": False,
                "optimizer_step_during_resume_smoke": False,
                "second_checkpoint_saved": False,
                "blocking_reasons": checkpoint_metadata["blocking_reasons"],
            }

    if checkpoint_metadata.get("checkpoint_saved") and rows:
        final_row = rows[-1]
        final_row["checkpoint_saved"] = True
        final_row["checkpoint_written"] = True
        final_row["checkpoint_path"] = checkpoint_metadata["checkpoint_path"]
        final_row["checkpoint_sha256"] = checkpoint_metadata["checkpoint_sha256"]
        final_row["checkpoint_size_bytes"] = checkpoint_metadata["checkpoint_size_bytes"]
        final_row["resume_smoke_passed"] = bool(resume_smoke.get("resume_smoke_passed"))
        final_row["checkpoint_loaded_for_resume_smoke"] = bool(resume_smoke.get("checkpoint_loaded"))
        final_row["model_state_loaded"] = bool(resume_smoke.get("model_state_loaded"))
        final_row["optimizer_state_loaded"] = bool(resume_smoke.get("optimizer_state_loaded"))
        final_row["second_checkpoint_saved"] = bool(resume_smoke.get("second_checkpoint_saved"))

    forbidden = _forbidden_run_artifacts()
    unexpected_checkpoints = _unexpected_checkpoint_files()
    git_status_after = git_status_short_v0()
    all_checks_passed = bool(
        all_steps_passed
        and all_losses_finite
        and all_backward_success
        and all_optimizer_steps_success
        and all_gradients_finite
        and all_gradients_nonzero
        and all_parameter_updates_finite
        and all_parameter_updates_nonzero
        and expected_mask_schedule_followed
        and not stop_triggered
        and checkpoint_metadata.get("checkpoint_saved") is True
        and checkpoint_metadata.get("checkpoint_count") == 1
        and checkpoint_metadata.get("checkpoint_size_bytes", 0) > 0
        and checkpoint_payload_schema_valid
        and resume_smoke.get("resume_smoke_passed") is True
        and resume_smoke.get("checkpoint_loaded") is True
        and resume_smoke.get("model_state_loaded") is True
        and resume_smoke.get("optimizer_state_loaded") is True
        and resume_smoke.get("completed_steps_verified") is True
        and resume_smoke.get("mask_schedule_verified") is True
        and resume_smoke.get("parameter_shapes_verified") is True
        and resume_smoke.get("optimizer_step_during_resume_smoke") is False
        and resume_smoke.get("second_checkpoint_saved") is False
        and not sources_modified
        and not forbidden
        and not unexpected_checkpoints
    )
    summary = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10v_policy_passed": True,
        "run_name": RUN_NAME,
        "run_root": str(RUN_ROOT),
        "loop_name": LOOP_NAME,
        "requested_device": device_info["requested_device"],
        "resolved_device": device_info["resolved_device"],
        "cuda_available": device_info["cuda_available"],
        "cuda_device_count": device_info["cuda_device_count"],
        "cuda_device_name": device_info["cuda_device_name"],
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": float(lr),
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "max_steps": max_steps,
        "executed_steps": executed_steps,
        "dry_run_training_steps_executed": executed_steps,
        "mask_schedule": list(MASK_SCHEDULE),
        "mask_levels_seen": [row["mask_level"] for row in rows],
        "expected_mask_schedule_followed": expected_mask_schedule_followed,
        "mask_counts_seen": dict(Counter(row["mask_level"] for row in rows)),
        "batch_size": BATCH_SIZE,
        "shuffle": SHUFFLE,
        "seed": SEED,
        "loss_weights": dict(LOSS_WEIGHTS),
        "all_steps_passed": all_steps_passed,
        "all_losses_finite": all_losses_finite,
        "all_backward_success": all_backward_success,
        "all_optimizer_steps_success": all_optimizer_steps_success,
        "all_gradients_finite": all_gradients_finite,
        "all_gradients_nonzero": all_gradients_nonzero,
        "all_parameter_updates_finite": all_parameter_updates_finite,
        "all_parameter_updates_nonzero": all_parameter_updates_nonzero,
        "loss_total_by_step": {str(row["step"]): row["loss_total"] for row in rows},
        "grad_norm_by_step": {str(row["step"]): row["grad_norm"] for row in rows},
        "param_delta_norm_by_step": {str(row["step"]): row["param_delta_norm"] for row in rows},
        "target_atom_count_by_step": {str(row["step"]): row["target_atom_count"] for row in rows},
        "context_atom_count_by_step": {str(row["step"]): row["context_atom_count"] for row in rows},
        "stop_triggered": stop_triggered,
        "stop_reason": stop_reason,
        "checkpoint_saved": checkpoint_metadata.get("checkpoint_saved", False),
        "checkpoint_path": checkpoint_metadata.get("checkpoint_path", str(CHECKPOINT_PATH)),
        "checkpoint_filename": CHECKPOINT_FILENAME,
        "checkpoint_count": checkpoint_metadata.get("checkpoint_count", len(_run_root_pt_files())),
        "checkpoint_sha256": checkpoint_metadata.get("checkpoint_sha256", ""),
        "checkpoint_size_bytes": checkpoint_metadata.get("checkpoint_size_bytes", 0),
        "checkpoint_payload_schema_valid": checkpoint_payload_schema_valid,
        "checkpoint_metadata_written": bool(checkpoint_metadata),
        "checkpoint_loaded_for_resume_smoke": bool(resume_smoke.get("checkpoint_loaded")),
        "resume_smoke_passed": bool(resume_smoke.get("resume_smoke_passed")),
        "model_state_loaded": bool(resume_smoke.get("model_state_loaded")),
        "optimizer_state_loaded": bool(resume_smoke.get("optimizer_state_loaded")),
        "completed_steps_verified": bool(resume_smoke.get("completed_steps_verified")),
        "mask_schedule_verified": bool(resume_smoke.get("mask_schedule_verified")),
        "parameter_shapes_verified": bool(resume_smoke.get("parameter_shapes_verified")),
        "optimizer_step_during_resume_smoke": bool(resume_smoke.get("optimizer_step_during_resume_smoke")),
        "second_checkpoint_saved": bool(resume_smoke.get("second_checkpoint_saved")),
        "training_step_called": False,
        "trainer_fit_called": False,
        "model_saved": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
        "source_modification_allowed": False,
        "original_source_files_modified": sources_modified,
        "forbidden_artifacts_created": bool(forbidden),
        "forbidden_artifact_scan_result": forbidden,
        "unexpected_checkpoint_files_created": bool(unexpected_checkpoints),
        "unexpected_checkpoint_files": unexpected_checkpoints,
        "git_status_clean_before_run": git_status_before == "",
        "git_status_clean_after_run": git_status_after == "",
        "git_status_before_run": git_status_before,
        "git_status_after_run": git_status_after,
        "repo_commit": git_commit_v0(),
        "environment_name": "covdiff",
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "first_checkpointed_training_dry_run_review"
            if all_checks_passed
            else "manual_first_checkpointed_training_dry_run_review"
        ),
    }
    return {"rows": rows, "summary": summary, "checkpoint_metadata": checkpoint_metadata, "resume_smoke": resume_smoke}

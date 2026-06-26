from __future__ import annotations

import csv
import hashlib
import inspect
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "first_checkpointed_training_dry_run_review_v0"
PREVIOUS_STAGE = "first_checkpointed_training_dry_run_v0"
RUN_NAME = "first_checkpointed_training_dry_run_v0"
RUN_ROOT = Path("data/derived/covalent_small/training_runs/first_checkpointed_training_dry_run_v0")
REPORT_CSV = RUN_ROOT / "reports" / "first_checkpointed_training_dry_run_report.csv"
MANIFEST_JSON = RUN_ROOT / "metadata" / "first_checkpointed_training_dry_run_manifest.json"
CHECKPOINT_METADATA_JSON = RUN_ROOT / "metadata" / "checkpoint_metadata.json"
RESUME_REPORT_CSV = RUN_ROOT / "resume_smoke" / "resume_smoke_report.csv"
RESUME_MANIFEST_JSON = RUN_ROOT / "resume_smoke" / "resume_smoke_manifest.json"
SUMMARY_MD = Path("docs/first_checkpointed_training_dry_run_v0_summary.md")
REVIEW_REPORT_CSV = RUN_ROOT / "reports" / "first_checkpointed_training_dry_run_review_report.csv"
REVIEW_MANIFEST_JSON = RUN_ROOT / "metadata" / "first_checkpointed_training_dry_run_review_manifest.json"
LOCAL_CHECKPOINT_REVIEW_JSON = RUN_ROOT / "metadata" / "local_checkpoint_artifact_review.json"
REVIEW_SUMMARY_MD = Path("docs/first_checkpointed_training_dry_run_review_v0_summary.md")
CHECKPOINT_FILENAME = "checkpoint_step_000012.pt"
CHECKPOINT_PATH = RUN_ROOT / "checkpoints" / CHECKPOINT_FILENAME
EXPECTED_CHECKPOINT_SHA256 = "c121b6555f1b29f70bcc53a09cecff32fb7c3a5ad72a291d44de1052c5ef72e4"
EXPECTED_CHECKPOINT_SIZE_BYTES = 58022805
MASK_CYCLE = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
MASK_SCHEDULE = MASK_CYCLE * 3
EXPECTED_MASK_COUNTS = {mask_level: 3 for mask_level in MASK_CYCLE}
FORBIDDEN_RUN_SUFFIXES = {".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
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


def _bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def _hash_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _path_is_tracked(path: str | Path) -> bool:
    return _git(["git", "ls-files", "--error-unmatch", str(path)]).returncode == 0


def _path_is_staged(path: str | Path) -> bool:
    staged = _git(["git", "diff", "--cached", "--name-only"]).stdout.splitlines()
    return str(path) in staged


def _path_is_ignored(path: str | Path) -> bool:
    return _git(["git", "check-ignore", "-q", str(path)]).returncode == 0


def _pt_files_under_run_root() -> list[str]:
    if not RUN_ROOT.exists():
        return []
    return sorted(str(path) for path in RUN_ROOT.rglob("*.pt") if path.is_file())


def _forbidden_artifacts_under_run_root() -> list[str]:
    if not RUN_ROOT.exists():
        return []
    return sorted(
        str(path)
        for path in RUN_ROOT.rglob("*")
        if path.is_file() and (path.suffix in FORBIDDEN_RUN_SUFFIXES or (path.suffix == ".pt" and path != CHECKPOINT_PATH))
    )


def _source_diff_exists() -> bool:
    unstaged = _git(["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"])
    staged = _git(["git", "diff", "--cached", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"])
    return unstaged.returncode != 0 or staged.returncode != 0


def _parse_mask_counts(value: Any) -> dict[str, int]:
    return {str(key): int(child) for key, child in dict(value).items()}


def _as_bool(value: str) -> bool:
    return str(value).lower() == "true"


def validate_step10w_outputs_v0(require_local_checkpoint: bool = True) -> bool:
    blockers: list[str] = []
    for path in [REPORT_CSV, MANIFEST_JSON, CHECKPOINT_METADATA_JSON, RESUME_REPORT_CSV, RESUME_MANIFEST_JSON, SUMMARY_MD]:
        _expect(path.is_file(), f"missing_step10w_file:{path}", blockers)
    if blockers:
        raise FileNotFoundError(";".join(blockers))

    report_rows = _rows_from_csv(REPORT_CSV)
    _expect(len(report_rows) == 12, f"report_row_count_invalid:{len(report_rows)}", blockers)
    _expect([row.get("step") for row in report_rows] == [str(index) for index in range(1, 13)], "report_steps_invalid", blockers)
    _expect([row.get("mask_level") for row in report_rows] == MASK_SCHEDULE, "report_mask_schedule_invalid", blockers)
    checkpoint_saved_steps = [row.get("step") for row in report_rows if row.get("checkpoint_saved") == "true"]
    checkpoint_written_steps = [row.get("step") for row in report_rows if row.get("checkpoint_written") == "true"]
    _expect(checkpoint_saved_steps == ["12"], f"checkpoint_saved_steps_invalid:{checkpoint_saved_steps}", blockers)
    _expect(checkpoint_written_steps == ["12"], f"checkpoint_written_steps_invalid:{checkpoint_written_steps}", blockers)
    for row in report_rows:
        step = row.get("step")
        for key in ["step_status", "loss_finite", "backward_success", "optimizer_step_success", "finite_gradients", "finite_parameter_delta"]:
            expected = "passed" if key == "step_status" else "true"
            _expect(row.get(key) == expected, f"report_step_{step}_{key}_invalid:{row.get(key)!r}", blockers)
        for key in ["training_step_called", "trainer_fit_called", "model_saved", "formal_training_executed", "real_finetune_executed"]:
            _expect(row.get(key) == "false", f"report_step_{step}_{key}_invalid:{row.get(key)!r}", blockers)

    manifest = _load_json(MANIFEST_JSON)
    manifest_expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "checkpoint_output_policy_design_v0",
        "step10v_policy_passed": True,
        "run_name": RUN_NAME,
        "max_steps": 12,
        "executed_steps": 12,
        "dry_run_training_steps_executed": 12,
        "mask_schedule": MASK_SCHEDULE,
        "mask_counts_seen": EXPECTED_MASK_COUNTS,
        "all_steps_passed": True,
        "all_losses_finite": True,
        "all_backward_success": True,
        "all_optimizer_steps_success": True,
        "all_gradients_finite": True,
        "all_gradients_nonzero": True,
        "all_parameter_updates_finite": True,
        "all_parameter_updates_nonzero": True,
        "checkpoint_saved": True,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_filename": CHECKPOINT_FILENAME,
        "checkpoint_count": 1,
        "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "checkpoint_size_bytes": EXPECTED_CHECKPOINT_SIZE_BYTES,
        "checkpoint_payload_schema_valid": True,
        "checkpoint_metadata_written": True,
        "checkpoint_loaded_for_resume_smoke": True,
        "resume_smoke_passed": True,
        "model_state_loaded": True,
        "optimizer_state_loaded": True,
        "completed_steps_verified": True,
        "mask_schedule_verified": True,
        "parameter_shapes_verified": True,
        "optimizer_step_during_resume_smoke": False,
        "second_checkpoint_saved": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "model_saved": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "unexpected_checkpoint_files_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "first_checkpointed_training_dry_run_review",
    }
    for key, expected in manifest_expected.items():
        _expect(manifest.get(key) == expected, f"manifest_{key}_invalid:{manifest.get(key)!r}", blockers)

    checkpoint_metadata = _load_json(CHECKPOINT_METADATA_JSON)
    checkpoint_expected = {
        "checkpoint_saved": True,
        "checkpoint_filename": CHECKPOINT_FILENAME,
        "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "checkpoint_size_bytes": EXPECTED_CHECKPOINT_SIZE_BYTES,
        "checkpoint_payload_schema_valid": True,
        "completed_steps": 12,
        "max_steps": 12,
        "source_modification_allowed": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
    }
    for key, expected in checkpoint_expected.items():
        _expect(checkpoint_metadata.get(key) == expected, f"checkpoint_metadata_{key}_invalid:{checkpoint_metadata.get(key)!r}", blockers)

    resume_rows = _rows_from_csv(RESUME_REPORT_CSV)
    _expect(len(resume_rows) == 1, f"resume_report_row_count_invalid:{len(resume_rows)}", blockers)
    resume_manifest = _load_json(RESUME_MANIFEST_JSON)
    resume_expected = {
        "checkpoint_loaded": True,
        "model_state_loaded": True,
        "optimizer_state_loaded": True,
        "completed_steps_verified": True,
        "mask_schedule_verified": True,
        "parameter_shapes_verified": True,
        "optimizer_step_during_resume_smoke": False,
        "second_checkpoint_saved": False,
        "trainer_fit_called": False,
        "training_step_called": False,
        "model_saved": False,
        "resume_smoke_passed": True,
    }
    for key, expected in resume_expected.items():
        _expect(resume_manifest.get(key) == expected, f"resume_manifest_{key}_invalid:{resume_manifest.get(key)!r}", blockers)
        if resume_rows:
            _expect(resume_rows[0].get(key) == _bool_text(expected), f"resume_report_{key}_invalid:{resume_rows[0].get(key)!r}", blockers)

    if require_local_checkpoint:
        _expect(CHECKPOINT_PATH.is_file(), "local_checkpoint_missing", blockers)
        if CHECKPOINT_PATH.is_file():
            _expect(_hash_file(CHECKPOINT_PATH) == EXPECTED_CHECKPOINT_SHA256, "local_checkpoint_sha256_mismatch", blockers)
            _expect(CHECKPOINT_PATH.stat().st_size == EXPECTED_CHECKPOINT_SIZE_BYTES, "local_checkpoint_size_mismatch", blockers)
        pt_files = _pt_files_under_run_root()
        _expect(pt_files == [str(CHECKPOINT_PATH)], f"run_root_pt_files_invalid:{pt_files}", blockers)
        _expect(not _forbidden_artifacts_under_run_root(), "forbidden_artifacts_under_run_root", blockers)
        _expect(not _path_is_tracked(CHECKPOINT_PATH), "checkpoint_tracked_by_git", blockers)
        _expect(_path_is_ignored(CHECKPOINT_PATH) or not _path_is_staged(CHECKPOINT_PATH), "checkpoint_not_ignored_or_staged", blockers)

    if blockers:
        raise ValueError(";".join(blockers))
    return True


def _local_checkpoint_artifact_review(require_local_checkpoint: bool) -> dict[str, Any]:
    present = CHECKPOINT_PATH.is_file()
    local_sha = _hash_file(CHECKPOINT_PATH) if present else ""
    local_size = int(CHECKPOINT_PATH.stat().st_size) if present else 0
    tracked = _path_is_tracked(CHECKPOINT_PATH)
    staged = _path_is_staged(CHECKPOINT_PATH)
    ignored_or_untracked = _path_is_ignored(CHECKPOINT_PATH) or (not tracked and not staged)
    pt_files = _pt_files_under_run_root()
    forbidden = _forbidden_artifacts_under_run_root()
    passed = bool(
        (present or not require_local_checkpoint)
        and local_sha == EXPECTED_CHECKPOINT_SHA256
        and local_size == EXPECTED_CHECKPOINT_SIZE_BYTES
        and pt_files == [str(CHECKPOINT_PATH)]
        and not forbidden
        and not tracked
        and not staged
        and ignored_or_untracked
    )
    return {
        "checkpoint_path": str(CHECKPOINT_PATH),
        "local_checkpoint_present": present,
        "local_checkpoint_sha256": local_sha,
        "expected_checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "local_checkpoint_sha256_matches": local_sha == EXPECTED_CHECKPOINT_SHA256,
        "local_checkpoint_size_bytes": local_size,
        "expected_checkpoint_size_bytes": EXPECTED_CHECKPOINT_SIZE_BYTES,
        "local_checkpoint_size_matches": local_size == EXPECTED_CHECKPOINT_SIZE_BYTES,
        "checkpoint_tracked_by_git": tracked,
        "checkpoint_staged_by_git": staged,
        "checkpoint_ignored_or_untracked": ignored_or_untracked,
        "run_root_pt_files": pt_files,
        "forbidden_artifacts_under_run_root": forbidden,
        "local_checkpoint_review_passed": passed,
        "checkpoint_git_commit_allowed": False,
        "checkpoint_keep_local_only": True,
    }


def summarize_step10w_evidence_v0(require_local_checkpoint: bool = True) -> dict[str, Any]:
    validate_step10w_outputs_v0(require_local_checkpoint=require_local_checkpoint)
    report_rows = _rows_from_csv(REPORT_CSV)
    manifest = _load_json(MANIFEST_JSON)
    checkpoint_metadata = _load_json(CHECKPOINT_METADATA_JSON)
    resume_manifest = _load_json(RESUME_MANIFEST_JSON)
    artifact = _local_checkpoint_artifact_review(require_local_checkpoint=require_local_checkpoint)
    warning_steps = [row["step"] for row in report_rows if row.get("warning_triggered") == "true"]
    return {
        "step10w_run_passed": True,
        "executed_steps": manifest["executed_steps"],
        "dry_run_training_steps_executed": manifest["dry_run_training_steps_executed"],
        "mask_schedule": manifest["mask_schedule"],
        "mask_counts_seen": _parse_mask_counts(manifest["mask_counts_seen"]),
        "all_steps_passed": manifest["all_steps_passed"],
        "all_losses_finite": manifest["all_losses_finite"],
        "all_backward_success": manifest["all_backward_success"],
        "all_optimizer_steps_success": manifest["all_optimizer_steps_success"],
        "all_gradients_finite": manifest["all_gradients_finite"],
        "all_parameter_updates_finite": manifest["all_parameter_updates_finite"],
        "warning_steps": warning_steps,
        "warnings_triggered": bool(warning_steps),
        "stop_triggered": manifest["stop_triggered"],
        "checkpoint_saved": manifest["checkpoint_saved"],
        "checkpoint_path": manifest["checkpoint_path"],
        "checkpoint_filename": manifest["checkpoint_filename"],
        "checkpoint_count": manifest["checkpoint_count"],
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "checkpoint_size_bytes": manifest["checkpoint_size_bytes"],
        "checkpoint_payload_schema_valid": manifest["checkpoint_payload_schema_valid"],
        "checkpoint_metadata_written": manifest["checkpoint_metadata_written"],
        "checkpoint_loaded_for_resume_smoke": manifest["checkpoint_loaded_for_resume_smoke"],
        "resume_smoke_passed": resume_manifest["resume_smoke_passed"],
        "model_state_loaded": resume_manifest["model_state_loaded"],
        "optimizer_state_loaded": resume_manifest["optimizer_state_loaded"],
        "completed_steps_verified": resume_manifest["completed_steps_verified"],
        "mask_schedule_verified": resume_manifest["mask_schedule_verified"],
        "parameter_shapes_verified": resume_manifest["parameter_shapes_verified"],
        "second_checkpoint_saved": resume_manifest["second_checkpoint_saved"],
        "training_step_called": manifest["training_step_called"],
        "trainer_fit_called": manifest["trainer_fit_called"],
        "model_saved": manifest["model_saved"],
        "formal_training_executed": manifest["formal_training_executed"],
        "real_finetune_executed": manifest["real_finetune_executed"],
        "forbidden_artifacts_created": manifest["forbidden_artifacts_created"],
        "unexpected_checkpoint_files_created": manifest["unexpected_checkpoint_files_created"],
        "checkpoint_metadata": checkpoint_metadata,
        "local_checkpoint_present": artifact["local_checkpoint_present"],
        "local_checkpoint_sha256": artifact["local_checkpoint_sha256"],
        "local_checkpoint_size_bytes": artifact["local_checkpoint_size_bytes"],
        "local_checkpoint_sha256_matches": artifact["local_checkpoint_sha256_matches"],
        "local_checkpoint_size_matches": artifact["local_checkpoint_size_matches"],
        "checkpoint_tracked_by_git": artifact["checkpoint_tracked_by_git"],
        "checkpoint_staged_by_git": artifact["checkpoint_staged_by_git"],
        "checkpoint_ignored_or_untracked": artifact["checkpoint_ignored_or_untracked"],
        "local_checkpoint_review_passed": artifact["local_checkpoint_review_passed"],
        "git_status_clean_before_run": manifest["git_status_clean_before_run"],
        "git_status_clean_after_run": manifest["git_status_clean_after_run"],
        "grad_norm_by_step": manifest["grad_norm_by_step"],
        "artifact_review": artifact,
    }


def _torch_load_cpu(checkpoint_path: str | Path) -> tuple[Any, bool]:
    path = Path(checkpoint_path)
    try:
        if "weights_only" in inspect.signature(torch.load).parameters:
            return torch.load(path, map_location="cpu", weights_only=True), True
    except TypeError:
        pass
    return torch.load(path, map_location="cpu"), False


def inspect_checkpoint_payload_schema_v0(checkpoint_path: str | Path = CHECKPOINT_PATH) -> dict[str, Any]:
    result: dict[str, Any] = {
        "checkpoint_path": str(checkpoint_path),
        "payload_schema_reviewed": False,
        "payload_load_used_weights_only": False,
        "payload_is_dict": False,
        "model_state_dict_present": False,
        "optimizer_state_dict_present": False,
        "completed_steps_verified": False,
        "max_steps_verified": False,
        "mask_schedule_verified": False,
        "source_modification_allowed_false": False,
        "formal_training_executed_false": False,
        "real_finetune_executed_false": False,
        "forbidden_payload_keys_absent": False,
        "payload_review_passed": False,
        "blocking_reasons": [],
    }
    try:
        payload, used_weights_only = _torch_load_cpu(checkpoint_path)
        result["payload_schema_reviewed"] = True
        result["payload_load_used_weights_only"] = used_weights_only
        result["payload_is_dict"] = isinstance(payload, dict)
        if not result["payload_is_dict"]:
            result["blocking_reasons"].append("payload_not_dict")
            return result
        result["model_state_dict_present"] = isinstance(payload.get("model_state_dict"), dict)
        result["optimizer_state_dict_present"] = isinstance(payload.get("optimizer_state_dict"), dict)
        result["completed_steps_verified"] = payload.get("completed_steps") == 12
        result["max_steps_verified"] = payload.get("max_steps") == 12
        result["mask_schedule_verified"] = payload.get("mask_schedule") == MASK_SCHEDULE
        result["source_modification_allowed_false"] = payload.get("source_modification_allowed") is False
        result["formal_training_executed_false"] = payload.get("formal_training_executed") is False
        result["real_finetune_executed_false"] = payload.get("real_finetune_executed") is False
        forbidden_present = sorted(FORBIDDEN_PAYLOAD_KEYS.intersection(payload.keys()))
        result["forbidden_payload_keys_absent"] = not forbidden_present
        for key in [
            "model_state_dict_present",
            "optimizer_state_dict_present",
            "completed_steps_verified",
            "max_steps_verified",
            "mask_schedule_verified",
            "source_modification_allowed_false",
            "formal_training_executed_false",
            "real_finetune_executed_false",
            "forbidden_payload_keys_absent",
        ]:
            if result[key] is not True:
                result["blocking_reasons"].append(f"{key}_false")
        if forbidden_present:
            result["blocking_reasons"].append(f"forbidden_payload_keys_present:{';'.join(forbidden_present)}")
        result["payload_review_passed"] = not result["blocking_reasons"]
    except Exception as exc:
        result["blocking_reasons"].append(f"payload_schema_review_failed:{type(exc).__name__}:{exc}")
    return result


def assess_first_checkpointed_dry_run_v0(evidence: dict[str, Any], payload_review: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    checkpoint_artifact_passed = bool(
        evidence["checkpoint_saved"]
        and evidence["checkpoint_count"] == 1
        and evidence["local_checkpoint_present"]
        and evidence["local_checkpoint_sha256_matches"]
        and evidence["local_checkpoint_size_matches"]
        and not evidence["checkpoint_tracked_by_git"]
        and not evidence["checkpoint_staged_by_git"]
        and evidence["local_checkpoint_review_passed"]
        and payload_review["payload_review_passed"]
    )
    resume_passed = bool(
        evidence["resume_smoke_passed"]
        and evidence["model_state_loaded"]
        and evidence["optimizer_state_loaded"]
        and evidence["completed_steps_verified"]
        and evidence["mask_schedule_verified"]
        and evidence["parameter_shapes_verified"]
        and not evidence["second_checkpoint_saved"]
    )
    training_boundary_passed = bool(
        not evidence["training_step_called"]
        and not evidence["trainer_fit_called"]
        and not evidence["model_saved"]
        and not evidence["formal_training_executed"]
        and not evidence["real_finetune_executed"]
        and not evidence["forbidden_artifacts_created"]
        and not evidence["unexpected_checkpoint_files_created"]
        and not _source_diff_exists()
    )
    run_passed = bool(
        evidence["step10w_run_passed"]
        and evidence["executed_steps"] == 12
        and evidence["dry_run_training_steps_executed"] == 12
        and evidence["mask_schedule"] == MASK_SCHEDULE
        and evidence["mask_counts_seen"] == EXPECTED_MASK_COUNTS
        and evidence["all_steps_passed"]
        and evidence["all_losses_finite"]
        and evidence["all_backward_success"]
        and evidence["all_optimizer_steps_success"]
        and evidence["all_gradients_finite"]
        and evidence["all_parameter_updates_finite"]
    )
    checks = {
        "run_review_failed": run_passed,
        "checkpoint_artifact_review_failed": checkpoint_artifact_passed,
        "resume_smoke_review_failed": resume_passed,
        "training_boundary_review_failed": training_boundary_passed,
    }
    blockers.extend(reason for reason, passed in checks.items() if not passed)
    return {
        "review_status": "passed" if not blockers else "blocked",
        "checkpoint_artifact_status": "passed" if checkpoint_artifact_passed else "blocked",
        "resume_smoke_status": "passed" if resume_passed else "blocked",
        "training_boundary_status": "passed" if training_boundary_passed else "blocked",
        "loss_decrease_required": False,
        "quality_claim_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "long_training_allowed": False,
        "model_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "checkpoint_git_commit_allowed": False,
        "blocking_reasons": blockers,
    }


def build_observations_v0(evidence: dict[str, Any]) -> dict[str, Any]:
    grad_by_step = {int(step): float(value) for step, value in evidence["grad_norm_by_step"].items()}
    highest_grad_step = max(grad_by_step, key=grad_by_step.get)
    highest_grad_value = grad_by_step[highest_grad_step]
    highest_grad_mask_level = MASK_SCHEDULE[highest_grad_step - 1]
    dirty_git_observation = not evidence["git_status_clean_before_run"] or not evidence["git_status_clean_after_run"]
    return {
        "checkpoint_not_committed_to_git": not evidence["checkpoint_tracked_by_git"],
        "checkpoint_kept_as_local_artifact": True,
        "checkpoint_size_bytes": evidence["checkpoint_size_bytes"],
        "checkpoint_size_observation": "large binary artifact; keep outside normal Git history",
        "git_status_clean_before_run": evidence["git_status_clean_before_run"],
        "git_status_clean_after_run": evidence["git_status_clean_after_run"],
        "git_status_observation": dirty_git_observation,
        "git_status_observation_reason": (
            "Step 10W was run before Step 10W files were committed" if dirty_git_observation else ""
        ),
        "not_blocker_for_step10w": True,
        "future_clean_run_recommended": True,
        "highest_grad_step": highest_grad_step,
        "highest_grad_mask_level": highest_grad_mask_level,
        "highest_grad_value": highest_grad_value,
        "generation_quality_claim_allowed": False,
        "loss_trend_claim_allowed": False,
    }


def build_next_boundary_decision_v0(assessment: dict[str, Any], observations: dict[str, Any]) -> dict[str, Any]:
    passed = assessment["review_status"] == "passed"
    if passed:
        return {
            "recommended_next_stage": "clean_checkpointed_dry_run_from_committed_code_design",
            "clean_checkpointed_rerun_design_allowed": True,
            "formal_training_allowed": False,
            "finetune_allowed": False,
            "long_training_allowed": False,
            "model_save_allowed": False,
            "checkpoint_git_commit_allowed": False,
            "direct_long_training_allowed": False,
            "direct_generation_quality_claim_allowed": False,
            "decision_reason": (
                "Step 10W passed, but its manifest records a non-clean git state during execution; "
                "design a clean committed-code checkpointed rerun before longer training."
            ),
            "proposed_clean_run_root": (
                "data/derived/covalent_small/training_runs/clean_checkpointed_dry_run_from_committed_code_v0/"
            ),
        }
    return {
        "recommended_next_stage": "manual_first_checkpointed_training_dry_run_review",
        "clean_checkpointed_rerun_design_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "long_training_allowed": False,
        "model_save_allowed": False,
        "checkpoint_git_commit_allowed": False,
        "direct_long_training_allowed": False,
        "direct_generation_quality_claim_allowed": False,
        "decision_reason": ";".join(assessment["blocking_reasons"]),
        "proposed_clean_run_root": "",
    }


def build_first_checkpointed_training_dry_run_review_v0(
    require_local_checkpoint: bool = True,
    skip_payload_load: bool = False,
) -> dict[str, Any]:
    evidence = summarize_step10w_evidence_v0(require_local_checkpoint=require_local_checkpoint)
    payload_review = (
        {
            "payload_schema_reviewed": False,
            "payload_review_passed": False,
            "blocking_reasons": ["payload_load_skipped"],
        }
        if skip_payload_load
        else inspect_checkpoint_payload_schema_v0(CHECKPOINT_PATH)
    )
    assessment = assess_first_checkpointed_dry_run_v0(evidence, payload_review)
    observations = build_observations_v0(evidence)
    next_decision = build_next_boundary_decision_v0(assessment, observations)
    all_checks_passed = bool(assessment["review_status"] == "passed" and next_decision["recommended_next_stage"])
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10w_run_passed": evidence["step10w_run_passed"],
        "local_checkpoint_artifact_review": evidence["artifact_review"],
        "payload_schema_review": payload_review,
        "assessment": assessment,
        "observations": observations,
        "next_boundary_decision": next_decision,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": next_decision["recommended_next_stage"],
        "evidence": evidence,
    }

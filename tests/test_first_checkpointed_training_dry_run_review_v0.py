import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_first_checkpointed_training_dry_run_review_v0 as review_script  # noqa: E402
from covalent_ext.first_checkpointed_training_dry_run_review import (  # noqa: E402
    CHECKPOINT_PATH,
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_CHECKPOINT_SIZE_BYTES,
    FORBIDDEN_PAYLOAD_KEYS,
    LOCAL_CHECKPOINT_REVIEW_JSON,
    MASK_CYCLE,
    MASK_SCHEDULE,
    REVIEW_MANIFEST_JSON,
    REVIEW_REPORT_CSV,
    REVIEW_SUMMARY_MD,
    RUN_ROOT,
    STAGE,
    assess_first_checkpointed_dry_run_v0,
    build_first_checkpointed_training_dry_run_review_v0,
    build_next_boundary_decision_v0,
    build_observations_v0,
    inspect_checkpoint_payload_schema_v0,
    summarize_step10w_evidence_v0,
    validate_step10w_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _copy_step10w_workspace_without_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source_root = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_runs" / "first_checkpointed_training_dry_run_v0"
    target_root = tmp_path / "data" / "derived" / "covalent_small" / "training_runs" / "first_checkpointed_training_dry_run_v0"
    shutil.copytree(source_root, target_root, ignore=shutil.ignore_patterns("*.pt"))
    docs_source = REPO_ROOT / "docs" / "first_checkpointed_training_dry_run_v0_summary.md"
    docs_target = tmp_path / "docs" / "first_checkpointed_training_dry_run_v0_summary.md"
    docs_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(docs_source, docs_target)


@pytest.fixture(scope="module")
def review_result():
    if not CHECKPOINT_PATH.is_file():
        pytest.skip("local checkpoint is intentionally untracked and is not present in this checkout")
    return build_first_checkpointed_training_dry_run_review_v0(require_local_checkpoint=True)


def test_validate_step10w_outputs_success_with_local_checkpoint():
    if not CHECKPOINT_PATH.is_file():
        pytest.skip("local checkpoint is intentionally untracked and is not present in this checkout")

    assert validate_step10w_outputs_v0(require_local_checkpoint=True) is True


def test_missing_local_checkpoint_branch_blocks_when_required(tmp_path, monkeypatch):
    _copy_step10w_workspace_without_checkpoint(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="local_checkpoint_missing"):
        validate_step10w_outputs_v0(require_local_checkpoint=True)


def test_summarize_step10w_evidence_local_artifact_fields(review_result):
    evidence = summarize_step10w_evidence_v0(require_local_checkpoint=True)

    assert evidence["step10w_run_passed"] is True
    assert evidence["executed_steps"] == 12
    assert evidence["dry_run_training_steps_executed"] == 12
    assert evidence["mask_schedule"] == MASK_SCHEDULE
    assert evidence["mask_counts_seen"] == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert evidence["all_steps_passed"] is True
    assert evidence["all_losses_finite"] is True
    assert evidence["all_backward_success"] is True
    assert evidence["all_optimizer_steps_success"] is True
    assert evidence["local_checkpoint_present"] is True
    assert evidence["local_checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256
    assert evidence["local_checkpoint_sha256_matches"] is True
    assert evidence["local_checkpoint_size_bytes"] == EXPECTED_CHECKPOINT_SIZE_BYTES
    assert evidence["local_checkpoint_size_matches"] is True
    assert evidence["checkpoint_tracked_by_git"] is False
    assert evidence["checkpoint_staged_by_git"] is False
    assert evidence["checkpoint_ignored_or_untracked"] is True
    assert evidence["local_checkpoint_review_passed"] is True


def test_payload_schema_review_is_top_level_only_and_passed(review_result):
    payload = inspect_checkpoint_payload_schema_v0(CHECKPOINT_PATH)

    assert payload["payload_schema_reviewed"] is True
    assert payload["payload_is_dict"] is True
    assert payload["model_state_dict_present"] is True
    assert payload["optimizer_state_dict_present"] is True
    assert payload["completed_steps_verified"] is True
    assert payload["max_steps_verified"] is True
    assert payload["mask_schedule_verified"] is True
    assert payload["source_modification_allowed_false"] is True
    assert payload["formal_training_executed_false"] is True
    assert payload["real_finetune_executed_false"] is True
    assert payload["forbidden_payload_keys_absent"] is True
    assert payload["payload_review_passed"] is True
    assert payload["blocking_reasons"] == []
    assert FORBIDDEN_PAYLOAD_KEYS == {
        "dataset",
        "dataloader",
        "model",
        "optimizer",
        "raw_pdb_contents",
        "raw_sdf_contents",
        "generated_molecule_archive",
    }


def test_assessment_observations_and_next_boundary(review_result):
    evidence = review_result["evidence"]
    payload = review_result["payload_schema_review"]
    assessment = assess_first_checkpointed_dry_run_v0(evidence, payload)
    observations = build_observations_v0(evidence)
    next_decision = build_next_boundary_decision_v0(assessment, observations)

    assert assessment["review_status"] == "passed"
    assert assessment["checkpoint_artifact_status"] == "passed"
    assert assessment["resume_smoke_status"] == "passed"
    assert assessment["training_boundary_status"] == "passed"
    assert assessment["loss_decrease_required"] is False
    assert assessment["quality_claim_allowed"] is False
    assert assessment["formal_training_allowed"] is False
    assert assessment["finetune_allowed"] is False
    assert assessment["long_training_allowed"] is False
    assert assessment["model_save_allowed"] is False
    assert assessment["checkpoint_git_commit_allowed"] is False
    assert observations["checkpoint_not_committed_to_git"] is True
    assert observations["checkpoint_kept_as_local_artifact"] is True
    assert observations["checkpoint_size_bytes"] == EXPECTED_CHECKPOINT_SIZE_BYTES
    assert observations["future_clean_run_recommended"] is True
    assert observations["generation_quality_claim_allowed"] is False
    assert observations["loss_trend_claim_allowed"] is False
    assert next_decision["recommended_next_stage"] == "clean_checkpointed_dry_run_from_committed_code_design"
    assert next_decision["clean_checkpointed_rerun_design_allowed"] is True
    assert next_decision["formal_training_allowed"] is False
    assert next_decision["finetune_allowed"] is False
    assert next_decision["long_training_allowed"] is False
    assert next_decision["checkpoint_git_commit_allowed"] is False
    assert next_decision["direct_long_training_allowed"] is False


def test_full_review_manifest_fields(review_result):
    assert review_result["stage"] == STAGE
    assert review_result["previous_stage"] == "first_checkpointed_training_dry_run_v0"
    assert review_result["step10w_run_passed"] is True
    assert review_result["all_checks_passed"] is True
    assert review_result["recommended_next_step"] == "clean_checkpointed_dry_run_from_committed_code_design"
    assert review_result["local_checkpoint_artifact_review"]["checkpoint_git_commit_allowed"] is False
    assert review_result["payload_schema_review"]["payload_review_passed"] is True
    assert review_result["assessment"]["review_status"] == "passed"
    assert review_result["assessment"]["formal_training_allowed"] is False
    assert review_result["assessment"]["long_training_allowed"] is False
    assert review_result["observations"]["future_clean_run_recommended"] is True


def test_script_writes_review_outputs_without_creating_new_checkpoint(review_result):
    before_pt_files = sorted(str(path) for path in RUN_ROOT.rglob("*.pt"))

    assert review_script.run(require_local_checkpoint=True, skip_payload_load=False) == 0

    after_pt_files = sorted(str(path) for path in RUN_ROOT.rglob("*.pt"))
    assert after_pt_files == before_pt_files == [str(CHECKPOINT_PATH)]
    assert REVIEW_REPORT_CSV.is_file()
    assert REVIEW_MANIFEST_JSON.is_file()
    assert LOCAL_CHECKPOINT_REVIEW_JSON.is_file()
    assert REVIEW_SUMMARY_MD.is_file()

    rows = _read_csv(REVIEW_REPORT_CSV)
    assert len(rows) == 8
    assert [row["review_section"] for row in rows] == [
        "run_evidence_review",
        "checkpoint_artifact_review",
        "payload_schema_review",
        "resume_smoke_review",
        "safety_boundary_review",
        "observations",
        "next_boundary_decision",
        "risk_register",
    ]
    assert all(row["stage"] == STAGE for row in rows)
    assert all(row["recommended_next_step"] == "clean_checkpointed_dry_run_from_committed_code_design" for row in rows)
    assert all(row["status"] == "passed" for row in rows)

    manifest = _load_json(REVIEW_MANIFEST_JSON)
    assert manifest["stage"] == STAGE
    assert manifest["step10w_run_passed"] is True
    assert manifest["executed_steps"] == 12
    assert manifest["checkpoint_saved"] is True
    assert manifest["checkpoint_count"] == 1
    assert manifest["checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256
    assert manifest["checkpoint_size_bytes"] == EXPECTED_CHECKPOINT_SIZE_BYTES
    assert manifest["local_checkpoint_present"] is True
    assert manifest["local_checkpoint_sha256_matches"] is True
    assert manifest["local_checkpoint_size_matches"] is True
    assert manifest["checkpoint_tracked_by_git"] is False
    assert manifest["checkpoint_staged_by_git"] is False
    assert manifest["checkpoint_git_commit_allowed"] is False
    assert manifest["payload_schema_reviewed"] is True
    assert manifest["payload_review_passed"] is True
    assert manifest["resume_smoke_passed"] is True
    assert manifest["second_checkpoint_saved"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["model_saved"] is False
    assert manifest["formal_training_executed"] is False
    assert manifest["real_finetune_executed"] is False
    assert manifest["review_status"] == "passed"
    assert manifest["checkpoint_artifact_status"] == "passed"
    assert manifest["resume_smoke_status"] == "passed"
    assert manifest["training_boundary_status"] == "passed"
    assert manifest["loss_decrease_required"] is False
    assert manifest["quality_claim_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["long_training_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert manifest["future_clean_run_recommended"] is True
    assert manifest["recommended_next_step"] == "clean_checkpointed_dry_run_from_committed_code_design"
    assert manifest["all_checks_passed"] is True

    artifact = _load_json(LOCAL_CHECKPOINT_REVIEW_JSON)
    assert artifact["checkpoint_path"] == str(CHECKPOINT_PATH)
    assert artifact["local_checkpoint_present"] is True
    assert artifact["local_checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256
    assert artifact["expected_checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256
    assert artifact["local_checkpoint_sha256_matches"] is True
    assert artifact["local_checkpoint_size_bytes"] == EXPECTED_CHECKPOINT_SIZE_BYTES
    assert artifact["expected_checkpoint_size_bytes"] == EXPECTED_CHECKPOINT_SIZE_BYTES
    assert artifact["local_checkpoint_size_matches"] is True
    assert artifact["checkpoint_tracked_by_git"] is False
    assert artifact["checkpoint_staged_by_git"] is False
    assert artifact["checkpoint_ignored_or_untracked"] is True
    assert artifact["run_root_pt_files"] == [str(CHECKPOINT_PATH)]
    assert artifact["forbidden_artifacts_under_run_root"] == []
    assert artifact["local_checkpoint_review_passed"] is True
    assert artifact["checkpoint_git_commit_allowed"] is False
    assert artifact["checkpoint_keep_local_only"] is True

    assert "Step 10X is a review step" in REVIEW_SUMMARY_MD.read_text(encoding="utf-8")


def test_no_forbidden_artifacts_or_source_modifications():
    forbidden_suffixes = [".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"]
    for suffix in forbidden_suffixes:
        assert not list(RUN_ROOT.rglob(f"*{suffix}"))
    assert sorted(str(path) for path in RUN_ROOT.rglob("*.pt")) == [str(CHECKPOINT_PATH)]

    diff = subprocess.run(
        ["git", "diff", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert diff.stdout == ""


def test_review_sources_do_not_call_forbidden_execution_paths():
    paths = [
        REPO_ROOT / "src" / "covalent_ext" / "first_checkpointed_training_dry_run_review.py",
        REPO_ROOT / "scripts" / "check_first_checkpointed_training_dry_run_review_v0.py",
        REPO_ROOT / "tests" / "test_first_checkpointed_training_dry_run_review_v0.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden_tokens = [
        "torch" + "." + "save",
        "optimizer" + "." + "step",
        "trainer" + "." + "fit",
        "training" + "_step(",
        "back" + "ward(",
        "save" + "_checkpoint",
        "load_from" + "_checkpoint",
    ]
    for token in forbidden_tokens:
        assert token not in text

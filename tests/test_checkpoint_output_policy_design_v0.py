import csv
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_checkpoint_output_policy_design_v0 as policy_script  # noqa: E402
from covalent_ext.checkpoint_output_policy_design import (  # noqa: E402
    CHECKPOINT_FILENAME,
    DEFAULT_ROOT,
    MASK_SCHEDULE,
    NEXT_STAGE,
    RUN_NAME,
    RUN_ROOT,
    STAGE,
    build_checkpoint_naming_policy_v0,
    build_checkpoint_output_policy_design_v0,
    build_checkpoint_payload_policy_v0,
    build_metadata_policy_v0,
    build_next_step_execution_boundary_v0,
    build_output_directory_policy_v0,
    build_resume_smoke_policy_v0,
    build_retention_policy_v0,
    validate_step10u_outputs_v0,
)


PROTECTED_SOURCE_FILES = [
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/conditional_model.py",
    "equivariant_diffusion/dynamics.py",
    "lightning_modules.py",
]


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step10u_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10u_outputs_v0() is True


def test_output_directory_policy_is_fixed_and_current_step_does_not_create_dirs():
    policy = build_output_directory_policy_v0()

    assert policy["run_root"] == str(RUN_ROOT)
    assert policy["checkpoints_dir"] == str(RUN_ROOT / "checkpoints")
    assert policy["reports_dir"] == str(RUN_ROOT / "reports")
    assert policy["metadata_dir"] == str(RUN_ROOT / "metadata")
    assert policy["resume_smoke_dir"] == str(RUN_ROOT / "resume_smoke")
    assert "reports/first_checkpointed_training_dry_run_report.csv" in policy["allowed_report_files"]
    assert "metadata/first_checkpointed_training_dry_run_manifest.json" in policy["allowed_report_files"]
    assert "metadata/checkpoint_metadata.json" in policy["allowed_report_files"]
    assert "resume_smoke/resume_smoke_report.csv" in policy["allowed_report_files"]
    assert "resume_smoke/resume_smoke_manifest.json" in policy["allowed_report_files"]
    assert policy["directory_creation_allowed_next_step"] is True
    assert policy["directory_creation_allowed_current_step"] is False
    assert policy["overwrite_existing_run_dir_allowed"] is False
    assert policy["next_step_must_fail_if_run_dir_exists"] is True


def test_checkpoint_naming_policy_allows_one_final_pt_checkpoint():
    policy = build_checkpoint_naming_policy_v0()

    assert policy["checkpoint_filename"] == CHECKPOINT_FILENAME
    assert policy["checkpoint_path"] == str(RUN_ROOT / "checkpoints" / CHECKPOINT_FILENAME)
    assert policy["checkpoint_extension"] == ".pt"
    assert policy["checkpoint_format"] == "torch.save dictionary"
    assert policy["checkpoint_count_limit"] == 1
    assert policy["save_at_step"] == 12
    assert policy["no_intermediate_checkpoints"] is True
    assert policy["no_epoch_checkpoints"] is True
    assert policy["no_lightning_checkpoint"] is True
    assert policy["no_model_only_checkpoint"] is True
    assert policy["no_optimizer_only_checkpoint"] is True


def test_payload_policy_requires_state_dicts_and_forbids_large_objects():
    policy = build_checkpoint_payload_policy_v0()
    required = set(policy["required_payload_fields"])
    forbidden = set(policy["forbidden_payload_fields"])

    assert "model_state_dict" in required
    assert "optimizer_state_dict" in required
    assert "loss_total_by_step" in required
    assert "grad_norm_by_step" in required
    assert "param_delta_norm_by_step" in required
    assert policy["required_false_fields"]["source_modification_allowed"] is False
    assert policy["required_false_fields"]["formal_training_executed"] is False
    assert policy["required_false_fields"]["real_finetune_executed"] is False
    assert "raw PDB contents" in forbidden
    assert "raw SDF contents" in forbidden
    assert "large tensor dumps" in forbidden
    assert "Dataset object" in forbidden
    assert "DataLoader object" in forbidden
    assert "model object pickle" in forbidden
    assert "optimizer object pickle" in forbidden


def test_metadata_policy_requires_checkpoint_hash_size_git_and_source_checks():
    policy = build_metadata_policy_v0()
    required = set(policy["required_metadata_fields"])

    assert policy["metadata_required"] is True
    assert "checkpoint_sha256" in required
    assert "checkpoint_size_bytes" in required
    assert "git_status_clean_before_run" in required
    assert "git_status_clean_after_run" in required
    assert "protected_source_diff_result" in required
    assert "forbidden_artifact_scan_result" in required
    assert policy["checkpoint_sha256_required"] is True
    assert policy["checkpoint_size_bytes_required"] is True
    assert policy["git_status_required"] is True
    assert policy["source_diff_check_required"] is True
    assert policy["forbidden_artifact_scan_required"] is True


def test_retention_and_resume_smoke_policies_are_fail_closed():
    retention = build_retention_policy_v0()
    resume = build_resume_smoke_policy_v0()

    assert retention["max_checkpoints"] == 1
    assert retention["keep_last_only"] is True
    assert retention["fail_if_unexpected_checkpoint_files_exist"] is True
    assert retention["fail_if_multiple_checkpoints_created"] is True
    assert retention["fail_if_checkpoint_size_zero"] is True
    assert retention["fail_if_checkpoint_missing"] is True
    assert retention["no_archive_creation"] is True
    assert resume["resume_smoke_required"] is True
    assert resume["load_model_state_dict"] is True
    assert resume["load_optimizer_state_dict"] is True
    assert resume["verify_completed_steps"] == 12
    assert resume["verify_mask_schedule_matches"] is True
    assert resume["verify_model_parameter_shapes_match"] is True
    assert resume["verify_optimizer_state_loaded"] is True
    assert resume["optimizer_step_during_resume_smoke"] is False
    assert resume["second_checkpoint_save_allowed"] is False
    assert resume["trainer_fit_allowed"] is False
    assert resume["training_step_allowed"] is False
    assert resume["model_save_allowed"] is False


def test_next_step_boundary_allows_checkpoint_only_inside_first_dry_run():
    boundary = build_next_step_execution_boundary_v0()

    assert boundary["first_checkpointed_training_dry_run_allowed"] is True
    assert boundary["checkpoint_save_allowed_next_step"] is True
    assert boundary["checkpoint_load_allowed_next_step"] is True
    assert boundary["checkpoint_load_scope"] == "resume smoke only"
    assert boundary["model_save_allowed_next_step"] is False
    assert boundary["trainer_fit_allowed_next_step"] is False
    assert boundary["training_step_allowed_next_step"] is False
    assert boundary["formal_training_allowed_next_step"] is False
    assert boundary["finetune_allowed_next_step"] is False
    assert boundary["source_modification_allowed_next_step"] is False
    assert boundary["allowed_checkpoint_files_next_step"] == [CHECKPOINT_FILENAME]
    assert ".pkl" in boundary["forbidden_outputs_next_step"]
    assert ".lmdb" in boundary["forbidden_outputs_next_step"]
    assert ".tar" in boundary["forbidden_outputs_next_step"]
    assert ".zip" in boundary["forbidden_outputs_next_step"]
    assert ".tgz" in boundary["forbidden_outputs_next_step"]
    assert ".ckpt" in boundary["forbidden_outputs_next_step"]
    assert ".pth" in boundary["forbidden_outputs_next_step"]
    assert "additional .pt files beyond the single allowed checkpoint" in boundary["forbidden_outputs_next_step"]


def test_full_policy_manifest_core_fields():
    policy = build_checkpoint_output_policy_design_v0()
    manifest = policy_script.preview_manifest(policy)

    assert policy["stage"] == STAGE
    assert policy["previous_stage"] == "longer_no_checkpoint_training_dry_run_review_v0"
    assert policy["step10u_review_passed"] is True
    assert policy["next_stage"] == NEXT_STAGE
    assert policy["run_name"] == RUN_NAME
    assert policy["current_step_checkpoint_saved"] is False
    assert policy["current_step_checkpoint_loaded"] is False
    assert policy["current_step_model_saved"] is False
    assert policy["current_step_formal_training_executed"] is False
    assert policy["all_checks_passed"] is True
    assert policy["recommended_next_step"] == "first_checkpointed_training_dry_run"

    assert manifest["stage"] == STAGE
    assert manifest["previous_stage"] == "longer_no_checkpoint_training_dry_run_review_v0"
    assert manifest["step10u_review_passed"] is True
    assert manifest["next_stage"] == NEXT_STAGE
    assert manifest["run_name"] == RUN_NAME
    assert manifest["run_root"] == str(RUN_ROOT) + "/"
    assert manifest["checkpoint_filename"] == CHECKPOINT_FILENAME
    assert manifest["checkpoint_count_limit"] == 1
    assert manifest["save_at_step"] == 12
    assert manifest["no_intermediate_checkpoints"] is True
    assert manifest["checkpoint_extension"] == ".pt"
    assert manifest["current_step_checkpoint_save_allowed"] is False
    assert manifest["current_step_checkpoint_load_allowed"] is False
    assert manifest["current_step_model_save_allowed"] is False
    assert manifest["current_step_formal_training_allowed"] is False
    assert manifest["next_step_checkpoint_save_allowed"] is True
    assert manifest["next_step_checkpoint_load_allowed"] is True
    assert manifest["next_step_model_save_allowed"] is False
    assert manifest["next_step_trainer_fit_allowed"] is False
    assert manifest["next_step_training_step_allowed"] is False
    assert manifest["next_step_formal_training_allowed"] is False
    assert manifest["next_step_finetune_allowed"] is False
    assert manifest["next_step_source_modification_allowed"] is False
    assert manifest["resume_smoke_required"] is True
    assert manifest["no_second_checkpoint_during_resume_smoke"] is True
    assert manifest["max_checkpoints"] == 1
    assert manifest["keep_last_only"] is True
    assert manifest["fail_if_multiple_checkpoints_created"] is True
    assert manifest["fail_if_unexpected_checkpoint_files_exist"] is True
    assert manifest["metadata_required"] is True
    assert manifest["checkpoint_sha256_required"] is True
    assert manifest["current_step_checkpoint_saved"] is False
    assert manifest["current_step_checkpoint_loaded"] is False
    assert manifest["current_step_model_saved"] is False
    assert manifest["current_step_formal_training_executed"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "first_checkpointed_training_dry_run"
    assert manifest["next_step_execution_boundary"]["allowed_checkpoint_files_next_step"] == [CHECKPOINT_FILENAME]
    assert manifest["checkpoint_payload_policy"]["required_payload_fields"] == build_checkpoint_payload_policy_v0()[
        "required_payload_fields"
    ]
    assert manifest["checkpoint_payload_policy"]["required_false_fields"]["formal_training_executed"] is False
    assert manifest["checkpoint_naming_policy"]["checkpoint_format"] == "torch.save dictionary"


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert policy_script.run() == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "checkpoint_output_policy_design_report.csv")
    assert len(rows) == 8
    assert [row["policy_section"] for row in rows] == [
        "output_directory_policy",
        "checkpoint_naming_policy",
        "checkpoint_payload_policy",
        "metadata_policy",
        "retention_policy",
        "resume_smoke_policy",
        "next_step_execution_boundary",
        "risk_register",
    ]
    assert all(row["stage"] == STAGE for row in rows)
    assert all(row["previous_stage"] == "longer_no_checkpoint_training_dry_run_review_v0" for row in rows)
    assert all(row["status"] == "passed" for row in rows)
    assert all(row["recommended_next_step"] == "first_checkpointed_training_dry_run" for row in rows)

    manifest = json.loads((root / "checkpoint_output_policy_design_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert manifest["run_name"] == RUN_NAME
    assert manifest["checkpoint_filename"] == CHECKPOINT_FILENAME
    assert manifest["checkpoint_count_limit"] == 1
    assert manifest["next_step_checkpoint_save_allowed"] is True
    assert manifest["next_step_checkpoint_load_allowed"] is True
    assert manifest["next_step_model_save_allowed"] is False
    assert manifest["next_step_training_step_allowed"] is False
    assert manifest["metadata_required"] is True
    assert manifest["checkpoint_sha256_required"] is True
    assert manifest["recommended_next_step"] == "first_checkpointed_training_dry_run"
    assert Path("docs/checkpoint_output_policy_design_v0_summary.md").is_file()

    assert not (tmp_path / "data/derived/covalent_small/training_runs/first_checkpointed_training_dry_run_v0").exists()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    assert not list(root.rglob("*.ckpt"))
    assert not list(root.rglob("*.pth"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before


def test_policy_sources_do_not_call_training_checkpoint_or_save_apis():
    source_paths = [
        REPO_ROOT / "src" / "covalent_ext" / "checkpoint_output_policy_design.py",
        REPO_ROOT / "scripts" / "check_checkpoint_output_policy_design_v0.py",
        REPO_ROOT / "tests" / "test_checkpoint_output_policy_design_v0.py",
    ]
    forbidden_call_tokens = [
        "." + "backward" + "(",
        "optimizer" + "." + "step" + "(",
        "trainer" + "." + "fit" + "(",
        "." + "fit" + "(",
        "training" + "_step" + "(",
        "torch" + "." + "save" + "(",
        "torch" + "." + "load" + "(",
        "save" + "_checkpoint" + "(",
        "load" + "_from" + "_checkpoint" + "(",
    ]
    for source_path in source_paths:
        text = source_path.read_text(encoding="utf-8")
        for token in forbidden_call_tokens:
            assert token not in text

from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from covalent_ext.model_input_adapter import expected_reactive_atom_region_for_mask_level_v0  # noqa: E402
from covalent_ext.real_covalent_pretrained_forward_loss_smoke import (  # noqa: E402
    BATCH_SIZE,
    CANONICAL_MASK_LEVELS,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    LOSS_TABLE_CSV,
    MANIFEST_JSON,
    NUM_WORKERS,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    build_real_covalent_forward_loss_batch_bundle_v0,
    validate_step12c_outputs_v0,
)

import check_real_covalent_pretrained_forward_loss_smoke_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (REPORT_CSV.is_file() and MANIFEST_JSON.is_file() and LOSS_TABLE_CSV.is_file() and SUMMARY_MD.is_file()):
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def _loss_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(LOSS_TABLE_CSV)


def test_step12c_precondition_validates():
    assert validate_step12c_outputs_v0() is True


def test_step12b_mask_level_aware_validator_contract():
    expected_regions = {
        "A_warhead_only": "target",
        "B_linker_warhead": "target",
        "B2_scaffold_warhead": "target",
        "B3_scaffold_only": "context",
        "C_scaffold_linker_warhead": "target",
    }
    for level, expected in expected_regions.items():
        assert expected_reactive_atom_region_for_mask_level_v0(level) == expected
    try:
        expected_reactive_atom_region_for_mask_level_v0("B3")
    except ValueError as exc:
        assert str(exc) == "unsupported_mask_level:B3"
    else:
        raise AssertionError("short alias B3 must be rejected")


def test_real_covalent_batch_bundle_is_read_only_and_valid_for_b3():
    bundle = build_real_covalent_forward_loss_batch_bundle_v0("B3_scaffold_only")

    assert bundle["dataset_created"] is True
    assert bundle["dataloader_created"] is True
    assert bundle["batch_size"] == BATCH_SIZE
    assert bundle["num_workers"] == NUM_WORKERS
    assert bundle["sample_ids"] == ["BTK_C481_6DI9_pre_reaction", "KRAS_G12C_5F2E_pre_reaction"]
    assert bundle["expected_reactive_atom_region"] == "context"
    assert bundle["adapted_valid"] is True
    assert bundle["model_input_valid"] is True
    assert bundle["diffsbdd_like_valid"] is True
    assert bundle["target_atom_count"] > 0
    assert bundle["context_atom_count"] > 0
    assert bundle["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert bundle["synthetic_fallback_used"] is False
    assert bundle["status"] == "passed"


def test_manifest_core_contract_and_counts():
    manifest = _manifest()

    assert manifest["stage"] == "real_covalent_pretrained_forward_loss_smoke_v0"
    assert manifest["previous_stage"] == "real_covalent_pretraining_smoke_design_v0"
    assert manifest["step12c_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert manifest["requested_device"] == "cpu"
    assert manifest["resolved_device"] == "cpu"
    assert manifest["batch_size"] == 2
    assert manifest["num_workers"] == 0
    assert manifest["canonical_mask_levels"] == CANONICAL_MASK_LEVELS
    assert manifest["canonical_mask_level_count"] == 5
    assert manifest["attempted_mask_level_count"] == 5
    assert manifest["passed_mask_level_count"] == 5
    assert manifest["failed_mask_level_count"] == 0


def test_manifest_forward_loss_and_strict_load_contract():
    manifest = _manifest()

    assert manifest["model_instantiated"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["model_strict_loaded_once"] is True
    assert manifest["model_forward_called"] is True
    assert manifest["model_forward_call_count"] == 5
    assert manifest["all_level_forward_call_count_exactly_one"] is True
    assert manifest["all_adapted_batches_valid"] is True
    assert manifest["all_model_inputs_valid"] is True
    assert manifest["all_diffsbdd_like_inputs_valid"] is True
    assert manifest["all_checkpoint_compatible_real_batches_constructed"] is True
    assert manifest["no_synthetic_fallback_used"] is True
    assert manifest["all_losses_computed"] is True
    assert manifest["all_losses_finite"] is True
    assert manifest["all_losses_require_grad"] is True
    assert manifest["selected_loss_key"] == "masked_loss_total_dry"
    assert float(manifest["min_selected_loss_value"]) > 0.0
    assert float(manifest["max_selected_loss_value"]) >= float(manifest["min_selected_loss_value"])
    assert float(manifest["mean_selected_loss_value"]) > 0.0


def test_manifest_decision_and_safety_boundary():
    manifest = _manifest()

    assert manifest["real_covalent_pretrained_forward_loss_smoke_passed"] is True
    assert manifest["real_covalent_forward_loss_contract_proven"] is True
    assert manifest["real_covalent_all_mask_levels_forward_loss_proven"] is True
    assert manifest["real_covalent_backward_smoke_allowed"] is True
    assert manifest["recommended_next_step"] == "real_covalent_backward_smoke"
    for key in [
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "original_diffsbdd_source_modified",
        "forbidden_artifacts_created",
    ]:
        assert manifest[key] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_loss_table_has_five_passed_finite_requires_grad_rows():
    rows = _loss_rows()

    assert len(rows) == 5
    assert [row["mask_level"] for row in rows] == CANONICAL_MASK_LEVELS
    assert {row["status"] for row in rows} == {"passed"}
    for row in rows:
        expected_region = "context" if row["mask_level"] == "B3_scaffold_only" else "target"
        assert row["expected_reactive_atom_region"] == expected_region
        assert row["adapted_valid"] == "True"
        assert row["model_input_valid"] == "True"
        assert row["diffsbdd_like_valid"] == "True"
        assert row["checkpoint_compatible_real_batch_constructed"] == "True"
        assert row["no_synthetic_fallback_used"] == "True"
        assert row["model_forward_called"] == "True"
        assert row["forward_call_count"] == "1"
        assert row["loss_computed"] == "True"
        assert row["selected_loss_key"] == "masked_loss_total_dry"
        assert float(row["selected_loss_value"]) > 0.0
        assert row["loss_requires_grad"] == "True"
        assert row["loss_finite"] == "True"
        assert int(row["target_atom_count"]) > 0
        assert int(row["ligand_feature_dim"]) == 10
        assert int(row["pocket_feature_dim"]) == 10


def test_report_manifest_loss_table_and_summary_written():
    _ensure_outputs()

    report_rows = _read_csv(REPORT_CSV)
    summary = SUMMARY_MD.read_text(encoding="utf-8")
    assert len(report_rows) == 9
    assert {row["status"] for row in report_rows} == {"passed"}
    assert "real covalent pretrained forward/loss smoke, not training" in summary
    assert "does not use synthetic fallback" in summary
    assert "recommended_next_step: real_covalent_backward_smoke" in summary


def test_no_forbidden_artifacts_under_output_root():
    _ensure_outputs()

    forbidden = [path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES]
    assert forbidden == []


def test_no_protected_source_modification():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_ast_safety_for_step12d_files():
    files = [
        "src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py",
        "scripts/check_real_covalent_pretrained_forward_loss_smoke_v0.py",
        "tests/test_real_covalent_pretrained_forward_loss_smoke_v0.py",
    ]
    forbidden_names = {"training_step", "save_checkpoint", "load_from_checkpoint"}
    for relative in files:
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                assert not (isinstance(func.value, ast.Name) and func.value.id == "torch" and func.attr == "save")
                assert not (isinstance(func.value, ast.Name) and func.value.id == "optimizer" and func.attr == "step")
                assert func.attr not in {"backward", "fit", "training_step", "save_checkpoint", "load_from_checkpoint"}
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_names

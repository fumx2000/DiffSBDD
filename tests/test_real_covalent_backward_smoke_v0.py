from __future__ import annotations

import ast
import csv
import json
import math
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
from covalent_ext.real_covalent_backward_smoke import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    GRAD_TABLE_CSV,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    validate_step12b_validator_behavior_v0,
    validate_step12d_outputs_v0,
)

import check_real_covalent_backward_smoke_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (REPORT_CSV.is_file() and MANIFEST_JSON.is_file() and GRAD_TABLE_CSV.is_file() and SUMMARY_MD.is_file()):
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def _grad_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(GRAD_TABLE_CSV)


def test_step12d_precondition_validates():
    assert validate_step12d_outputs_v0() is True


def test_step12b_mask_level_aware_validator_validates():
    assert validate_step12b_validator_behavior_v0() is True
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


def test_manifest_core_real_data_and_strict_load_contract():
    manifest = _manifest()

    assert manifest["stage"] == "real_covalent_backward_smoke_v0"
    assert manifest["previous_stage"] == "real_covalent_pretrained_forward_loss_smoke_v0"
    assert manifest["step12d_validated"] is True
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
    assert manifest["model_instantiated"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["model_strict_loaded_once"] is True


def test_manifest_forward_loss_and_backward_contract():
    manifest = _manifest()

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
    assert manifest["aggregate_loss_reduction"] == "mean"
    assert math.isfinite(float(manifest["aggregate_loss_value"]))
    assert manifest["aggregate_loss_finite"] is True
    assert manifest["aggregate_loss_requires_grad"] is True
    assert manifest["backward_called"] is True
    assert manifest["backward_call_count"] == 1
    assert manifest["backward_exactly_once"] is True
    assert manifest["backward_success"] is True


def test_manifest_gradient_statistics_and_decision():
    manifest = _manifest()

    assert manifest["trainable_parameter_count"] > 0
    assert manifest["parameters_with_grad_count"] > 0
    assert manifest["parameters_with_nonzero_grad_count"] > 0
    assert manifest["finite_nonzero_gradients"] is True
    assert math.isfinite(float(manifest["total_grad_norm"]))
    assert float(manifest["total_grad_norm"]) > 0.0
    assert math.isfinite(float(manifest["max_abs_grad"]))
    assert float(manifest["max_abs_grad"]) > 0.0
    assert manifest["grad_nan_count"] == 0
    assert manifest["grad_inf_count"] == 0
    assert manifest["real_covalent_backward_smoke_passed"] is True
    assert manifest["real_covalent_backward_contract_proven"] is True
    assert manifest["real_covalent_single_optimizer_step_smoke_allowed"] is True
    assert manifest["recommended_next_step"] == "real_covalent_single_optimizer_step_smoke"


def test_manifest_safety_boundary():
    manifest = _manifest()

    for key in [
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


def test_grad_table_has_five_loss_rows_and_one_aggregate_row():
    rows = _grad_rows()

    assert len(rows) == 6
    loss_rows = [row for row in rows if row["row_type"] == "mask_level_loss"]
    aggregate_rows = [row for row in rows if row["row_type"] == "aggregate_backward"]
    assert [row["mask_level"] for row in loss_rows] == CANONICAL_MASK_LEVELS
    assert len(aggregate_rows) == 1
    for row in loss_rows:
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
        assert math.isfinite(float(row["selected_loss_value"]))
        assert row["loss_requires_grad"] == "True"
        assert row["loss_finite"] == "True"
        assert row["status"] == "passed"
    aggregate = aggregate_rows[0]
    assert aggregate["mask_level"] == "ALL"
    assert aggregate["aggregate_loss_reduction"] == "mean"
    assert math.isfinite(float(aggregate["aggregate_loss_value"]))
    assert aggregate["aggregate_loss_requires_grad"] == "True"
    assert aggregate["aggregate_loss_finite"] == "True"
    assert aggregate["backward_called"] == "True"
    assert aggregate["backward_call_count"] == "1"
    assert aggregate["backward_success"] == "True"
    assert int(aggregate["trainable_parameter_count"]) > 0
    assert int(aggregate["parameters_with_grad_count"]) > 0
    assert int(aggregate["parameters_with_nonzero_grad_count"]) > 0
    assert aggregate["finite_nonzero_gradients"] == "True"
    assert float(aggregate["total_grad_norm"]) > 0.0
    assert float(aggregate["max_abs_grad"]) > 0.0
    assert aggregate["grad_nan_count"] == "0"
    assert aggregate["grad_inf_count"] == "0"
    assert aggregate["status"] == "passed"


def test_report_manifest_grad_table_and_summary_written():
    _ensure_outputs()

    report_rows = _read_csv(REPORT_CSV)
    summary = SUMMARY_MD.read_text(encoding="utf-8")
    assert len(report_rows) == 9
    assert {row["status"] for row in report_rows} == {"passed"}
    assert "real covalent backward smoke, not training" in summary
    assert "feature semantics audit" in summary
    assert "recommended_next_step: real_covalent_single_optimizer_step_smoke" in summary


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


def test_ast_safety_and_controlled_backward_for_step12e_files():
    source_file = "src/covalent_ext/real_covalent_backward_smoke.py"
    script_file = "scripts/check_real_covalent_backward_smoke_v0.py"
    test_file = "tests/test_real_covalent_backward_smoke_v0.py"

    def call_names(relative: str) -> list[tuple[str, str | None]]:
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        names: list[tuple[str, str | None]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                names.append((func.attr, owner))
            elif isinstance(func, ast.Name):
                names.append((func.id, None))
        return names

    source_calls = call_names(source_file)
    script_calls = call_names(script_file)
    test_calls = call_names(test_file)

    assert sum(1 for name, _owner in source_calls if name == "backward") == 1
    assert all(name != "backward" for name, _owner in script_calls)
    assert all(name != "backward" for name, _owner in test_calls)
    for calls in [source_calls, script_calls, test_calls]:
        for name, owner in calls:
            assert not (owner == "torch" and name == "save")
            assert not (owner == "optimizer" and name == "step")
            assert name not in {"fit", "training_step", "save_checkpoint", "load_from_checkpoint"}
            assert name not in {"Adam", "AdamW", "SGD", "RMSprop"}

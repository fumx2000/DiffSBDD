from __future__ import annotations

import csv
import functools
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

from covalent_ext.b3_backward_smoke import (  # noqa: E402
    BWD,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    GRADIENT_TABLE_CSV,
    INPUT_SOURCE,
    MANIFEST_JSON,
    MASK_LEVEL,
    O,
    O_STEP,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    TR_FIT,
    build_b3_backward_smoke_decision_v0,
    build_b3_backward_smoke_v0,
    run_b3_backward_smoke_v0,
    validate_step11p_outputs_v0,
)

import check_b3_backward_smoke_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def _cached_result_json_text() -> str:
    return json.dumps(build_b3_backward_smoke_v0(device="cpu"), default=str)


def _cached_result() -> dict:
    return json.loads(_cached_result_json_text())


def test_validate_step11p_outputs_success_and_loss_table_contract():
    assert validate_step11p_outputs_v0() is True
    rows = _read_csv(
        "data/derived/covalent_small/b3_pretrained_masked_loss_smoke_v0/"
        "b3_pretrained_masked_loss_smoke_table.csv"
    )

    assert len(rows) == 1
    assert rows[0]["mask_level"] == MASK_LEVEL
    assert rows[0]["selected_loss_key"] == "masked_loss_total_dry"
    assert math.isfinite(float(rows[0]["selected_loss_value"]))
    assert rows[0]["loss_requires_grad"] == "True"
    assert rows[0]["loss_finite"] == "True"
    assert rows[0]["b3_target_atom_count"] == "3"
    assert rows[0]["b3_context_atom_count"] == "4"
    assert rows[0]["model_forward_called"] == "True"
    assert rows[0][BWD + "_called"] == "False"
    assert rows[0][O + "_created"] == "False"
    assert rows[0][O_STEP + "_called"] == "False"
    assert rows[0]["status"] == "passed"


def test_run_b3_backward_smoke_returns_finite_nonzero_gradients():
    result = run_b3_backward_smoke_v0(device="cpu")

    assert result["step11p_validated"] is True
    assert result["mask_level"] == MASK_LEVEL
    assert result["input_source"] == INPUT_SOURCE
    assert result["requested_device"] == "cpu"
    assert result["resolved_device"] == "cpu"
    assert result["model_instantiated"] is True
    assert result["strict_load_success"] is True
    assert result["pretrained_weights_loaded"] is True
    assert result["pretrained_base_integration_proven"] is True
    assert result["model_forward_called"] is True
    assert result["loss_computed"] is True
    assert result["selected_loss_key"] == "masked_loss_total_dry"
    assert math.isfinite(float(result["selected_loss_value"]))
    assert result["loss_requires_grad"] is True
    assert result["loss_finite"] is True
    assert result[BWD + "_called"] is True
    assert result[BWD + "_call_count"] == 1
    assert result[BWD + "_success"] is True
    assert result["finite_nonzero_grad_exists"] is True
    assert result["trainable_parameter_count"] > 0
    assert result["parameters_with_grad_count"] > 0
    assert math.isfinite(float(result["total_grad_norm"]))
    assert float(result["total_grad_norm"]) > 0.0
    assert math.isfinite(float(result["max_abs_grad"]))
    assert float(result["max_abs_grad"]) > 0.0
    assert result["grad_nan_count"] == 0
    assert result["grad_inf_count"] == 0
    assert result["b3_target_atom_count"] == 3
    assert result["b3_context_atom_count"] == 4
    assert result["b3_reactive_atom_in_context"] is True
    assert result["b3_reactive_atom_in_target"] is False
    assert result[O + "_created"] is False
    assert result[O_STEP + "_called"] is False
    assert result["status"] == "passed"
    assert result["blocking_reasons"] == []


def test_decision_allows_single_update_smoke_only_when_backward_passes():
    result = run_b3_backward_smoke_v0(device="cpu")
    decision = build_b3_backward_smoke_decision_v0(result)
    blocked = dict(result, status="blocked", finite_nonzero_grad_exists=False)
    blocked_decision = build_b3_backward_smoke_decision_v0(blocked)

    assert decision["b3_backward_smoke_passed"] is True
    assert decision["b3_backward_gradient_contract_proven"] is True
    assert decision["b3_finite_nonzero_gradient_proven"] is True
    assert decision["b3_single_optimizer_step_smoke_allowed"] is True
    assert decision["optimizer_allowed_next_step"] is True
    assert decision["recommended_next_step"] == "b3_single_optimizer_step_smoke"
    assert blocked_decision["b3_backward_smoke_passed"] is False
    assert blocked_decision["recommended_next_step"] == "b3_backward_smoke_debug"
    for item in [decision, blocked_decision]:
        assert item["training_allowed"] is False
        assert item["formal_training_allowed"] is False
        assert item["finetune_allowed"] is False
        assert item["quality_claim_allowed"] is False
        assert item["parameter_update_allowed"] is False


def test_manifest_contract_and_safety_boundary():
    manifest = _cached_result()["manifest"]

    assert manifest["stage"] == "b3_backward_smoke_v0"
    assert manifest["previous_stage"] == "b3_pretrained_masked_loss_smoke_v0"
    assert manifest["step11p_validated"] is True
    assert manifest["mask_level"] == MASK_LEVEL
    assert manifest["input_source"] == INPUT_SOURCE
    assert manifest["checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert manifest["requested_device"] == "cpu"
    assert manifest["resolved_device"] == "cpu"
    assert manifest["model_instantiated"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["model_forward_called"] is True
    assert manifest["loss_computed"] is True
    assert manifest["selected_loss_key"] == "masked_loss_total_dry"
    assert math.isfinite(float(manifest["selected_loss_value"]))
    assert manifest["loss_requires_grad"] is True
    assert manifest["loss_finite"] is True
    assert manifest[BWD + "_called"] is True
    assert manifest[BWD + "_call_count"] == 1
    assert manifest[BWD + "_success"] is True
    assert manifest["finite_nonzero_grad_exists"] is True
    assert manifest["trainable_parameter_count"] > 0
    assert manifest["parameters_with_grad_count"] > 0
    assert float(manifest["total_grad_norm"]) > 0.0
    assert float(manifest["max_abs_grad"]) > 0.0
    assert manifest["grad_nan_count"] == 0
    assert manifest["grad_inf_count"] == 0
    assert manifest["b3_target_atom_count"] == 3
    assert manifest["b3_context_atom_count"] == 4
    assert manifest["b3_reactive_atom_in_context"] is True
    assert manifest["b3_reactive_atom_in_target"] is False
    assert manifest["b3_backward_smoke_passed"] is True
    assert manifest["b3_backward_gradient_contract_proven"] is True
    assert manifest["b3_finite_nonzero_gradient_proven"] is True
    assert manifest["b3_single_optimizer_step_smoke_allowed"] is True
    assert manifest["recommended_next_step"] == "b3_single_optimizer_step_smoke"
    for key in [
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        O + "_created",
        O_STEP + "_called",
        "training_step_called",
        TR_FIT + "_called",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "original_diffsbdd_source_modified",
        "forbidden_artifacts_created",
    ]:
        assert manifest[key] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_gradient_table_contract():
    rows = _cached_result()["gradient_table_rows"]

    assert len(rows) == 1
    row = rows[0]
    assert row["mask_level"] == MASK_LEVEL
    assert row["input_source"] == INPUT_SOURCE
    assert row["selected_loss_key"] == "masked_loss_total_dry"
    assert math.isfinite(float(row["selected_loss_value"]))
    assert row["loss_requires_grad"] is True
    assert row["loss_finite"] is True
    assert row[BWD + "_called"] is True
    assert row[BWD + "_call_count"] == 1
    assert row[BWD + "_success"] is True
    assert row["finite_nonzero_grad_exists"] is True
    assert row["trainable_parameter_count"] > 0
    assert row["parameters_with_grad_count"] > 0
    assert float(row["total_grad_norm"]) > 0.0
    assert float(row["max_abs_grad"]) > 0.0
    assert row["grad_nan_count"] == 0
    assert row["grad_inf_count"] == 0
    assert row[O + "_created"] is False
    assert row[O_STEP + "_called"] is False
    assert row["status"] == "passed"
    assert row["blocking_reasons"] == ""


def test_script_writes_report_manifest_gradient_table_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "b3_backward_smoke_v0"
    report_csv = output_root / "report.csv"
    manifest_json = output_root / "manifest.json"
    gradient_csv = output_root / "gradient.csv"
    summary_md = tmp_path / "docs" / "summary.md"
    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "GRADIENT_TABLE_CSV", gradient_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu") == 0

    report_rows = _read_csv(report_csv)
    gradient_rows = _read_csv(gradient_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    summary = summary_md.read_text(encoding="utf-8")
    assert len(report_rows) == 8
    assert {row["status"] for row in report_rows} == {"passed"}
    assert len(gradient_rows) == 1
    assert gradient_rows[0]["status"] == "passed"
    assert manifest["all_checks_passed"] is True
    assert "not training" in summary
    assert "exactly one controlled reverse pass" in summary
    assert "recommended_next_step: b3_single_optimizer_step_smoke" in summary


def test_generated_outputs_and_no_forbidden_artifacts():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert GRADIENT_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()

    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    gradient_rows = _read_csv(GRADIENT_TABLE_CSV)
    assert len(_read_csv(REPORT_CSV)) == 8
    assert len(gradient_rows) == 1
    assert gradient_rows[0]["status"] == "passed"
    assert manifest["all_checks_passed"] is True
    assert not [
        path
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES
    ]


def test_no_protected_source_modification():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_no_forbidden_execution_calls_in_step11q_files():
    forbidden = [
        "torch." + "save",
        O + ".step",
        "trainer." + "fit",
        "training_" + "step(",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "torch." + "optim",
    ]
    files = [
        "src/covalent_ext/b3_backward_smoke.py",
        "scripts/check_b3_backward_smoke_v0.py",
        "tests/test_b3_backward_smoke_v0.py",
    ]
    for relative in files:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for snippet in forbidden:
            assert snippet not in text


def test_controlled_backward_call_location_is_single_module_call():
    module_text = (REPO_ROOT / "src/covalent_ext/b3_backward_smoke.py").read_text(encoding="utf-8")
    script_text = (REPO_ROOT / "scripts/check_b3_backward_smoke_v0.py").read_text(encoding="utf-8")
    test_text = (REPO_ROOT / "tests/test_b3_backward_smoke_v0.py").read_text(encoding="utf-8")

    assert module_text.count("." + BWD + "(") == 1
    assert script_text.count("." + BWD + "(") == 0
    assert test_text.count("." + BWD + "(") == 0

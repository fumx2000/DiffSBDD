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

from covalent_ext.b3_pretrained_masked_loss_smoke import (  # noqa: E402
    B3_CONTEXT_COMPONENTS,
    B3_EXPECTED_CONTEXT_COUNT,
    B3_EXPECTED_TARGET_COUNT,
    B3_TARGET_COMPONENTS,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    LOSS_TABLE_CSV,
    MANIFEST_JSON,
    MASK_LEVEL,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    build_b3_pretrained_loss_candidate_inputs_v0,
    build_b3_pretrained_masked_loss_smoke_decision_v0,
    build_b3_pretrained_masked_loss_smoke_v0,
    run_b3_pretrained_masked_loss_smoke_v0,
    validate_step11o_outputs_v0,
)
from covalent_ext.pretrained_masked_loss_smoke import (  # noqa: E402
    build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0,
)

import check_b3_pretrained_masked_loss_smoke_v0 as script  # noqa: E402


O = "opti" + "mizer"
O_STEP = O + "_step"
BWD = "back" + "ward"
TR_FIT = "trainer" + "_fit"


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def _cached_result_json_text() -> str:
    return json.dumps(build_b3_pretrained_masked_loss_smoke_v0(device="cpu"), default=str)


def _cached_result() -> dict:
    return json.loads(_cached_result_json_text())


def test_validate_step11o_outputs_success_and_b3_row_contract():
    assert validate_step11o_outputs_v0() is True
    rows = _read_csv("data/derived/covalent_small/b3_scaffold_only_mask_sweep_v0/b3_scaffold_only_mask_sweep_table.csv")
    b3 = [row for row in rows if row["mask_level"] == MASK_LEVEL]

    assert len(b3) == 1
    assert json.loads(b3[0]["target_atoms"]) == [0, 1, 2]
    assert json.loads(b3[0]["context_atoms"]) == [3, 4, 5, 6]
    assert b3[0]["target_atom_count"] == "3"
    assert b3[0]["context_atom_count"] == "4"
    assert b3[0]["status"] == "passed"


def test_fresh_strict_loaded_pretrained_model_succeeds():
    result = build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(device="cpu")

    assert result["model_instantiated"] is True
    assert result["strict_load_success"] is True
    assert result["pretrained_weights_loaded"] is True
    assert result["pretrained_base_integration_proven"] is True


def test_b3_candidate_input_contract_matches_step11o_counts():
    bundle = build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(device="cpu")
    candidate = build_b3_pretrained_loss_candidate_inputs_v0(bundle["input_contract"], device="cpu")
    metadata = candidate["metadata"]

    assert metadata["mask_level"] == MASK_LEVEL
    assert metadata["b3_target_components"] == B3_TARGET_COMPONENTS
    assert metadata["b3_context_components"] == B3_CONTEXT_COMPONENTS
    assert metadata["b3_target_atom_count"] == B3_EXPECTED_TARGET_COUNT
    assert metadata["b3_context_atom_count"] == B3_EXPECTED_CONTEXT_COUNT
    assert metadata["b3_reactive_atom_in_context"] is True
    assert metadata["b3_reactive_atom_in_target"] is False
    assert metadata["synthetic_shape_smoke_only"] is True
    assert metadata["feature_semantics_known"] is False


def test_run_smoke_returns_finite_differentiable_loss():
    result = run_b3_pretrained_masked_loss_smoke_v0(device="cpu")

    assert result["model_instantiated"] is True
    assert result["strict_load_success"] is True
    assert result["pretrained_weights_loaded"] is True
    assert result["pretrained_base_integration_proven"] is True
    assert result["model_forward_called"] is True
    assert result["loss_computed"] is True
    assert result["selected_loss_key"] == "masked_loss_total_dry"
    assert isinstance(result["selected_loss_value"], float)
    assert math.isfinite(result["selected_loss_value"])
    assert result["loss_requires_grad"] is True
    assert result["loss_finite"] is True
    assert result["b3_target_atom_count"] == 3
    assert result["b3_context_atom_count"] == 4
    assert result["b3_reactive_atom_in_context"] is True
    assert result["b3_reactive_atom_in_target"] is False
    assert result["status"] == "passed"
    assert result["blocking_reasons"] == []


def test_decision_allows_b3_next_smoke_only_when_loss_contract_passes():
    result = run_b3_pretrained_masked_loss_smoke_v0(device="cpu")
    decision = build_b3_pretrained_masked_loss_smoke_decision_v0(result)
    blocked = dict(result, status="blocked", loss_finite=False)
    blocked_decision = build_b3_pretrained_masked_loss_smoke_decision_v0(blocked)

    assert decision["b3_pretrained_masked_loss_smoke_passed"] is True
    assert decision["b3_pretrained_forward_loss_contract_proven"] is True
    assert decision["b3_backward_smoke_allowed"] is True
    assert decision["recommended_next_step"] == "b3_backward_smoke"
    assert blocked_decision["b3_pretrained_masked_loss_smoke_passed"] is False
    assert blocked_decision["recommended_next_step"] == "b3_pretrained_masked_loss_debug"
    for item in [decision, blocked_decision]:
        assert item["training_allowed"] is False
        assert item["formal_training_allowed"] is False
        assert item["finetune_allowed"] is False
        assert item["quality_claim_allowed"] is False
        assert item["parameter_update_allowed"] is False


def test_manifest_contract_and_non_training_boundary():
    manifest = _cached_result()["manifest"]

    assert manifest["stage"] == "b3_pretrained_masked_loss_smoke_v0"
    assert manifest["previous_stage"] == "b3_scaffold_only_mask_sweep_v0"
    assert manifest["step11o_validated"] is True
    assert manifest["mask_level"] == MASK_LEVEL
    assert manifest["input_source"] == "synthetic_10d_shape_contract"
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
    assert manifest["b3_target_components"] == B3_TARGET_COMPONENTS
    assert manifest["b3_context_components"] == B3_CONTEXT_COMPONENTS
    assert manifest["b3_target_atom_count"] == 3
    assert manifest["b3_context_atom_count"] == 4
    assert manifest["b3_target_count_matches_step11o"] is True
    assert manifest["b3_context_count_matches_step11o"] is True
    assert manifest["b3_reactive_atom_in_context"] is True
    assert manifest["b3_reactive_atom_in_target"] is False
    assert manifest["b3_pretrained_masked_loss_smoke_passed"] is True
    assert manifest["b3_pretrained_forward_loss_contract_proven"] is True
    assert manifest["b3_backward_smoke_allowed"] is True
    assert manifest["recommended_next_step"] == "b3_backward_smoke"
    for key in [
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        BWD + "_called",
        O + "_created",
        O_STEP + "_called",
        "training_step_called",
        TR_FIT + "_called",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
    ]:
        assert manifest[key] is False
    assert manifest["all_checks_passed"] is True


def test_script_writes_report_manifest_loss_table_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "b3_pretrained_masked_loss_smoke_v0"
    report_csv = output_root / "report.csv"
    manifest_json = output_root / "manifest.json"
    loss_table_csv = output_root / "loss.csv"
    summary_md = tmp_path / "docs" / "summary.md"
    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "LOSS_TABLE_CSV", loss_table_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu") == 0

    report_rows = _read_csv(report_csv)
    loss_rows = _read_csv(loss_table_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    summary = summary_md.read_text(encoding="utf-8")
    assert len(report_rows) == 8
    assert {row["status"] for row in report_rows} == {"passed"}
    assert len(loss_rows) == 1
    assert loss_rows[0]["status"] == "passed"
    assert manifest["all_checks_passed"] is True
    assert "not training" in summary
    assert "recommended_next_step: b3_backward_smoke" in summary


def test_generated_outputs_and_safety_boundary():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert LOSS_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()

    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    rows = _read_csv(LOSS_TABLE_CSV)
    assert len(_read_csv(REPORT_CSV)) == 8
    assert len(rows) == 1
    assert rows[0]["status"] == "passed"
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


def test_no_forbidden_artifacts_in_step11p_output_root():
    if not OUTPUT_ROOT.exists():
        return
    assert [path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES] == []

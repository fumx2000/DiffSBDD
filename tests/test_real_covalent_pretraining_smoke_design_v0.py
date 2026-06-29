from __future__ import annotations

import ast
import csv
import functools
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
from covalent_ext.real_covalent_pretraining_smoke_design import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    PLAN_TABLE_CSV,
    PLANNED_NEXT_STAGE,
    REPORT_CSV,
    SUMMARY_MD,
    build_real_covalent_pretraining_smoke_design_v0,
    build_real_covalent_pretraining_smoke_plan_v0,
    validate_step12a_outputs_v0,
)

import check_real_covalent_pretraining_smoke_design_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def _cached_result_text() -> str:
    return json.dumps(build_real_covalent_pretraining_smoke_design_v0(), default=str)


def _cached_result() -> dict:
    return json.loads(_cached_result_text())


def test_step12a_precondition_validates():
    assert validate_step12a_outputs_v0() is True


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
        raise AssertionError("short alias B3 must not be accepted")


def test_pretraining_smoke_plan_scope_and_mask_levels():
    plan = build_real_covalent_pretraining_smoke_plan_v0()

    assert plan["planned_stage"] == PLANNED_NEXT_STAGE
    assert plan["planned_input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert plan["planned_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert plan["planned_checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert plan["planned_device_default"] == "cpu"
    assert plan["planned_batch_size"] == 2
    assert plan["planned_num_workers"] == 0
    assert plan["planned_mask_levels"] == CANONICAL_MASK_LEVELS
    assert plan["planned_mask_level_count"] == 5
    assert plan["planned_use_mask_level_aware_validator"] is True
    assert plan["planned_use_synthetic_fallback"] is False
    assert len(plan["plan_table_rows"]) == 5
    assert [row["mask_level"] for row in plan["plan_table_rows"]] == CANONICAL_MASK_LEVELS
    assert {row["status"] for row in plan["plan_table_rows"]} == {"planned"}


def test_pretraining_smoke_plan_safety_flags():
    plan = build_real_covalent_pretraining_smoke_plan_v0()

    assert plan["planned_allow_model_forward"] is True
    assert plan["planned_allow_loss_compute"] is True
    for key in [
        "planned_allow_backward",
        "planned_allow_optimizer",
        "planned_allow_optimizer_step",
        "planned_allow_training_step",
        "planned_allow_trainer_fit",
        "planned_allow_checkpoint_save",
        "planned_allow_model_save",
        "planned_allow_tensor_dump",
    ]:
        assert plan[key] is False
    assert ".npz" in plan["planned_forbidden_artifact_suffixes"]
    assert any("synthetic fallback" in item for item in plan["planned_blocking_criteria"])


def test_manifest_contract_and_decision():
    manifest = _cached_result()["manifest"]

    assert manifest["stage"] == "real_covalent_pretraining_smoke_design_v0"
    assert manifest["previous_stage"] == "real_covalent_feature_mapping_loader_gate_v0"
    assert manifest["step12a_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["selected_real_data_root"] == "data/derived/covalent_small/training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["planned_next_stage"] == PLANNED_NEXT_STAGE
    assert manifest["planned_checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert manifest["planned_batch_size"] == 2
    assert manifest["planned_num_workers"] == 0
    assert manifest["planned_mask_levels"] == CANONICAL_MASK_LEVELS
    assert manifest["planned_mask_level_count"] == 5
    assert manifest["planned_use_mask_level_aware_validator"] is True
    assert manifest["planned_use_synthetic_fallback"] is False
    assert manifest["real_covalent_pretraining_smoke_design_passed"] is True
    assert manifest["real_covalent_forward_loss_smoke_plan_ready"] is True
    assert manifest["real_covalent_forward_loss_smoke_allowed"] is True
    assert manifest["recommended_next_step"] == "real_covalent_pretrained_forward_loss_smoke"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_manifest_current_step_safety_flags():
    manifest = _cached_result()["manifest"]

    for key in [
        "model_forward_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "original_diffsbdd_source_modified",
        "forbidden_artifacts_created",
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
    ]:
        assert manifest[key] is False


def test_plan_table_reactive_regions():
    rows = build_real_covalent_pretraining_smoke_plan_v0()["plan_table_rows"]
    by_level = {row["mask_level"]: row for row in rows}

    assert by_level["B3_scaffold_only"]["expected_reactive_atom_region"] == "context"
    for level in ["A_warhead_only", "B_linker_warhead", "B2_scaffold_warhead", "C_scaffold_linker_warhead"]:
        assert by_level[level]["expected_reactive_atom_region"] == "target"


def test_script_writes_report_manifest_plan_table_and_summary(tmp_path, monkeypatch):
    report_csv = tmp_path / "report.csv"
    manifest_json = tmp_path / "manifest.json"
    plan_csv = tmp_path / "plan.csv"
    summary_md = tmp_path / "summary.md"
    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "PLAN_TABLE_CSV", plan_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run() == 0

    report_rows = _read_csv(report_csv)
    plan_rows = _read_csv(plan_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    summary = summary_md.read_text(encoding="utf-8")
    assert len(report_rows) == 8
    assert {row["status"] for row in report_rows} == {"passed"}
    assert len(plan_rows) == 5
    assert [row["mask_level"] for row in plan_rows] == CANONICAL_MASK_LEVELS
    assert manifest["all_checks_passed"] is True
    assert "design only, not training" in summary
    assert "recommended_next_step: real_covalent_pretrained_forward_loss_smoke" in summary


def test_generated_outputs_and_no_forbidden_artifacts():
    if not MANIFEST_JSON.is_file():
        assert script.run() == 0

    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert PLAN_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()
    assert len(_read_csv(REPORT_CSV)) == 8
    assert len(_read_csv(PLAN_TABLE_CSV)) == 5
    assert json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))["all_checks_passed"] is True
    forbidden = [path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES]
    assert forbidden == []


def test_no_protected_source_modification():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_ast_safety_for_step12c_files():
    files = [
        "src/covalent_ext/real_covalent_pretraining_smoke_design.py",
        "scripts/check_real_covalent_pretraining_smoke_design_v0.py",
        "tests/test_real_covalent_pretraining_smoke_design_v0.py",
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

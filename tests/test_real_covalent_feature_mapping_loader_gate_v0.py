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

from covalent_ext.real_covalent_feature_mapping_loader_gate import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SAMPLE_TABLE_CSV,
    SUMMARY_MD,
    audit_real_covalent_sample_fields_v0,
    build_real_covalent_feature_mapping_loader_gate_v0,
    derive_and_validate_five_level_masks_for_real_sample_v0,
    discover_existing_real_covalent_artifacts_v0,
    run_real_covalent_batch_adapter_gate_v0,
    validate_step11r_outputs_v0,
)

import check_real_covalent_feature_mapping_loader_gate_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def _cached_result_text() -> str:
    return json.dumps(build_real_covalent_feature_mapping_loader_gate_v0(), default=str)


def _cached_result() -> dict:
    return json.loads(_cached_result_text())


def test_validate_step11r_outputs_success():
    assert validate_step11r_outputs_v0() is True


def test_artifact_discovery_is_read_only_and_selects_real_covalent_npz():
    before = sorted(str(path) for path in OUTPUT_ROOT.rglob("*")) if OUTPUT_ROOT.exists() else []
    discovery = discover_existing_real_covalent_artifacts_v0()
    after = sorted(str(path) for path in OUTPUT_ROOT.rglob("*")) if OUTPUT_ROOT.exists() else []

    assert before == after
    assert discovery["discovered_artifact_count"] >= 1
    assert discovery["discovered_manifest_count"] >= 1
    assert discovery["discovered_npz_count"] >= 3
    assert discovery["selected_artifact_is_real_covalent"] is True
    assert discovery["selected_artifact_is_synthetic_only"] is False
    assert discovery["selected_real_data_root"] == "data/derived/covalent_small/training_tensor_materialized_v0"
    assert discovery["selected_loader_or_tensor_artifact"].endswith("sample_index.csv")


def test_real_sample_field_audit_passes_three_existing_samples():
    discovery = discover_existing_real_covalent_artifacts_v0()
    rows = audit_real_covalent_sample_fields_v0(discovery["selected"])

    assert len(rows) == 3
    assert {row["status"] for row in rows} == {"passed"}
    for row in rows:
        assert row["selected_artifact_is_real_covalent"] is True
        assert row["selected_artifact_is_synthetic_only"] is False
        assert row["ligand_atom_count"] > 0
        assert row["protein_atom_count"] > 0
        assert row["ligand_coords_shape"][-1] == 3
        assert row["protein_coords_shape"][-1] == 3
        assert row["ligand_feature_source"] == "ligand_atomic_numbers_read_only"
        assert row["ligand_feature_dim"] == 10
        assert row["scaffold_atom_count"] > 0
        assert row["linker_atom_count"] > 0
        assert row["warhead_atom_count"] > 0
        assert row["masks_disjoint"] is True
        assert row["masks_cover_assigned_ligand_atoms"] is True
        assert row["reactive_atom_in_range"] is True
        assert row["reactive_atom_in_warhead"] is True
        assert row["coords_finite"] is True
        assert row["features_finite"] is True


def test_five_level_real_mask_derivation_and_b3_b2_contrast():
    discovery = discover_existing_real_covalent_artifacts_v0()
    rows = audit_real_covalent_sample_fields_v0(discovery["selected"])
    results = [derive_and_validate_five_level_masks_for_real_sample_v0(row) for row in rows]

    assert {result["status"] for result in results} == {"passed"}
    for result in results:
        assert result["all_five_level_masks_available"] is True
        assert set(result["per_level"]) == set(CANONICAL_MASK_LEVELS)
        assert result["real_b3_target_is_scaffold"] is True
        assert result["real_b3_context_is_linker_warhead"] is True
        assert result["real_b3_reactive_atom_in_context"] is True
        assert result["real_b3_reactive_atom_in_target"] is False
        assert result["real_b2_target_includes_scaffold"] is True
        assert result["real_b2_target_includes_warhead"] is True
        assert result["real_b2_context_is_linker"] is True
        assert result["real_b2_b3_contrast_passed"] is True


def test_real_batch_adapter_and_model_input_mapping_gate_pass():
    discovery = discover_existing_real_covalent_artifacts_v0()
    gate = run_real_covalent_batch_adapter_gate_v0(discovery["selected"])

    assert gate["dataset_created"] is True
    assert gate["dataloader_created"] is True
    assert gate["batch_size"] == 2
    assert gate["real_batch_adapter_gate_passed"] is True
    assert gate["real_model_input_mapping_gate_passed"] is True
    assert set(gate["level_results"]) == set(CANONICAL_MASK_LEVELS)
    for level, result in gate["level_results"].items():
        assert result["adapted_valid"] is True
        assert result["model_input_valid"] is True
        assert result["diffsbdd_like_valid"] is True
        assert result["target_atom_count"] > 0
        assert result["ligand_feature_dim"] == 11
        assert result["pocket_feature_dim"] == 11
        if level == "B3_scaffold_only":
            assert result["model_input_valid_raw"] is False
            assert result["model_input_b3_aware_override"] is True


def test_missing_artifact_path_blocks_cleanly_without_synthetic_pass():
    gate = run_real_covalent_batch_adapter_gate_v0(None)

    assert gate["dataset_created"] is False
    assert gate["dataloader_created"] is False
    assert gate["real_batch_adapter_gate_passed"] is False
    assert gate["real_model_input_mapping_gate_passed"] is False
    assert gate["blocking_reasons"] == ["selected_artifact_missing"]


def test_manifest_contract_and_safety_boundary():
    manifest = _cached_result()["manifest"]

    assert manifest["stage"] == "real_covalent_feature_mapping_loader_gate_v0"
    assert manifest["previous_stage"] == "b3_single_optimizer_step_smoke_v0"
    assert manifest["step11r_validated"] is True
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["audited_real_sample_count"] == 3
    assert manifest["passed_real_sample_count"] == 3
    assert manifest["failed_real_sample_count"] == 0
    assert manifest["canonical_mask_levels"] == CANONICAL_MASK_LEVELS
    assert manifest["all_five_level_masks_available"] is True
    assert manifest["real_five_level_mask_contract_proven"] is True
    assert manifest["real_b3_target_is_scaffold"] is True
    assert manifest["real_b3_context_is_linker_warhead"] is True
    assert manifest["real_b3_reactive_atom_in_context"] is True
    assert manifest["real_b3_reactive_atom_in_target"] is False
    assert manifest["real_b2_b3_contrast_passed"] is True
    assert manifest["real_batch_adapter_gate_passed"] is True
    assert manifest["real_model_input_mapping_gate_passed"] is True
    assert manifest["real_covalent_feature_mapping_loader_gate_passed"] is True
    assert manifest["real_covalent_sample_field_contract_proven"] is True
    assert manifest["real_b3_loader_contract_proven"] is True
    assert manifest["real_covalent_pretraining_smoke_allowed"] is True
    assert manifest["recommended_next_step"] == "real_covalent_pretraining_smoke_design"
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
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "parameter_update_allowed",
        "original_diffsbdd_source_modified",
        "forbidden_artifacts_created",
    ]:
        assert manifest[key] is False
    assert manifest["all_checks_passed"] is True


def test_script_writes_report_manifest_sample_table_and_summary(tmp_path, monkeypatch):
    report_csv = tmp_path / "report.csv"
    manifest_json = tmp_path / "manifest.json"
    sample_csv = tmp_path / "sample.csv"
    summary_md = tmp_path / "summary.md"
    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "SAMPLE_TABLE_CSV", sample_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run() == 0

    report_rows = _read_csv(report_csv)
    sample_rows = _read_csv(sample_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    summary = summary_md.read_text(encoding="utf-8")
    assert len(report_rows) == 9
    assert {row["status"] for row in report_rows} == {"passed"}
    assert len(sample_rows) == 3
    assert {row["status"] for row in sample_rows} == {"passed"}
    assert manifest["all_checks_passed"] is True
    assert "not training" in summary
    assert "recommended_next_step: real_covalent_pretraining_smoke_design" in summary


def test_generated_outputs_and_no_forbidden_artifacts():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert SAMPLE_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()
    assert len(_read_csv(REPORT_CSV)) == 9
    assert len(_read_csv(SAMPLE_TABLE_CSV)) == 3
    assert json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))["all_checks_passed"] is True
    assert [path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES] == []


def test_no_protected_source_modification():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_ast_safety_for_step12a_files():
    files = [
        "src/covalent_ext/real_covalent_feature_mapping_loader_gate.py",
        "scripts/check_real_covalent_feature_mapping_loader_gate_v0.py",
        "tests/test_real_covalent_feature_mapping_loader_gate_v0.py",
    ]
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
                assert func.id not in {"training_step", "save_checkpoint", "load_from_checkpoint"}

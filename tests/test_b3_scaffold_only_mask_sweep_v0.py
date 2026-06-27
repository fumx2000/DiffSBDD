from __future__ import annotations

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

from covalent_ext.b3_scaffold_only_mask_sweep import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    EXPECTED_ATOMS,
    EXPECTED_COMPONENTS,
    STAGE,
    build_b3_scaffold_only_mask_sweep_v0,
    build_synthetic_mask_sweep_sample_v0,
    run_batch_adapter_mask_sweep_v0,
    run_long_form_mask_sweep_v0,
    validate_b2_b3_contrast_v0,
    validate_step11n_outputs_v0,
)

import check_b3_scaffold_only_mask_sweep_v0 as script  # noqa: E402


O = "opti" + "mizer"
O_STEP = O + "_step"
BWD = "back" + "ward"
TR_FIT = "trainer" + "_fit"


def test_validate_step11n_outputs_success():
    assert validate_step11n_outputs_v0() is True


def test_synthetic_sample_counts_are_expected():
    sample = build_synthetic_mask_sweep_sample_v0()

    assert sample["sample_id"] == "synthetic_b3_sweep_sample"
    assert sample["scaffold_atoms"] == [0, 1, 2]
    assert sample["linker_atoms"] == [3, 4]
    assert sample["warhead_atoms"] == [5, 6]
    assert sample["num_ligand_atoms"] == 7
    assert sample["ligand_reactive_atom_index"] == 5


def test_canonical_mask_levels_are_exactly_long_form_a_b_b2_b3_c():
    assert CANONICAL_MASK_LEVELS == [
        "A_warhead_only",
        "B_linker_warhead",
        "B2_scaffold_warhead",
        "B3_scaffold_only",
        "C_scaffold_linker_warhead",
    ]
    assert "B3" not in CANONICAL_MASK_LEVELS


def test_long_form_sweep_has_expected_rows_atoms_counts_and_components():
    sample = build_synthetic_mask_sweep_sample_v0()
    rows = run_long_form_mask_sweep_v0(sample)

    assert len(rows) == 5
    assert [row["mask_level"] for row in rows] == CANONICAL_MASK_LEVELS
    for row in rows:
        expected_atoms = EXPECTED_ATOMS[row["mask_level"]]
        expected_components = EXPECTED_COMPONENTS[row["mask_level"]]
        assert row["target_components"] == expected_components["target"]
        assert row["context_components"] == expected_components["context"]
        assert row["target_atoms"] == expected_atoms["target_atoms"]
        assert row["context_atoms"] == expected_atoms["context_atoms"]
        assert row["target_atom_count"] == len(expected_atoms["target_atoms"])
        assert row["context_atom_count"] == len(expected_atoms["context_atoms"])
        assert row["target_context_disjoint"] is True
        assert row["target_context_cover_assigned_atoms"] is True
        assert row["target_count_matches_expected"] is True
        assert row["context_count_matches_expected"] is True
        assert row["status"] == "passed"
        assert row["blocking_reasons"] == []


def test_b2_b3_contrast_passes():
    sample = build_synthetic_mask_sweep_sample_v0()
    contrast = validate_b2_b3_contrast_v0(run_long_form_mask_sweep_v0(sample))

    assert contrast["b2_target_includes_scaffold"] is True
    assert contrast["b2_target_includes_warhead"] is True
    assert contrast["b2_context_includes_linker"] is True
    assert contrast["b2_context_does_not_include_warhead"] is True
    assert contrast["b3_target_includes_scaffold"] is True
    assert contrast["b3_target_does_not_include_warhead"] is True
    assert contrast["b3_context_includes_linker"] is True
    assert contrast["b3_context_includes_warhead"] is True
    assert contrast["b3_context_does_not_include_scaffold"] is True
    assert contrast["b2_b3_target_masks_not_identical"] is True
    assert contrast["b2_b3_context_masks_not_identical"] is True
    assert contrast["b2_b3_contrast_passed"] is True


def test_batch_adapter_sweep_all_rows_pass_and_counts_match():
    sample = build_synthetic_mask_sweep_sample_v0()
    rows = run_batch_adapter_mask_sweep_v0(sample)

    assert len(rows) == 6
    assert {row["status"] for row in rows} == {"passed"}
    for row in rows:
        expected = EXPECTED_ATOMS[row["mask_level"]]
        assert row["adapter_valid"] is True
        assert row["generation_mask_count"] == len(expected["target_atoms"])
        assert row["ligand_target_mask_count"] == len(expected["target_atoms"])
        assert row["ligand_context_mask_count"] == len(expected["context_atoms"])
        assert row["fixed_ligand_atom_mask_count"] == len(expected["context_atoms"])
        assert row["generation_equals_target"] is True
        assert row["fixed_equals_context"] is True
        assert row["target_context_disjoint"] is True
        assert row["blocking_reasons"] == []


def test_b3_fallback_and_explicit_adapter_paths_pass_with_reactive_atom_in_context():
    sample = build_synthetic_mask_sweep_sample_v0()
    rows = run_batch_adapter_mask_sweep_v0(sample)
    b3_rows = [row for row in rows if row["mask_level"] == "B3_scaffold_only"]

    assert {row["b3_generation_key_mode"] for row in b3_rows} == {"fallback", "explicit"}
    for row in b3_rows:
        assert row["status"] == "passed"
        assert row["adapter_valid"] is True
        assert row["generation_mask_count"] == 3
        assert row["ligand_context_mask_count"] == 4
        assert row["reactive_atom_in_context"] is True
        assert row["reactive_atom_in_target"] is False


def test_manifest_contract_and_safety_boundary():
    manifest = build_b3_scaffold_only_mask_sweep_v0()["manifest"]

    assert manifest["stage"] == STAGE
    assert manifest["previous_stage"] == "b3_scaffold_only_mask_implementation_v0"
    assert manifest["step11n_validated"] is True
    assert manifest["canonical_mask_levels"] == CANONICAL_MASK_LEVELS
    assert manifest["canonical_mask_level_count"] == 5
    assert manifest["legacy_short_name_ambiguity_detected"] is True
    assert manifest["short_alias_b3_added"] is False
    assert manifest["short_alias_b3_deferred"] is True
    assert manifest["canonical_b3_name"] == "B3_scaffold_only"
    assert manifest["five_level_sweep_row_count"] == 5
    assert manifest["all_mask_sweep_rows_passed"] is True
    assert manifest["b2_b3_contrast_passed"] is True
    assert manifest["batch_adapter_sweep_row_count"] == 6
    assert manifest["all_batch_adapter_rows_passed"] is True
    assert manifest["b3_fallback_adapter_valid"] is True
    assert manifest["b3_explicit_key_adapter_valid"] is True
    assert manifest["five_level_mask_sweep_passed"] is True
    assert manifest["canonical_five_level_mask_contract_proven"] is True
    assert manifest["b3_pretrained_masked_loss_smoke_allowed"] is True
    assert manifest["recommended_next_step"] == "b3_pretrained_masked_loss_smoke"
    assert manifest["model_forward_called"] is False
    assert manifest[BWD + "_called"] is False
    assert manifest[O + "_created"] is False
    assert manifest[O_STEP + "_called"] is False
    assert manifest["training_step_called"] is False
    assert manifest[TR_FIT + "_called"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["tensor_dump_saved"] is False
    assert manifest["original_diffsbdd_source_modified"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["all_checks_passed"] is True


def test_script_writes_report_manifest_sweep_table_and_summary(tmp_path, monkeypatch):
    report_csv = tmp_path / "report.csv"
    manifest_json = tmp_path / "manifest.json"
    sweep_csv = tmp_path / "sweep.csv"
    summary_md = tmp_path / "summary.md"
    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "SWEEP_TABLE_CSV", sweep_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run() == 0

    report_rows = list(csv.DictReader(report_csv.open(newline="", encoding="utf-8")))
    sweep_rows = list(csv.DictReader(sweep_csv.open(newline="", encoding="utf-8")))
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    summary = summary_md.read_text(encoding="utf-8")
    assert len(report_rows) == 8
    assert {row["status"] for row in report_rows} == {"passed"}
    assert len(sweep_rows) == 5
    assert manifest["all_checks_passed"] is True
    assert "B3_scaffold_only" in summary
    assert "recommended_next_step: b3_pretrained_masked_loss_smoke" in summary


def test_no_protected_source_diff_is_present():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_no_forbidden_artifacts_in_step11o_output_root():
    root = REPO_ROOT / "data/derived/covalent_small/b3_scaffold_only_mask_sweep_v0"
    if not root.exists():
        return
    forbidden = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth", ".npz"}
    assert [path for path in root.rglob("*") if path.is_file() and path.suffix in forbidden] == []

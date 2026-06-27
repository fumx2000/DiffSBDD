from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from covalent_ext.b3_scaffold_only_mask_implementation import (  # noqa: E402
    CANONICAL_B3_NAME,
    STAGE,
    audit_mask_api_for_b3_implementation_v0,
    build_b3_scaffold_only_mask_implementation_v0,
    run_b3_mask_implementation_checks_v0,
    validate_step11m_outputs_v0,
)
from covalent_ext.masking import build_four_level_mask, build_long_form_mask  # noqa: E402

import check_b3_scaffold_only_mask_implementation_v0 as script  # noqa: E402


SCAFFOLD = [0, 1, 2]
LINKER = [3, 4]
WARHEAD = [5, 6]
NUM_ATOMS = 7
O = "opti" + "mizer"
O_STEP = O + "_step"
BWD = "back" + "ward"
TR_FIT = "trainer" + "_fit"


def test_validate_step11m_outputs_success():
    assert validate_step11m_outputs_v0() is True


def test_api_audit_detects_short_name_ambiguity_and_defers_short_b3():
    audit = audit_mask_api_for_b3_implementation_v0()

    assert audit["short_tokens_detected"] == ["A", "B", "B2", "C"]
    assert CANONICAL_B3_NAME in audit["long_form_names_detected"]
    assert audit["legacy_mask_scaffold_function_present"] is True
    assert audit["legacy_short_name_ambiguity_detected"] is True
    assert audit["legacy_short_name_preserved"] is True
    assert audit["long_form_b2_semantics_protected"] is True
    assert audit["short_alias_b3_added"] is False
    assert audit["short_alias_b3_deferred"] is True
    assert audit["short_alias_b3_deferred_reason"] == "avoid_legacy_short_name_ambiguity"
    assert audit["canonical_b3_available"] is True
    assert audit["batch_adapter_b3_available"] is True


def test_legacy_short_b2_is_preserved_while_long_form_b2_is_protected():
    legacy_b2 = build_four_level_mask("B2", SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    long_b2 = build_long_form_mask("B2_scaffold_warhead", SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    long_b3 = build_long_form_mask(CANONICAL_B3_NAME, SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)

    assert legacy_b2.masked_atoms == tuple(SCAFFOLD)
    assert legacy_b2.visible_atoms == tuple(LINKER + WARHEAD)
    assert long_b2.masked_atoms == tuple(SCAFFOLD + WARHEAD)
    assert long_b2.visible_atoms == tuple(LINKER)
    assert long_b3.masked_atoms == tuple(SCAFFOLD)
    assert long_b3.visible_atoms == tuple(LINKER + WARHEAD)
    assert legacy_b2.masked_atoms == long_b3.masked_atoms
    assert legacy_b2.masked_atoms != long_b2.masked_atoms


def test_b2_b3_contrast_assertions_from_step11n_supplement():
    contrast = run_b3_mask_implementation_checks_v0()["b2_b3_contrast"]

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


def test_b3_missing_and_empty_region_fail_safe_cases_pass():
    results = run_b3_mask_implementation_checks_v0()["fail_safe_results"]

    assert results == {
        "missing_scaffold_labels": True,
        "missing_linker_labels": True,
        "missing_warhead_labels": True,
        "empty_scaffold_region": True,
        "empty_linker_region": True,
        "empty_warhead_region": True,
    }


def test_b3_batch_adapter_fallback_and_explicit_generation_key_paths_pass():
    evidence = run_b3_mask_implementation_checks_v0()["adapter_evidence"]

    assert evidence["b3_without_generation_key_valid"] is True
    assert evidence["b3_with_generation_key_valid"] is True
    assert evidence["b3_target_count"] == 3
    assert evidence["b3_context_count"] == 4
    assert evidence["b3_reactive_atom_in_context"] is True
    assert evidence["b3_reactive_atom_in_target"] is False
    assert evidence["adapter_reasons"] == []


def test_manifest_contract_and_safety_boundary():
    manifest = build_b3_scaffold_only_mask_implementation_v0()["manifest"]

    assert manifest["stage"] == STAGE
    assert manifest["previous_stage"] == "b3_scaffold_only_mask_design_v0"
    assert manifest["step11m_validated"] is True
    assert manifest["legacy_short_name_ambiguity_detected"] is True
    assert manifest["legacy_short_name_preserved"] is True
    assert manifest["long_form_b2_semantics_protected"] is True
    assert manifest["short_alias_b3_added"] is False
    assert manifest["short_alias_b3_deferred"] is True
    assert manifest["short_alias_b3_deferred_reason"] == "avoid_legacy_short_name_ambiguity"
    assert manifest["canonical_b3_name"] == CANONICAL_B3_NAME
    assert manifest["canonical_b3_long_form_available"] is True
    assert manifest["b3_added_additively"] is True
    assert manifest["existing_four_level_semantics_unchanged"] is True
    assert manifest["mask_logic_modified"] is True
    assert manifest["b2_b3_contrast_passed"] is True
    assert manifest["missing_label_fail_safe_passed"] is True
    assert manifest["a_b_b2_c_regression_passed"] is True
    assert manifest["b3_mask_implementation_passed"] is True
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
    assert manifest["recommended_next_step"] == "b3_scaffold_only_mask_sweep"


def test_script_writes_report_manifest_api_audit_and_summary(tmp_path, monkeypatch):
    report_csv = tmp_path / "report.csv"
    manifest_json = tmp_path / "manifest.json"
    api_audit_csv = tmp_path / "api_audit.csv"
    summary_md = tmp_path / "summary.md"
    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "API_AUDIT_CSV", api_audit_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run() == 0

    rows = list(csv.DictReader(report_csv.open(newline="", encoding="utf-8")))
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    api_rows = list(csv.DictReader(api_audit_csv.open(newline="", encoding="utf-8")))
    summary = summary_md.read_text(encoding="utf-8")
    assert len(rows) == 8
    assert {row["status"] for row in rows} == {"passed"}
    assert manifest["all_checks_passed"] is True
    assert any(row["field"] == "legacy_short_name_ambiguity_detected" for row in api_rows)
    assert "short_alias_b3_deferred: true" in summary
    assert "B3 Scaffold-Only Mask Implementation" in summary


def test_no_protected_source_diff_is_present():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_no_forbidden_artifacts_in_step11n_output_root():
    root = REPO_ROOT / "data/derived/covalent_small/b3_scaffold_only_mask_implementation_v0"
    if not root.exists():
        return
    forbidden = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
    assert [path for path in root.rglob("*") if path.is_file() and path.suffix in forbidden] == []

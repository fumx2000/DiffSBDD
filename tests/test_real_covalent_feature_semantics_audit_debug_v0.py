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

from covalent_ext.real_covalent_feature_semantics_audit_debug import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    DEBUG_TABLE_CSV,
    FILTER_POLICY_NAME,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    locate_unknown_protein_atoms_v0,
    simulate_noncheckpoint_pocket_atom_filter_projection_v0,
    validate_step12b_validator_behavior_v0,
    validate_step12f_clean_block_v0,
)

import check_real_covalent_feature_semantics_audit_debug_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (REPORT_CSV.is_file() and MANIFEST_JSON.is_file() and DEBUG_TABLE_CSV.is_file() and SUMMARY_MD.is_file()):
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def _debug_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(DEBUG_TABLE_CSV)


def _bool(value: str) -> bool:
    return str(value).lower() == "true"


def _json_value(value: str):
    return json.loads(value) if value else []


def test_step12f_clean_block_and_step12b_validator_validate():
    assert validate_step12f_clean_block_v0() is True
    assert validate_step12b_validator_behavior_v0() is True


def test_localization_finds_two_real_mg_atoms_with_finite_geometry():
    localization = locate_unknown_protein_atoms_v0()

    assert localization["mg_localization_passed"] is True
    assert localization["mg_atom_count"] == 2
    assert localization["mg_sample_ids"] == ["KRAS_G12C_5F2E_pre_reaction", "KRAS_G12C_6OIM_pre_reaction"]
    assert localization["mg_all_coords_available"] is True
    assert localization["mg_direct_ligand_contact_detected"] is False
    assert localization["mg_close_to_ligand_detected"] is True
    assert localization["metadata_available_for_any_mg"] is True
    for row in localization["rows"]:
        assert row["sample_id"]
        assert row["protein_atom_local_index"] >= 0
        assert math.isfinite(row["protein_coord_x"])
        assert math.isfinite(row["protein_coord_y"])
        assert math.isfinite(row["protein_coord_z"])
        assert math.isfinite(row["min_distance_to_any_ligand_atom"])
        assert row["nearest_ligand_atom_index"] >= 0
        assert math.isfinite(row["distance_to_ligand_centroid"])
        assert math.isfinite(row["ligand_reactive_atom_distance"])
        assert isinstance(row["direct_ligand_contact_candidate"], bool)


def test_projection_filter_restores_sample_vocabulary_and_mask_conversions():
    projection = simulate_noncheckpoint_pocket_atom_filter_projection_v0()

    assert projection["filter_policy_name"] == FILTER_POLICY_NAME
    assert projection["projection_filter_only_debug"] is True
    assert projection["production_adapter_modified"] is False
    assert projection["original_data_modified"] is False
    assert set(projection["filtered_atom_numbers"]).issubset({12})
    assert projection["total_removed_pocket_atom_count"] == 2
    assert projection["post_filter_protein_unknown_atom_count"] == 0
    assert projection["post_filter_ligand_unknown_atom_count"] == 0
    assert projection["all_remaining_protein_atoms_in_checkpoint_10d_vocab"] is True
    assert projection["all_ligand_atoms_in_checkpoint_10d_vocab"] is True
    assert projection["audited_mask_level_count"] == 5
    assert projection["passed_mask_level_count"] == 5
    assert projection["failed_mask_level_count"] == 0
    assert projection["all_checkpoint_compatible_batches_constructed_after_filter"] is True
    assert projection["all_ligand_one_hot_row_sums_valid_after_filter"] is True
    assert projection["all_pocket_one_hot_row_sums_valid_after_filter"] is True
    assert projection["all_pocket_unknown_atom_count_zero_after_filter"] is True
    assert projection["all_ligand_unknown_atom_count_zero_after_filter"] is True
    assert projection["ligand_masks_unchanged_after_filter"] is True
    assert projection["ligand_reactive_atom_region_preserved"] is True
    assert projection["no_synthetic_fallback_used"] is True


def test_manifest_core_contract_and_decision():
    manifest = _manifest()

    assert manifest["stage"] == "real_covalent_feature_semantics_audit_debug_v0"
    assert manifest["previous_stage"] == "real_covalent_feature_semantics_audit_v0"
    assert manifest["step12f_clean_block_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["pre_debug_protein_unknown_atom_numbers"] == [12]
    assert manifest["pre_debug_protein_unknown_atom_count"] == 2
    assert manifest["pre_debug_ligand_unknown_atom_count"] == 0
    assert manifest["unknown_protein_atom_symbol"] == "Mg"
    assert manifest["unknown_protein_atom_atomic_number"] == 12
    assert manifest["unknown_protein_atom_localization_passed"] is True
    assert manifest["mg_localization_passed"] is True
    assert manifest["mg_atom_count"] == 2
    assert manifest["mg_sample_ids"] == ["KRAS_G12C_5F2E_pre_reaction", "KRAS_G12C_6OIM_pre_reaction"]
    assert manifest["mg_direct_ligand_contact_detected"] is False
    assert manifest["mg_close_to_ligand_detected"] is True
    assert manifest["filter_policy_name"] == FILTER_POLICY_NAME
    assert manifest["projection_filter_only_debug"] is True
    assert manifest["production_adapter_modified"] is False
    assert manifest["original_data_modified"] is False
    assert manifest["filtered_atom_numbers"] == [12]
    assert manifest["filtered_atom_symbols"] == ["Mg"]
    assert manifest["total_removed_pocket_atom_count"] == 2
    assert manifest["post_filter_protein_unknown_atom_count"] == 0
    assert manifest["post_filter_ligand_unknown_atom_count"] == 0
    assert manifest["all_remaining_protein_atoms_in_checkpoint_10d_vocab"] is True
    assert manifest["all_ligand_atoms_in_checkpoint_10d_vocab"] is True


def test_manifest_mask_level_projection_and_safety():
    manifest = _manifest()

    assert manifest["audited_mask_level_count"] == 5
    assert manifest["passed_mask_level_count"] == 5
    assert manifest["failed_mask_level_count"] == 0
    assert manifest["all_checkpoint_compatible_batches_constructed_after_filter"] is True
    assert manifest["all_ligand_one_hot_row_sums_valid_after_filter"] is True
    assert manifest["all_pocket_one_hot_row_sums_valid_after_filter"] is True
    assert manifest["all_pocket_unknown_atom_count_zero_after_filter"] is True
    assert manifest["all_ligand_unknown_atom_count_zero_after_filter"] is True
    assert manifest["ligand_masks_unchanged_after_filter"] is True
    assert manifest["ligand_reactive_atom_region_preserved"] is True
    assert manifest["no_synthetic_fallback_used"] is True
    assert manifest["noncheckpoint_pocket_atom_filter_policy_recommended"] is True
    assert manifest["projection_filter_debug_passed"] is True
    assert manifest["real_covalent_feature_semantics_audit_debug_passed"] is True
    assert manifest["real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed"] is True
    assert manifest["real_covalent_cuda_forward_backward_smoke_allowed"] is False
    assert manifest["real_covalent_single_optimizer_step_smoke_allowed"] is False
    assert manifest["recommended_next_step"] == "real_covalent_noncheckpoint_pocket_atom_filter_gate"
    for key in [
        "model_forward_called",
        "loss_compute_called",
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


def test_debug_table_row_counts_and_unknown_atom_rows():
    rows = _debug_rows()
    unknown_rows = [row for row in rows if row["row_type"] == "unknown_protein_atom"]
    sample_rows = [row for row in rows if row["row_type"] == "sample_filter_projection"]
    mask_rows = [row for row in rows if row["row_type"] == "mask_level_filter_projection"]
    decision_rows = [row for row in rows if row["row_type"] == "filter_policy_decision"]

    assert len(unknown_rows) == 2
    assert len(sample_rows) == 3
    assert len(mask_rows) == 5
    assert len(decision_rows) == 1
    for row in unknown_rows:
        assert row["sample_id"]
        assert int(row["protein_atom_local_index"]) >= 0
        assert math.isfinite(float(row["protein_coord_x"]))
        assert math.isfinite(float(row["protein_coord_y"]))
        assert math.isfinite(float(row["protein_coord_z"]))
        assert math.isfinite(float(row["min_distance_to_any_ligand_atom"]))
        assert int(row["nearest_ligand_atom_index"]) >= 0
        assert math.isfinite(float(row["distance_to_ligand_centroid"]))
        assert math.isfinite(float(row["ligand_reactive_atom_distance"]))
        assert row["direct_ligand_contact_candidate"] in {"True", "False"}
        assert row["metadata_available"] in {"True", "False"}


def test_debug_table_sample_and_mask_projection_rows():
    rows = _debug_rows()
    sample_rows = [row for row in rows if row["row_type"] == "sample_filter_projection"]
    mask_rows = [row for row in rows if row["row_type"] == "mask_level_filter_projection"]

    assert sum(int(row["removed_protein_atom_count"]) for row in sample_rows) == 2
    for row in sample_rows:
        assert _bool(row["all_remaining_protein_atoms_in_checkpoint_10d_vocab"])
        assert _bool(row["all_ligand_atoms_in_checkpoint_10d_vocab"])
        assert int(row["post_filter_unknown_protein_atom_count"]) == 0
        assert int(row["post_filter_unknown_ligand_atom_count"]) == 0
        assert row["status"] == "passed"
    assert [row["mask_level"] for row in mask_rows] == CANONICAL_MASK_LEVELS
    for row in mask_rows:
        expected_region = "context" if row["mask_level"] == "B3_scaffold_only" else "target"
        assert row["expected_reactive_atom_region"] == expected_region
        assert _bool(row["checkpoint_compatible_batch_constructed_after_filter"])
        assert row["ligand_feature_dim"] == "10"
        assert row["pocket_feature_dim"] == "10"
        assert _bool(row["ligand_one_hot_row_sums_valid_after_filter"])
        assert _bool(row["pocket_one_hot_row_sums_valid_after_filter"])
        assert row["ligand_unknown_atom_count_after_filter"] == "0"
        assert row["pocket_unknown_atom_count_after_filter"] == "0"
        assert set(_json_value(row["removed_pocket_atom_numbers"])).issubset({12})
        assert _bool(row["no_synthetic_fallback_used"])
        assert _bool(row["ligand_masks_unchanged_after_filter"])
        assert _bool(row["ligand_reactive_atom_region_preserved"])
        assert row["status"] == "passed"


def test_report_manifest_debug_table_and_summary_written():
    _ensure_outputs()

    report_rows = _read_csv(REPORT_CSV)
    summary = SUMMARY_MD.read_text(encoding="utf-8")
    assert len(report_rows) == 8
    assert {row["status"] for row in report_rows} == {"passed"}
    assert "Mg / atomic_number=12" in summary
    assert "projection-level" in summary
    assert "not an optimizer step" in summary
    assert "recommended_next_step: real_covalent_noncheckpoint_pocket_atom_filter_gate" in summary


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


def test_ast_safety_for_step12g_files():
    files = [
        "src/covalent_ext/real_covalent_feature_semantics_audit_debug.py",
        "scripts/check_real_covalent_feature_semantics_audit_debug_v0.py",
        "tests/test_real_covalent_feature_semantics_audit_debug_v0.py",
    ]
    for relative in files:
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner == "torch" and func.attr == "save")
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in {"backward", "fit", "training_step"}
            if isinstance(func, ast.Name):
                assert func.id not in {"Adam", "AdamW", "SGD", "RMSprop"}

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

from covalent_ext.real_covalent_noncheckpoint_pocket_atom_filter_gate import (  # noqa: E402
    ALLOWED_FILTERED_ATOM_SYMBOLS_FOR_THIS_GATE,
    ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE,
    CANONICAL_MASK_LEVELS,
    FILTER_POLICY_NAME,
    FILTER_TABLE_CSV,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    filter_noncheckpoint_vocab_pocket_atoms_v0,
    run_noncheckpoint_pocket_atom_filter_gate_v0,
    validate_step12b_validator_behavior_v0,
    validate_step12g_filter_policy_debug_v0,
)
from covalent_ext.real_covalent_pretrained_forward_loss_smoke import (  # noqa: E402
    build_real_covalent_forward_loss_batch_bundle_v0,
)

import check_real_covalent_noncheckpoint_pocket_atom_filter_gate_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (REPORT_CSV.is_file() and MANIFEST_JSON.is_file() and FILTER_TABLE_CSV.is_file() and SUMMARY_MD.is_file()):
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def _rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(FILTER_TABLE_CSV)


def _bool(value: str) -> bool:
    return str(value).lower() == "true"


def _json_value(value: str):
    return json.loads(value) if value else []


def test_step12g_and_step12b_preconditions_validate():
    assert validate_step12g_filter_policy_debug_v0() is True
    assert validate_step12b_validator_behavior_v0() is True


def test_production_filter_helper_filters_pocket_only_for_b3_bundle():
    bundle = build_real_covalent_forward_loss_batch_bundle_v0("B3_scaffold_only", "cpu")
    filtered = filter_noncheckpoint_vocab_pocket_atoms_v0(bundle["diffsbdd_like"], "B3_scaffold_only", "cpu")
    metadata = filtered["metadata"]

    assert filtered["status"] == "passed"
    assert metadata["filter_policy_name"] == FILTER_POLICY_NAME
    assert metadata["filtered_pocket_atom_count"] == 1
    assert metadata["filtered_pocket_atom_numbers"] == [12]
    assert metadata["filtered_pocket_atom_symbols"] == ["Mg"]
    assert metadata["filtered_atoms_direct_ligand_contact_detected"] is False
    assert metadata["filtered_atoms_ligand_reactive_contact_detected"] is False
    assert metadata["ligand_unknown_atom_count"] == 0
    assert metadata["pocket_unknown_atom_count_before_filter"] == 1
    assert metadata["pocket_unknown_atom_count_after_filter"] == 0
    assert metadata["all_remaining_pocket_atoms_in_checkpoint_10d_vocab"] is True
    assert metadata["ligand_atoms_in_checkpoint_10d_vocab"] is True
    assert metadata["ligand_masks_unchanged_after_filter"] is True
    assert metadata["ligand_reactive_atom_region_preserved"] is True
    assert metadata["checkpoint_compatible_batch_constructed_after_filter"] is True
    assert metadata["no_synthetic_fallback_used"] is True
    assert metadata["production_filter_helper"] is True
    assert metadata["production_adapter_modified"] is False


def test_gate_projection_aggregates_all_samples_and_mask_levels():
    gate = run_noncheckpoint_pocket_atom_filter_gate_v0()

    assert gate["sample_count"] == 3
    assert gate["pre_filter_ligand_unknown_atom_count"] == 0
    assert gate["pre_filter_pocket_unknown_atom_count"] == 2
    assert gate["pre_filter_unknown_pocket_atom_numbers"] == [12]
    assert gate["pre_filter_unknown_pocket_atom_symbols"] == ["Mg"]
    assert gate["total_filtered_pocket_atom_count"] == 2
    assert gate["filtered_pocket_atom_numbers"] == [12]
    assert gate["filtered_pocket_atom_symbols"] == ["Mg"]
    assert gate["post_filter_ligand_unknown_atom_count"] == 0
    assert gate["post_filter_pocket_unknown_atom_count"] == 0
    assert gate["all_remaining_pocket_atoms_in_checkpoint_10d_vocab"] is True
    assert gate["all_ligand_atoms_in_checkpoint_10d_vocab"] is True
    assert gate["filtered_atoms_direct_ligand_contact_detected"] is False
    assert gate["filtered_atoms_ligand_reactive_contact_detected"] is False
    assert gate["audited_mask_level_count"] == 5
    assert gate["passed_mask_level_count"] == 5
    assert gate["failed_mask_level_count"] == 0
    assert gate["all_checkpoint_compatible_batches_constructed_after_filter"] is True
    assert gate["all_ligand_one_hot_row_sums_valid_after_filter"] is True
    assert gate["all_pocket_one_hot_row_sums_valid_after_filter"] is True
    assert gate["all_ligand_unknown_atom_count_zero_after_filter"] is True
    assert gate["all_pocket_unknown_atom_count_zero_after_filter"] is True
    assert gate["ligand_masks_unchanged_after_filter"] is True
    assert gate["ligand_reactive_atom_region_preserved"] is True
    assert gate["no_synthetic_fallback_used"] is True


def test_manifest_core_filter_contract_and_decision():
    manifest = _manifest()

    assert manifest["stage"] == "real_covalent_noncheckpoint_pocket_atom_filter_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_feature_semantics_audit_debug_v0"
    assert manifest["step12g_filter_policy_debug_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert manifest["filter_policy_name"] == FILTER_POLICY_NAME
    assert manifest["allowed_filtered_atomic_numbers_for_this_gate"] == ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE
    assert manifest["allowed_filtered_atom_symbols_for_this_gate"] == ALLOWED_FILTERED_ATOM_SYMBOLS_FOR_THIS_GATE
    assert manifest["pre_filter_ligand_unknown_atom_count"] == 0
    assert manifest["pre_filter_pocket_unknown_atom_count"] == 2
    assert manifest["pre_filter_unknown_pocket_atom_numbers"] == [12]
    assert manifest["pre_filter_unknown_pocket_atom_symbols"] == ["Mg"]
    assert manifest["total_filtered_pocket_atom_count"] == 2
    assert manifest["filtered_pocket_atom_numbers"] == [12]
    assert manifest["filtered_pocket_atom_symbols"] == ["Mg"]
    assert manifest["filtered_atoms_direct_ligand_contact_detected"] is False
    assert manifest["filtered_atoms_ligand_reactive_contact_detected"] is False
    assert manifest["post_filter_ligand_unknown_atom_count"] == 0
    assert manifest["post_filter_pocket_unknown_atom_count"] == 0


def test_manifest_filtered_conversion_and_non_cys_boundary():
    manifest = _manifest()

    assert manifest["all_remaining_pocket_atoms_in_checkpoint_10d_vocab"] is True
    assert manifest["all_ligand_atoms_in_checkpoint_10d_vocab"] is True
    assert manifest["production_filter_helper_created"] is True
    assert manifest["production_filter_helper_validated"] is True
    assert manifest["production_adapter_modified"] is False
    assert manifest["original_data_modified"] is False
    assert manifest["audited_mask_level_count"] == 5
    assert manifest["passed_mask_level_count"] == 5
    assert manifest["failed_mask_level_count"] == 0
    assert manifest["all_checkpoint_compatible_batches_constructed_after_filter"] is True
    assert manifest["all_ligand_one_hot_row_sums_valid_after_filter"] is True
    assert manifest["all_pocket_one_hot_row_sums_valid_after_filter"] is True
    assert manifest["all_ligand_unknown_atom_count_zero_after_filter"] is True
    assert manifest["all_pocket_unknown_atom_count_zero_after_filter"] is True
    assert manifest["ligand_masks_unchanged_after_filter"] is True
    assert manifest["ligand_reactive_atom_region_preserved"] is True
    assert manifest["no_synthetic_fallback_used"] is True
    assert manifest["non_cys_reactive_residue_support_status"] == "schema_supported_but_template_audit_pending"
    assert manifest["reaction_family_template_audit_required_before_broad_covalent_training"] is True
    assert manifest["ligand_reconstruction_template_gate_required"] is True
    assert manifest["real_covalent_noncheckpoint_pocket_atom_filter_gate_passed"] is True
    assert manifest["real_covalent_filtered_feature_semantics_audit_allowed"] is True
    assert manifest["real_covalent_cuda_forward_backward_smoke_allowed"] is False
    assert manifest["real_covalent_single_optimizer_step_smoke_allowed"] is False
    assert manifest["recommended_next_step"] == "real_covalent_filtered_feature_semantics_audit"


def test_manifest_safety_boundary():
    manifest = _manifest()

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


def test_filter_table_rows_and_mask_level_details():
    rows = _rows()
    sample_rows = [row for row in rows if row["row_type"] == "sample_filter_projection"]
    mask_rows = [row for row in rows if row["row_type"] == "mask_level_filtered_conversion"]
    boundary_rows = [row for row in rows if row["row_type"] == "non_cys_reaction_scope_boundary"]

    assert len(sample_rows) == 3
    assert len(mask_rows) == 5
    assert len(boundary_rows) == 1
    assert sum(int(row["removed_pocket_atom_count"]) for row in sample_rows) == 2
    for row in sample_rows:
        assert row["status"] == "passed"
        assert row["ligand_atom_count_changed"] == "False"
        assert int(row["post_filter_pocket_unknown_atom_count"]) == 0
        assert int(row["post_filter_ligand_unknown_atom_count"]) == 0
        assert _bool(row["all_remaining_pocket_atoms_in_checkpoint_10d_vocab"])
        assert _bool(row["all_ligand_atoms_in_checkpoint_10d_vocab"])
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
        assert set(_json_value(row["filtered_pocket_atom_numbers"])).issubset({12})
        assert _bool(row["no_synthetic_fallback_used"])
        assert _bool(row["ligand_masks_unchanged_after_filter"])
        assert _bool(row["ligand_reactive_atom_region_preserved"])
        assert row["status"] == "passed"


def test_report_manifest_filter_table_and_summary_written():
    _ensure_outputs()

    report_rows = _read_csv(REPORT_CSV)
    summary = SUMMARY_MD.read_text(encoding="utf-8")
    assert len(report_rows) == 8
    assert {row["status"] for row in report_rows} == {"passed"}
    assert "projection-level filter policy" in summary
    assert "Original data is unchanged" in summary
    assert "not optimizer step" in summary
    assert "template audit is pending" in summary
    assert "recommended_next_step: real_covalent_filtered_feature_semantics_audit" in summary


def test_no_forbidden_artifacts_under_output_root():
    _ensure_outputs()

    forbidden = [path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES]
    assert forbidden == []


def test_no_protected_source_modification_and_no_cys_only_gate():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0
    source = (REPO_ROOT / "src/covalent_ext/real_covalent_noncheckpoint_pocket_atom_filter_gate.py").read_text(
        encoding="utf-8"
    )
    assert '== "CYS"' not in source
    assert "== 'CYS'" not in source


def test_ast_safety_for_step12h_files():
    files = [
        "src/covalent_ext/real_covalent_noncheckpoint_pocket_atom_filter_gate.py",
        "scripts/check_real_covalent_noncheckpoint_pocket_atom_filter_gate_v0.py",
        "tests/test_real_covalent_noncheckpoint_pocket_atom_filter_gate_v0.py",
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

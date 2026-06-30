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
from covalent_ext.real_covalent_feature_semantics_audit import (  # noqa: E402
    AUDIT_TABLE_CSV,
    CANONICAL_MASK_LEVELS,
    CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    audit_checkpoint_feature_contract_v0,
    audit_real_covalent_atom_vocabulary_v0,
    validate_step12e_outputs_v0,
)

import check_real_covalent_feature_semantics_audit_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (REPORT_CSV.is_file() and MANIFEST_JSON.is_file() and AUDIT_TABLE_CSV.is_file() and SUMMARY_MD.is_file()):
        assert script.run() in {0, 1}


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def _audit_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(AUDIT_TABLE_CSV)


def test_step12e_and_step12b_preconditions_validate():
    assert validate_step12e_outputs_v0() is True
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


def test_checkpoint_contract_and_project_mapping():
    contract = audit_checkpoint_feature_contract_v0()

    assert contract["checkpoint_ligand_feature_dim"] == 10
    assert contract["checkpoint_pocket_feature_dim"] == 10
    assert contract["ligand_feature_dim_is_10"] is True
    assert contract["pocket_feature_dim_is_10"] is True
    assert contract["checkpoint_10d_feature_contract_detected"] is True
    assert contract["checkpoint_feature_semantics_source"] == "repo_dataset_info_or_config"
    assert contract["checkpoint_feature_semantics_directly_encoded"] is True
    assert contract["checkpoint_10d_mapping_matches_project_mapping"] is True
    assert CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX == {
        6: 0,
        7: 1,
        8: 2,
        16: 3,
        5: 4,
        35: 5,
        17: 6,
        15: 7,
        53: 8,
        9: 9,
    }


def test_real_atom_vocabulary_blocks_on_observed_protein_unknown_atoms():
    vocab = audit_real_covalent_atom_vocabulary_v0()

    assert vocab["sample_count"] > 0
    assert vocab["sample_ids"]
    assert vocab["ligand_atom_count_total"] > 0
    assert vocab["protein_atom_count_total"] > 0
    assert vocab["ligand_atomic_numbers_unique"]
    assert vocab["protein_atomic_numbers_unique"]
    assert vocab["ligand_unknown_atom_numbers"] == []
    assert vocab["protein_unknown_atom_numbers"] == [12]
    assert vocab["ligand_unknown_atom_count"] == 0
    assert vocab["protein_unknown_atom_count"] == 2
    assert vocab["all_ligand_atoms_in_checkpoint_10d_vocab"] is True
    assert vocab["all_protein_atoms_in_checkpoint_10d_vocab"] is False
    assert vocab["unknown_atom_policy_triggered"] is True
    assert vocab["zero_vector_unknown_atom_policy_safe"] is False


def test_manifest_core_contract_and_decision():
    manifest = _manifest()

    assert manifest["stage"] == "real_covalent_feature_semantics_audit_v0"
    assert manifest["previous_stage"] == "real_covalent_backward_smoke_v0"
    assert manifest["step12e_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert manifest["checkpoint_ligand_feature_dim"] == 10
    assert manifest["checkpoint_pocket_feature_dim"] == 10
    assert manifest["ligand_feature_dim_is_10"] is True
    assert manifest["pocket_feature_dim_is_10"] is True
    assert manifest["checkpoint_10d_feature_contract_detected"] is True
    assert manifest["checkpoint_feature_semantics_source"] == "repo_dataset_info_or_config"
    assert manifest["checkpoint_feature_semantics_directly_encoded"] is True
    assert manifest["checkpoint_10d_mapping_matches_project_mapping"] is True


def test_manifest_real_vocabulary_and_unknown_policy():
    manifest = _manifest()

    assert manifest["sample_count"] > 0
    assert manifest["sample_ids"]
    assert manifest["ligand_atom_count_total"] > 0
    assert manifest["protein_atom_count_total"] > 0
    assert manifest["ligand_atomic_numbers_unique"]
    assert manifest["protein_atomic_numbers_unique"]
    assert manifest["ligand_unknown_atom_numbers"] == []
    assert manifest["protein_unknown_atom_numbers"] == [12]
    assert manifest["ligand_unknown_atom_count"] == 0
    assert manifest["protein_unknown_atom_count"] == 2
    assert manifest["all_ligand_atoms_in_checkpoint_10d_vocab"] is True
    assert manifest["all_protein_atoms_in_checkpoint_10d_vocab"] is False
    assert manifest["unknown_atom_policy_triggered"] is True
    assert manifest["zero_vector_unknown_atom_policy_safe"] is False


def test_manifest_mask_level_conversion_semantics():
    manifest = _manifest()

    assert manifest["canonical_mask_levels"] == CANONICAL_MASK_LEVELS
    assert manifest["canonical_mask_level_count"] == 5
    assert manifest["audited_mask_level_count"] == 5
    assert manifest["passed_mask_level_count"] == 0
    assert manifest["failed_mask_level_count"] == 5
    assert manifest["all_checkpoint_compatible_batches_constructed"] is True
    assert manifest["all_ligand_one_hot_row_sums_valid"] is True
    assert manifest["all_pocket_one_hot_row_sums_valid"] is False
    assert manifest["all_ligand_unknown_atom_count_zero"] is True
    assert manifest["all_pocket_unknown_atom_count_zero"] is False
    assert manifest["no_synthetic_fallback_used"] is True


def test_manifest_feature_semantics_decision_and_safety():
    manifest = _manifest()

    assert manifest["feature_semantics_dimension_contract_passed"] is False
    assert manifest["feature_semantics_mapping_confirmed"] is True
    assert manifest["feature_semantics_known_after_audit"] is False
    assert manifest["feature_semantics_mapping_source_needs_confirmation"] is False
    assert manifest["real_covalent_feature_semantics_audit_passed"] is False
    assert manifest["real_covalent_cuda_forward_backward_smoke_allowed"] is False
    assert manifest["real_covalent_single_optimizer_step_smoke_allowed"] is False
    assert manifest["recommended_next_step"] == "real_covalent_feature_semantics_audit_debug"
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
    assert manifest["all_checks_passed"] is False
    assert "protein_unknown_atoms_present" in manifest["blocking_reasons"]


def test_audit_table_rows_and_mask_level_regions():
    rows = _audit_rows()
    row_types = [row["row_type"] for row in rows]
    conversion_rows = [row for row in rows if row["row_type"] == "mask_level_conversion"]

    assert "checkpoint_feature_contract" in row_types
    assert "real_atom_vocabulary" in row_types
    assert "decision" in row_types
    assert len(conversion_rows) == 5
    assert [row["mask_level"] for row in conversion_rows] == CANONICAL_MASK_LEVELS
    for row in conversion_rows:
        expected_region = "context" if row["mask_level"] == "B3_scaffold_only" else "target"
        assert row["expected_reactive_atom_region"] == expected_region
        assert row["checkpoint_compatible_batch_constructed"] == "True"
        assert row["ligand_feature_dim"] == "10"
        assert row["pocket_feature_dim"] == "10"
        assert row["ligand_one_hot_row_sums_valid"] == "True"
        assert row["pocket_one_hot_row_sums_valid"] == "False"
        assert row["ligand_unknown_atom_count"] == "0"
        assert row["pocket_unknown_atom_count"] == "1"
        assert row["no_synthetic_fallback_used"] == "True"
        assert row["status"] == "blocked"


def test_report_manifest_audit_table_and_summary_written():
    _ensure_outputs()

    report_rows = _read_csv(REPORT_CSV)
    summary = SUMMARY_MD.read_text(encoding="utf-8")
    assert len(report_rows) == 8
    assert "blocked" in {row["status"] for row in report_rows}
    assert "feature semantics audit" in summary
    assert "UNKNOWN_ATOM_FEATURE_POLICY" in summary
    assert "feature_semantics_known=False" in summary
    assert "recommended_next_step: real_covalent_feature_semantics_audit_debug" in summary


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


def test_ast_safety_for_step12f_files():
    files = [
        "src/covalent_ext/real_covalent_feature_semantics_audit.py",
        "scripts/check_real_covalent_feature_semantics_audit_v0.py",
        "tests/test_real_covalent_feature_semantics_audit_v0.py",
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
                assert func.id not in {"Adam", "AdamW", "SGD", "RMSprop", "training_step"}

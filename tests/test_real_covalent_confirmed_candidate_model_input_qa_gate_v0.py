from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_confirmed_candidate_model_input_qa_gate as qa


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_model_input_qa_gate_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not qa.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(qa.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_check_script_passes_and_validates_step13w_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_model_input_qa_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == qa.STAGE
    assert manifest["previous_stage"] == qa.PREVIOUS_STAGE
    assert manifest["step13w_model_input_materialization_smoke_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_row_qa_audit_has_three_expected_model_input_smoke_rows() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.ROW_QA_AUDIT_CSV)
    assert manifest["model_input_smoke_row_qa_audit_written"] is True
    assert manifest["model_input_smoke_row_qa_audit_row_count"] == len(rows) == 3
    assert [row["model_input_smoke_row_id"] for row in rows] == qa.EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS
    assert [row["sample_index_row_id"] for row in rows] == qa.EXPECTED_SAMPLE_INDEX_ROW_IDS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    assert {row["model_input_smoke_row_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_model_input_smoke_rows_unique"] is True
    assert manifest["all_model_input_smoke_row_ids_validated"] is True
    assert manifest["all_sample_index_row_ids_validated"] is True
    assert manifest["all_identity_fields_validated"] is True


def test_row_qa_validates_scope_contract_counts_dependencies_and_boundaries() -> None:
    manifest = _manifest()
    row_qa = _csv_rows(qa.ROW_QA_AUDIT_CSV)
    smoke_index = _csv_rows(qa.STEP13W_SMOKE_INDEX_CSV)
    assert {row["cys_sg_scope_validated"] for row in row_qa} == {"True"}
    assert {row["sample_contract_consistency_validated"] for row in row_qa} == {"True"}
    assert {row["sample_index_consistency_validated"] for row in row_qa} == {"True"}
    assert {row["ligand_counts_validated"] for row in row_qa} == {"True"}
    assert {row["endpoint_counts_validated"] for row in row_qa} == {"True"}
    assert {row["pocket_dependency_validated"] for row in row_qa} == {"True"}
    assert {row["ligand_topology_dependency_validated"] for row in row_qa} == {"True"}
    assert {row["mask_fields_validated"] for row in row_qa} == {"True"}
    assert {row["feature_semantics_status_validated"] for row in row_qa} == {"True"}
    assert {row["tensor_status_validated"] for row in row_qa} == {"True"}
    assert {row["loader_training_boundary_validated"] for row in row_qa} == {"True"}
    assert {
        row["review_row_id"]: (int(row["ligand_atom_count"]), int(row["ligand_bond_count"]))
        for row in smoke_index
    } == {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
    assert {row["endpoint_atom_count"] for row in smoke_index} == {"1"}
    assert {row["endpoint_touching_bond_count"] for row in smoke_index} == {"1"}
    assert manifest["all_candidates_cys_sg_scope"] is True
    assert manifest["all_sample_contract_consistency_validated"] is True
    assert manifest["all_sample_index_consistency_validated"] is True
    assert manifest["all_ligand_counts_validated"] is True
    assert manifest["all_endpoint_counts_validated"] is True
    assert manifest["all_pocket_dependencies_validated"] is True
    assert manifest["all_ligand_topology_dependencies_validated"] is True
    assert manifest["all_tensor_status_validated"] is True
    assert manifest["all_loader_training_boundaries_validated"] is True


def test_dependency_qa_audit_has_ten_existing_count_validated_dependencies() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.DEPENDENCY_QA_AUDIT_CSV)
    assert manifest["model_input_smoke_dependency_qa_audit_written"] is True
    assert manifest["model_input_smoke_dependency_qa_audit_row_count"] == len(rows) == 10
    assert {row["dependency_exists"] for row in rows} == {"True"}
    assert {row["dependency_count_validated"] for row in rows} == {"True"}
    assert {row["dependency_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_dependency_artifacts_exist"] is True
    assert manifest["all_dependency_counts_validated"] is True


def test_feature_qa_audit_preserves_audit_required_and_no_full_audit_claim() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.FEATURE_QA_AUDIT_CSV)
    assert manifest["model_input_smoke_feature_qa_audit_written"] is True
    assert manifest["model_input_smoke_feature_qa_audit_row_count"] == len(rows) == 12
    assert {row["audit_required_before_training"] for row in rows} == {"True"}
    assert {row["fully_audited_claimed"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert {row["blocking_for_smoke_materialization"] for row in rows} == {"False"}
    assert all(row["recommended_audit_step"] for row in rows)
    assert {row["feature_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_feature_semantics_audit_required_before_training"] is True
    assert manifest["no_feature_semantics_claimed_fully_audited"] is True
    assert manifest["all_feature_qa_passed"] is True


def test_mask_qa_audit_preserves_five_canonical_masks_with_b3() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.MASK_QA_AUDIT_CSV)
    assert manifest["model_input_smoke_mask_qa_audit_written"] is True
    assert manifest["model_input_smoke_mask_qa_audit_row_count"] == len(rows) == 5
    assert [row["canonical_mask_task_name"] for row in rows] == qa.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in rows] == qa.CANONICAL_MASK_TASK_ALIASES
    assert {row["source_of_truth_status"] for row in rows} == {"long_semantic_name_source_of_truth"}
    assert {row["alias_status"] for row in rows} == {"display_only"}
    assert {row["tensor_mask_written"] for row in rows} == {"False"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert {row["mask_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == qa.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == qa.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["all_mask_fields_validated"] is True
    assert manifest["all_mask_qa_passed"] is True


def test_model_input_qa_passes_without_modifying_smoke_or_writing_tensors() -> None:
    manifest = _manifest()
    assert manifest["all_model_input_smoke_row_qa_passed"] is True
    assert manifest["model_input_qa_passed"] is True
    false_keys = [
        "sample_index_written",
        "sample_index_modified",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_smoke_modified",
        "model_input_materialized",
        "model_input_written",
        "tensor_artifact_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_ready_samples_claimed",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
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
        "pt_created",
        "rdkit_used",
        "sdf_read",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "ligand_auto_restoration_run",
        "non_cys_generalization_run",
        "raw_files_read",
        "gzip_open_used",
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        "gemmi_used",
        "dataloader_modified",
        "forward_modified",
        "loss_modified",
        "loader_shape_dry_run_performed",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_readiness_boundary_allows_loader_shape_dry_run_design_gate_only() -> None:
    manifest = _manifest()
    assert manifest["ready_for_loader_shape_dry_run"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == qa.RECOMMENDED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        qa.ROW_QA_AUDIT_CSV,
        qa.DEPENDENCY_QA_AUDIT_CSV,
        qa.FEATURE_QA_AUDIT_CSV,
        qa.MASK_QA_AUDIT_CSV,
        qa.REPORT_CSV,
        qa.MANIFEST_JSON,
        qa.SUMMARY_MD,
    ]:
        assert path.is_file()
    forbidden = [
        path
        for path in qa.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in qa.FORBIDDEN_COMMITTABLE_SUFFIXES
    ]
    assert forbidden == []
    protected_diff = subprocess.run(
        ["git", "diff", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    protected_cached_diff = subprocess.run(
        ["git", "diff", "--cached", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw_tracked = subprocess.run(
        ["git", "ls-files", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert protected_diff.stdout == ""
    assert protected_cached_diff.stdout == ""
    assert raw_staged.stdout == ""
    assert raw_tracked.stdout == ""


def test_summary_states_model_input_qa_boundary() -> None:
    _manifest()
    summary = qa.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "model_input QA gate only",
        "does not modify the Step 13W CSV/JSON smoke artifacts",
        "validates row identity, CYS/SG scope",
        "five canonical mask tasks including scaffold_only/B3",
        "does not generate tensor, NPZ, or PT",
        "does not modify dataloader, forward, loss",
        "does not run loader shape dry run",
        "does not allow training",
        "Feature semantics audit remains required before formal training",
        qa.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_execution_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_model_input_qa_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_model_input_qa_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_model_input_qa_gate_v0.py"),
    ]
    text_scan_files = files[:2]
    forbidden_text = [
        "urllib",
        "requests",
        "urlopen",
        "wget",
        "curl",
        "gzip.open",
        "Bio.PDB",
        "MMCIFParser",
        "PDBParser",
        "Chem.MolFrom",
        "AllChem",
        "compute_masked_loss",
        ".backward(",
        "torch.optim",
        "optimizer.step",
        "trainer.fit",
        "training_step(",
        "torch.save",
        "save_checkpoint",
        "load_from_checkpoint",
        "numpy.load",
        "np.load",
    ]
    dangerous_attrs = {
        "backward",
        "fit",
        "save",
        "save_checkpoint",
        "load_from_checkpoint",
        "MolFromSmiles",
        "MolFromMolFile",
        "MolFromPDBFile",
        "GetMorganFingerprint",
        "GetMorganFingerprintAsBitVect",
        "urlopen",
    }
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    for path in text_scan_files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_text:
            assert pattern not in text, f"{pattern} in {path}"
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner in {"np", "numpy"} and func.attr == "load")
                assert not (owner == "torch" and func.attr in {"save", "optim"})
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in dangerous_attrs
            if isinstance(func, ast.Name):
                assert func.id not in dangerous_names

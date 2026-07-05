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

from covalent_ext import real_covalent_confirmed_candidate_model_input_design_gate as design


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_model_input_design_gate_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not design.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(design.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_check_script_passes_and_validates_step13u_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_model_input_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == design.STAGE
    assert manifest["previous_stage"] == design.PREVIOUS_STAGE
    assert manifest["step13u_sample_index_qa_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_schema_contract_written_with_required_field_groups() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.SCHEMA_CONTRACT_CSV)
    groups = {row["field_group"] for row in rows}
    assert manifest["schema_contract_written"] is True
    assert manifest["schema_contract_row_count"] == len(rows)
    assert {
        "sample_identity",
        "protein_pocket_input",
        "ligand_topology_coordinates",
        "group_labels",
        "canonical_mask_tasks",
        "auxiliary_labels",
        "model_compatibility_safety",
    } <= groups
    assert {row["materialization_status"] for row in rows} == {"design_only_not_materialized"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}


def test_dependency_contract_includes_required_dependencies_and_counts() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.DEPENDENCY_CONTRACT_CSV)
    names = {row["dependency_name"] for row in rows}
    assert manifest["dependency_contract_written"] is True
    assert manifest["dependency_contract_row_count"] == len(rows) == 10
    assert {
        "step13u_manifest",
        "step13u_row_qa_audit",
        "step13u_dependency_qa_audit",
        "step13u_schema_qa_audit",
        "step13t_sample_index_smoke",
        "step13s_candidate_contract",
        "step13s_mask_task_contract",
        "step13r_atom_topology_smoke_table",
        "step13r_bond_topology_smoke_table",
        "step13l_pocket_atom_table",
    } <= names
    assert {row["dependency_exists"] for row in rows} == {"True"}
    assert {row["dependency_validation_status"] for row in rows} == {"exists_and_count_validated"}
    assert manifest["all_dependency_artifacts_exist"] is True
    assert manifest["all_dependency_counts_validated"] is True


def test_sample_contract_has_three_valid_rows_matching_sample_index_qa() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.SAMPLE_CONTRACT_CSV)
    assert manifest["sample_contract_written"] is True
    assert manifest["sample_contract_row_count"] == len(rows) == 3
    assert [row["sample_index_row_id"] for row in rows] == design.EXPECTED_SAMPLE_INDEX_ROW_IDS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    assert {
        row["review_row_id"]: (int(row["ligand_atom_count"]), int(row["ligand_bond_count"]))
        for row in rows
    } == {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
    assert {row["topology_counts_validated"] for row in rows} == {"True"}
    assert {row["sample_index_qa_passed"] for row in rows} == {"True"}
    assert {row["future_model_input_row_allowed_next_step"] for row in rows} == {"True"}
    assert {row["model_input_materialized"] for row in rows} == {"False"}
    assert {row["tensor_artifact_written"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert manifest["all_sample_contract_rows_validated"] is True


def test_mask_contract_preserves_five_canonical_tasks_with_b3() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.MASK_CONTRACT_CSV)
    assert manifest["mask_contract_written"] is True
    assert manifest["mask_contract_row_count"] == len(rows) == 5
    assert [row["canonical_mask_task_name"] for row in rows] == design.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in rows] == design.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert {row["source_of_truth_status"] for row in rows} == {"long_semantic_name_source_of_truth"}
    assert {row["alias_status"] for row in rows} == {"display_only"}
    assert {row["materialization_status"] for row in rows} == {"design_only_not_materialized"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert manifest["all_mask_contract_rows_validated"] is True


def test_feature_semantics_contract_requires_future_audit_and_claims_no_full_audit() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.FEATURE_SEMANTICS_CONTRACT_CSV)
    assert manifest["feature_semantics_contract_written"] is True
    assert manifest["feature_semantics_contract_row_count"] == len(rows) >= 12
    assert {row["audit_required_before_training"] for row in rows} == {"True"}
    assert "fully_audited" not in {row["current_status"] for row in rows}
    assert {row["blocking_for_design_gate"] for row in rows} == {"False"}
    assert all(row["recommended_audit_step"] for row in rows)
    assert manifest["all_feature_semantics_audit_required_before_training"] is True
    assert manifest["no_feature_semantics_claimed_fully_audited"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True


def test_design_gate_boundary_does_not_materialize_model_input_or_training() -> None:
    manifest = _manifest()
    false_keys = [
        "sample_index_written",
        "sample_index_modified",
        "enriched_sample_index_written",
        "final_dataset_written",
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
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_readiness_allows_materialization_smoke_only_not_training() -> None:
    manifest = _manifest()
    assert manifest["ready_for_model_input_materialization_smoke"] is True
    assert manifest["ready_for_loader_shape_dry_run"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == design.RECOMMENDED_NEXT_STEP
    assert manifest["model_input_design_gate_passed"] is True


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        design.SCHEMA_CONTRACT_CSV,
        design.DEPENDENCY_CONTRACT_CSV,
        design.SAMPLE_CONTRACT_CSV,
        design.MASK_CONTRACT_CSV,
        design.FEATURE_SEMANTICS_CONTRACT_CSV,
        design.REPORT_CSV,
        design.MANIFEST_JSON,
        design.SUMMARY_MD,
    ]:
        assert path.is_file()
    forbidden = [
        path
        for path in design.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in design.FORBIDDEN_COMMITTABLE_SUFFIXES
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


def test_summary_states_design_boundary_and_feature_audit_requirement() -> None:
    _manifest()
    summary = design.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "model_input design gate only",
        "does not materialize model input",
        "does not modify dataloader, forward, loss",
        "scaffold_only/B3",
        "feature semantics audit requirements",
        "Step 12D was smoke legality only",
        "allows model_input materialization smoke next",
        "does not allow loader shape dry run",
        "does not allow training",
        "Feature semantics audit remains required before formal training",
        design.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_execution_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_model_input_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_model_input_design_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_model_input_design_gate_v0.py"),
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

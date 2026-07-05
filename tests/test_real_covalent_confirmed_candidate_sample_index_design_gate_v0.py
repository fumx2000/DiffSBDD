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

from covalent_ext import real_covalent_confirmed_candidate_sample_index_design_gate as design


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_sample_index_design_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13r_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_sample_index_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == design.STAGE
    assert manifest["previous_stage"] == design.PREVIOUS_STAGE
    assert manifest["step13r_ligand_topology_smoke_retry_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_schema_contract_written_with_expected_field_groups() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.SCHEMA_CONTRACT_CSV)
    groups = {row["field_group"] for row in rows}
    assert manifest["schema_contract_written"] is True
    assert manifest["schema_contract_row_count"] == len(rows)
    assert len(rows) >= 47
    assert {
        "identity_provenance",
        "ligand_topology",
        "pocket_protein_dependency",
        "mask_task_contract",
        "auxiliary_task_contract",
        "readiness_safety",
    } <= groups
    required_fields = {
        "sample_index_row_id",
        "review_row_id",
        "pdb_id",
        "ligand_atom_topology_table_path",
        "ligand_bond_topology_table_path",
        "canonical_mask_task_names",
        "supports_scaffold_only",
        "sample_index_materialization_status",
        "ready_to_train_now",
    }
    assert required_fields <= {row["field_name"] for row in rows}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}


def test_dependency_contract_includes_required_existing_artifacts() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.DEPENDENCY_CONTRACT_CSV)
    names = {row["dependency_name"] for row in rows}
    assert manifest["dependency_contract_written"] is True
    assert manifest["dependency_contract_row_count"] == len(rows)
    assert {
        "step13r_manifest",
        "step13r_atom_smoke_table",
        "step13r_bond_smoke_table",
        "step13r_smoke_retry_audit",
        "step13m_ligand_topology_restoration_candidate_contract",
        "step13l_pocket_extraction_manifest",
        "step13l_pocket_atom_table",
        "step13l_pocket_extraction_audit",
        "step13j_ligand_full_atom_table",
        "step13j_endpoint_recovery_audit",
    } <= names
    assert {row["dependency_exists"] for row in rows} == {"True"}
    assert manifest["all_dependency_artifacts_exist"] is True
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}


def test_candidate_contract_has_three_cys_sg_goldens_matching_step13r_counts() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.CANDIDATE_CONTRACT_CSV)
    assert manifest["candidate_contract_written"] is True
    assert manifest["candidate_contract_row_count"] == len(rows) == 3
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    assert {row["v1_train_ready_scope"] for row in rows} == {design.V1_TRAIN_READY_SCOPE}
    assert {row["residue_scope"] for row in rows} == {design.DESIGN_SCOPE}
    assert {row["residue_name"] for row in rows} == {"CYS"}
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {row["endpoint_atom_true_count"] for row in rows} == {"1"}
    assert {row["endpoint_touching_bond_true_count"] for row in rows} == {"1"}
    assert {
        row["review_row_id"]: (int(row["ligand_atom_count"]), int(row["ligand_bond_count"]))
        for row in rows
    } == {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
    assert {row["sample_index_design_status"] for row in rows} == {"design_gate_passed"}
    assert {row["sample_index_materialization_allowed_next_step"] for row in rows} == {"True"}
    assert {row["sample_index_written"] for row in rows} == {"False"}
    assert {row["model_input_materialized"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert manifest["all_candidate_counts_match_step13r"] is True
    assert manifest["all_candidates_cys_sg_scope"] is True
    assert manifest["all_candidates_design_gate_passed"] is True


def test_mask_task_contract_preserves_five_canonical_tasks_and_b3() -> None:
    manifest = _manifest()
    rows = _csv_rows(design.MASK_TASK_CONTRACT_CSV)
    names = [row["canonical_mask_task_name"] for row in rows]
    aliases = [row["display_alias"] for row in rows]
    assert manifest["mask_task_contract_written"] is True
    assert manifest["mask_task_contract_row_count"] == len(rows) == 5
    assert names == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert aliases == ["A", "B", "B2", "B3", "C"]
    assert manifest["canonical_mask_task_names"] == names
    assert manifest["canonical_mask_task_aliases"] == aliases
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert {row["active_in_v1"] for row in rows} == {"True"}
    assert {row["source_of_truth_status"] for row in rows} == {
        "long_semantic_name_source_of_truth_alias_display_only"
    }
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}


def test_no_rdkit_sdf_raw_sample_index_model_input_or_training() -> None:
    manifest = _manifest()
    false_keys = [
        "sample_index_written",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_materialized",
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
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_readiness_boundary_points_to_materialization_smoke_not_model_input_or_training() -> None:
    manifest = _manifest()
    assert manifest["sample_index_materialization_allowed_next_step"] is True
    assert manifest["ready_for_sample_index_materialization_smoke"] is True
    assert manifest["ready_to_write_sample_index_now"] is False
    assert manifest["ready_for_model_input_design_gate"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == design.RECOMMENDED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        design.SCHEMA_CONTRACT_CSV,
        design.DEPENDENCY_CONTRACT_CSV,
        design.CANDIDATE_CONTRACT_CSV,
        design.MASK_TASK_CONTRACT_CSV,
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


def test_summary_states_design_gate_boundary_and_mask_semantics() -> None:
    _manifest()
    summary = design.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "sample_index design gate only",
        "does not write a real sample_index",
        "does not write enriched_sample_index",
        "does not run forward",
        "`warhead_only` with display alias `A`",
        "`scaffold_only` with display alias `B3`",
        "Long semantic mask names are the source of truth",
        "aliases are display-only",
        "No sixth or seventh mask task was added",
        "does not allow model input materialization and does not allow training",
        "Feature semantics audit remains required before formal training",
        design.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_execution_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_sample_index_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_sample_index_design_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_sample_index_design_gate_v0.py"),
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
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
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

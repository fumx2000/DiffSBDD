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

from covalent_ext import real_covalent_confirmed_candidate_sample_index_qa_gate as qa


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_sample_index_qa_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13t_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_sample_index_qa_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == qa.STAGE
    assert manifest["previous_stage"] == qa.PREVIOUS_STAGE
    assert manifest["step13t_sample_index_materialization_smoke_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_sample_index_rows_are_read_and_identity_lineage_scope_passes() -> None:
    manifest = _manifest()
    sample_rows = _csv_rows(qa.STEP13T_SAMPLE_INDEX_CSV)
    row_audit = _csv_rows(qa.ROW_QA_AUDIT_CSV)
    assert manifest["sample_index_smoke_read"] is True
    assert manifest["sample_index_smoke_row_count"] == len(sample_rows) == 3
    assert [row["sample_index_row_id"] for row in sample_rows] == qa.EXPECTED_SAMPLE_INDEX_ROW_IDS
    assert [row["review_row_id"] for row in sample_rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in sample_rows] == ["6DI9", "5F2E", "6OIM"]
    assert {row["row_identity_validated"] for row in row_audit} == {"True"}
    assert {row["lineage_validated"] for row in row_audit} == {"True"}
    assert {row["cys_sg_scope_validated"] for row in row_audit} == {"True"}
    assert manifest["all_sample_index_rows_unique"] is True
    assert manifest["all_identity_fields_validated"] is True
    assert manifest["all_lineage_fields_validated"] is True
    assert manifest["all_candidates_cys_sg_scope"] is True


def test_mask_fields_are_canonical_five_task_set_with_b3() -> None:
    manifest = _manifest()
    row_audit = _csv_rows(qa.ROW_QA_AUDIT_CSV)
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == qa.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == qa.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert {row["mask_task_names_validated"] for row in row_audit} == {"True"}
    assert {row["mask_task_aliases_validated"] for row in row_audit} == {"True"}
    assert {row["b3_scaffold_only_included"] for row in row_audit} == {"True"}
    assert {row["no_extra_mask_tasks"] for row in row_audit} == {"True"}
    assert manifest["all_mask_task_fields_validated"] is True


def test_topology_counts_paths_and_endpoint_counts_validate() -> None:
    manifest = _manifest()
    row_audit = _csv_rows(qa.ROW_QA_AUDIT_CSV)
    assert {row["topology_counts_match_candidate_contract"] for row in row_audit} == {"True"}
    assert {row["topology_table_paths_exist"] for row in row_audit} == {"True"}
    assert {row["topology_table_counts_match_sample_index"] for row in row_audit} == {"True"}
    assert {row["endpoint_counts_validated"] for row in row_audit} == {"True"}
    assert manifest["all_topology_counts_match_candidate_contract"] is True
    assert manifest["all_topology_table_paths_exist"] is True
    assert manifest["all_topology_table_counts_match_sample_index"] is True
    assert manifest["all_endpoint_counts_validated"] is True


def test_dependency_qa_audit_has_nine_existing_count_validated_dependencies() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.DEPENDENCY_QA_AUDIT_CSV)
    assert manifest["sample_index_dependency_qa_audit_written"] is True
    assert manifest["sample_index_dependency_qa_audit_row_count"] == len(rows) == 9
    assert {row["dependency_exists"] for row in rows} == {"True"}
    assert {row["dependency_count_validated"] for row in rows} == {"True"}
    assert {row["dependency_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_dependency_artifacts_exist"] is True
    assert manifest["all_dependency_counts_validated"] is True


def test_schema_qa_has_no_blocking_missing_materialized_fields() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.SCHEMA_QA_AUDIT_CSV)
    assert manifest["sample_index_schema_qa_audit_written"] is True
    assert manifest["sample_index_schema_qa_audit_row_count"] == len(rows) > 0
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_required_schema_fields_present_or_intentionally_deferred"] is True
    present_fields = {row["required_field_name"] for row in rows if row["present_in_sample_index_smoke"] == "True"}
    assert {
        "sample_index_row_id",
        "review_row_id",
        "pdb_id",
        "ligand_atom_count",
        "ligand_bond_count",
        "canonical_mask_task_names",
        "supports_scaffold_only",
        "sample_index_materialization_status",
        "ready_to_train_now",
    } <= present_fields


def test_row_qa_and_overall_qa_pass() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.ROW_QA_AUDIT_CSV)
    assert manifest["sample_index_row_qa_audit_written"] is True
    assert manifest["sample_index_row_qa_audit_row_count"] == len(rows) == 3
    assert {row["sample_index_row_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_sample_index_row_qa_passed"] is True
    assert manifest["sample_index_qa_passed"] is True


def test_qa_does_not_rewrite_sample_index_or_write_downstream_outputs() -> None:
    manifest = _manifest()
    assert manifest["sample_index_written"] is False
    assert manifest["sample_index_modified"] is False
    false_keys = [
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


def test_readiness_boundary_allows_design_gate_only() -> None:
    manifest = _manifest()
    assert manifest["ready_for_model_input_design_gate"] is True
    assert manifest["ready_for_model_input_materialization_smoke"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == qa.RECOMMENDED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        qa.ROW_QA_AUDIT_CSV,
        qa.DEPENDENCY_QA_AUDIT_CSV,
        qa.SCHEMA_QA_AUDIT_CSV,
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


def test_summary_states_qa_boundary() -> None:
    _manifest()
    summary = qa.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "sample_index QA gate only",
        "does not rewrite the Step 13T sample_index",
        "validates identity, lineage, CYS/SG scope",
        "five canonical mask tasks",
        "B3 scaffold_only",
        "does not write enriched_sample_index",
        "does not allow model_input materialization",
        "does not allow training",
        "Feature semantics audit remains required before formal training",
        qa.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_execution_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_sample_index_qa_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_sample_index_qa_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_sample_index_qa_gate_v0.py"),
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

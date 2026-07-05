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

from covalent_ext import real_covalent_confirmed_candidate_sample_index_materialization_smoke as smoke


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not smoke.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_check_script_passes_and_validates_step13s_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13s_sample_index_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_sample_index_smoke_has_three_expected_rows_and_ids() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.SAMPLE_INDEX_SMOKE_CSV)
    assert manifest["sample_index_smoke_written"] is True
    assert manifest["sample_index_smoke_row_count"] == len(rows) == 3
    assert [row["sample_index_row_id"] for row in rows] == smoke.EXPECTED_SAMPLE_INDEX_ROW_IDS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    assert {row["v1_train_ready_scope"] for row in rows} == {smoke.V1_TRAIN_READY_SCOPE}
    assert {row["residue_scope"] for row in rows} == {smoke.SAMPLE_INDEX_SCOPE}
    assert {row["residue_name"] for row in rows} == {"CYS"}
    assert {row["residue_atom_name"] for row in rows} == {"SG"}


def test_sample_index_rows_preserve_canonical_mask_tasks_and_b3() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.SAMPLE_INDEX_SMOKE_CSV)
    expected_names = ";".join(smoke.CANONICAL_MASK_TASK_NAMES)
    expected_aliases = ";".join(smoke.CANONICAL_MASK_TASK_ALIASES)
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert {row["canonical_mask_task_names"] for row in rows} == {expected_names}
    assert {row["canonical_mask_task_aliases"] for row in rows} == {expected_aliases}
    assert {row["mask_task_count"] for row in rows} == {"5"}
    for support_key in [
        "supports_warhead_only",
        "supports_linker_plus_warhead",
        "supports_scaffold_plus_warhead",
        "supports_scaffold_only",
        "supports_scaffold_plus_linker_plus_warhead",
    ]:
        assert {row[support_key] for row in rows} == {"True"}


def test_counts_match_candidate_contract_and_endpoint_counts_are_validated() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.SAMPLE_INDEX_SMOKE_CSV)
    assert {
        row["review_row_id"]: (int(row["ligand_atom_count"]), int(row["ligand_bond_count"]))
        for row in rows
    } == {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
    assert {row["endpoint_atom_true_count"] for row in rows} == {"1"}
    assert {row["endpoint_touching_bond_true_count"] for row in rows} == {"1"}
    assert manifest["all_counts_match_candidate_contract"] is True
    assert manifest["all_endpoint_counts_validated"] is True


def test_materialization_audit_passes_for_all_rows() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.AUDIT_CSV)
    assert manifest["sample_index_audit_written"] is True
    assert manifest["sample_index_audit_row_count"] == len(rows) == 3
    for key in [
        "candidate_contract_row_found",
        "mask_task_contract_validated",
        "ligand_atom_count_matches_candidate_contract",
        "ligand_bond_count_matches_candidate_contract",
        "endpoint_counts_validated",
        "canonical_mask_count_validated",
        "b3_scaffold_only_included",
        "sample_index_row_materialized",
        "materialization_smoke_passed",
    ]:
        assert {row[key] for row in rows} == {"True"}
    assert {row["model_input_materialized"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_sample_index_rows_materialized"] is True
    assert manifest["all_candidate_rows_found"] is True
    assert manifest["all_mask_task_contracts_validated"] is True


def test_sample_index_is_written_but_downstream_outputs_and_training_are_false() -> None:
    manifest = _manifest()
    assert manifest["sample_index_written"] is True
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


def test_readiness_boundary_points_to_qa_gate_not_model_input_or_training() -> None:
    manifest = _manifest()
    assert manifest["ready_for_sample_index_qa_gate"] is True
    assert manifest["ready_for_model_input_design_gate"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == smoke.RECOMMENDED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        smoke.SAMPLE_INDEX_SMOKE_CSV,
        smoke.AUDIT_CSV,
        smoke.REPORT_CSV,
        smoke.MANIFEST_JSON,
        smoke.SUMMARY_MD,
    ]:
        assert path.is_file()
    forbidden = [
        path
        for path in smoke.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in smoke.FORBIDDEN_COMMITTABLE_SUFFIXES
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


def test_summary_states_materialization_boundary() -> None:
    _manifest()
    summary = smoke.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "writes a 3-row sample_index smoke artifact",
        "not an enriched_sample_index",
        "not a final_dataset",
        "not model input",
        "does not allow model input materialization",
        "does not allow training",
        "scaffold_only`/`B3",
        "sample_index QA gate",
        "Feature semantics audit remains required before formal training",
        smoke.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_execution_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_sample_index_materialization_smoke.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0.py"),
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

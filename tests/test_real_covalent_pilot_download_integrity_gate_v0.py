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

from covalent_ext import real_covalent_pilot_download_integrity_gate as gate  # noqa: E402
import check_real_covalent_pilot_download_integrity_gate_v0 as script  # noqa: E402


EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        gate.REPORT_CSV.is_file()
        and gate.MANIFEST_JSON.is_file()
        and gate.RAW_FILE_INTEGRITY_TABLE_CSV.is_file()
        and gate.SUMMARY_MD.is_file()
    )
    if not needs_run:
        manifest = json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))
        needs_run = manifest["stage"] != gate.STAGE or not manifest["all_checks_passed"]
    if needs_run:
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _raw_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(gate.RAW_FILE_INTEGRITY_TABLE_CSV)


def _bool_text(value: str) -> bool:
    return value == "True"


def test_step12t_precondition_validates_and_step12b_inherited():
    assert gate.validate_step12t_pilot_download_execution_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_pilot_download_integrity_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_pilot_download_execution_gate_v0"
    assert manifest["step12t_pilot_download_execution_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True


def test_raw_file_integrity_summary():
    manifest = _manifest()
    assert manifest["raw_file_integrity_table_written"] is True
    assert manifest["raw_file_integrity_row_count"] == 3
    assert manifest["all_raw_files_exist"] is True
    assert manifest["all_raw_files_nonempty"] is True
    assert manifest["all_raw_file_sizes_match_expected"] is True
    assert manifest["all_raw_sha256_match_expected"] is True
    assert manifest["all_raw_gzip_magic_valid"] is True
    assert manifest["all_raw_paths_under_data_raw"] is True
    assert manifest["all_raw_files_gitignored"] is True
    assert manifest["no_raw_files_staged"] is True
    assert manifest["no_raw_files_tracked"] is True
    assert manifest["raw_files_commit_allowed"] is False
    assert manifest["data_raw_gitignore_is_local_exclude_only"] is True
    assert manifest["gitignore_modified"] is False


def test_raw_file_integrity_table_rows():
    rows = _raw_rows()
    assert len(rows) == 3
    assert [row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS
    for row in rows:
        info = gate.EXPECTED_RAW_FILE_INFO[row["pdb_id"]]
        raw_path = REPO_ROOT / row["raw_path"]
        assert raw_path.is_file()
        assert int(row["expected_size_bytes"]) == info["size_bytes"]
        assert int(row["observed_size_bytes"]) == info["size_bytes"]
        assert row["expected_sha256"] == info["sha256"]
        assert row["observed_sha256"] == info["sha256"]
        assert _bool_text(row["file_exists"]) is True
        assert _bool_text(row["file_nonempty"]) is True
        assert _bool_text(row["size_matches_expected"]) is True
        assert _bool_text(row["sha256_matches_expected"]) is True
        assert _bool_text(row["gzip_magic_valid"]) is True
        assert _bool_text(row["path_under_data_raw"]) is True
        assert _bool_text(row["git_check_ignore_passed"]) is True
        assert _bool_text(row["git_staged"]) is False
        assert _bool_text(row["git_tracked"]) is False
        assert _bool_text(row["raw_commit_allowed"]) is False
        assert _bool_text(row["mmcif_decompressed"]) is False
        assert _bool_text(row["mmcif_parsed"]) is False
        assert row["integrity_status"] == "passed"
        assert row["blocking_reasons"] == ""


def test_provenance_cross_check_summary():
    manifest = _manifest()
    assert manifest["provenance_cross_check_defined"] is True
    assert manifest["provenance_csv_read"] is True
    assert manifest["provenance_row_count"] == 6
    assert manifest["pdb_download_provenance_row_count"] == 3
    assert manifest["local_curated_provenance_row_count"] == 3
    assert manifest["all_pdb_download_rows_match_raw_files"] is True
    assert manifest["all_pdb_download_rows_sha256_match_raw_recompute"] is True
    assert manifest["all_pdb_download_rows_size_match_raw_recompute"] is True
    assert manifest["all_local_curated_rows_recorded_without_npz_read"] is True
    assert manifest["provenance_cross_check_passed"] is True


def test_no_execution_or_training_side_effects():
    manifest = _manifest()
    for key in [
        "external_network_called",
        "data_downloaded",
        "download_attempted",
        "raw_storage_directories_created",
        "raw_download_files_written",
        "raw_structure_files_written",
        "mmcif_decompressed",
        "mmcif_parsed",
        "adapter_implementation_written",
        "adapter_execution_run",
        "rdkit_processing_run",
        "uniprot_mapping_run",
        "cdhit_run",
        "coordinate_geometry_calculation_run",
        "npz_files_loaded",
        "npz_contents_read",
        "enriched_sample_index_written",
        "actual_split_assignments_written",
        "actual_leakage_matrix_written",
        "final_split_created",
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
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "original_diffsbdd_source_modified",
        "forbidden_committable_artifacts_created",
    ]:
        assert manifest[key] is False


def test_gate_decision_and_next_step():
    manifest = _manifest()
    assert manifest["real_covalent_pilot_download_integrity_gate_passed"] is True
    assert manifest["pilot_download_integrity_contract_defined"] is True
    assert manifest["ready_for_minimal_mmcif_parser_design_gate"] is True
    assert manifest["ready_to_parse_mmcif_now"] is False
    assert manifest["ready_to_run_adapter_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_minimal_mmcif_parser_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary_written():
    _ensure_outputs()
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.RAW_FILE_INTEGRITY_TABLE_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    assert len(_read_csv(gate.REPORT_CSV)) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "no network calls, no re-download, no decompression, and no mmCIF parsing",
        "6DI9",
        "5F2E",
        "6OIM",
        "file size",
        "SHA256",
        "gzip magic",
        "gitignored",
        "not staged",
        "not tracked",
        "provenance cross-check passed",
        "no adapters",
        "RDKit/UniProt/CD-HIT/geometry",
        "no training",
        "real_covalent_minimal_mmcif_parser_design_gate",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_raw_files_are_ignored_unstaged_and_untracked():
    for pdb_id in EXPECTED_PDB_IDS:
        raw_path = str(gate.EXPECTED_RAW_FILE_INFO[pdb_id]["path"])
        ignored = subprocess.run(["git", "check-ignore", raw_path], cwd=REPO_ROOT, check=False)
        staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", raw_path], cwd=REPO_ROOT, check=False, stdout=subprocess.PIPE, text=True)
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", raw_path], cwd=REPO_ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert ignored.returncode == 0
        assert staged.stdout.strip() == ""
        assert tracked.returncode != 0


def test_ast_and_text_safety():
    files = [
        REPO_ROOT / "src/covalent_ext/real_covalent_pilot_download_integrity_gate.py",
        REPO_ROOT / "scripts/check_real_covalent_pilot_download_integrity_gate_v0.py",
        REPO_ROOT / "tests/test_real_covalent_pilot_download_integrity_gate_v0.py",
    ]
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    dangerous_attrs = {
        "back" + "ward",
        "fit",
        "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "MolFrom" + "Smiles",
        "MolFrom" + "MolFile",
        "MolFrom" + "PDBFile",
        "GetMorgan" + "Fingerprint",
        "GetMorgan" + "FingerprintAsBitVect",
        "url" + "open",
    }
    forbidden_text = [
        "url" + "lib",
        "requ" + "ests",
        "url" + "open",
        "w" + "get",
        "cu" + "rl",
        "gzip." + "open",
        "Bio." + "PDB",
        "MM" + "CIFParser",
        "PDB" + "Parser",
        "Chem." + "MolFrom",
        "AllChem." + "GetMorganFingerprint",
        "mod" + "el(",
        "compute_" + "masked_loss",
        ".back" + "ward(",
        "torch." + "optim",
        "optimizer." + "step",
        "trainer." + "fit",
        "training_" + "step(",
        "torch." + "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "numpy." + "load",
        "np." + "load",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_text:
            assert pattern not in text
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

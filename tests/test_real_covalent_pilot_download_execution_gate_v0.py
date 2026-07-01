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

from covalent_ext import real_covalent_pilot_download_execution_gate as gate  # noqa: E402
import check_real_covalent_pilot_download_execution_gate_v0 as script  # noqa: E402


EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        gate.REPORT_CSV.is_file()
        and gate.MANIFEST_JSON.is_file()
        and gate.PROVENANCE_CSV.is_file()
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


def _provenance_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(gate.PROVENANCE_CSV)


def _bool_text(value: str) -> bool:
    return value == "True"


def test_step12s_precondition_validates():
    assert gate.validate_step12s_pilot_download_dry_run_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_pilot_download_execution_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_pilot_download_dry_run_gate_v0"
    assert manifest["step12s_pilot_download_dry_run_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True


def test_download_execution_counts_and_status():
    manifest = _manifest()
    assert manifest["pilot_download_execution_defined"] is True
    assert manifest["pilot_download_execution_performed"] is True
    assert manifest["external_network_called"] is True
    assert manifest["data_downloaded"] is True
    assert manifest["raw_storage_directories_created"] is True
    assert manifest["raw_download_files_written"] is True
    assert manifest["raw_structure_files_written"] is True
    assert manifest["pdb_mmcif_download_attempt_count"] == 3
    assert manifest["pdb_mmcif_download_success_count"] == 3
    assert manifest["pdb_mmcif_download_failure_count"] == 0
    assert manifest["downloaded_pdb_ids"] == EXPECTED_PDB_IDS
    assert manifest["downloaded_raw_file_count"] == 3


def test_downloaded_files_exist_and_have_integrity_metadata():
    manifest = _manifest()
    assert manifest["all_downloaded_files_exist"] is True
    assert manifest["all_downloaded_files_nonempty"] is True
    assert manifest["all_downloaded_files_gzip_magic_valid"] is True
    assert manifest["all_downloaded_files_sha256_recorded"] is True
    for raw_path in manifest["downloaded_raw_paths"]:
        path = REPO_ROOT / raw_path
        assert path.is_file()
        assert path.stat().st_size > 0
        with path.open("rb") as handle:
            assert handle.read(2) == b"\x1f\x8b"


def test_provenance_csv_records_downloads_and_local_curated_rows():
    manifest = _manifest()
    rows = _provenance_rows()
    assert gate.PROVENANCE_CSV.is_file()
    assert manifest["provenance_csv_written"] is True
    assert manifest["provenance_row_count"] == 6
    assert len(rows) == 6
    download_rows = [row for row in rows if row["record_type"] == "pdb_mmcif_download"]
    local_rows = [row for row in rows if row["record_type"] == "local_curated_provenance"]
    assert [row["pdb_id"] for row in download_rows] == EXPECTED_PDB_IDS
    assert manifest["local_curated_provenance_row_count"] == 3
    for row in download_rows:
        assert _bool_text(row["download_attempted"]) is True
        assert _bool_text(row["download_succeeded"]) is True
        assert _bool_text(row["file_exists_after_download"]) is True
        assert int(row["file_size_bytes"]) > 0
        assert len(row["sha256"]) == 64
        assert _bool_text(row["gzip_magic_valid"]) is True
        assert row["provenance_status"] == "downloaded_raw_file_recorded"
        assert row["error_message"] == ""
    for row in local_rows:
        assert row["source_name"] == "local curated"
        assert _bool_text(row["npz_loaded"]) is False
        assert _bool_text(row["npz_contents_read"]) is False
        assert row["provenance_status"] == "recorded_without_raw_file_copy"
    assert manifest["local_curated_npz_loaded"] is False
    assert manifest["local_curated_npz_contents_read"] is False


def test_raw_git_safety_and_committable_artifact_policy():
    manifest = _manifest()
    assert manifest["local_git_exclude_checked"] is True
    assert manifest["data_raw_gitignored"] is True
    assert manifest["gitignore_modified"] is False
    assert manifest["raw_files_expected_to_be_untracked_or_ignored"] is True
    assert manifest["raw_files_staged"] is False
    assert manifest["raw_files_committed_allowed"] is False
    assert manifest["committable_output_files_only_csv_json_md_py"] is True
    assert manifest["forbidden_committable_artifacts_created"] is False
    ignored = subprocess.run(
        ["git", "check-ignore", "data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert ignored.returncode == 0
    assert "data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz" in ignored.stdout


def test_prohibited_operations_remain_false():
    manifest = _manifest()
    for key in [
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
    ]:
        assert manifest[key] is False


def test_gate_decision_and_next_step():
    manifest = _manifest()
    assert manifest["real_covalent_pilot_download_execution_gate_passed"] is True
    assert manifest["pilot_download_execution_contract_defined"] is True
    assert manifest["ready_for_pilot_download_integrity_gate"] is True
    assert manifest["ready_to_parse_mmcif_now"] is False
    assert manifest["ready_to_run_adapter_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_pilot_download_integrity_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_report_manifest_provenance_and_summary_written():
    _ensure_outputs()
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.PROVENANCE_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    assert len(_read_csv(gate.REPORT_CSV)) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "pilot download execution gate",
        "actually used the network",
        "6DI9",
        "5F2E",
        "6OIM",
        "Raw files are not committed and must never be committed",
        "SHA256",
        "file size",
        "gzip magic validation",
        "download provenance",
        "No mmCIF parsing",
        "No adapters",
        "RDKit/UniProt/CD-HIT/geometry",
        "training",
        "real_covalent_pilot_download_integrity_gate",
        "should still not parse mmCIF",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_ast_and_text_safety():
    files = [
        REPO_ROOT / "src/covalent_ext/real_covalent_pilot_download_execution_gate.py",
        REPO_ROOT / "scripts/check_real_covalent_pilot_download_execution_gate_v0.py",
        REPO_ROOT / "tests/test_real_covalent_pilot_download_execution_gate_v0.py",
    ]
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    dangerous_attrs = {
        "backward",
        "fit",
        "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "MolFromSmiles",
        "MolFromMolFile",
        "MolFromPDBFile",
        "GetMorganFingerprint",
        "GetMorganFingerprintAsBitVect",
    }
    forbidden_text = [
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
        "Chem." + "MolFrom",
        "AllChem." + "GetMorganFingerprint",
        "Bio." + "PDB",
        "MM" + "CIFParser",
        "PDB" + "Parser",
        "SD" + "MolSupplier",
        "Mol2" + "MolSupplier",
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

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

from covalent_ext import real_covalent_pilot_download_dry_run_gate as gate  # noqa: E402
import check_real_covalent_pilot_download_dry_run_gate_v0 as script  # noqa: E402


EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_SAMPLE_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]
EXPECTED_BLOCKED_SOURCES = ["CovPDB", "CovBinderInPDB", "CovalentInDB"]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        gate.REPORT_CSV.is_file()
        and gate.MANIFEST_JSON.is_file()
        and gate.DRY_RUN_TABLE_CSV.is_file()
        and gate.SUMMARY_MD.is_file()
    )
    if not needs_run:
        manifest = json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))
        needs_run = manifest["stage"] != gate.STAGE
    if needs_run:
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _dry_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(gate.DRY_RUN_TABLE_CSV)


def _bool_text(value: str) -> bool:
    return value == "True"


def test_step12r_precondition_and_manifest_csv_validates():
    assert gate.validate_step12r_pilot_download_manifest_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_pilot_download_dry_run_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_pilot_download_manifest_gate_v0"
    assert manifest["step12r_pilot_download_manifest_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["current_sample_count"] == 3
    assert manifest["metadata_completeness_ratio_text"] == "2/38"
    assert manifest["metadata_gap_level"] == "severe"
    assert gate.STEP12R_PILOT_MANIFEST_CSV.is_file()


def test_dry_run_manifest_summary_counts():
    manifest = _manifest()
    assert manifest["pilot_download_dry_run_defined"] is True
    assert manifest["pilot_download_dry_run_table_written"] is True
    assert manifest["dry_run_total_rows"] == 9
    assert manifest["dry_run_passed_rows"] == 6
    assert manifest["dry_run_blocked_as_expected_rows"] == 3
    assert manifest["dry_run_failed_rows"] == 0
    assert manifest["dry_run_pdb_direct_passed_rows"] == 3
    assert manifest["dry_run_local_curated_passed_rows"] == 3
    assert manifest["dry_run_blocked_source_rows"] == 3
    assert manifest["dry_run_network_called"] is False
    assert manifest["dry_run_files_downloaded"] is False
    assert manifest["dry_run_raw_dirs_created"] is False
    assert manifest["dry_run_raw_files_written"] is False
    assert manifest["dry_run_adapters_run"] is False
    assert manifest["all_allowed_pilot_jobs_ready_for_execution_after_dry_run"] is True
    assert manifest["all_blocked_sources_remain_not_ready_for_execution"] is True


def test_dry_run_policy_validations_and_decision():
    manifest = _manifest()
    assert manifest["dry_run_validated_manifest_schema"] is True
    assert manifest["dry_run_validated_url_strings"] is True
    assert manifest["dry_run_validated_local_output_paths"] is True
    assert manifest["dry_run_validated_checksum_policy"] is True
    assert manifest["dry_run_validated_provenance_policy"] is True
    assert manifest["dry_run_validated_blocked_source_policy"] is True
    assert manifest["ready_to_execute_pilot_download_after_dry_run"] is True
    assert manifest["pilot_download_execution_allowed_in_this_step"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["real_covalent_pilot_download_dry_run_gate_passed"] is True
    assert manifest["pilot_download_dry_run_contract_defined"] is True
    assert manifest["recommended_next_step"] == "real_covalent_pilot_download_execution_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_dry_run_table_shape_and_columns():
    rows = _dry_rows()
    assert gate.DRY_RUN_TABLE_CSV.is_file()
    assert len(rows) == 9
    assert list(rows[0]) == gate.DRY_RUN_TABLE_COLUMNS


def test_pdb_direct_dry_run_rows_pass():
    rows = [row for row in _dry_rows() if row["source_name"] == "PDB/mmCIF direct"]
    assert [row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS
    for row in rows:
        assert row["dry_run_status"] == "passed"
        assert _bool_text(row["schema_valid"]) is True
        assert _bool_text(row["source_policy_valid"]) is True
        assert _bool_text(row["url_string_valid"]) is True
        assert _bool_text(row["local_output_path_valid"]) is True
        assert _bool_text(row["checksum_policy_valid"]) is True
        assert _bool_text(row["provenance_policy_valid"]) is True
        assert _bool_text(row["blocked_source_policy_valid"]) is True
        assert _bool_text(row["ready_for_execution_after_dry_run"]) is True


def test_local_curated_dry_run_rows_pass():
    rows = [row for row in _dry_rows() if row["source_name"] == "local curated"]
    assert [row["sample_id"] for row in rows] == EXPECTED_SAMPLE_IDS
    for row in rows:
        assert row["dry_run_status"] == "passed"
        assert _bool_text(row["schema_valid"]) is True
        assert _bool_text(row["source_policy_valid"]) is True
        assert _bool_text(row["url_string_valid"]) is True
        assert _bool_text(row["local_output_path_valid"]) is True
        assert _bool_text(row["checksum_policy_valid"]) is True
        assert _bool_text(row["provenance_policy_valid"]) is True
        assert _bool_text(row["blocked_source_policy_valid"]) is True
        assert _bool_text(row["ready_for_execution_after_dry_run"]) is True


def test_blocked_source_dry_run_rows_remain_blocked():
    rows = [row for row in _dry_rows() if row["source_name"] in EXPECTED_BLOCKED_SOURCES]
    assert [row["source_name"] for row in rows] == EXPECTED_BLOCKED_SOURCES
    for row in rows:
        assert row["dry_run_status"] == "blocked_as_expected"
        assert _bool_text(row["schema_valid"]) is True
        assert _bool_text(row["source_policy_valid"]) is True
        assert _bool_text(row["url_string_valid"]) is True
        assert _bool_text(row["local_output_path_valid"]) is True
        assert _bool_text(row["checksum_policy_valid"]) is True
        assert _bool_text(row["provenance_policy_valid"]) is True
        assert _bool_text(row["blocked_source_policy_valid"]) is True
        assert _bool_text(row["ready_for_execution_after_dry_run"]) is False


def test_no_dry_run_row_performed_side_effects():
    for row in _dry_rows():
        assert _bool_text(row["network_called"]) is False
        assert _bool_text(row["file_downloaded"]) is False
        assert _bool_text(row["raw_dir_created"]) is False
        assert _bool_text(row["raw_file_written"]) is False
        assert _bool_text(row["adapter_run"]) is False


def test_safety_fields_are_false():
    manifest = _manifest()
    for key in [
        "data_downloaded",
        "external_network_called",
        "raw_storage_directories_created",
        "raw_download_files_written",
        "raw_structure_files_written",
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
        "forbidden_artifacts_created",
    ]:
        assert manifest[key] is False


def test_report_manifest_table_and_summary_written():
    _ensure_outputs()
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.DRY_RUN_TABLE_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    assert len(_read_csv(gate.REPORT_CSV)) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "pilot download dry-run gate",
        "not download execution",
        "not network",
        "not adapter execution",
        "not enrichment",
        "not split",
        "not training",
        "manifest schema",
        "URL strings",
        "local output paths",
        "checksum policy",
        "provenance policy",
        "blocked source policy",
        "6DI9",
        "5F2E",
        "6OIM",
        "BTK_C481_6DI9_pre_reaction",
        "KRAS_G12C_5F2E_pre_reaction",
        "KRAS_G12C_6OIM_pre_reaction",
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        "No data download/network/raw dirs/raw files/adapters",
        "No RDKit/UniProt/CD-HIT/geometry/NPZ/training",
        "ready_to_execute_pilot_download_after_dry_run=true",
        "pilot_download_execution_allowed_in_this_step=false",
        "real_covalent_pilot_download_execution_gate",
        "actually download 3 PDB/mmCIF .cif.gz files",
        "raw files cannot commit",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_no_forbidden_artifacts_and_protected_source_modification():
    if gate.OUTPUT_ROOT.exists():
        forbidden = [
            path
            for path in gate.OUTPUT_ROOT.rglob("*")
            if path.is_file() and path.suffix in gate.FORBIDDEN_ARTIFACT_SUFFIXES
        ]
        assert forbidden == []
    protected = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert protected.returncode == 0


def test_ast_and_text_safety():
    files = [
        REPO_ROOT / "src/covalent_ext/real_covalent_pilot_download_dry_run_gate.py",
        REPO_ROOT / "scripts/check_real_covalent_pilot_download_dry_run_gate_v0.py",
        REPO_ROOT / "tests/test_real_covalent_pilot_download_dry_run_gate_v0.py",
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
        "get",
        "urlopen",
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
        "requests." + "get",
        "ur" + "llib",
        "w" + "get ",
        "cu" + "rl ",
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

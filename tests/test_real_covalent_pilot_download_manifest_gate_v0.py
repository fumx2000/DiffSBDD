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

from covalent_ext import real_covalent_pilot_download_manifest_gate as gate  # noqa: E402
import check_real_covalent_pilot_download_manifest_gate_v0 as script  # noqa: E402


EXPECTED_SAMPLE_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_BLOCKED_SOURCES = ["CovPDB", "CovBinderInPDB", "CovalentInDB"]
EXPECTED_ALLOWED_SOURCES = ["PDB/mmCIF direct", "local curated"]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        gate.REPORT_CSV.is_file()
        and gate.MANIFEST_JSON.is_file()
        and gate.PILOT_DOWNLOAD_MANIFEST_CSV.is_file()
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


def _pilot_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(gate.PILOT_DOWNLOAD_MANIFEST_CSV)


def _bool_text(value: str) -> bool:
    return value == "True"


def test_step12q_precondition_and_metadata_state():
    assert gate.validate_step12q_source_registry_license_audit_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_pilot_download_manifest_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_source_registry_license_audit_gate_v0"
    assert manifest["step12q_source_registry_license_audit_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["current_sample_count"] == 3
    assert manifest["required_split_metadata_field_count"] == 38
    assert manifest["present_required_metadata_field_count"] == 2
    assert manifest["missing_required_metadata_field_count"] == 36
    assert manifest["metadata_completeness_ratio_text"] == "2/38"
    assert manifest["metadata_gap_level"] == "severe"


def test_sample_index_audit_for_pilot_ids():
    manifest = _manifest()
    assert manifest["sample_index_exists"] is True
    assert manifest["sample_index_current_sample_count"] == 3
    assert manifest["sample_index_sample_ids"] == EXPECTED_SAMPLE_IDS
    assert manifest["pilot_pdb_ids_derived_from_sample_ids"] == EXPECTED_PDB_IDS
    assert manifest["pilot_pdb_id_derivation_authoritative_for_manifest"] is True
    assert manifest["npz_files_loaded"] is False
    assert manifest["npz_contents_read"] is False


def test_pilot_manifest_counts_and_source_sets():
    manifest = _manifest()
    assert manifest["pilot_download_manifest_defined"] is True
    assert manifest["pilot_download_manifest_written"] is True
    assert manifest["pilot_download_manifest_row_count"] == 9
    assert manifest["pilot_download_job_count"] == 6
    assert manifest["blocked_source_row_count"] == 3
    assert manifest["pdb_direct_pilot_job_count"] == 3
    assert manifest["local_curated_pilot_job_count"] == 3
    assert manifest["pilot_pdb_ids"] == EXPECTED_PDB_IDS
    assert manifest["pilot_local_sample_ids"] == EXPECTED_SAMPLE_IDS
    assert manifest["blocked_sources"] == EXPECTED_BLOCKED_SOURCES
    assert manifest["allowed_pilot_sources"] == EXPECTED_ALLOWED_SOURCES
    assert manifest["all_pilot_jobs_download_disabled_in_this_step"] is True
    assert manifest["all_pilot_jobs_ready_for_dry_run"] is True
    assert manifest["any_pilot_job_ready_for_execution"] is False
    assert manifest["all_blocked_sources_not_ready_for_dry_run"] is True
    assert manifest["rcsb_mmcif_url_template_defined"] is True
    assert manifest["rcsb_mmcif_url_template_verified_by_external_audit"] is True
    assert manifest["checksum_required_for_pdb_downloads"] is True
    assert manifest["provenance_required_for_all_pilot_jobs"] is True
    assert manifest["pilot_manifest_does_not_grant_download_execution"] is True


def test_pilot_manifest_csv_columns_and_row_count():
    rows = _pilot_rows()
    assert gate.PILOT_DOWNLOAD_MANIFEST_CSV.is_file()
    assert len(rows) == 9
    assert list(rows[0]) == gate.PILOT_DOWNLOAD_MANIFEST_COLUMNS


def test_pdb_direct_manifest_rows():
    rows = [row for row in _pilot_rows() if row["source_name"] == "PDB/mmCIF direct"]
    assert [row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS
    for row in rows:
        pdb_id = row["pdb_id"]
        assert row["source_license_status"] == "verified_cc0_for_pdb_archive"
        assert _bool_text(row["source_license_verified_for_pilot"]) is True
        assert _bool_text(row["source_requires_manual_review"]) is False
        assert row["url_template"] == "https://files.rcsb.org/download/{pdb_id}.cif.gz"
        assert row["candidate_download_url"].endswith(f"/{pdb_id}.cif.gz")
        assert row["file_type"] == "pdbx_mmcif_gzip"
        assert row["compression"] == "gzip"
        assert row["expected_local_output_path"] == f"data/raw/covalent_sources/pdb_mmcif_direct/structures/{pdb_id}.cif.gz"
        assert _bool_text(row["checksum_required"]) is True
        assert row["sha256_expected_now"] == "not_available_until_download"
        assert row["checksum_status"] == "pending_download"
        assert _bool_text(row["resume_supported"]) is True
        assert row["retry_policy"] == "max_retries_3_exponential_backoff_design"
        assert _bool_text(row["provenance_required"]) is True
        assert _bool_text(row["download_enabled_in_this_step"]) is False
        assert _bool_text(row["ready_for_dry_run"]) is True
        assert _bool_text(row["ready_for_execution"]) is False
        assert row["blocked_reason"] == "download_execution_not_allowed_in_manifest_gate"
    by_pdb = {row["pdb_id"]: row for row in rows}
    assert by_pdb["6DI9"]["candidate_download_url"].endswith("/6DI9.cif.gz")
    assert by_pdb["5F2E"]["candidate_download_url"].endswith("/5F2E.cif.gz")
    assert by_pdb["6OIM"]["candidate_download_url"].endswith("/6OIM.cif.gz")


def test_local_curated_manifest_rows():
    rows = [row for row in _pilot_rows() if row["source_name"] == "local curated"]
    assert [row["sample_id"] for row in rows] == EXPECTED_SAMPLE_IDS
    assert [row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS
    for row in rows:
        assert row["candidate_download_url"] == "local_only"
        assert row["url_template"] == "local_only"
        assert row["file_type"] == "local_curated_existing_record"
        assert row["compression"] == "none"
        assert row["expected_local_output_path"] == "local_curated_existing_sample_index"
        assert row["raw_storage_root"] == "not_applicable"
        assert row["raw_subdir"] == "not_applicable"
        assert _bool_text(row["checksum_required"]) is False
        assert row["sha256_expected_now"] == "not_applicable"
        assert row["checksum_status"] == "not_applicable"
        assert _bool_text(row["resume_supported"]) is False
        assert row["retry_policy"] == "not_applicable"
        assert _bool_text(row["provenance_required"]) is True
        assert _bool_text(row["download_enabled_in_this_step"]) is False
        assert _bool_text(row["ready_for_dry_run"]) is True
        assert _bool_text(row["ready_for_execution"]) is False
        assert row["blocked_reason"] == "manual_provenance_manifest_not_created_yet"


def test_blocked_source_manifest_rows():
    rows = [row for row in _pilot_rows() if row["source_name"] in EXPECTED_BLOCKED_SOURCES]
    assert [row["source_name"] for row in rows] == EXPECTED_BLOCKED_SOURCES
    for row in rows:
        assert row["job_type"] == "blocked_source_no_pilot_download"
        assert row["source_license_status"] == "requires_manual_review"
        assert _bool_text(row["source_license_verified_for_pilot"]) is False
        assert _bool_text(row["source_requires_manual_review"]) is True
        assert row["candidate_download_url"] == ""
        assert row["url_template"] == ""
        assert _bool_text(row["checksum_required"]) is False
        assert _bool_text(row["download_enabled_in_this_step"]) is False
        assert _bool_text(row["ready_for_dry_run"]) is False
        assert _bool_text(row["ready_for_execution"]) is False
        assert row["blocked_reason"] == "manual_license_review_required"
        assert row["notes"] == "blocked by Step 12Q license audit"


def test_download_dry_run_readiness_policy_and_decision():
    manifest = _manifest()
    assert manifest["download_dry_run_readiness_policy_defined"] is True
    assert manifest["dry_run_checks_url_strings_only"] is True
    assert manifest["dry_run_may_create_raw_dirs"] is False
    assert manifest["dry_run_may_download_files"] is False
    assert manifest["dry_run_may_call_network"] is False
    assert manifest["dry_run_may_validate_manifest_schema"] is True
    assert manifest["dry_run_may_validate_local_output_paths"] is True
    assert manifest["dry_run_may_validate_source_license_status"] is True
    assert manifest["dry_run_may_validate_blocked_sources"] is True
    assert manifest["pilot_download_execution_requires_next_gate"] is True
    assert manifest["pilot_download_execution_allowed_after_this_step"] is False
    assert manifest["ready_to_run_pilot_download_dry_run"] is True
    assert manifest["ready_to_execute_pilot_download"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["real_covalent_pilot_download_manifest_gate_passed"] is True
    assert manifest["pilot_download_manifest_contract_defined"] is True
    assert manifest["recommended_next_step"] == "real_covalent_pilot_download_dry_run_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


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


def test_report_manifest_pilot_csv_and_summary_written():
    _ensure_outputs()
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.PILOT_DOWNLOAD_MANIFEST_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    assert len(_read_csv(gate.REPORT_CSV)) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "pilot download manifest gate",
        "not download execution",
        "not network",
        "not adapter execution",
        "not enrichment",
        "not split",
        "not training",
        "6DI9",
        "5F2E",
        "6OIM",
        "BTK_C481_6DI9_pre_reaction",
        "KRAS_G12C_5F2E_pre_reaction",
        "KRAS_G12C_6OIM_pre_reaction",
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        "https://files.rcsb.org/download/{pdb_id}.cif.gz",
        "verified_cc0_for_pdb_archive",
        "All downloads disabled",
        "ready_to_run_pilot_download_dry_run=true",
        "ready_to_execute_pilot_download=false",
        "No data download/network/raw dirs/raw files/adapters",
        "No RDKit/UniProt/CD-HIT/geometry/NPZ/training",
        "real_covalent_pilot_download_dry_run_gate",
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
        REPO_ROOT / "src/covalent_ext/real_covalent_pilot_download_manifest_gate.py",
        REPO_ROOT / "scripts/check_real_covalent_pilot_download_manifest_gate_v0.py",
        REPO_ROOT / "tests/test_real_covalent_pilot_download_manifest_gate_v0.py",
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

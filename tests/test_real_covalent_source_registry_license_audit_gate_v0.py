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

from covalent_ext import real_covalent_source_registry_license_audit_gate as audit  # noqa: E402
import check_real_covalent_source_registry_license_audit_gate_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        audit.REPORT_CSV.is_file()
        and audit.MANIFEST_JSON.is_file()
        and audit.SOURCE_REGISTRY_AUDIT_TABLE_CSV.is_file()
        and audit.SUMMARY_MD.is_file()
    )
    if not needs_run:
        manifest = json.loads(audit.MANIFEST_JSON.read_text(encoding="utf-8"))
        needs_run = manifest["stage"] != audit.STAGE
    if needs_run:
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(audit.MANIFEST_JSON.read_text(encoding="utf-8"))


def _audit_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(audit.SOURCE_REGISTRY_AUDIT_TABLE_CSV)


def _rows_by_source() -> dict[str, dict[str, str]]:
    return {row["source_name"]: row for row in _audit_rows()}


def _bool_text(value: str) -> bool:
    return value == "True"


def test_step12p_precondition_and_gap_state():
    assert audit.validate_step12p_multi_source_dataset_ingestion_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_source_registry_license_audit_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_multi_source_dataset_ingestion_design_gate_v0"
    assert manifest["step12p_multi_source_dataset_ingestion_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["current_sample_count"] == 3
    assert manifest["required_split_metadata_field_count"] == 38
    assert manifest["present_required_metadata_field_count"] == 2
    assert manifest["missing_required_metadata_field_count"] == 36
    assert manifest["metadata_completeness_ratio_text"] == "2/38"
    assert manifest["metadata_gap_level"] == "severe"


def test_source_registry_license_audit_seed_counts():
    manifest = _manifest()
    assert manifest["source_registry_license_audit_seed_defined"] is True
    assert manifest["source_registry_audit_record_count"] == 5
    assert manifest["audited_source_names"] == ["CovPDB", "CovBinderInPDB", "CovalentInDB", "PDB/mmCIF direct", "local curated"]
    assert manifest["sources_with_verified_license_count"] == 2
    assert manifest["sources_with_verified_license"] == ["PDB/mmCIF direct", "local curated"]
    assert manifest["sources_requiring_manual_license_review_count"] == 3
    assert manifest["sources_requiring_manual_license_review"] == ["CovPDB", "CovBinderInPDB", "CovalentInDB"]
    assert manifest["sources_pilot_candidate_count"] == 2
    assert manifest["sources_pilot_candidate_after_audit"] == ["PDB/mmCIF direct", "local curated"]
    assert manifest["sources_bulk_download_candidate_count"] == 0
    assert manifest["sources_bulk_download_candidate_after_audit"] == []
    assert manifest["all_bulk_downloads_disabled_after_audit"] is True
    assert manifest["source_registry_audit_table_written"] is True


def test_non_pdb_source_records_are_not_overclaimed():
    rows = _rows_by_source()
    covpdb = rows["CovPDB"]
    assert covpdb["license_usage_status"] == "requires_manual_review"
    assert _bool_text(covpdb["requires_manual_license_review"]) is True
    assert _bool_text(covpdb["download_enabled_after_audit"]) is False
    assert _bool_text(covpdb["pilot_download_candidate_after_audit"]) is False
    assert _bool_text(covpdb["bulk_download_candidate_after_audit"]) is False
    assert "explicit_bulk_download_license_not_verified" in json.loads(covpdb["audit_blocking_reasons"])

    covbinder = rows["CovBinderInPDB"]
    assert covbinder["license_usage_status"] == "requires_manual_review"
    assert "dataset_download_endpoint_not_verified" in json.loads(covbinder["audit_blocking_reasons"])

    covalentindb = rows["CovalentInDB"]
    assert covalentindb["license_usage_status"] == "requires_manual_review"
    reasons = json.loads(covalentindb["audit_blocking_reasons"])
    assert "robot_or_access_control_possible" in reasons
    assert "bulk_reuse_license_not_verified" in reasons


def test_pdb_direct_and_local_curated_pilot_candidates():
    rows = _rows_by_source()
    pdb = rows["PDB/mmCIF direct"]
    assert pdb["license_usage_status"] == "verified_cc0_for_pdb_archive"
    assert _bool_text(pdb["requires_manual_license_review"]) is False
    assert _bool_text(pdb["download_enabled_after_audit"]) is False
    assert _bool_text(pdb["pilot_download_candidate_after_audit"]) is True
    assert _bool_text(pdb["bulk_download_candidate_after_audit"]) is False
    assert "download_manifest_not_created_yet" in json.loads(pdb["audit_blocking_reasons"])
    assert "CC0" in pdb["usage_note"]

    local = rows["local curated"]
    assert local["license_usage_status"] == "local_project_controlled"
    assert _bool_text(local["requires_manual_license_review"]) is False
    assert _bool_text(local["pilot_download_candidate_after_audit"]) is True
    assert _bool_text(local["bulk_download_candidate_after_audit"]) is False
    assert "manual_provenance_manifest_required" in json.loads(local["audit_blocking_reasons"])


def test_license_decision_policy():
    manifest = _manifest()
    assert manifest["license_decision_policy_defined"] is True
    assert manifest["explicit_license_required_for_bulk_download"] is True
    assert manifest["unclear_license_blocks_bulk_download"] is True
    assert manifest["unclear_license_blocks_pilot_download"] is True
    assert manifest["pdb_direct_cc0_allows_future_pilot_manifest"] is True
    assert manifest["local_curated_allows_future_pilot_manifest"] is True
    assert manifest["non_pdb_sources_require_manual_license_review"] is True
    assert manifest["publication_found_is_not_license_clearance"] is True
    assert manifest["free_web_access_is_not_bulk_download_permission"] is True
    assert manifest["robot_access_control_blocks_automated_download"] is True
    assert manifest["manual_review_required_before_non_pdb_pilot"] is True
    assert manifest["license_audit_does_not_grant_download_permission"] is True


def test_pilot_eligibility_decision():
    manifest = _manifest()
    assert manifest["pilot_eligibility_decision_defined"] is True
    assert manifest["pilot_eligible_sources_after_audit"] == ["PDB/mmCIF direct", "local curated"]
    assert manifest["pilot_blocked_sources_after_audit"] == ["CovPDB", "CovBinderInPDB", "CovalentInDB"]
    assert manifest["recommended_pilot_download_manifest_sources"] == ["PDB/mmCIF direct", "local curated"]
    assert manifest["ready_to_create_pilot_download_manifest"] is True
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["pilot_download_allowed_after_this_step"] is False


def test_audit_output_schema():
    manifest = _manifest()
    assert manifest["source_registry_audit_output_schema_defined"] is True
    assert manifest["source_registry_license_audit_table_required"] is True
    assert manifest["source_registry_license_audit_table_written"] is True
    assert manifest["source_registry_json_for_download_written"] is False
    assert manifest["download_manifest_written"] is False
    assert manifest["raw_registry_written"] is False
    assert manifest["raw_data_written"] is False
    assert len(_audit_rows()) == 5
    assert set(_audit_rows()[0]) == set(audit.AUDIT_TABLE_COLUMNS)


def test_safety_fields_and_decision():
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
    assert manifest["real_covalent_source_registry_license_audit_gate_passed"] is True
    assert manifest["source_registry_license_audit_contract_defined"] is True
    assert manifest["recommended_next_step"] == "real_covalent_pilot_download_manifest_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_report_manifest_table_and_summary_written():
    _ensure_outputs()
    assert audit.REPORT_CSV.is_file()
    assert audit.MANIFEST_JSON.is_file()
    assert audit.SOURCE_REGISTRY_AUDIT_TABLE_CSV.is_file()
    assert audit.SUMMARY_MD.is_file()
    assert len(_read_csv(audit.REPORT_CSV)) == 8
    assert len(_read_csv(audit.SOURCE_REGISTRY_AUDIT_TABLE_CSV)) == 5
    summary = audit.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "source registry license audit gate",
        "not downloading",
        "not adapter implementation",
        "not enrichment",
        "not split",
        "not training",
        "manual web-audit seed",
        "PDB archive license status verified CC0",
        "local project controlled",
        "CovPDB / CovBinderInPDB / CovalentInDB require manual license review",
        "Publication found is not license clearance",
        "Free web access is not bulk download permission",
        "All bulk downloads disabled",
        "Pilot candidates after audit are PDB/mmCIF direct and local curated",
        "No data download/network/raw dirs/raw files/adapters",
        "real_covalent_pilot_download_manifest_gate",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_no_forbidden_artifacts_and_protected_source_modification():
    if audit.OUTPUT_ROOT.exists():
        forbidden = [
            path
            for path in audit.OUTPUT_ROOT.rglob("*")
            if path.is_file() and path.suffix in audit.FORBIDDEN_ARTIFACT_SUFFIXES
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
        REPO_ROOT / "src/covalent_ext/real_covalent_source_registry_license_audit_gate.py",
        REPO_ROOT / "scripts/check_real_covalent_source_registry_license_audit_gate_v0.py",
        REPO_ROOT / "tests/test_real_covalent_source_registry_license_audit_gate_v0.py",
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

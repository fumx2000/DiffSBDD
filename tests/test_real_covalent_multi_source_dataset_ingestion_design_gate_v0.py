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

from covalent_ext import real_covalent_multi_source_dataset_ingestion_design_gate as design  # noqa: E402
import check_real_covalent_multi_source_dataset_ingestion_design_gate_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        design.REPORT_CSV.is_file()
        and design.MANIFEST_JSON.is_file()
        and design.DESIGN_TABLE_CSV.is_file()
        and design.SUMMARY_MD.is_file()
    )
    if not needs_run:
        manifest = json.loads(design.MANIFEST_JSON.read_text(encoding="utf-8"))
        needs_run = manifest["stage"] != design.STAGE
    if needs_run:
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(design.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_step12o_precondition_and_gap_state():
    assert design.validate_step12o_split_metadata_enrichment_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_multi_source_dataset_ingestion_design_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_split_metadata_enrichment_design_gate_v0"
    assert manifest["step12o_split_metadata_enrichment_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["current_sample_count"] == 3
    assert manifest["required_split_metadata_field_count"] == 38
    assert manifest["present_required_metadata_field_count"] == 2
    assert manifest["missing_required_metadata_field_count"] == 36
    assert manifest["metadata_completeness_ratio_text"] == "2/38"
    assert manifest["metadata_gap_level"] == "severe"


def test_multi_source_ingestion_concept():
    manifest = _manifest()
    assert manifest["multi_source_ingestion_concept_defined"] is True
    assert (
        manifest["multi_source_ingestion_definition"]
        == "standardize_source_specific_covalent_dataset_downloads_into_versioned_raw_records_before_enrichment"
    )
    assert manifest["multi_source_ingestion_not_equal_to_downloading"] is True
    assert manifest["multi_source_ingestion_not_equal_to_enrichment"] is True
    assert manifest["multi_source_ingestion_not_equal_to_training"] is True
    assert manifest["ingestion_design_precedes_actual_download"] is True
    assert manifest["ingestion_design_precedes_metadata_enrichment"] is True
    assert manifest["ingestion_design_defines_storage_registry_resume_checksum_and_provenance"] is True
    assert manifest["large_scale_download_still_blocked_until_source_registry_license_audit"] is True


def test_source_registry_schema_and_placeholder_policy():
    manifest = _manifest()
    assert manifest["source_registry_schema_defined"] is True
    assert manifest["source_registry_entry_count"] == 5
    assert manifest["planned_source_registry_entries"] == [
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        "PDB/mmCIF direct",
        "local curated",
    ]
    assert manifest["source_urls_are_placeholders"] is True
    assert manifest["source_url_currentness_not_verified"] is True
    assert manifest["license_usage_currentness_not_verified"] is True
    assert manifest["source_registry_license_audit_required"] is True
    assert manifest["source_registry_written"] is False
    for field in [
        "source_name",
        "adapter_name",
        "source_url",
        "license_or_usage_note",
        "checksum_policy",
        "resume_policy",
        "quality_flags",
        "blocking_reasons",
    ]:
        assert field in manifest["source_registry_entry_fields"]


def test_raw_storage_and_download_job_manifest_design():
    manifest = _manifest()
    assert manifest["raw_storage_layout_defined"] is True
    assert manifest["raw_storage_root_design"] == "data/raw/covalent_sources"
    for subdir in ["downloads", "structures", "tables", "manifests", "logs", "checksums"]:
        assert subdir in manifest["raw_source_subdirectories"]
    assert manifest["raw_storage_directories_created"] is False
    assert manifest["raw_download_files_written"] is False
    assert manifest["raw_structure_files_written"] is False
    assert manifest["raw_data_must_not_be_committed"] is True
    assert manifest["design_outputs_only_in_git"] is True

    assert manifest["download_job_manifest_schema_defined"] is True
    assert manifest["download_job_manifest_required_before_download"] is True
    assert manifest["incremental_download_manifest_required"] is True
    assert manifest["checksum_manifest_required"] is True
    assert manifest["resume_policy_required"] is True
    assert manifest["retry_policy_required"] is True
    assert manifest["provenance_record_required"] is True
    assert manifest["download_jobs_written"] is False
    assert manifest["download_jobs_run"] is False


def test_source_adapter_interface_contract():
    manifest = _manifest()
    assert manifest["source_adapter_interface_contract_defined"] is True
    assert manifest["adapter_input_contract_defined"] is True
    assert manifest["adapter_output_contract_defined"] is True
    assert manifest["canonical_raw_record_required_fields_defined"] is True
    assert manifest["all_adapters_must_emit_canonical_raw_records"] is True
    assert manifest["adapter_quality_report_required"] is True
    assert manifest["deferred_raw_records_report_required"] is True
    assert manifest["duplicate_candidate_keys_required"] is True
    assert manifest["adapter_implementation_allowed_after_this_step"] is False
    assert manifest["adapter_execution_allowed_after_this_step"] is False
    for field in [
        "source_dataset",
        "source_record_id",
        "source_version",
        "source_license_or_usage_note",
        "source_url_or_local_path",
        "pdb_id",
        "ligand_structure_path",
        "protein_structure_path",
        "complex_structure_path",
        "covalent_bond_annotation_raw",
    ]:
        assert field in manifest["canonical_raw_record_required_fields"]


def test_source_specific_ingestion_design_details():
    manifest = _manifest()
    assert manifest["source_specific_ingestion_design_details_defined"] is True
    assert manifest["covpdb_ingestion_design_defined"] is True
    assert manifest["covbinderinpdb_ingestion_design_defined"] is True
    assert manifest["covalentindb_ingestion_design_defined"] is True
    assert manifest["pdb_direct_ingestion_design_defined"] is True
    assert manifest["local_curated_ingestion_design_defined"] is True
    details = manifest["source_specific_ingestion_details"]
    expected = {
        "CovPDB": "covpdb_adapter",
        "CovBinderInPDB": "covbinderinpdb_adapter",
        "CovalentInDB": "covalentindb_adapter",
        "PDB/mmCIF direct": "pdb_direct_adapter",
        "local curated": "local_curated_adapter",
    }
    for source_name, adapter_name in expected.items():
        assert details[source_name]["adapter_name"] == adapter_name
        assert details[source_name]["expected_raw_inputs"]
        assert details[source_name]["known_risks"]


def test_duplicate_provenance_priority_policy():
    manifest = _manifest()
    assert manifest["duplicate_provenance_priority_policy_defined"] is True
    for key in [
        "pdb_id",
        "chain_id",
        "ligand_id",
        "residue_id",
        "ligand_inchikey_after_enrichment",
        "parent_complex_id_after_enrichment",
    ]:
        assert key in manifest["duplicate_detection_keys"]
    assert manifest["duplicate_detection_across_sources_required"] is True
    assert manifest["source_priority_policy_defined"] is True
    assert manifest["source_priority_order_design"][0] == "local_curated"
    assert manifest["source_priority_is_design_only"] is True
    assert manifest["duplicate_resolution_requires_audit"] is True
    assert manifest["duplicate_records_not_dropped_without_report"] is True
    assert manifest["provenance_chain_required"] is True
    assert manifest["source_record_id_required"] is True
    assert manifest["source_version_required"] is True
    assert manifest["source_license_or_usage_note_required"] is True


def test_small_pilot_and_git_data_policy():
    manifest = _manifest()
    assert manifest["small_pilot_ingestion_plan_defined"] is True
    assert manifest["pilot_before_large_scale_download_required"] is True
    assert manifest["recommended_pilot_scope"] == "one_to_three_records_per_source_after_license_audit"
    assert manifest["pilot_max_records_per_source"] == 3
    assert manifest["pilot_requires_current_source_registry"] is True
    assert manifest["pilot_requires_license_audit"] is True
    assert manifest["pilot_requires_download_manifest"] is True
    assert manifest["pilot_requires_checksum_manifest"] is True
    assert manifest["pilot_requires_raw_data_not_in_git"] is True
    assert manifest["pilot_download_allowed_in_this_step"] is False
    assert manifest["large_scale_download_allowed_in_this_step"] is False

    assert manifest["git_data_policy_defined"] is True
    for suffix in [".py", ".csv", ".json", ".md"]:
        assert suffix in manifest["allowed_git_artifact_suffixes_for_design"]
    for suffix in [".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2"]:
        assert suffix in manifest["forbidden_git_artifact_suffixes"]
    assert manifest["raw_data_not_in_git_policy_defined"] is True
    assert manifest["raw_downloads_must_not_be_committed"] is True
    assert manifest["raw_structures_must_not_be_committed"] is True
    assert manifest["generated_training_tensors_must_not_be_committed"] is True
    assert manifest["checkpoint_files_must_not_be_committed"] is True
    assert manifest["future_download_outputs_go_under_data_raw_or_external_storage"] is True


def test_safety_fields_and_decision():
    manifest = _manifest()
    for key in [
        "data_downloaded",
        "external_network_called",
        "source_registry_written",
        "raw_storage_directories_created",
        "raw_download_files_written",
        "raw_structure_files_written",
        "download_jobs_written",
        "download_jobs_run",
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
    assert manifest["real_covalent_multi_source_dataset_ingestion_design_gate_passed"] is True
    assert manifest["multi_source_dataset_ingestion_design_contract_defined"] is True
    assert manifest["ready_to_create_source_registry_license_audit"] is True
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_source_registry_license_audit_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_report_manifest_table_and_summary_written():
    _ensure_outputs()
    assert design.REPORT_CSV.is_file()
    assert design.MANIFEST_JSON.is_file()
    assert design.DESIGN_TABLE_CSV.is_file()
    assert design.SUMMARY_MD.is_file()
    assert len(_read_csv(design.REPORT_CSV)) == 11
    table = _read_csv(design.DESIGN_TABLE_CSV)
    assert [row["row_type"] for row in table] == [
        "step12o_precondition",
        "multi_source_ingestion_concept",
        "source_registry_schema",
        "raw_storage_layout_design",
        "download_job_manifest_schema",
        "source_adapter_interface_contract",
        "source_specific_ingestion_design_details",
        "duplicate_provenance_priority_policy",
        "small_pilot_ingestion_plan",
        "git_data_policy",
        "safety_and_next_step_decision",
    ]
    summary = design.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "multi-source dataset ingestion design gate",
        "not downloading",
        "not enrichment",
        "not split",
        "not training",
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        "PDB/mmCIF direct",
        "local curated",
        "Source URL placeholders",
        "source registry license audit",
        "canonical raw covalent records",
        "cannot one-pot merge before normalization",
        "data/raw/covalent_sources",
        "created no raw dirs",
        "Download manifest, checksum, resume, and provenance",
        "Raw downloads and large binary structures cannot commit",
        "1-3 records per source",
        "No data download/network/source registry/raw dirs/adapters",
        "No RDKit/UniProt/CD-HIT/geometry/NPZ/training",
        "real_covalent_source_registry_license_audit_gate",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_no_forbidden_artifacts_and_protected_source_modification():
    if design.OUTPUT_ROOT.exists():
        forbidden = [
            path
            for path in design.OUTPUT_ROOT.rglob("*")
            if path.is_file() and path.suffix in design.FORBIDDEN_ARTIFACT_SUFFIXES
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
        REPO_ROOT / "src/covalent_ext/real_covalent_multi_source_dataset_ingestion_design_gate.py",
        REPO_ROOT / "scripts/check_real_covalent_multi_source_dataset_ingestion_design_gate_v0.py",
        REPO_ROOT / "tests/test_real_covalent_multi_source_dataset_ingestion_design_gate_v0.py",
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

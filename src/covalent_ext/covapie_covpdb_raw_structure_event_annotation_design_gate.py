from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_covpdb_raw_structure_event_annotation_design_gate_v0"
PREVIOUS_STAGE = "covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AT_ROOT = Path("data/derived/covalent_small/covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0")
STEP13AT_MANIFEST_JSON = STEP13AT_ROOT / "covapie_covpdb_complex_card_metadata_acquisition_qa_gate_manifest.json"
STEP13AT_EVENT_FIELD_SUMMARY_CSV = STEP13AT_ROOT / "covapie_covpdb_complex_card_event_field_status_summary_qa.csv"
STEP13AT_EVENT_KEY_SUMMARY_CSV = STEP13AT_ROOT / "covapie_covpdb_complex_card_event_key_resolution_summary_qa.csv"
STEP13AT_UNRESOLVED_REASON_CSV = STEP13AT_ROOT / "covapie_covpdb_complex_card_unresolved_reason_qa.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_annotation_precondition_audit.csv"
DOWNLOAD_SCOPE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_raw_structure_download_scope_contract.csv"
SOURCE_URL_CONTRACT_CSV = OUTPUT_ROOT / "covapie_raw_structure_source_url_contract.csv"
STORAGE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_raw_structure_storage_contract.csv"
PARSER_PRIORITY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_raw_structure_parser_priority_contract.csv"
MMCIF_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "covapie_mmcif_struct_conn_field_mapping_contract.csv"
PDB_LINK_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "covapie_pdb_link_record_field_mapping_contract.csv"
EVENT_KEY_RESOLUTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_key_resolution_contract.csv"
FAILURE_TAXONOMY_CSV = OUTPUT_ROOT / "covapie_raw_structure_failure_taxonomy.csv"
MATERIALIZATION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_materialization_boundary_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_annotation_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_raw_structure_event_annotation_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_covpdb_raw_structure_event_annotation_design_gate_v0_summary.md")

RAW_STORAGE_ROOT = "data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0/"
CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
FORBIDDEN_SUFFIXES = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
DOWNLOAD_SCOPE_COLUMNS = ["card_index", "pdb_id", "het_code", "allowed_for_next_smoke", "preferred_format", "fallback_format", "max_structure_count", "ligand_sdf_allowed", "archive_download_allowed", "recursive_crawling_allowed", "web_link_following_allowed", "download_scope_contract_passed", "blocking_reasons"]
SOURCE_URL_COLUMNS = ["card_index", "pdb_id", "het_code", "url_role", "source_domain", "url_template", "resolved_url", "allowed_for_next_smoke", "accessed_current_step", "source_url_contract_passed", "blocking_reasons"]
STORAGE_COLUMNS = ["storage_contract_item", "contract_value", "raw_files_must_remain_untracked", "git_add_allowed", "git_commit_allowed", "storage_contract_passed", "blocking_reasons"]
PARSER_PRIORITY_COLUMNS = ["parser_priority", "parser_source", "parser_role", "allowed_in_first_raw_annotation_smoke", "fallback_only", "contract_status", "parser_priority_contract_passed", "blocking_reasons"]
MAPPING_COLUMNS = ["source_format", "source_category", "source_field", "maps_to_covapie_field", "required_for_minimal_event_key", "required_for_preferred_event_key", "validation_role", "mapping_contract_passed", "blocking_reasons"]
EVENT_KEY_COLUMNS = ["resolution_status", "preferred_event_key_allowed", "minimal_event_key_allowed", "candidate_metadata_can_materialize", "allowlist_can_materialize", "manual_review_required", "policy", "event_key_resolution_contract_passed", "blocking_reasons"]
FAILURE_COLUMNS = ["failure_reason", "failure_class", "blocks_automatic_materialization", "recommended_handling", "failure_taxonomy_passed", "blocking_reasons"]
MATERIALIZATION_COLUMNS = ["boundary_item", "current_step_status", "future_condition", "materialization_boundary_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_raw_structure_event_annotation_design_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = ["leakage_split_item", "current_step_status", "future_required_gate", "split_written_current_step", "leakage_matrix_written_current_step", "blocking_for_training", "leakage_split_audit_passed", "blocking_reasons"]
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]

MMCIF_FIELDS = [
    ("struct_conn", "conn_type_id", "connection_type", False, False, "filter_explicit_covalent_connections"),
    ("struct_conn", "ptnr1_label_atom_id", "partner1_atom_name", True, True, "candidate_partner_atom"),
    ("struct_conn", "ptnr1_label_comp_id", "partner1_residue_or_ligand_name", True, True, "candidate_partner_residue"),
    ("struct_conn", "ptnr1_label_asym_id", "partner1_label_chain_id", False, False, "label_chain_crosscheck"),
    ("struct_conn", "ptnr1_auth_asym_id", "partner1_chain_id", True, True, "auth_chain_source"),
    ("struct_conn", "ptnr1_auth_seq_id", "partner1_residue_index", True, True, "auth_residue_index_source"),
    ("struct_conn", "ptnr2_label_atom_id", "partner2_atom_name", True, True, "candidate_partner_atom"),
    ("struct_conn", "ptnr2_label_comp_id", "partner2_residue_or_ligand_name", True, True, "candidate_partner_residue"),
    ("struct_conn", "ptnr2_label_asym_id", "partner2_label_chain_id", False, False, "label_chain_crosscheck"),
    ("struct_conn", "ptnr2_auth_asym_id", "partner2_chain_id", True, True, "auth_chain_source"),
    ("struct_conn", "ptnr2_auth_seq_id", "partner2_residue_index", True, True, "auth_residue_index_source"),
    ("struct_conn", "pdbx_dist_value", "covalent_bond_distance", False, False, "optional_distance_evidence"),
    ("atom_site", "label_atom_id", "atom_site_atom_name", False, False, "validate_partner_atoms_exist"),
    ("atom_site", "label_comp_id", "atom_site_residue_or_ligand_name", False, False, "validate_partner_compounds_exist"),
    ("atom_site", "auth_asym_id", "atom_site_chain_id", False, False, "validate_chain_exists"),
    ("atom_site", "auth_seq_id", "atom_site_residue_index", False, False, "validate_residue_exists"),
    ("atom_site", "Cartn_x", "atom_site_x_coordinate", False, False, "metadata_count_only_no_coordinate_export"),
    ("atom_site", "Cartn_y", "atom_site_y_coordinate", False, False, "metadata_count_only_no_coordinate_export"),
    ("atom_site", "Cartn_z", "atom_site_z_coordinate", False, False, "metadata_count_only_no_coordinate_export"),
]
PDB_FIELDS = [
    ("LINK", "atomName1", "link_partner1_atom_name", True, True, "candidate_partner_atom"),
    ("LINK", "resName1", "link_partner1_residue_or_ligand_name", True, True, "candidate_partner_residue"),
    ("LINK", "chainID1", "link_partner1_chain_id", True, True, "chain_source"),
    ("LINK", "resSeq1", "link_partner1_residue_index", True, True, "residue_index_source"),
    ("LINK", "atomName2", "link_partner2_atom_name", True, True, "candidate_partner_atom"),
    ("LINK", "resName2", "link_partner2_residue_or_ligand_name", True, True, "candidate_partner_residue"),
    ("LINK", "chainID2", "link_partner2_chain_id", True, True, "chain_source"),
    ("LINK", "resSeq2", "link_partner2_residue_index", True, True, "residue_index_source"),
    ("LINK", "distance", "covalent_bond_distance", False, False, "optional_distance_evidence"),
    ("ATOM/HETATM", "serial", "atom_serial", False, False, "conect_atom_mapping"),
    ("ATOM/HETATM", "atom name", "atom_name", False, False, "validate_partner_atoms_exist"),
    ("ATOM/HETATM", "residue name", "residue_or_ligand_name", False, False, "validate_partner_compounds_exist"),
    ("ATOM/HETATM", "chain ID", "chain_id", False, False, "validate_chain_exists"),
    ("ATOM/HETATM", "residue sequence", "residue_index", False, False, "validate_residue_exists"),
    ("ATOM/HETATM", "x/y/z", "atom_coordinates", False, False, "metadata_count_only_no_coordinate_export"),
]
EVENT_STATUSES = [
    "raw_resolves_preferred_event_key",
    "raw_resolves_minimal_event_key",
    "raw_partial_event_key_only",
    "raw_no_connectivity_records_found",
    "raw_multiple_candidate_links",
    "raw_ligand_het_code_not_found",
    "raw_protein_partner_not_found",
    "raw_requires_manual_review",
    "raw_parse_failed",
]
FAILURE_REASONS = [
    "raw_download_deferred_current_step",
    "mmcif_url_not_allowed",
    "pdb_url_not_allowed",
    "raw_file_saved_to_wrong_location",
    "raw_file_staged_or_tracked",
    "mmcif_struct_conn_missing",
    "mmcif_struct_conn_parse_failed",
    "mmcif_atom_site_missing",
    "pdb_link_missing",
    "pdb_link_parse_failed",
    "pdb_conect_missing",
    "ligand_het_code_not_found",
    "multiple_candidate_covalent_links",
    "protein_ligand_partner_ambiguous",
    "covalent_bond_atom_pair_missing",
    "distance_fallback_not_allowed_current_smoke",
    "candidate_metadata_attempted_too_early",
    "training_attempted_too_early",
]
EXECUTION_BOUNDARY_STATUSES = {
    "raw_structure_event_annotation_design_gate": "executed_design_gate_only",
    "step13at_manifest_read": "executed_manifest_read_only",
    "metadata_csv_first5_pdb_ids_read": "executed_metadata_read_only",
    "raw_download_scope_contract_write": "executed_contract_only",
    "source_url_contract_write": "executed_contract_only",
    "parser_priority_contract_write": "executed_contract_only",
    "mmcif_mapping_contract_write": "executed_contract_only",
    "pdb_link_mapping_contract_write": "executed_contract_only",
    "external_network_access": "not_executed_or_not_allowed",
    "raw_structure_download": "not_executed_or_not_allowed",
    "raw_ligand_download": "not_executed_or_not_allowed",
    "raw_file_created": "not_executed_or_not_allowed",
    "raw_data_read": "not_executed_or_not_allowed",
    "sdf_read": "not_executed_or_not_allowed",
    "pdb_read": "not_executed_or_not_allowed",
    "mmcif_read": "not_executed_or_not_allowed",
    "gzip_open": "not_executed_or_not_allowed",
    "rdkit_use": "not_executed_or_not_allowed",
    "biopdb_use": "not_executed_or_not_allowed",
    "gemmi_use": "not_executed_or_not_allowed",
    "candidate_metadata_materialization": "not_executed_or_not_allowed",
    "allowlist_materialization": "not_executed_or_not_allowed",
    "torch_import": "not_executed_or_not_allowed",
    "model_forward": "not_executed_or_not_allowed",
    "training_claim": "not_executed_or_not_allowed",
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def _metadata_hash() -> str:
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _bool_text(value: Any) -> str:
    return "True" if value is True or str(value) == "True" else "False"


def first5_metadata_rows() -> list[dict[str, str]]:
    return _csv_rows(METADATA_CSV)[:5]


def _precondition_rows(manifest13at: dict[str, Any], metadata_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    checks = [
        ("step13at_manifest", str(STEP13AT_MANIFEST_JSON), "exists", STEP13AT_MANIFEST_JSON.exists(), STEP13AT_MANIFEST_JSON.exists()),
        ("step13at_stage", str(STEP13AT_MANIFEST_JSON), PREVIOUS_STAGE, manifest13at.get("stage"), manifest13at.get("stage") == PREVIOUS_STAGE),
        ("step13at_ready_for_html_probe", str(STEP13AT_MANIFEST_JSON), "true", manifest13at.get("ready_for_covapie_covpdb_complex_card_html_structure_probe_design_gate"), manifest13at.get("ready_for_covapie_covpdb_complex_card_html_structure_probe_design_gate") is True),
        ("step13at_event_fields_unresolved", str(STEP13AT_MANIFEST_JSON), "0 resolved", manifest13at.get("minimal_event_key_resolved_card_count"), manifest13at.get("minimal_event_key_resolved_card_count") == 0),
        ("event_field_summary", str(STEP13AT_EVENT_FIELD_SUMMARY_CSV), "5 rows", len(_csv_rows(STEP13AT_EVENT_FIELD_SUMMARY_CSV)) if STEP13AT_EVENT_FIELD_SUMMARY_CSV.exists() else "missing", STEP13AT_EVENT_FIELD_SUMMARY_CSV.exists() and len(_csv_rows(STEP13AT_EVENT_FIELD_SUMMARY_CSV)) == 5),
        ("event_key_summary", str(STEP13AT_EVENT_KEY_SUMMARY_CSV), "1 row", len(_csv_rows(STEP13AT_EVENT_KEY_SUMMARY_CSV)) if STEP13AT_EVENT_KEY_SUMMARY_CSV.exists() else "missing", STEP13AT_EVENT_KEY_SUMMARY_CSV.exists() and len(_csv_rows(STEP13AT_EVENT_KEY_SUMMARY_CSV)) == 1),
        ("unresolved_reason_qa", str(STEP13AT_UNRESOLVED_REASON_CSV), "5 rows", len(_csv_rows(STEP13AT_UNRESOLVED_REASON_CSV)) if STEP13AT_UNRESOLVED_REASON_CSV.exists() else "missing", STEP13AT_UNRESOLVED_REASON_CSV.exists() and len(_csv_rows(STEP13AT_UNRESOLVED_REASON_CSV)) == 5),
        ("metadata_csv_first5", str(METADATA_CSV), "5 rows", len(metadata_rows), len(metadata_rows) == 5),
        ("covapie_naming_convention", str(NAMING_CONVENTION_MD), "exists", NAMING_CONVENTION_MD.exists(), NAMING_CONVENTION_MD.exists()),
        ("metadata_csv_hash_unchanged", str(METADATA_CSV), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("protected_source_diff", "git diff equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff", "git diff dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("raw_files_staged", "git diff --cached data/raw/covalent_sources", "false", _raw_files_staged(), not _raw_files_staged()),
        ("raw_files_tracked", "git ls-files data/raw/covalent_sources", "false", _raw_files_tracked(), not _raw_files_tracked()),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": artifact,
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else f"{item}_failed",
        }
        for item, artifact, expected, observed, passed in checks
    ]


def _download_scope_rows(metadata_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "card_index": index,
            "pdb_id": row["pdb_id"],
            "het_code": row["het_code"],
            "allowed_for_next_smoke": True,
            "preferred_format": "mmcif",
            "fallback_format": "pdb",
            "max_structure_count": 5,
            "ligand_sdf_allowed": False,
            "archive_download_allowed": False,
            "recursive_crawling_allowed": False,
            "web_link_following_allowed": False,
            "download_scope_contract_passed": True,
            "blocking_reasons": "",
        }
        for index, row in enumerate(metadata_rows, start=1)
    ]


def _source_url_rows(metadata_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(metadata_rows, start=1):
        pdb_id = row["pdb_id"].upper()
        for role, template, resolved in [
            ("primary_mmcif", "https://files.rcsb.org/download/{pdb_id}.cif", f"https://files.rcsb.org/download/{pdb_id}.cif"),
            ("fallback_pdb", "https://files.rcsb.org/download/{pdb_id}.pdb", f"https://files.rcsb.org/download/{pdb_id}.pdb"),
        ]:
            rows.append(
                {
                    "card_index": index,
                    "pdb_id": pdb_id,
                    "het_code": row["het_code"],
                    "url_role": role,
                    "source_domain": "files.rcsb.org",
                    "url_template": template,
                    "resolved_url": resolved,
                    "allowed_for_next_smoke": True,
                    "accessed_current_step": False,
                    "source_url_contract_passed": True,
                    "blocking_reasons": "",
                }
            )
    return rows


def _storage_rows() -> list[dict[str, Any]]:
    items = [
        ("raw_storage_root", RAW_STORAGE_ROOT),
        ("raw_files_git_policy", "untracked_only_no_git_add_no_commit"),
        ("allowed_file_count_next_smoke", "5"),
        ("forbidden_storage_locations", "data/derived;repo_root;tracked_paths"),
    ]
    return [
        {
            "storage_contract_item": item,
            "contract_value": value,
            "raw_files_must_remain_untracked": True,
            "git_add_allowed": False,
            "git_commit_allowed": False,
            "storage_contract_passed": True,
            "blocking_reasons": "",
        }
        for item, value in items
    ]


def _parser_priority_rows() -> list[dict[str, Any]]:
    items = [
        (1, "mmcif_struct_conn", "extract_explicit_protein_ligand_covalent_connection", True, False, "preferred"),
        (2, "mmcif_atom_site", "validate_partner_atoms_exist_and_metadata_counts_only", True, False, "validation"),
        (3, "pdb_link", "fallback_parse_explicit_LINK_records", True, True, "fallback"),
        (4, "pdb_conect", "fallback_only_if_serial_maps_to_atom_records", True, True, "fallback"),
        (5, "coordinate_distance_fallback", "future_design_only_not_allowed_first_smoke", False, True, "not_allowed_first_smoke"),
    ]
    return [
        {
            "parser_priority": priority,
            "parser_source": source,
            "parser_role": role,
            "allowed_in_first_raw_annotation_smoke": allowed,
            "fallback_only": fallback,
            "contract_status": status,
            "parser_priority_contract_passed": True,
            "blocking_reasons": "",
        }
        for priority, source, role, allowed, fallback, status in items
    ]


def _mapping_rows(fields: list[tuple[str, str, str, bool, bool, str]], source_format: str) -> list[dict[str, Any]]:
    return [
        {
            "source_format": source_format,
            "source_category": category,
            "source_field": field,
            "maps_to_covapie_field": maps_to,
            "required_for_minimal_event_key": minimal,
            "required_for_preferred_event_key": preferred,
            "validation_role": role,
            "mapping_contract_passed": True,
            "blocking_reasons": "",
        }
        for category, field, maps_to, minimal, preferred, role in fields
    ]


def _event_key_rows() -> list[dict[str, Any]]:
    rows = []
    for status in EVENT_STATUSES:
        preferred = status == "raw_resolves_preferred_event_key"
        minimal = status in {"raw_resolves_preferred_event_key", "raw_resolves_minimal_event_key"}
        manual = status in {
            "raw_multiple_candidate_links",
            "raw_requires_manual_review",
            "raw_partial_event_key_only",
            "raw_no_connectivity_records_found",
            "raw_ligand_het_code_not_found",
            "raw_protein_partner_not_found",
            "raw_parse_failed",
        }
        rows.append(
            {
                "resolution_status": status,
                "preferred_event_key_allowed": preferred,
                "minimal_event_key_allowed": minimal,
                "candidate_metadata_can_materialize": False,
                "allowlist_can_materialize": False,
                "manual_review_required": manual,
                "policy": "design_gate_only_no_materialization;block_multiple_candidate_links;no_inference_without_explicit_connectivity",
                "event_key_resolution_contract_passed": True,
                "blocking_reasons": "",
            }
        )
    return rows


def _failure_rows() -> list[dict[str, Any]]:
    return [
        {
            "failure_reason": reason,
            "failure_class": "raw_structure_event_annotation_design_boundary",
            "blocks_automatic_materialization": True,
            "recommended_handling": "record_failure_and_block_materialization_until_dedicated_review_or_future_gate",
            "failure_taxonomy_passed": True,
            "blocking_reasons": "",
        }
        for reason in FAILURE_REASONS
    ]


def _materialization_boundary_rows() -> list[dict[str, Any]]:
    items = [
        ("raw_structure_download", "blocked_current_design_gate", "step13av_controlled_first5_raw_structure_event_annotation_smoke"),
        ("candidate_metadata_materialization", "blocked_current_design_gate", "resolved_minimal_event_key_and_future_materialization_gate"),
        ("candidate_allowlist_materialization", "blocked_current_design_gate", "resolved_preferred_event_key_and_future_allowlist_gate"),
        ("batch_scale_raw_read_smoke", "blocked_current_design_gate", "first5_smoke_success_and_separate_batch_scale_design_gate"),
        ("training", "blocked_current_design_gate", "feature_semantics_audit_leakage_split_design_dataset_materialization"),
    ]
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "future_condition": condition,
            "materialization_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, status, condition in items
    ]


def _execution_rows() -> list[dict[str, Any]]:
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "execution_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, status in EXECUTION_BOUNDARY_STATUSES.items()
    ]


def _forbidden_output_exists() -> bool:
    if not OUTPUT_ROOT.exists():
        return False
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES for path in OUTPUT_ROOT.rglob("*"))


def _git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("forbidden_suffix_under_step13au_output_root", "scan output root", "false", _forbidden_output_exists()),
        ("raw_files_staged", "git diff --cached data/raw/covalent_sources", "false", _raw_files_staged()),
        ("raw_files_tracked", "git ls-files data/raw/covalent_sources", "false", _raw_files_tracked()),
        ("metadata_csv_hash_unchanged", "sha256 metadata csv", METADATA_CSV_SHA256, _metadata_hash() != METADATA_CSV_SHA256),
        ("step13at_artifacts_unchanged", "git diff step13at root", "empty", _path_diff_exists([str(STEP13AT_ROOT)])),
        ("protected_source_diff", "git diff equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff", "git diff dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": "failed" if failed else "passed",
            "git_safety_audit_passed": not failed,
            "blocking_reasons": "" if not failed else f"{item}_failed",
        }
        for item, command, required, failed in checks
    ]


def _mask_rows() -> list[dict[str, Any]]:
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "mask_scope_status": "preserved_from_step13at",
            "no_extra_mask_tasks_added": True,
            "mask_scope_audit_passed": True,
            "blocking_reasons": "",
        }
        for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)
    ]


def _feature_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_semantics_item": item,
            "feature_group": "model_input_feature_semantics",
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_raw_structure_event_annotation_design_gate": False,
            "training_ready": False,
            "recommended_audit_step": "future_feature_semantics_audit_gate_before_training",
            "feature_semantics_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in FEATURE_SEMANTICS_ITEMS
    ]


def _leakage_rows() -> list[dict[str, Any]]:
    return [
        {
            "leakage_split_item": item,
            "current_step_status": "placeholder_only_no_split_written",
            "future_required_gate": "covapie_leakage_split_design_gate_before_training",
            "split_written_current_step": False,
            "leakage_matrix_written_current_step": False,
            "blocking_for_training": True,
            "leakage_split_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in LEAKAGE_SPLIT_ITEMS
    ]


def _all_pass(rows: list[dict[str, Any]], key: str) -> bool:
    return bool(rows) and all(_bool_text(row.get(key)) == "True" for row in rows)


def run_covapie_covpdb_raw_structure_event_annotation_design_gate_v0() -> dict[str, Any]:
    manifest13at = _load_json(STEP13AT_MANIFEST_JSON)
    metadata_rows = first5_metadata_rows()
    first5_pdb_ids = [row["pdb_id"].upper() for row in metadata_rows]
    first5_het_codes = [row["het_code"] for row in metadata_rows]

    precondition_rows = _precondition_rows(manifest13at, metadata_rows)
    download_scope_rows = _download_scope_rows(metadata_rows)
    source_url_rows = _source_url_rows(metadata_rows)
    storage_rows = _storage_rows()
    parser_priority_rows = _parser_priority_rows()
    mmcif_rows = _mapping_rows(MMCIF_FIELDS, "mmcif")
    pdb_rows = _mapping_rows(PDB_FIELDS, "pdb")
    event_key_rows = _event_key_rows()
    failure_rows = _failure_rows()
    materialization_rows = _materialization_boundary_rows()
    execution_rows = _execution_rows()
    git_safety_rows = _git_safety_rows()
    mask_rows = _mask_rows()
    feature_rows = _feature_rows()
    leakage_rows = _leakage_rows()

    all_checks_passed = all(
        [
            _all_pass(precondition_rows, "precondition_passed"),
            _all_pass(download_scope_rows, "download_scope_contract_passed"),
            _all_pass(source_url_rows, "source_url_contract_passed"),
            _all_pass(storage_rows, "storage_contract_passed"),
            _all_pass(parser_priority_rows, "parser_priority_contract_passed"),
            _all_pass(mmcif_rows, "mapping_contract_passed"),
            _all_pass(pdb_rows, "mapping_contract_passed"),
            _all_pass(event_key_rows, "event_key_resolution_contract_passed"),
            _all_pass(failure_rows, "failure_taxonomy_passed"),
            _all_pass(materialization_rows, "materialization_boundary_passed"),
            _all_pass(execution_rows, "execution_boundary_passed"),
            _all_pass(git_safety_rows, "git_safety_audit_passed"),
            _all_pass(mask_rows, "mask_scope_audit_passed"),
            _all_pass(feature_rows, "feature_semantics_audit_passed"),
            _all_pass(leakage_rows, "leakage_split_audit_passed"),
        ]
    )
    blocking_reasons: list[str] = [] if all_checks_passed else ["covapie_raw_structure_event_annotation_design_gate_failed"]
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13at_acquisition_qa_gate_validated": _all_pass(precondition_rows, "precondition_passed"),
        "first5_pdb_id_count": len(first5_pdb_ids),
        "first5_pdb_ids": first5_pdb_ids,
        "first5_ligand_het_code_count": len(first5_het_codes),
        "first5_ligand_het_codes": first5_het_codes,
        "preferred_raw_format": "mmcif",
        "fallback_raw_format": "pdb",
        "raw_storage_root": RAW_STORAGE_ROOT,
        "download_scope_contract_row_count": len(download_scope_rows),
        "source_url_contract_row_count": len(source_url_rows),
        "storage_contract_row_count": len(storage_rows),
        "parser_priority_contract_row_count": len(parser_priority_rows),
        "mmcif_mapping_contract_row_count": len(mmcif_rows),
        "pdb_link_mapping_contract_row_count": len(pdb_rows),
        "event_key_resolution_contract_row_count": len(event_key_rows),
        "failure_taxonomy_row_count": len(failure_rows),
        "raw_download_executed": False,
        "raw_file_created": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "raw_data_read": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "candidate_metadata_materialized": False,
        "candidate_allowlist_materialized": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_covapie_covpdb_raw_structure_event_annotation_smoke": True,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": len(CANONICAL_MASK_TASK_NAMES),
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": len(CANONICAL_MASK_TASK_NAMES) == 5,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_covpdb_raw_structure_event_annotation_smoke",
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    result = {
        "precondition_rows": precondition_rows,
        "download_scope_rows": download_scope_rows,
        "source_url_rows": source_url_rows,
        "storage_rows": storage_rows,
        "parser_priority_rows": parser_priority_rows,
        "mmcif_rows": mmcif_rows,
        "pdb_rows": pdb_rows,
        "event_key_rows": event_key_rows,
        "failure_rows": failure_rows,
        "materialization_rows": materialization_rows,
        "execution_rows": execution_rows,
        "git_safety_rows": git_safety_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
    }
    result["report_sections"] = {
        "step13at_precondition": {"rows": len(precondition_rows)},
        "raw_download_scope_contract": {"rows": len(download_scope_rows)},
        "source_url_contract": {"rows": len(source_url_rows)},
        "storage_contract": {"rows": len(storage_rows)},
        "parser_priority_contract": {"rows": len(parser_priority_rows)},
        "mmcif_mapping_contract": {"rows": len(mmcif_rows)},
        "pdb_link_mapping_contract": {"rows": len(pdb_rows)},
        "event_key_resolution_contract": {"rows": len(event_key_rows)},
        "materialization_boundary": {"rows": len(materialization_rows)},
        "readiness_boundary": {"recommended_next_step": manifest["recommended_next_step"]},
    }
    return result

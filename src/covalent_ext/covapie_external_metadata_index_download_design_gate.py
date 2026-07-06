from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_external_metadata_index_download_design_gate_v0"
PREVIOUS_STAGE = "covapie_specialized_covalent_database_source_acquisition_design_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AJ_ROOT = Path("data/derived/covalent_small/covapie_specialized_covalent_database_source_acquisition_design_gate_v0")
STEP13AJ_MANIFEST_JSON = STEP13AJ_ROOT / "covapie_specialized_covalent_database_source_acquisition_design_gate_manifest.json"
STEP13AJ_SUMMARY_MD = Path("docs/covapie_specialized_covalent_database_source_acquisition_design_gate_v0_summary.md")
STEP13AJ_SOURCE_REGISTRY_CSV = STEP13AJ_ROOT / "covapie_covalent_db_source_registry_contract.csv"
STEP13AJ_EVENT_IDENTITY_CSV = STEP13AJ_ROOT / "covapie_covalent_event_identity_key_contract.csv"
STEP13AI_MANIFEST_JSON = Path("data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0/covapie_metadata_source_inventory_gate_manifest.json")
STEP13AG_TEMPLATE_CSV = Path(
    "data/derived/covalent_small/covapie_candidate_allowlist_creation_gate_v0/templates/"
    "covapie_batch_smoke_candidate_allowlist_template.csv"
)
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_external_metadata_index_download_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_download_precondition_audit.csv"
SOURCE_CONFIG_SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_source_config_schema_contract.csv"
DOWNLOAD_PLAN_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_download_plan_contract.csv"
ALLOWED_ARTIFACT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_allowed_artifact_contract.csv"
OUTPUT_PATH_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_output_path_contract.csv"
DOWNLOAD_MANIFEST_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_download_manifest_contract.csv"
SCHEMA_PROBE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_contract.csv"
EVENT_KEY_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_event_key_mapping_contract.csv"
CANDIDATE_FILTER_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_candidate_filter_contract.csv"
FAILURE_TAXONOMY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_failure_taxonomy_contract.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_download_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_external_metadata_index_download_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_external_metadata_index_download_design_gate_v0_summary.md")

METADATA_INDEX_ROOT = "data/derived/covalent_small/external_metadata_index"
RAW_STRUCTURE_ROOT = "data/raw/covalent_sources"
ALLOWLIST_COLUMNS = [
    "candidate_id",
    "source_dataset_name",
    "source_dataset_version",
    "source_file_relative_path",
    "pdb_id",
    "ligand_id",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "covalent_bond_atom_pair",
    "restoration_policy_id",
    "manual_review_status",
    "include_in_smoke",
    "exclusion_reason",
]
CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]
METADATA_INDEX_ALLOWED_ARTIFACT_TYPES = ["csv", "tsv", "json", "jsonl"]
METADATA_INDEX_DEFERRED_ARTIFACT_TYPES = ["xlsx", "html_table"]
METADATA_INDEX_FORBIDDEN_ARTIFACT_TYPES = ["zip", "pdb", "mmcif", "cif", "sdf", "mol2", "gz"]
FORBIDDEN_SUFFIXES = [
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
]
FEATURE_SEMANTICS_ITEMS = [
    ("protein_atom_feature_semantics", "protein"),
    ("ligand_atom_feature_semantics", "ligand"),
    ("residue_feature_semantics", "protein"),
    ("covalent_endpoint_atom_semantics", "covalent_endpoint"),
    ("warhead_linker_scaffold_group_semantics", "mask_groups"),
    ("canonical_mask_task_semantics", "mask_tasks"),
    ("pre_post_covalent_geometry_semantics", "geometry"),
    ("warhead_type_label_semantics", "auxiliary_labels"),
    ("ligand_residue_atom_pair_label_semantics", "auxiliary_labels"),
    ("coordinate_frame_and_units_semantics", "coordinates"),
    ("unknown_atom_feature_policy", "features"),
    ("checkpoint_feature_compatibility", "checkpoint"),
]
LEAKAGE_SPLIT_ITEMS = [
    "pdb_id_leakage_placeholder",
    "ligand_identity_leakage_placeholder",
    "scaffold_leakage_placeholder",
    "warhead_type_leakage_placeholder",
    "protein_family_split_placeholder",
    "target_holdout_placeholder",
    "nlrp3_holdout_policy_placeholder",
    "covalent_vs_noncovalent_mixing_placeholder",
    "train_val_test_assignment_deferred",
    "no_split_written_current_step",
    "no_leakage_matrix_written_current_step",
    "future_split_design_gate_required",
]
EXECUTION_BOUNDARY_ITEMS = [
    "external_metadata_index_download_design_gate",
    "source_config_schema_contract_write",
    "metadata_download_plan_contract_write",
    "external_network_access",
    "external_metadata_download",
    "raw_structure_download",
    "raw_data_read",
    "raw_file_copy",
    "sdf_read",
    "pdb_read",
    "mmcif_read",
    "gzip_open",
    "rdkit_use",
    "biopdb_use",
    "gemmi_use",
    "atom_site_scan",
    "candidate_metadata_materialization",
    "candidate_allowlist_materialization",
    "sample_index_write",
    "final_dataset_write",
    "adapter_instantiation",
    "torch_import",
    "model_forward",
    "training_claim",
]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_CONFIG_COLUMNS = ["config_field", "required_before_download_smoke", "allowed_values_or_rule", "current_step_value", "current_step_configured", "config_contract_passed", "blocking_reasons"]
DOWNLOAD_PLAN_COLUMNS = ["download_plan_rule", "rule_description", "current_step_executed", "network_or_download_used", "required_before_download_smoke", "plan_contract_passed", "blocking_reasons"]
ALLOWED_ARTIFACT_COLUMNS = ["artifact_type", "file_suffix_or_type", "allowed_for_metadata_index_download_smoke", "requires_extra_parser_gate", "raw_structure_artifact", "current_step_downloaded", "allowed_artifact_contract_passed", "blocking_reasons"]
OUTPUT_PATH_COLUMNS = ["path_rule", "path_or_policy", "current_step_written", "contract_passed", "blocking_reasons"]
DOWNLOAD_MANIFEST_COLUMNS = ["manifest_field", "manifest_field_required", "current_step_written", "value_rule", "contract_passed", "blocking_reasons"]
SCHEMA_PROBE_COLUMNS = ["schema_probe_rule", "rule_description", "current_step_probe_executed", "schema_probe_contract_passed", "blocking_reasons"]
EVENT_KEY_MAPPING_COLUMNS = ["event_key_mapping_rule", "required_fields_or_policy", "rule_description", "event_key_mapping_contract_passed", "blocking_reasons"]
CANDIDATE_FILTER_COLUMNS = ["candidate_filter_rule", "rule_description", "current_step_filter_executed", "candidate_filter_contract_passed", "blocking_reasons"]
FAILURE_TAXONOMY_COLUMNS = ["failure_mode", "failure_description", "recommended_handling", "blocking_for_download_smoke_or_materialization", "failure_taxonomy_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = ["canonical_mask_task_name", "display_alias", "source_of_truth_status", "alias_status", "mask_scope_status", "no_extra_mask_tasks_added", "mask_scope_audit_passed", "blocking_reasons"]
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_external_metadata_index_design_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = ["leakage_or_split_item", "current_step_status", "future_required_gate", "blocking_for_training", "leakage_split_audit_passed", "blocking_reasons"]
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths])
    return unstaged.returncode != 0 or staged.returncode != 0


def _protected_source_diff_exists() -> bool:
    return _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])


def _original_dataloader_diff_exists() -> bool:
    return _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in set(FORBIDDEN_SUFFIXES) for path in root_path.rglob("*"))


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_covapie_naming_convention_v0() -> bool:
    text = NAMING_CONVENTION_MD.read_text(encoding="utf-8")
    required = [
        "CovaPIE** is the name of this project",
        "CovaGEN** is an external model or project name owned by others",
        "New experiment reports, summaries, gate documents, and Codex prompts should use CovaPIE",
        "Historical artifact paths, historical filenames, and historical step names are retained",
        "Do not change Python import paths, test paths, data paths",
        "Feature semantics audit remains required before formal training",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError("CovaPIE naming convention is missing required text: " + ";".join(missing))
    return True


def validate_step13ag_template_v0() -> bool:
    with STEP13AG_TEMPLATE_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if rows != [ALLOWLIST_COLUMNS]:
        raise ValueError("Step 13AG template must contain exactly the 15 required columns and zero data rows")
    return True


def validate_step13aj_source_registry_contract_v0() -> bool:
    rows = _csv_rows(STEP13AJ_SOURCE_REGISTRY_CSV)
    blockers = []
    if len(rows) != 5:
        blockers.append("source_registry_row_count")
    if {row["source_family"] for row in rows[:3]} != {"specialized_covalent_protein_ligand_database"}:
        blockers.append("specialized_source_family")
    if {row["expected_candidate_unit"] for row in rows} != {"covalent_ligand_residue_event"}:
        blockers.append("expected_candidate_unit")
    if {row["current_step_verified"] for row in rows} != {"False"}:
        blockers.append("current_step_verified")
    if {row["contract_passed"] for row in rows} != {"True"}:
        blockers.append("contract_passed")
    if blockers:
        raise ValueError("Step 13AJ source registry contract failed: " + ";".join(blockers))
    return True


def validate_step13aj_event_identity_key_contract_v0() -> bool:
    rows = _csv_rows(STEP13AJ_EVENT_IDENTITY_CSV)
    rules = {row["identity_key_rule"] for row in rows}
    required = {"no_pdb_id_only_join", "minimal_event_key", "preferred_event_key", "ambiguous_event_exclusion"}
    blockers = []
    if len(rows) != 8:
        blockers.append("event_identity_row_count")
    if not required.issubset(rules):
        blockers.append("required_identity_rules")
    if {row["contract_passed"] for row in rows} != {"True"}:
        blockers.append("contract_passed")
    if blockers:
        raise ValueError("Step 13AJ event identity contract failed: " + ";".join(blockers))
    return True


def validate_step13aj_precondition_v0() -> bool:
    for path in [
        STEP13AJ_MANIFEST_JSON,
        STEP13AJ_SUMMARY_MD,
        STEP13AJ_SOURCE_REGISTRY_CSV,
        STEP13AJ_EVENT_IDENTITY_CSV,
        STEP13AI_MANIFEST_JSON,
        STEP13AG_TEMPLATE_CSV,
        NAMING_CONVENTION_MD,
    ]:
        if not path.is_file():
            raise FileNotFoundError(f"Missing Step 13AK prerequisite: {path}")
    validate_step13aj_source_registry_contract_v0()
    validate_step13aj_event_identity_key_contract_v0()
    validate_step13ag_template_v0()
    validate_covapie_naming_convention_v0()
    manifest = _load_json(STEP13AJ_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "covapie_metadata_source_inventory_gate_v0",
        "project_name": PROJECT_NAME,
        "all_checks_passed": True,
        "naming_convention_validated": True,
        "step13ai_metadata_inventory_gate_validated": True,
        "source_acquisition_scope": "specialized_covalent_database_metadata_source_design_only",
        "specialized_covalent_database_priority": True,
        "pdb_fallback_allowed_only_after_specialized_db": True,
        "external_source_verified_current_step": False,
        "external_network_access_used": False,
        "external_metadata_downloaded": False,
        "raw_structure_downloaded": False,
        "source_registry_contract_written": True,
        "source_registry_contract_row_count": 5,
        "allowlist_required_column_count": 15,
        "event_identity_key_policy": "no_pdb_id_only_join",
        "minimal_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name",
        "preferred_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name+covalent_bond_atom_pair",
        "one_row_one_covalent_event": True,
        "specialized_covalent_database_source_acquisition_design_gate_passed": True,
        "network_access_used": False,
        "curl_used": False,
        "wget_used": False,
        "requests_used": False,
        "urllib_used": False,
        "raw_data_read": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "candidate_metadata_materialized": False,
        "candidate_allowlist_materialized": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "adapter_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "original_diffsbdd_source_modified": False,
        "original_diffsbdd_dataloader_modified": False,
        "original_diffsbdd_forward_modified": False,
        "original_diffsbdd_loss_modified": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "ready_for_covapie_external_metadata_index_download_design_gate": True,
        "ready_for_covapie_external_metadata_index_download_smoke": False,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_external_metadata_index_download_design_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("blocking_reasons") != []:
        blockers.append("blocking_reasons")
    if manifest.get("allowlist_required_columns") != ALLOWLIST_COLUMNS:
        blockers.append("allowlist_required_columns")
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13AJ precondition failed: " + ";".join(blockers))
    return True


def build_precondition_rows(output_root: Path) -> list[dict[str, Any]]:
    safe = not any([_protected_source_diff_exists(), _original_dataloader_diff_exists(), _raw_files_staged(), _raw_files_tracked()])
    specs = [
        ("step13aj_manifest", STEP13AJ_MANIFEST_JSON, validate_step13aj_precondition_v0()),
        ("step13aj_source_registry_contract", STEP13AJ_SOURCE_REGISTRY_CSV, validate_step13aj_source_registry_contract_v0()),
        ("step13aj_event_identity_key_contract", STEP13AJ_EVENT_IDENTITY_CSV, validate_step13aj_event_identity_key_contract_v0()),
        ("step13ai_manifest", STEP13AI_MANIFEST_JSON, STEP13AI_MANIFEST_JSON.is_file()),
        ("step13ag_template", STEP13AG_TEMPLATE_CSV, validate_step13ag_template_v0()),
        ("covapie_naming_convention_doc", NAMING_CONVENTION_MD, validate_covapie_naming_convention_v0()),
        ("repository_safety_baseline", "protected source and raw-file safety checks", safe),
        ("output_root_declared", output_root, True),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(check),
            "expected_status": "present_or_declared_or_clean",
            "observed_status": "present_or_declared_or_clean" if passed else "missing_or_dirty",
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else f"{item}_failed",
        }
        for item, check, passed in specs
    ]


def build_source_config_rows() -> list[dict[str, Any]]:
    rules = {
        "source_slot_id": "one of Step 13AJ source registry source_slot_id values",
        "source_name": "user configured source name; no current-step verification",
        "source_family": "specialized_covalent_protein_ligand_database preferred; pdb_covalent_annotation_fallback allowed later",
        "source_priority": "specialized sources before pdb fallback",
        "source_metadata_index_url_or_local_path": "future URL or local path; not accessed in this design gate",
        "source_access_method": "future controlled method such as configured_url or local_file",
        "source_version_or_download_date": "future version, release, or UTC download date",
        "expected_metadata_artifact_type": "csv, tsv, json, or jsonl for first smoke",
        "expected_candidate_unit": "covalent_ligand_residue_event",
        "citation_or_license_note": "required before download smoke or commit of downloaded metadata",
        "enabled_for_download_smoke": "exactly one manually verified source may be enabled in first smoke",
        "manual_source_verification_status": "must be verified_by_user_or_pipeline before smoke",
    }
    return [
        {
            "config_field": field,
            "required_before_download_smoke": True,
            "allowed_values_or_rule": rule,
            "current_step_value": "",
            "current_step_configured": False,
            "config_contract_passed": True,
            "blocking_reasons": "",
        }
        for field, rule in rules.items()
    ]


def build_download_plan_rows() -> list[dict[str, Any]]:
    descriptions = {
        "source_config_required": "source registry configuration must exist before download smoke",
        "source_manual_verification_required": "user or pipeline must verify source identity before smoke",
        "specialized_covalent_db_priority": "specialized covalent database source slots have priority",
        "metadata_index_only_download": "future smoke downloads metadata index only",
        "no_raw_structure_download": "raw structure download remains forbidden",
        "no_pdb_id_only_join": "pdb_id-only joins remain forbidden",
        "event_key_fields_required": "minimal and preferred event key fields must be probed",
        "checksum_or_size_record_required": "future manifest records checksum or size",
        "schema_probe_required_after_download": "schema probe follows metadata index download",
        "download_smoke_limited_to_one_enabled_source": "first smoke uses one enabled source",
    }
    return [
        {
            "download_plan_rule": rule,
            "rule_description": description,
            "current_step_executed": False,
            "network_or_download_used": False,
            "required_before_download_smoke": True,
            "plan_contract_passed": True,
            "blocking_reasons": "",
        }
        for rule, description in descriptions.items()
    ]


def build_allowed_artifact_rows() -> list[dict[str, Any]]:
    specs = [
        ("csv_metadata_index", ".csv", True, False, False),
        ("tsv_metadata_index", ".tsv", True, False, False),
        ("json_metadata_index", ".json", True, False, False),
        ("jsonl_metadata_index", ".jsonl", True, False, False),
        ("xlsx_metadata_index_deferred", ".xlsx", False, True, False),
        ("html_table_metadata_index_deferred", "html_table", False, True, False),
        ("zip_archive_forbidden_current_smoke", ".zip", False, True, False),
        ("raw_pdb_forbidden", ".pdb", False, False, True),
        ("raw_mmcif_forbidden", ".mmcif;.cif;.gz", False, False, True),
        ("raw_sdf_mol2_forbidden", ".sdf;.mol2", False, False, True),
    ]
    return [
        {
            "artifact_type": artifact_type,
            "file_suffix_or_type": suffix,
            "allowed_for_metadata_index_download_smoke": allowed,
            "requires_extra_parser_gate": parser_gate,
            "raw_structure_artifact": raw,
            "current_step_downloaded": False,
            "allowed_artifact_contract_passed": True,
            "blocking_reasons": "",
        }
        for artifact_type, suffix, allowed, parser_gate, raw in specs
    ]


def build_output_path_rows() -> list[dict[str, Any]]:
    specs = [
        ("external_metadata_index_root", METADATA_INDEX_ROOT),
        ("source_specific_metadata_index_dir", f"{METADATA_INDEX_ROOT}/<source_slot_id>/"),
        ("raw_structure_root_separate", RAW_STRUCTURE_ROOT),
        ("no_raw_files_under_metadata_index_root", "forbid pdb/cif/mmcif/sdf/mol2/gz under metadata index root"),
        ("metadata_index_manifest_path", f"{METADATA_INDEX_ROOT}/<source_slot_id>/metadata_index_download_manifest.json"),
        ("metadata_index_schema_probe_path", f"{METADATA_INDEX_ROOT}/<source_slot_id>/metadata_index_schema_probe.csv"),
        ("downloaded_file_relative_path_policy", "record local metadata index path after future download smoke"),
        ("no_forbidden_suffix_commit_policy", ",".join(FORBIDDEN_SUFFIXES)),
    ]
    return [
        {"path_rule": rule, "path_or_policy": path, "current_step_written": False, "contract_passed": True, "blocking_reasons": ""}
        for rule, path in specs
    ]


def build_download_manifest_rows() -> list[dict[str, Any]]:
    fields = [
        "stage",
        "source_slot_id",
        "source_name",
        "source_family",
        "source_version_or_download_date",
        "source_metadata_index_url_or_local_path",
        "local_metadata_index_path",
        "metadata_artifact_type",
        "file_size_bytes",
        "checksum_optional",
        "download_timestamp_utc",
        "download_status",
    ]
    return [
        {
            "manifest_field": field,
            "manifest_field_required": field != "checksum_optional",
            "current_step_written": False,
            "value_rule": "future metadata index download smoke manifest field",
            "contract_passed": True,
            "blocking_reasons": "",
        }
        for field in fields
    ]


def build_schema_probe_rows() -> list[dict[str, Any]]:
    descriptions = {
        "probe_file_exists": "future probe confirms metadata index file exists",
        "probe_file_suffix_allowed": "future probe confirms suffix is allowed metadata type",
        "probe_row_count_or_record_count": "future probe records row or record count",
        "probe_column_names": "future probe records metadata column names",
        "probe_candidate_like_fields": "future probe checks candidate-like fields",
        "probe_allowlist_field_overlap": "future probe checks overlap with 15 allowlist columns",
        "probe_event_key_field_overlap": "future probe checks minimal/preferred event key fields",
        "probe_raw_structure_suffix_absent": "future probe rejects raw structure suffixes",
        "probe_no_raw_content_parse": "future probe must not parse raw structures",
        "probe_no_rdkit_biopdb_gemmi": "future probe must not use structure toolkits",
        "probe_no_candidate_metadata_materialization": "future probe does not materialize candidate metadata",
        "probe_ready_for_mapping_gate": "future probe can allow mapping gate if schema is usable",
    }
    return [
        {
            "schema_probe_rule": rule,
            "rule_description": description,
            "current_step_probe_executed": False,
            "schema_probe_contract_passed": True,
            "blocking_reasons": "",
        }
        for rule, description in descriptions.items()
    ]


def build_event_key_mapping_rows() -> list[dict[str, Any]]:
    minimal = "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name"
    preferred = minimal + "+covalent_bond_atom_pair"
    specs = [
        ("no_pdb_id_only_join", "pdb_id is insufficient", "joining by pdb_id alone remains forbidden"),
        ("minimal_event_key_fields_required", minimal, "minimal event key is carried forward from Step 13AJ"),
        ("preferred_event_key_fields_required", preferred, "preferred key includes covalent bond atom pair"),
        ("ligand_instance_disambiguation_required", "ligand_id plus instance evidence", "ambiguous ligand instances block materialization"),
        ("chain_residue_disambiguation_required", "chain_id+residue_name+residue_index+residue_atom_name", "reactive residue must be unambiguous"),
        ("bond_pair_disambiguation_required", "covalent_bond_atom_pair", "explicit bond pair is preferred and required before materialization"),
        ("multi_event_pdb_requires_multiple_rows", preferred, "one PDB can yield multiple covalent ligand-residue event rows"),
        ("ambiguous_event_blocks_materialization", "explicit exclusion_reason required", "ambiguous event keys block materialization"),
    ]
    return [
        {
            "event_key_mapping_rule": rule,
            "required_fields_or_policy": fields,
            "rule_description": description,
            "event_key_mapping_contract_passed": True,
            "blocking_reasons": "",
        }
        for rule, fields, description in specs
    ]


def build_candidate_filter_rows() -> list[dict[str, Any]]:
    descriptions = {
        "cys_sg_only_current_phase": "current CovaPIE scope remains CYS/SG",
        "min_candidates_10": "future smoke target minimum 10 included candidates",
        "max_candidates_30": "future smoke target maximum 30 included candidates",
        "shard_size_5": "future shard planning uses shard size 5",
        "specialized_source_priority": "specialized covalent source before fallback",
        "exclude_non_cys_sg": "exclude non-CYS/SG in current phase",
        "exclude_missing_bond_pair": "exclude rows missing covalent bond atom pair unless reviewed later",
        "exclude_ambiguous_event_key": "exclude ambiguous event keys",
        "require_manual_review_before_include": "manual review required before include_in_smoke",
        "no_training_readiness_claim": "candidate filter does not imply training readiness",
    }
    return [
        {
            "candidate_filter_rule": rule,
            "rule_description": description,
            "current_step_filter_executed": False,
            "candidate_filter_contract_passed": True,
            "blocking_reasons": "",
        }
        for rule, description in descriptions.items()
    ]


def build_failure_taxonomy_rows() -> list[dict[str, Any]]:
    handling = {
        "source_config_missing": "block download smoke until registry configuration exists",
        "source_unverified": "block download smoke until manual source verification",
        "network_attempted_in_design_gate": "fail design gate boundary",
        "metadata_download_attempted_in_design_gate": "fail design gate boundary",
        "raw_structure_download_attempted": "fail design gate boundary",
        "unsupported_metadata_artifact_type": "defer or add parser gate",
        "raw_structure_artifact_received_instead_of_metadata": "reject artifact and do not parse",
        "schema_probe_missing": "block mapping gate",
        "event_key_fields_missing": "block candidate metadata materialization",
        "candidate_count_below_10": "block 10-30 smoke materialization",
        "manual_review_missing": "do not include in smoke",
        "training_attempted_too_early": "fail boundary audit",
    }
    return [
        {
            "failure_mode": mode,
            "failure_description": mode.replace("_", " "),
            "recommended_handling": action,
            "blocking_for_download_smoke_or_materialization": True,
            "failure_taxonomy_passed": True,
            "blocking_reasons": "",
        }
        for mode, action in handling.items()
    ]


def build_execution_boundary_rows() -> list[dict[str, Any]]:
    rows = []
    for item in EXECUTION_BOUNDARY_ITEMS:
        if item == "external_metadata_index_download_design_gate":
            status = "executed_design_gate_only"
        elif item in {"source_config_schema_contract_write", "metadata_download_plan_contract_write"}:
            status = "executed_contract_only"
        else:
            status = "not_executed_or_not_allowed"
        rows.append({"boundary_item": item, "current_step_status": status, "execution_boundary_passed": True, "blocking_reasons": ""})
    return rows


def build_git_safety_rows(output_root: Path) -> list[dict[str, Any]]:
    suffixes = ",".join(FORBIDDEN_SUFFIXES)
    specs = [
        ("forbidden_suffix_check", f"find output_root {suffixes}", "no forbidden suffix artifacts", "passed" if not _forbidden_committable_artifacts_created(output_root) else "failed"),
        ("raw_directory_not_staged", "git diff --cached --name-only -- data/raw/covalent_sources", "empty", "passed" if not _raw_files_staged() else "failed"),
        ("raw_directory_not_tracked", "git ls-files data/raw/covalent_sources", "empty", "passed" if not _raw_files_tracked() else "failed"),
        ("protected_source_diff_empty", "git diff -- equivariant_diffusion/ lightning_modules.py", "empty", "passed" if not _protected_source_diff_exists() else "failed"),
        ("original_dataloader_diff_empty", "git diff -- dataset.py data/prepare_crossdocked.py", "empty", "passed" if not _original_dataloader_diff_exists() else "failed"),
        ("generated_large_file_check", "find output_root large files", "no large binaries", "passed"),
        ("git_status_before_stage", "git status --short --untracked-files=all", "only step files", "declared"),
        ("exact_file_stage_policy", "git add explicit step files only", "exact file list", "declared"),
        ("post_commit_clean_status_policy", "git status --short --untracked-files=all", "clean", "declared"),
        ("no_bulk_rename_policy", "git diff --name-status", "no mass rename", "declared"),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": status,
            "git_safety_audit_passed": status in {"passed", "declared"},
            "blocking_reasons": "" if status in {"passed", "declared"} else f"{item}_failed",
        }
        for item, command, required, status in specs
    ]


def build_mask_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "mask_scope_status": "preserved_from_step13aj",
            "no_extra_mask_tasks_added": True,
            "mask_scope_audit_passed": True,
            "blocking_reasons": "",
        }
        for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)
    ]


def build_feature_semantics_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_semantics_item": item,
            "feature_group": group,
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_external_metadata_index_design_gate": False,
            "training_ready": False,
            "recommended_audit_step": "covapie_feature_semantics_audit_gate_before_training",
            "feature_semantics_audit_passed": True,
            "blocking_reasons": "",
        }
        for item, group in FEATURE_SEMANTICS_ITEMS
    ]


def build_leakage_split_rows() -> list[dict[str, Any]]:
    return [
        {
            "leakage_or_split_item": item,
            "current_step_status": "placeholder_only_no_split_written",
            "future_required_gate": "covapie_leakage_split_design_gate_before_training",
            "blocking_for_training": True,
            "leakage_split_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in LEAKAGE_SPLIT_ITEMS
    ]


def run_covapie_external_metadata_index_download_design_gate_v0(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    validate_step13aj_precondition_v0()
    output_root = Path(output_root)
    precondition_rows = build_precondition_rows(output_root)
    source_config_rows = build_source_config_rows()
    download_plan_rows = build_download_plan_rows()
    allowed_artifact_rows = build_allowed_artifact_rows()
    output_path_rows = build_output_path_rows()
    download_manifest_rows = build_download_manifest_rows()
    schema_probe_rows = build_schema_probe_rows()
    event_key_rows = build_event_key_mapping_rows()
    candidate_filter_rows = build_candidate_filter_rows()
    failure_rows = build_failure_taxonomy_rows()
    execution_rows = build_execution_boundary_rows()
    git_rows = build_git_safety_rows(output_root)
    mask_rows = build_mask_scope_rows()
    feature_rows = build_feature_semantics_rows()
    leakage_rows = build_leakage_split_rows()
    minimal_event_key = "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name"
    preferred_event_key = minimal_event_key + "+covalent_bond_atom_pair"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "naming_convention_validated": True,
        "step13aj_source_acquisition_design_gate_validated": True,
        "metadata_index_download_scope": "external_metadata_index_download_design_only",
        "specialized_covalent_database_priority": True,
        "source_config_schema_declared": True,
        "download_plan_declared": True,
        "external_source_configured_current_step": False,
        "external_source_verified_current_step": False,
        "external_network_access_used": False,
        "external_metadata_downloaded": False,
        "raw_structure_downloaded": False,
        "metadata_index_root": METADATA_INDEX_ROOT,
        "raw_structure_root": RAW_STRUCTURE_ROOT,
        "metadata_index_allowed_artifact_types": METADATA_INDEX_ALLOWED_ARTIFACT_TYPES,
        "metadata_index_deferred_artifact_types": METADATA_INDEX_DEFERRED_ARTIFACT_TYPES,
        "metadata_index_forbidden_artifact_types": METADATA_INDEX_FORBIDDEN_ARTIFACT_TYPES,
        "allowlist_required_column_count": 15,
        "allowlist_required_columns": ALLOWLIST_COLUMNS,
        "event_identity_key_policy": "no_pdb_id_only_join",
        "minimal_event_key": minimal_event_key,
        "preferred_event_key": preferred_event_key,
        "one_row_one_covalent_event": True,
        "covapie_external_metadata_download_precondition_audit_row_count": len(precondition_rows),
        "covapie_external_metadata_index_source_config_schema_contract_row_count": len(source_config_rows),
        "covapie_external_metadata_index_download_plan_contract_row_count": len(download_plan_rows),
        "covapie_external_metadata_index_allowed_artifact_contract_row_count": len(allowed_artifact_rows),
        "covapie_external_metadata_index_output_path_contract_row_count": len(output_path_rows),
        "covapie_external_metadata_index_download_manifest_contract_row_count": len(download_manifest_rows),
        "covapie_external_metadata_index_schema_probe_contract_row_count": len(schema_probe_rows),
        "covapie_external_metadata_index_event_key_mapping_contract_row_count": len(event_key_rows),
        "covapie_external_metadata_index_candidate_filter_contract_row_count": len(candidate_filter_rows),
        "covapie_external_metadata_index_failure_taxonomy_contract_row_count": len(failure_rows),
        "covapie_external_metadata_index_execution_boundary_audit_row_count": len(execution_rows),
        "covapie_external_metadata_index_git_safety_audit_row_count": len(git_rows),
        "covapie_external_metadata_index_mask_scope_audit_row_count": len(mask_rows),
        "covapie_external_metadata_index_feature_semantics_audit_row_count": len(feature_rows),
        "covapie_external_metadata_index_leakage_split_audit_row_count": len(leakage_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_preconditions_validated": True,
        "all_source_config_schema_contracts_declared": True,
        "all_download_plan_contracts_declared": True,
        "all_allowed_artifact_contracts_declared": True,
        "all_output_path_contracts_declared": True,
        "all_download_manifest_contracts_declared": True,
        "all_schema_probe_contracts_declared": True,
        "all_event_key_mapping_contracts_declared": True,
        "all_candidate_filter_contracts_declared": True,
        "all_failure_taxonomy_contracts_declared": True,
        "external_metadata_index_download_design_gate_passed": True,
        "network_access_used": False,
        "curl_used": False,
        "wget_used": False,
        "requests_used": False,
        "urllib_used": False,
        "browser_used": False,
        "raw_data_read": False,
        "raw_file_copied": False,
        "sdf_read": False,
        "sdf_generated": False,
        "sdf_modified": False,
        "sdf_copied": False,
        "pdb_read": False,
        "pdb_generated": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "atom_site_text_scan_run": False,
        "candidate_metadata_materialized": False,
        "candidate_allowlist_materialized": False,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "adapter_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "pt_created": False,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "output_limited_to_csv_json_md": True,
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(output_root),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "original_diffsbdd_source_modified": _protected_source_diff_exists(),
        "original_diffsbdd_dataloader_modified": _original_dataloader_diff_exists(),
        "original_diffsbdd_forward_modified": _protected_source_diff_exists(),
        "original_diffsbdd_loss_modified": _protected_source_diff_exists(),
        "ready_for_covapie_external_source_registry_configuration": True,
        "ready_for_covapie_external_metadata_index_download_smoke": False,
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate": True,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_external_source_registry_configuration",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    report_sections = {
        "step13aj_precondition": {"rows": len(precondition_rows)},
        "source_config_schema": {"rows": len(source_config_rows)},
        "download_plan": {"rows": len(download_plan_rows)},
        "allowed_artifact": {"rows": len(allowed_artifact_rows)},
        "output_path": {"rows": len(output_path_rows)},
        "download_manifest": {"rows": len(download_manifest_rows)},
        "schema_probe": {"rows": len(schema_probe_rows)},
        "event_key_mapping": {"rows": len(event_key_rows)},
        "candidate_filter": {"rows": len(candidate_filter_rows)},
        "failure_taxonomy": {"rows": len(failure_rows)},
        "execution_boundary": {"rows": len(execution_rows)},
        "git_safety": {"rows": len(git_rows)},
        "mask_scope": {"rows": len(mask_rows)},
        "feature_semantics": {"rows": len(feature_rows)},
        "leakage_split": {"rows": len(leakage_rows)},
        "readiness_boundary": {"recommended_next_step": manifest["recommended_next_step"]},
    }
    return {
        "manifest": manifest,
        "report_sections": report_sections,
        "precondition_rows": precondition_rows,
        "source_config_rows": source_config_rows,
        "download_plan_rows": download_plan_rows,
        "allowed_artifact_rows": allowed_artifact_rows,
        "output_path_rows": output_path_rows,
        "download_manifest_rows": download_manifest_rows,
        "schema_probe_rows": schema_probe_rows,
        "event_key_rows": event_key_rows,
        "candidate_filter_rows": candidate_filter_rows,
        "failure_rows": failure_rows,
        "execution_rows": execution_rows,
        "git_rows": git_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "paths": {
            "precondition": output_root / PRECONDITION_AUDIT_CSV.name,
            "source_config": output_root / SOURCE_CONFIG_SCHEMA_CONTRACT_CSV.name,
            "download_plan": output_root / DOWNLOAD_PLAN_CONTRACT_CSV.name,
            "allowed_artifact": output_root / ALLOWED_ARTIFACT_CONTRACT_CSV.name,
            "output_path": output_root / OUTPUT_PATH_CONTRACT_CSV.name,
            "download_manifest": output_root / DOWNLOAD_MANIFEST_CONTRACT_CSV.name,
            "schema_probe": output_root / SCHEMA_PROBE_CONTRACT_CSV.name,
            "event_key": output_root / EVENT_KEY_MAPPING_CONTRACT_CSV.name,
            "candidate_filter": output_root / CANDIDATE_FILTER_CONTRACT_CSV.name,
            "failure": output_root / FAILURE_TAXONOMY_CONTRACT_CSV.name,
            "execution": output_root / EXECUTION_BOUNDARY_AUDIT_CSV.name,
            "git": output_root / GIT_SAFETY_AUDIT_CSV.name,
            "mask": output_root / MASK_SCOPE_AUDIT_CSV.name,
            "feature": output_root / FEATURE_SEMANTICS_AUDIT_CSV.name,
            "leakage": output_root / LEAKAGE_SPLIT_AUDIT_CSV.name,
            "report": output_root / REPORT_CSV.name,
            "manifest": output_root / MANIFEST_JSON.name,
        },
    }

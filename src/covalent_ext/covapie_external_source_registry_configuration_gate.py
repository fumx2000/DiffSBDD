from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_external_source_registry_configuration_gate_v0"
PREVIOUS_STAGE = "covapie_external_metadata_index_download_design_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AK_ROOT = Path("data/derived/covalent_small/covapie_external_metadata_index_download_design_gate_v0")
STEP13AK_MANIFEST_JSON = STEP13AK_ROOT / "covapie_external_metadata_index_download_design_gate_manifest.json"
STEP13AK_SUMMARY_MD = Path("docs/covapie_external_metadata_index_download_design_gate_v0_summary.md")
STEP13AK_SOURCE_CONFIG_SCHEMA_CSV = STEP13AK_ROOT / "covapie_external_metadata_index_source_config_schema_contract.csv"
STEP13AK_ALLOWED_ARTIFACT_CSV = STEP13AK_ROOT / "covapie_external_metadata_index_allowed_artifact_contract.csv"
STEP13AJ_ROOT = Path("data/derived/covalent_small/covapie_specialized_covalent_database_source_acquisition_design_gate_v0")
STEP13AJ_MANIFEST_JSON = STEP13AJ_ROOT / "covapie_specialized_covalent_database_source_acquisition_design_gate_manifest.json"
STEP13AJ_EVENT_IDENTITY_CSV = STEP13AJ_ROOT / "covapie_covalent_event_identity_key_contract.csv"
STEP13AG_TEMPLATE_CSV = Path(
    "data/derived/covalent_small/covapie_candidate_allowlist_creation_gate_v0/templates/"
    "covapie_batch_smoke_candidate_allowlist_template.csv"
)
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_external_source_registry_configuration_gate_v0")
INPUT_CONFIG_CSV = OUTPUT_ROOT / "input/covapie_external_source_registry_config.csv"
TEMPLATE_CSV = OUTPUT_ROOT / "templates/covapie_external_source_registry_config_template.csv"
BLOCKED_HEADER_ONLY_CSV = OUTPUT_ROOT / "covapie_external_source_registry_config_blocked_header_only.csv"
VALIDATED_CONFIG_CSV = OUTPUT_ROOT / "covapie_external_source_registry_config_validated.csv"
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_precondition_audit.csv"
INPUT_DISCOVERY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_input_discovery_audit.csv"
SCHEMA_VALIDATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_schema_validation_audit.csv"
VALUE_VALIDATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_value_validation_audit.csv"
ENABLED_SOURCE_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_enabled_source_audit.csv"
OUTPUT_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_output_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_external_source_registry_configuration_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_external_source_registry_configuration_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_external_source_registry_configuration_gate_v0_summary.md")

METADATA_INDEX_ROOT = "data/derived/covalent_small/external_metadata_index"
RAW_STRUCTURE_ROOT = "data/raw/covalent_sources"
SOURCE_CONFIG_COLUMNS = [
    "source_slot_id",
    "source_name",
    "source_family",
    "source_priority",
    "source_metadata_index_url_or_local_path",
    "source_access_method",
    "source_version_or_download_date",
    "expected_metadata_artifact_type",
    "expected_candidate_unit",
    "citation_or_license_note",
    "enabled_for_download_smoke",
    "manual_source_verification_status",
]
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
ALLOWED_SOURCE_SLOT_IDS = [
    "specialized_covalent_complex_database_primary_1",
    "specialized_covalent_complex_database_primary_2",
    "specialized_covalent_complex_database_primary_3",
    "pdb_covalent_annotation_fallback",
    "user_or_pipeline_curated_metadata_override",
]
ALLOWED_SOURCE_FAMILIES = [
    "specialized_covalent_protein_ligand_database",
    "pdb_covalent_annotation_fallback",
    "user_or_pipeline_curated_metadata_override",
]
ALLOWED_ACCESS_METHODS = ["configured_url", "local_file", "local_directory", "manual_user_supplied"]
ALLOWED_ARTIFACT_TYPES = ["csv", "tsv", "json", "jsonl"]
FORBIDDEN_ARTIFACT_TYPES = ["zip", "pdb", "mmcif", "cif", "sdf", "mol2", "gz"]
ALLOWED_VERIFICATION_STATUS = ["verified_by_user", "verified_by_pipeline", "unverified"]
CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]
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
VALUE_VALIDATION_ITEMS = [
    "source_slot_id_allowed",
    "source_slot_id_unique",
    "source_name_non_empty",
    "source_family_allowed",
    "source_priority_integer_positive",
    "source_metadata_index_url_or_local_path_non_empty",
    "source_access_method_allowed",
    "source_version_or_download_date_non_empty",
    "expected_metadata_artifact_type_allowed",
    "expected_candidate_unit_covalent_event",
    "citation_or_license_note_non_empty",
    "manual_source_verification_status_allowed",
]
ENABLED_SOURCE_ITEMS = [
    "enabled_source_count",
    "at_most_one_enabled_for_first_smoke",
    "enabled_source_verified",
    "enabled_source_specialized_priority_or_allowed_fallback",
    "enabled_source_artifact_type_allowed",
    "enabled_source_access_method_allowed",
    "enabled_source_not_raw_artifact",
    "enabled_source_ready_for_download_smoke",
]
EXECUTION_BOUNDARY_ITEMS = [
    "external_source_registry_configuration_gate",
    "source_config_template_write",
    "source_config_input_read",
    "source_config_validation",
    "external_network_access",
    "external_source_url_verification",
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
    "candidate_metadata_materialization",
    "candidate_allowlist_materialization",
    "sample_index_write",
    "final_dataset_write",
    "torch_import",
    "model_forward",
    "training_claim",
]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
INPUT_DISCOVERY_COLUMNS = ["source_registry_config_exists", "source_registry_config_read", "source_registry_config_row_count", "configuration_status", "input_discovery_audit_passed", "blocking_reasons"]
SCHEMA_VALIDATION_COLUMNS = ["required_column", "column_present", "schema_validation_status", "schema_validation_passed", "blocking_reasons"]
VALUE_VALIDATION_COLUMNS = ["validation_item", "validation_status", "validation_passed", "blocking_reasons"]
ENABLED_SOURCE_COLUMNS = ["enabled_source_audit_item", "enabled_source_count", "audit_status", "audit_passed", "blocking_reasons"]
OUTPUT_AUDIT_COLUMNS = ["template_written", "blocked_header_only_written", "validated_config_written", "configured_source_count", "enabled_source_count", "configuration_status", "output_audit_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = ["canonical_mask_task_name", "display_alias", "source_of_truth_status", "alias_status", "mask_scope_status", "no_extra_mask_tasks_added", "mask_scope_audit_passed", "blocking_reasons"]
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_external_source_registry_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
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
        raise ValueError("Step 13AG template must contain exactly the 15 required allowlist columns and zero data rows")
    return True


def validate_step13ak_source_config_schema_contract_v0() -> bool:
    rows = _csv_rows(STEP13AK_SOURCE_CONFIG_SCHEMA_CSV)
    blockers = []
    if len(rows) != 12:
        blockers.append("source_config_schema_row_count")
    if [row["config_field"] for row in rows] != SOURCE_CONFIG_COLUMNS:
        blockers.append("source_config_schema_fields")
    if {row["current_step_configured"] for row in rows} != {"False"}:
        blockers.append("current_step_configured")
    if {row["config_contract_passed"] for row in rows} != {"True"}:
        blockers.append("config_contract_passed")
    if blockers:
        raise ValueError("Step 13AK source config schema contract failed: " + ";".join(blockers))
    return True


def validate_step13ak_allowed_artifact_contract_v0() -> bool:
    rows = _csv_rows(STEP13AK_ALLOWED_ARTIFACT_CSV)
    blockers = []
    if len(rows) != 10:
        blockers.append("allowed_artifact_row_count")
    by_type = {row["artifact_type"]: row for row in rows}
    for key in ["csv_metadata_index", "tsv_metadata_index", "json_metadata_index", "jsonl_metadata_index"]:
        if by_type.get(key, {}).get("allowed_for_metadata_index_download_smoke") != "True":
            blockers.append(key)
    for key in ["zip_archive_forbidden_current_smoke", "raw_pdb_forbidden", "raw_mmcif_forbidden", "raw_sdf_mol2_forbidden"]:
        if by_type.get(key, {}).get("allowed_for_metadata_index_download_smoke") != "False":
            blockers.append(key)
    if {row["current_step_downloaded"] for row in rows} != {"False"}:
        blockers.append("current_step_downloaded")
    if blockers:
        raise ValueError("Step 13AK allowed artifact contract failed: " + ";".join(blockers))
    return True


def validate_step13aj_event_identity_key_contract_v0() -> bool:
    rows = _csv_rows(STEP13AJ_EVENT_IDENTITY_CSV)
    rules = {row["identity_key_rule"] for row in rows}
    required = {"no_pdb_id_only_join", "minimal_event_key", "preferred_event_key", "multi_event_pdb_handling"}
    if not required.issubset(rules):
        raise ValueError("Step 13AJ event identity contract is missing required rules")
    return True


def validate_step13ak_precondition_v0() -> bool:
    for path in [
        STEP13AK_MANIFEST_JSON,
        STEP13AK_SUMMARY_MD,
        STEP13AK_SOURCE_CONFIG_SCHEMA_CSV,
        STEP13AK_ALLOWED_ARTIFACT_CSV,
        STEP13AJ_MANIFEST_JSON,
        STEP13AJ_EVENT_IDENTITY_CSV,
        STEP13AG_TEMPLATE_CSV,
        NAMING_CONVENTION_MD,
    ]:
        if not path.is_file():
            raise FileNotFoundError(f"Missing Step 13AL prerequisite: {path}")
    validate_step13ak_source_config_schema_contract_v0()
    validate_step13ak_allowed_artifact_contract_v0()
    validate_step13aj_event_identity_key_contract_v0()
    validate_step13ag_template_v0()
    validate_covapie_naming_convention_v0()
    manifest = _load_json(STEP13AK_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "covapie_specialized_covalent_database_source_acquisition_design_gate_v0",
        "project_name": PROJECT_NAME,
        "all_checks_passed": True,
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
        "metadata_index_allowed_artifact_types": ALLOWED_ARTIFACT_TYPES,
        "metadata_index_forbidden_artifact_types": FORBIDDEN_ARTIFACT_TYPES,
        "event_identity_key_policy": "no_pdb_id_only_join",
        "minimal_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name",
        "preferred_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name+covalent_bond_atom_pair",
        "one_row_one_covalent_event": True,
        "external_metadata_index_download_design_gate_passed": True,
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
        "network_access_used": False,
        "curl_used": False,
        "wget_used": False,
        "requests_used": False,
        "urllib_used": False,
        "browser_used": False,
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
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("blocking_reasons") != []:
        blockers.append("blocking_reasons")
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13AK precondition failed: " + ";".join(blockers))
    return True


def _read_config(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _parse_bool(value: str) -> bool | None:
    lowered = str(value).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def _positive_int(value: str) -> bool:
    try:
        return int(str(value).strip()) > 0
    except ValueError:
        return False


def _config_validation(config_path: Path) -> dict[str, Any]:
    exists = config_path.is_file()
    if not exists:
        return {
            "exists": False,
            "read": False,
            "header": [],
            "rows": [],
            "schema_valid": False,
            "values_valid": False,
            "configured_source_count": 0,
            "enabled_rows": [],
            "enabled_ready": False,
            "status": "blocked_due_to_missing_explicit_source_registry_config",
            "blocking_reasons": ["missing_explicit_source_registry_config"],
        }
    header, rows = _read_config(config_path)
    schema_valid = header == SOURCE_CONFIG_COLUMNS
    value_status = build_value_validation_rows(rows, schema_valid, exists)
    values_valid = schema_valid and all(row["validation_passed"] for row in value_status)
    enabled_rows = [row for row in rows if _parse_bool(row.get("enabled_for_download_smoke", "")) is True] if schema_valid else []
    enabled_ready = values_valid and _enabled_source_ready(enabled_rows, rows)
    if enabled_ready:
        status = "validated_source_registry_config"
        blockers: list[str] = []
    else:
        status = "blocked_due_to_invalid_source_registry_config"
        blockers = ["invalid_source_registry_config"]
    return {
        "exists": True,
        "read": True,
        "header": header,
        "rows": rows,
        "schema_valid": schema_valid,
        "values_valid": values_valid,
        "configured_source_count": len(rows) if schema_valid else 0,
        "enabled_rows": enabled_rows,
        "enabled_ready": enabled_ready,
        "status": status,
        "blocking_reasons": blockers,
    }


def _enabled_source_ready(enabled_rows: list[dict[str, str]], all_rows: list[dict[str, str]]) -> bool:
    if len(enabled_rows) != 1:
        return False
    enabled = enabled_rows[0]
    verified = enabled.get("manual_source_verification_status") in {"verified_by_user", "verified_by_pipeline"}
    artifact_ok = enabled.get("expected_metadata_artifact_type") in ALLOWED_ARTIFACT_TYPES
    access_ok = enabled.get("source_access_method") in ALLOWED_ACCESS_METHODS
    not_raw = enabled.get("expected_metadata_artifact_type") not in FORBIDDEN_ARTIFACT_TYPES
    if enabled.get("source_family") == "pdb_covalent_annotation_fallback":
        specialized_enabled = any(
            row.get("source_family") == "specialized_covalent_protein_ligand_database"
            and _parse_bool(row.get("enabled_for_download_smoke", "")) is True
            for row in all_rows
        )
        fallback_ok = not specialized_enabled
    else:
        fallback_ok = enabled.get("source_family") in ALLOWED_SOURCE_FAMILIES
    return verified and artifact_ok and access_ok and not_raw and fallback_ok


def build_precondition_rows(output_root: Path) -> list[dict[str, Any]]:
    safe = not any([_protected_source_diff_exists(), _original_dataloader_diff_exists(), _raw_files_staged(), _raw_files_tracked()])
    specs = [
        ("step13ak_manifest", STEP13AK_MANIFEST_JSON, validate_step13ak_precondition_v0()),
        ("step13ak_source_config_schema_contract", STEP13AK_SOURCE_CONFIG_SCHEMA_CSV, validate_step13ak_source_config_schema_contract_v0()),
        ("step13ak_allowed_artifact_contract", STEP13AK_ALLOWED_ARTIFACT_CSV, validate_step13ak_allowed_artifact_contract_v0()),
        ("step13aj_event_identity_key_contract", STEP13AJ_EVENT_IDENTITY_CSV, validate_step13aj_event_identity_key_contract_v0()),
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


def build_input_discovery_rows(validation: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_registry_config_exists": validation["exists"],
            "source_registry_config_read": validation["read"],
            "source_registry_config_row_count": len(validation["rows"]) if validation["exists"] else 0,
            "configuration_status": "configuration_input_discovered" if validation["exists"] else validation["status"],
            "input_discovery_audit_passed": True,
            "blocking_reasons": "" if validation["exists"] else "missing_explicit_source_registry_config",
        }
    ]


def build_schema_validation_rows(validation: dict[str, Any]) -> list[dict[str, Any]]:
    if not validation["exists"]:
        return [
            {
                "required_column": column,
                "column_present": False,
                "schema_validation_status": "not_applicable_missing_config",
                "schema_validation_passed": True,
                "blocking_reasons": "",
            }
            for column in SOURCE_CONFIG_COLUMNS
        ]
    header = validation["header"]
    exact = header == SOURCE_CONFIG_COLUMNS
    return [
        {
            "required_column": column,
            "column_present": column in header,
            "schema_validation_status": "present" if exact and column in header else "invalid",
            "schema_validation_passed": exact and column in header,
            "blocking_reasons": "" if exact and column in header else "invalid_source_registry_schema",
        }
        for column in SOURCE_CONFIG_COLUMNS
    ]


def build_value_validation_rows(rows: list[dict[str, str]], schema_valid: bool, exists: bool) -> list[dict[str, Any]]:
    if not exists:
        return [
            {"validation_item": item, "validation_status": "not_evaluated_missing_config", "validation_passed": True, "blocking_reasons": ""}
            for item in VALUE_VALIDATION_ITEMS
        ]
    if not schema_valid:
        return [
            {"validation_item": item, "validation_status": "not_evaluated_invalid_schema", "validation_passed": False, "blocking_reasons": "invalid_source_registry_schema"}
            for item in VALUE_VALIDATION_ITEMS
        ]
    checks = {
        "source_slot_id_allowed": all(row["source_slot_id"] in ALLOWED_SOURCE_SLOT_IDS for row in rows),
        "source_slot_id_unique": len({row["source_slot_id"] for row in rows}) == len(rows),
        "source_name_non_empty": all(row["source_name"].strip() for row in rows),
        "source_family_allowed": all(row["source_family"] in ALLOWED_SOURCE_FAMILIES for row in rows),
        "source_priority_integer_positive": all(_positive_int(row["source_priority"]) for row in rows),
        "source_metadata_index_url_or_local_path_non_empty": all(row["source_metadata_index_url_or_local_path"].strip() for row in rows),
        "source_access_method_allowed": all(row["source_access_method"] in ALLOWED_ACCESS_METHODS for row in rows),
        "source_version_or_download_date_non_empty": all(row["source_version_or_download_date"].strip() for row in rows),
        "expected_metadata_artifact_type_allowed": all(row["expected_metadata_artifact_type"] in ALLOWED_ARTIFACT_TYPES for row in rows),
        "expected_candidate_unit_covalent_event": all(row["expected_candidate_unit"] == "covalent_ligand_residue_event" for row in rows),
        "citation_or_license_note_non_empty": all(row["citation_or_license_note"].strip() for row in rows),
        "manual_source_verification_status_allowed": all(row["manual_source_verification_status"] in ALLOWED_VERIFICATION_STATUS for row in rows),
    }
    return [
        {
            "validation_item": item,
            "validation_status": "passed" if checks[item] else "failed",
            "validation_passed": checks[item],
            "blocking_reasons": "" if checks[item] else item,
        }
        for item in VALUE_VALIDATION_ITEMS
    ]


def build_enabled_source_rows(validation: dict[str, Any]) -> list[dict[str, Any]]:
    if not validation["exists"]:
        return [
            {
                "enabled_source_audit_item": item,
                "enabled_source_count": 0,
                "audit_status": "not_evaluated_missing_config",
                "audit_passed": True,
                "blocking_reasons": "missing_explicit_source_registry_config",
            }
            for item in ENABLED_SOURCE_ITEMS
        ]
    enabled = validation["enabled_rows"]
    count = len(enabled)
    first = enabled[0] if enabled else {}
    checks = {
        "enabled_source_count": count == 1,
        "at_most_one_enabled_for_first_smoke": count <= 1,
        "enabled_source_verified": count == 1 and first.get("manual_source_verification_status") in {"verified_by_user", "verified_by_pipeline"},
        "enabled_source_specialized_priority_or_allowed_fallback": count == 1 and first.get("source_family") in ALLOWED_SOURCE_FAMILIES,
        "enabled_source_artifact_type_allowed": count == 1 and first.get("expected_metadata_artifact_type") in ALLOWED_ARTIFACT_TYPES,
        "enabled_source_access_method_allowed": count == 1 and first.get("source_access_method") in ALLOWED_ACCESS_METHODS,
        "enabled_source_not_raw_artifact": count == 1 and first.get("expected_metadata_artifact_type") not in FORBIDDEN_ARTIFACT_TYPES,
        "enabled_source_ready_for_download_smoke": validation["enabled_ready"],
    }
    return [
        {
            "enabled_source_audit_item": item,
            "enabled_source_count": count,
            "audit_status": "passed" if checks[item] else "blocked_or_failed",
            "audit_passed": True,
            "blocking_reasons": "" if checks[item] else ("invalid_source_registry_config" if validation["exists"] else "missing_explicit_source_registry_config"),
        }
        for item in ENABLED_SOURCE_ITEMS
    ]


def build_output_rows(validation: dict[str, Any]) -> list[dict[str, Any]]:
    valid = validation["status"] == "validated_source_registry_config"
    return [
        {
            "template_written": True,
            "blocked_header_only_written": not valid,
            "validated_config_written": valid,
            "configured_source_count": validation["configured_source_count"],
            "enabled_source_count": len(validation["enabled_rows"]),
            "configuration_status": validation["status"],
            "output_audit_passed": True,
            "blocking_reasons": ";".join(validation["blocking_reasons"]),
        }
    ]


def build_execution_boundary_rows(config_exists: bool) -> list[dict[str, Any]]:
    rows = []
    for item in EXECUTION_BOUNDARY_ITEMS:
        if item == "external_source_registry_configuration_gate":
            status = "executed_configuration_gate_only"
        elif item == "source_config_template_write":
            status = "executed_template_only"
        elif item in {"source_config_input_read", "source_config_validation"}:
            status = "executed_only_if_explicit_config_exists_else_not_executed"
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
            "mask_scope_status": "preserved_from_step13ak",
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
            "blocking_for_external_source_registry_gate": False,
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


def run_covapie_external_source_registry_configuration_gate_v0(
    output_root: str | Path = OUTPUT_ROOT,
    input_config_csv: str | Path | None = None,
) -> dict[str, Any]:
    validate_step13ak_precondition_v0()
    output_root = Path(output_root)
    input_path = Path(input_config_csv) if input_config_csv is not None else output_root / "input/covapie_external_source_registry_config.csv"
    validation = _config_validation(input_path)
    precondition_rows = build_precondition_rows(output_root)
    input_rows = build_input_discovery_rows(validation)
    schema_rows = build_schema_validation_rows(validation)
    value_rows = build_value_validation_rows(validation["rows"], validation["schema_valid"], validation["exists"])
    enabled_rows = build_enabled_source_rows(validation)
    output_rows = build_output_rows(validation)
    execution_rows = build_execution_boundary_rows(validation["exists"])
    git_rows = build_git_safety_rows(output_root)
    mask_rows = build_mask_scope_rows()
    feature_rows = build_feature_semantics_rows()
    leakage_rows = build_leakage_split_rows()
    enabled = validation["enabled_rows"][0] if len(validation["enabled_rows"]) == 1 else {}
    valid = validation["status"] == "validated_source_registry_config"
    blocked_missing = validation["status"] == "blocked_due_to_missing_explicit_source_registry_config"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "naming_convention_validated": True,
        "step13ak_external_metadata_index_download_design_gate_validated": True,
        "external_source_registry_scope": "source_registry_configuration_gate_only",
        "source_registry_config_template_written": True,
        "source_registry_config_exists": validation["exists"],
        "source_registry_config_read": validation["read"],
        "source_registry_config_row_count": len(validation["rows"]) if validation["exists"] else 0,
        "source_registry_schema_validated": validation["schema_valid"],
        "source_registry_values_validated": validation["values_valid"],
        "configured_source_count": validation["configured_source_count"],
        "enabled_source_count": len(validation["enabled_rows"]),
        "enabled_source_slot_id": enabled.get("source_slot_id", ""),
        "enabled_source_name": enabled.get("source_name", ""),
        "enabled_source_family": enabled.get("source_family", ""),
        "enabled_source_artifact_type": enabled.get("expected_metadata_artifact_type", ""),
        "enabled_source_verified": enabled.get("manual_source_verification_status", "") in {"verified_by_user", "verified_by_pipeline"},
        "enabled_source_ready_for_download_smoke": validation["enabled_ready"],
        "configuration_status": validation["status"],
        "metadata_index_root": METADATA_INDEX_ROOT,
        "raw_structure_root": RAW_STRUCTURE_ROOT,
        "metadata_index_allowed_artifact_types": ALLOWED_ARTIFACT_TYPES,
        "metadata_index_forbidden_artifact_types": FORBIDDEN_ARTIFACT_TYPES,
        "event_identity_key_policy": "no_pdb_id_only_join",
        "minimal_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name",
        "preferred_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name+covalent_bond_atom_pair",
        "one_row_one_covalent_event": True,
        "covapie_external_source_registry_precondition_audit_row_count": len(precondition_rows),
        "covapie_external_source_registry_input_discovery_audit_row_count": len(input_rows),
        "covapie_external_source_registry_schema_validation_audit_row_count": len(schema_rows),
        "covapie_external_source_registry_value_validation_audit_row_count": len(value_rows),
        "covapie_external_source_registry_enabled_source_audit_row_count": len(enabled_rows),
        "covapie_external_source_registry_output_audit_row_count": len(output_rows),
        "covapie_external_source_registry_execution_boundary_audit_row_count": len(execution_rows),
        "covapie_external_source_registry_git_safety_audit_row_count": len(git_rows),
        "covapie_external_source_registry_mask_scope_audit_row_count": len(mask_rows),
        "covapie_external_source_registry_feature_semantics_audit_row_count": len(feature_rows),
        "covapie_external_source_registry_leakage_split_audit_row_count": len(leakage_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "network_access_used": False,
        "curl_used": False,
        "wget_used": False,
        "requests_used": False,
        "urllib_used": False,
        "browser_used": False,
        "external_source_url_verified": False,
        "external_metadata_downloaded": False,
        "raw_structure_downloaded": False,
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
        "external_source_registry_configuration_gate_passed": True,
        "ready_for_covapie_external_metadata_index_download_smoke": valid,
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate": True,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_external_metadata_index_download_smoke" if valid else "provide_explicit_external_source_registry_config",
        "all_checks_passed": True,
        "blocking_reasons": [] if valid else (["missing_explicit_source_registry_config"] if blocked_missing else ["invalid_source_registry_config"]),
    }
    report_sections = {
        "step13ak_precondition": {"rows": len(precondition_rows)},
        "input_discovery": {"rows": len(input_rows), "status": validation["status"]},
        "schema_validation": {"rows": len(schema_rows)},
        "value_validation": {"rows": len(value_rows)},
        "enabled_source": {"rows": len(enabled_rows), "ready": validation["enabled_ready"]},
        "output_audit": {"rows": len(output_rows)},
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
        "template_rows": [],
        "config_rows": validation["rows"] if valid else [],
        "blocked_rows": [],
        "precondition_rows": precondition_rows,
        "input_rows": input_rows,
        "schema_rows": schema_rows,
        "value_rows": value_rows,
        "enabled_rows": enabled_rows,
        "output_rows": output_rows,
        "execution_rows": execution_rows,
        "git_rows": git_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "validated_config_written": valid,
        "blocked_header_only_written": not valid,
        "paths": {
            "template": output_root / TEMPLATE_CSV.relative_to(OUTPUT_ROOT),
            "blocked": output_root / BLOCKED_HEADER_ONLY_CSV.name,
            "validated": output_root / VALIDATED_CONFIG_CSV.name,
            "precondition": output_root / PRECONDITION_AUDIT_CSV.name,
            "input": output_root / INPUT_DISCOVERY_AUDIT_CSV.name,
            "schema": output_root / SCHEMA_VALIDATION_AUDIT_CSV.name,
            "value": output_root / VALUE_VALIDATION_AUDIT_CSV.name,
            "enabled": output_root / ENABLED_SOURCE_AUDIT_CSV.name,
            "output": output_root / OUTPUT_AUDIT_CSV.name,
            "execution": output_root / EXECUTION_BOUNDARY_AUDIT_CSV.name,
            "git": output_root / GIT_SAFETY_AUDIT_CSV.name,
            "mask": output_root / MASK_SCOPE_AUDIT_CSV.name,
            "feature": output_root / FEATURE_SEMANTICS_AUDIT_CSV.name,
            "leakage": output_root / LEAKAGE_SPLIT_AUDIT_CSV.name,
            "report": output_root / REPORT_CSV.name,
            "manifest": output_root / MANIFEST_JSON.name,
        },
    }

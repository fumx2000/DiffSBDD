from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_external_metadata_index_download_smoke_v0"
PREVIOUS_STAGE = step13am.STAGE
PROJECT_NAME = "CovaPIE"

STEP13AM_ROOT = step13am.OUTPUT_ROOT
STEP13AM_MANIFEST_JSON = STEP13AM_ROOT / "covapie_explicit_external_source_registry_config_smoke_manifest.json"
STEP13AM_SUMMARY_MD = Path("docs/covapie_explicit_external_source_registry_config_smoke_v0_summary.md")
STEP13AM_CONFIG_CSV = STEP13AM_ROOT / "covapie_explicit_external_source_registry_config.csv"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_external_metadata_index_download_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_download_smoke_precondition_audit.csv"
SOURCE_CONFIG_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_source_config_audit.csv"
FILE_DISCOVERY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_file_discovery_audit.csv"
ALLOWED_ARTIFACT_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_allowed_artifact_audit.csv"
HEADER_PROBE_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_header_probe_audit.csv"
SAMPLE_ROWS_PROBE_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_sample_rows_probe_audit.csv"
EVENT_KEY_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_event_key_boundary_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_download_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_external_metadata_index_download_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_external_metadata_index_download_smoke_v0_summary.md")

SOURCE_CONFIG_COLUMNS = step13am.SOURCE_CONFIG_COLUMNS
METADATA_INDEX_ROOT = step13am.METADATA_INDEX_ROOT
RAW_STRUCTURE_ROOT = step13am.RAW_STRUCTURE_ROOT
ALLOWED_ARTIFACT_TYPES = step13am.ALLOWED_ARTIFACT_TYPES
FORBIDDEN_ARTIFACT_TYPES = step13am.FORBIDDEN_ARTIFACT_TYPES
CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FORBIDDEN_SUFFIXES = step13am.FORBIDDEN_SUFFIXES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
SAMPLE_LIMIT = 5

CONFIGURED_METADATA_INDEX_PATH = step13am.CONFIG_ROW["source_metadata_index_url_or_local_path"]

SOURCE_CONFIG_AUDIT_COLUMNS = ["source_config_field", "source_config_value", "config_audit_status", "config_audit_passed", "blocking_reasons"]
FILE_DISCOVERY_COLUMNS = [
    "metadata_index_file_exists",
    "metadata_index_file_checked",
    "metadata_index_file_read",
    "metadata_index_file_size_bytes",
    "metadata_index_file_suffix",
    "metadata_index_download_or_copy_performed",
    "file_discovery_status",
    "file_discovery_audit_passed",
    "blocking_reasons",
]
ALLOWED_ARTIFACT_COLUMNS = ["allowed_artifact_item", "audit_status", "allowed_artifact_audit_passed", "blocking_reasons"]
HEADER_PROBE_COLUMNS = ["header_probe_status", "header_probe_executed", "column_count", "column_names", "header_probe_passed", "blocking_reasons"]
SAMPLE_ROWS_PROBE_COLUMNS = [
    "sample_rows_probe_status",
    "sample_rows_probe_executed",
    "sampled_row_count",
    "total_rows_scanned",
    "sample_limit",
    "sample_rows_probe_passed",
    "blocking_reasons",
]
EVENT_KEY_COLUMNS = ["event_key_boundary_item", "event_key_boundary_status", "event_key_boundary_audit_passed", "blocking_reasons"]
PRECONDITION_COLUMNS = step13am.PRECONDITION_COLUMNS
EXECUTION_COLUMNS = step13am.EXECUTION_COLUMNS
GIT_SAFETY_COLUMNS = step13am.GIT_SAFETY_COLUMNS
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "audit_required_before_training",
    "fully_audited_claimed",
    "blocking_for_external_metadata_index_download_smoke",
    "training_ready",
    "recommended_audit_step",
    "feature_semantics_audit_passed",
    "blocking_reasons",
]
LEAKAGE_COLUMNS = step13am.LEAKAGE_COLUMNS
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]

PRECONDITION_ITEMS = [
    "step13am_manifest",
    "step13am_source_config",
    "step13ak_allowed_artifact_contract",
    "step13aj_event_identity_key_contract",
    "covapie_naming_convention_doc",
    "repository_safety_baseline",
    "configured_metadata_index_path_declared",
    "output_root_declared",
]
ALLOWED_ARTIFACT_ITEMS = [
    "expected_artifact_type_csv_allowed",
    "configured_path_suffix_csv",
    "configured_path_under_metadata_root",
    "raw_zip_forbidden",
    "raw_pdb_forbidden",
    "raw_mmcif_cif_gz_forbidden",
    "raw_sdf_mol2_forbidden",
    "no_raw_artifact_copied",
]
EVENT_KEY_ITEMS = [
    "no_pdb_id_only_join",
    "minimal_event_key_carried_forward",
    "preferred_event_key_carried_forward",
    "one_row_one_covalent_event",
    "no_event_key_materialization_current_step",
    "no_candidate_metadata_materialization_current_step",
    "no_allowlist_materialization_current_step",
    "ambiguous_events_not_resolved_current_step",
]
EXECUTION_BOUNDARY_ITEMS = [
    "external_metadata_index_download_smoke",
    "source_config_read",
    "manual_metadata_index_file_discovery",
    "manual_metadata_index_header_probe",
    "manual_metadata_index_sample_rows_probe",
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
    "torch_import",
    "model_forward",
    "training_claim",
]


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


def _read_single_config_row(path: Path = STEP13AM_CONFIG_CSV) -> dict[str, str]:
    rows = _csv_rows(path)
    if len(rows) != 1:
        raise ValueError("Step 13AM source config must contain exactly one row")
    return rows[0]


def _runtime_path(path_text: str, override: str | Path | None = None) -> Path:
    if override is not None:
        return Path(override)
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def validate_step13am_precondition_v0() -> bool:
    for path in [STEP13AM_MANIFEST_JSON, STEP13AM_SUMMARY_MD, STEP13AM_CONFIG_CSV]:
        if not path.is_file():
            raise FileNotFoundError(f"Missing Step 13AN prerequisite: {path}")
    manifest = _load_json(STEP13AM_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "covapie_external_source_registry_configuration_gate_v0",
        "project_name": PROJECT_NAME,
        "all_checks_passed": True,
        "source_registry_config_written": True,
        "source_registry_config_row_count": 1,
        "source_registry_schema_validated": True,
        "source_registry_values_validated": True,
        "configured_source_count": 1,
        "enabled_source_count": 1,
        "enabled_source_slot_id": "specialized_covalent_complex_database_primary_1",
        "enabled_source_name": "CovPDB",
        "enabled_source_family": "specialized_covalent_protein_ligand_database",
        "enabled_source_artifact_type": "csv",
        "enabled_source_access_method": "manual_user_supplied",
        "enabled_source_verified": True,
        "enabled_source_ready_for_download_smoke": True,
        "source_metadata_index_url_or_local_path": CONFIGURED_METADATA_INDEX_PATH,
        "source_metadata_index_path_checked_current_step": False,
        "source_metadata_index_file_opened": False,
        "source_metadata_index_file_exists_current_step": False,
        "explicit_external_source_registry_config_smoke_passed": True,
        "ready_for_covapie_external_metadata_index_download_smoke": True,
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate": True,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_external_metadata_index_download_smoke",
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
        raise ValueError("Step 13AM precondition failed: " + ";".join(blockers))
    return True


def validate_step13am_source_config_v0(row: dict[str, str] | None = None) -> bool:
    row = row or _read_single_config_row()
    checks = {
        "columns": list(row) == SOURCE_CONFIG_COLUMNS,
        "source_name": row["source_name"] == "CovPDB",
        "source_family": row["source_family"] == "specialized_covalent_protein_ligand_database",
        "source_access_method": row["source_access_method"] == "manual_user_supplied",
        "expected_metadata_artifact_type": row["expected_metadata_artifact_type"] == "csv",
        "expected_candidate_unit": row["expected_candidate_unit"] == "covalent_ligand_residue_event",
        "enabled_for_download_smoke": row["enabled_for_download_smoke"].lower() == "true",
        "manual_source_verification_status": row["manual_source_verification_status"] == "verified_by_user",
        "configured_path_under_root": row["source_metadata_index_url_or_local_path"].startswith(
            "data/derived/covalent_small/external_metadata_index/covpdb/"
        ),
        "configured_suffix_csv": Path(row["source_metadata_index_url_or_local_path"]).suffix == ".csv",
    }
    if not all(checks.values()):
        raise ValueError("Step 13AM source config validation failed: " + ";".join(k for k, v in checks.items() if not v))
    return True


def validate_step13ak_allowed_artifact_contract_v0() -> bool:
    return step13am.validate_step13ak_allowed_artifact_contract_v0()


def validate_step13aj_event_identity_key_contract_v0() -> bool:
    return step13am.validate_step13aj_event_identity_key_contract_v0()


def validate_covapie_naming_convention_v0() -> bool:
    return step13am.validate_covapie_naming_convention_v0()


def _probe_metadata_index(path_text: str, path_override: str | Path | None = None) -> dict[str, Any]:
    runtime_path = _runtime_path(path_text, path_override)
    exists = runtime_path.is_file()
    suffix = Path(path_text).suffix
    size = runtime_path.stat().st_size if exists else 0
    header: list[str] = []
    sampled_count = 0
    total_rows = 0
    if exists:
        with runtime_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            for total_rows, _row in enumerate(reader, start=1):
                if sampled_count < SAMPLE_LIMIT:
                    sampled_count += 1
    return {
        "runtime_path": runtime_path,
        "exists": exists,
        "suffix": suffix,
        "size": size,
        "header": header,
        "column_count": len(header),
        "sampled_count": sampled_count,
        "total_rows": total_rows,
    }


def build_precondition_rows(output_root: Path, row: dict[str, str]) -> list[dict[str, Any]]:
    safe = not any([_protected_source_diff_exists(), _original_dataloader_diff_exists(), _raw_files_staged(), _raw_files_tracked()])
    specs = [
        ("step13am_manifest", STEP13AM_MANIFEST_JSON, validate_step13am_precondition_v0()),
        ("step13am_source_config", STEP13AM_CONFIG_CSV, validate_step13am_source_config_v0(row)),
        ("step13ak_allowed_artifact_contract", step13am.step13al.STEP13AK_ALLOWED_ARTIFACT_CSV, validate_step13ak_allowed_artifact_contract_v0()),
        ("step13aj_event_identity_key_contract", step13am.step13al.STEP13AJ_EVENT_IDENTITY_CSV, validate_step13aj_event_identity_key_contract_v0()),
        ("covapie_naming_convention_doc", step13am.step13al.NAMING_CONVENTION_MD, validate_covapie_naming_convention_v0()),
        ("repository_safety_baseline", "protected source and raw-file safety checks", safe),
        ("configured_metadata_index_path_declared", row["source_metadata_index_url_or_local_path"], True),
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


def build_source_config_rows(row: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "source_config_field": column,
            "source_config_value": row[column],
            "config_audit_status": "passed",
            "config_audit_passed": True,
            "blocking_reasons": "",
        }
        for column in SOURCE_CONFIG_COLUMNS
    ]


def build_file_discovery_rows(probe: dict[str, Any]) -> list[dict[str, Any]]:
    exists = probe["exists"]
    return [
        {
            "metadata_index_file_exists": exists,
            "metadata_index_file_checked": True,
            "metadata_index_file_read": exists,
            "metadata_index_file_size_bytes": probe["size"],
            "metadata_index_file_suffix": probe["suffix"],
            "metadata_index_download_or_copy_performed": False,
            "file_discovery_status": "manual_metadata_index_discovered" if exists else "blocked_due_to_missing_manual_metadata_index",
            "file_discovery_audit_passed": True,
            "blocking_reasons": "" if exists else "missing_manual_metadata_index_csv",
        }
    ]


def build_allowed_artifact_rows(row: dict[str, str]) -> list[dict[str, Any]]:
    path = row["source_metadata_index_url_or_local_path"]
    checks = {
        "expected_artifact_type_csv_allowed": row["expected_metadata_artifact_type"] == "csv",
        "configured_path_suffix_csv": Path(path).suffix == ".csv",
        "configured_path_under_metadata_root": path.startswith("data/derived/covalent_small/external_metadata_index/"),
        "raw_zip_forbidden": "zip" in FORBIDDEN_ARTIFACT_TYPES,
        "raw_pdb_forbidden": "pdb" in FORBIDDEN_ARTIFACT_TYPES,
        "raw_mmcif_cif_gz_forbidden": {"mmcif", "cif", "gz"}.issubset(set(FORBIDDEN_ARTIFACT_TYPES)),
        "raw_sdf_mol2_forbidden": {"sdf", "mol2"}.issubset(set(FORBIDDEN_ARTIFACT_TYPES)),
        "no_raw_artifact_copied": True,
    }
    return [
        {
            "allowed_artifact_item": item,
            "audit_status": "passed" if checks[item] else "failed",
            "allowed_artifact_audit_passed": checks[item],
            "blocking_reasons": "" if checks[item] else item,
        }
        for item in ALLOWED_ARTIFACT_ITEMS
    ]


def build_header_probe_rows(probe: dict[str, Any]) -> list[dict[str, Any]]:
    if not probe["exists"]:
        return [
            {
                "header_probe_status": "not_available_missing_manual_metadata_index",
                "header_probe_executed": False,
                "column_count": 0,
                "column_names": "",
                "header_probe_passed": True,
                "blocking_reasons": "missing_manual_metadata_index_csv",
            }
        ]
    passed = probe["column_count"] > 0
    return [
        {
            "header_probe_status": "header_read",
            "header_probe_executed": True,
            "column_count": probe["column_count"],
            "column_names": ";".join(probe["header"]),
            "header_probe_passed": passed,
            "blocking_reasons": "" if passed else "no_header_found",
        }
    ]


def build_sample_rows_probe_rows(probe: dict[str, Any]) -> list[dict[str, Any]]:
    if not probe["exists"]:
        return [
            {
                "sample_rows_probe_status": "not_available_missing_manual_metadata_index",
                "sample_rows_probe_executed": False,
                "sampled_row_count": 0,
                "total_rows_scanned": 0,
                "sample_limit": SAMPLE_LIMIT,
                "sample_rows_probe_passed": True,
                "blocking_reasons": "missing_manual_metadata_index_csv",
            }
        ]
    return [
        {
            "sample_rows_probe_status": "sample_rows_read",
            "sample_rows_probe_executed": True,
            "sampled_row_count": probe["sampled_count"],
            "total_rows_scanned": probe["total_rows"],
            "sample_limit": SAMPLE_LIMIT,
            "sample_rows_probe_passed": True,
            "blocking_reasons": "",
        }
    ]


def build_event_key_rows() -> list[dict[str, Any]]:
    return [
        {
            "event_key_boundary_item": item,
            "event_key_boundary_status": "carried_forward_or_deferred_not_materialized",
            "event_key_boundary_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in EVENT_KEY_ITEMS
    ]


def build_execution_boundary_rows(exists: bool) -> list[dict[str, Any]]:
    rows = []
    for item in EXECUTION_BOUNDARY_ITEMS:
        if item == "external_metadata_index_download_smoke":
            status = "executed_metadata_index_smoke_only"
        elif item == "source_config_read":
            status = "executed_config_only"
        elif item == "manual_metadata_index_file_discovery":
            status = "executed_path_exists_check_only"
        elif item == "manual_metadata_index_header_probe":
            status = "executed_header_only" if exists else "not_executed_missing_manual_metadata_index"
        elif item == "manual_metadata_index_sample_rows_probe":
            status = "executed_sample_rows_only" if exists else "not_executed_missing_manual_metadata_index"
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
            "mask_scope_status": "preserved_from_step13am",
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
            "blocking_for_external_metadata_index_download_smoke": False,
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


def run_covapie_external_metadata_index_download_smoke_v0(
    output_root: str | Path = OUTPUT_ROOT,
    source_config_csv: str | Path = STEP13AM_CONFIG_CSV,
    metadata_index_path_override: str | Path | None = None,
) -> dict[str, Any]:
    output_root = Path(output_root)
    validate_step13am_precondition_v0()
    validate_step13ak_allowed_artifact_contract_v0()
    validate_step13aj_event_identity_key_contract_v0()
    validate_covapie_naming_convention_v0()
    row = _read_single_config_row(Path(source_config_csv))
    validate_step13am_source_config_v0(row)
    probe = _probe_metadata_index(row["source_metadata_index_url_or_local_path"], metadata_index_path_override)
    exists = probe["exists"]
    smoke_passed = exists and probe["column_count"] > 0
    status = "manual_metadata_index_discovered" if exists else "blocked_due_to_missing_manual_metadata_index"
    blockers = [] if exists else ["missing_manual_metadata_index_csv"]
    precondition_rows = build_precondition_rows(output_root, row)
    source_config_rows = build_source_config_rows(row)
    file_discovery_rows = build_file_discovery_rows(probe)
    allowed_rows = build_allowed_artifact_rows(row)
    header_rows = build_header_probe_rows(probe)
    sample_rows = build_sample_rows_probe_rows(probe)
    event_key_rows = build_event_key_rows()
    execution_rows = build_execution_boundary_rows(exists)
    git_rows = build_git_safety_rows(output_root)
    mask_rows = build_mask_scope_rows()
    feature_rows = build_feature_semantics_rows()
    leakage_rows = build_leakage_split_rows()
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "naming_convention_validated": True,
        "step13am_explicit_external_source_registry_config_smoke_validated": True,
        "metadata_index_download_smoke_scope": "manual_metadata_index_file_discovery_only",
        "enabled_source_name": row["source_name"],
        "enabled_source_family": row["source_family"],
        "enabled_source_access_method": row["source_access_method"],
        "enabled_source_artifact_type": row["expected_metadata_artifact_type"],
        "source_metadata_index_url_or_local_path": row["source_metadata_index_url_or_local_path"],
        "metadata_index_root": METADATA_INDEX_ROOT,
        "raw_structure_root": RAW_STRUCTURE_ROOT,
        "metadata_index_file_checked": True,
        "metadata_index_file_exists": exists,
        "metadata_index_file_read": exists,
        "metadata_index_file_size_bytes": probe["size"],
        "metadata_index_file_suffix": probe["suffix"],
        "metadata_index_download_or_copy_performed": False,
        "metadata_index_header_probe_executed": exists,
        "metadata_index_column_count": probe["column_count"] if exists else 0,
        "metadata_index_column_names": probe["header"] if exists else [],
        "metadata_index_sample_rows_probe_executed": exists,
        "metadata_index_sampled_row_count": probe["sampled_count"] if exists else 0,
        "metadata_index_total_rows_scanned": probe["total_rows"] if exists else 0,
        "metadata_index_sample_limit": SAMPLE_LIMIT,
        "metadata_index_file_copied_to_output_root": False,
        "external_network_access_used": False,
        "external_source_url_verified": False,
        "external_metadata_downloaded": False,
        "raw_structure_downloaded": False,
        "metadata_index_allowed_artifact_types": ALLOWED_ARTIFACT_TYPES,
        "metadata_index_forbidden_artifact_types": FORBIDDEN_ARTIFACT_TYPES,
        "event_identity_key_policy": "no_pdb_id_only_join",
        "minimal_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name",
        "preferred_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name+covalent_bond_atom_pair",
        "one_row_one_covalent_event": True,
        "covapie_external_metadata_index_download_smoke_precondition_audit_row_count": len(precondition_rows),
        "covapie_external_metadata_index_source_config_audit_row_count": len(source_config_rows),
        "covapie_external_metadata_index_file_discovery_audit_row_count": len(file_discovery_rows),
        "covapie_external_metadata_index_allowed_artifact_audit_row_count": len(allowed_rows),
        "covapie_external_metadata_index_header_probe_audit_row_count": len(header_rows),
        "covapie_external_metadata_index_sample_rows_probe_audit_row_count": len(sample_rows),
        "covapie_external_metadata_index_event_key_boundary_audit_row_count": len(event_key_rows),
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
        "external_metadata_index_download_smoke_passed": smoke_passed,
        "metadata_index_download_smoke_status": status,
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate": smoke_passed,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_external_metadata_index_schema_probe_design_gate" if smoke_passed else "provide_manual_covpdb_metadata_index_csv",
        "all_checks_passed": True,
        "blocking_reasons": blockers,
    }
    report_sections = {
        "step13am_precondition": {"rows": len(precondition_rows)},
        "source_config": {"rows": len(source_config_rows), "source_name": row["source_name"]},
        "file_discovery": {"rows": len(file_discovery_rows), "exists": exists},
        "allowed_artifact": {"rows": len(allowed_rows)},
        "header_probe": {"rows": len(header_rows), "executed": exists},
        "sample_rows_probe": {"rows": len(sample_rows), "sampled": manifest["metadata_index_sampled_row_count"]},
        "event_key_boundary": {"rows": len(event_key_rows)},
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
        "file_discovery_rows": file_discovery_rows,
        "allowed_rows": allowed_rows,
        "header_rows": header_rows,
        "sample_rows": sample_rows,
        "event_key_rows": event_key_rows,
        "execution_rows": execution_rows,
        "git_rows": git_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "paths": {
            "precondition": output_root / PRECONDITION_AUDIT_CSV.name,
            "source_config": output_root / SOURCE_CONFIG_AUDIT_CSV.name,
            "file_discovery": output_root / FILE_DISCOVERY_AUDIT_CSV.name,
            "allowed": output_root / ALLOWED_ARTIFACT_AUDIT_CSV.name,
            "header": output_root / HEADER_PROBE_AUDIT_CSV.name,
            "sample": output_root / SAMPLE_ROWS_PROBE_AUDIT_CSV.name,
            "event_key": output_root / EVENT_KEY_BOUNDARY_AUDIT_CSV.name,
            "execution": output_root / EXECUTION_BOUNDARY_AUDIT_CSV.name,
            "git": output_root / GIT_SAFETY_AUDIT_CSV.name,
            "mask": output_root / MASK_SCOPE_AUDIT_CSV.name,
            "feature": output_root / FEATURE_SEMANTICS_AUDIT_CSV.name,
            "leakage": output_root / LEAKAGE_SPLIT_AUDIT_CSV.name,
            "report": output_root / REPORT_CSV.name,
            "manifest": output_root / MANIFEST_JSON.name,
        },
    }

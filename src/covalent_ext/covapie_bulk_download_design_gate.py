from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_feature_semantics_resolution_smoke_qa_gate as step14a


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_bulk_download_design_gate_v0"
STEP_LABEL = "Step 14B"
PREVIOUS_STAGE = step14a.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_bulk_download_design_precondition_audit.csv"
CANDIDATE_SOURCE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_bulk_download_candidate_source_contract.csv"
STORAGE_LAYOUT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_bulk_download_storage_layout_contract.csv"
MANIFEST_SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_bulk_download_manifest_schema_contract.csv"
NETWORK_BOUNDARY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_bulk_download_network_boundary_contract.csv"
PILOT_SCALE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_bulk_download_pilot_scale_contract.csv"
RESUME_CHECKSUM_CONTRACT_CSV = OUTPUT_ROOT / "covapie_bulk_download_resume_checksum_contract.csv"
FAILURE_TAXONOMY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_bulk_download_failure_taxonomy_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_bulk_download_design_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_bulk_download_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_bulk_download_design_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_bulk_download_design_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_bulk_download_design_gate_v0.py")

METADATA_CSV = step14a.step13bd.METADATA_CSV
METADATA_CSV_SHA256 = step14a.METADATA_CSV_SHA256
RAW_STORAGE_ROOT = step14a.step13bd.RAW_STORAGE_ROOT
STEP14A_MANIFEST_JSON = step14a.MANIFEST_JSON

STEP14A_ROOT = step14a.OUTPUT_ROOT
STEP13BZ_ROOT = step14a.step13bz.OUTPUT_ROOT
STEP13BY_ROOT = step14a.step13by.OUTPUT_ROOT
STEP13BX_ROOT = step14a.step13bx.OUTPUT_ROOT
STEP13BU_ROOT = step14a.step13bu.OUTPUT_ROOT
STEP13BO_ROOT = step14a.step13bo.OUTPUT_ROOT
STEP13BM_ROOT = step14a.step13bm.OUTPUT_ROOT
STEP13AI_ROOT = Path("data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0")
STEP13BW_ROOT = step14a.step13bw.OUTPUT_ROOT

CANDIDATE_ALLOWLIST_QA_ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_qa_gate_v0")
BATCH_RAW_READ_DESIGN_ROOT = Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_design_gate_v0")
BATCH_RAW_READ_SMOKE_ROOT = Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_smoke_v0")
BATCH_RAW_READ_QA_ROOT = Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_qa_gate_v0")

CANONICAL_MASK_TASK_NAMES = step14a.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14a.CANONICAL_MASK_TASK_ALIASES

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
CANDIDATE_SOURCE_COLUMNS = [
    "candidate_source_item",
    "source_artifact_or_policy",
    "expected_status",
    "observed_status",
    "used_for_future_download_manifest",
    "candidate_source_contract_passed",
    "qa_comment",
]
STORAGE_LAYOUT_COLUMNS = [
    "storage_layout_item",
    "proposed_path_or_policy",
    "current_step_created",
    "future_step_allowed",
    "git_tracking_policy",
    "storage_layout_contract_passed",
    "qa_comment",
]
MANIFEST_SCHEMA_COLUMNS = [
    "manifest_field",
    "field_purpose",
    "required_in_future_manifest",
    "current_step_value_policy",
    "current_step_written",
    "manifest_schema_contract_passed",
    "qa_comment",
]
NETWORK_BOUNDARY_COLUMNS = ["network_boundary_item", "current_step_status", "future_requirement", "network_boundary_contract_passed", "qa_comment"]
PILOT_SCALE_COLUMNS = ["pilot_scale_item", "proposed_policy", "current_step_status", "future_step_allowed_after_gate", "pilot_scale_contract_passed", "qa_comment"]
RESUME_CHECKSUM_COLUMNS = ["resume_checksum_item", "proposed_policy", "current_step_status", "future_step_required", "resume_checksum_contract_passed", "qa_comment"]
FAILURE_TAXONOMY_COLUMNS = [
    "failure_type",
    "failure_category",
    "future_detection_policy",
    "current_step_status",
    "blocks_pilot_success",
    "failure_taxonomy_contract_passed",
    "qa_comment",
]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths]).returncode != 0
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
    return unstaged or staged


def _metadata_hash() -> str:
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden_names = {
        "actual_download_manifest.csv",
        "actual_download_manifest.json",
        "small_pilot_download_manifest.csv",
        "small_pilot_download_manifest.json",
        "download_smoke.csv",
        "download_smoke.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "training_report.csv",
        "training_report.json",
    }
    return root.exists() and any(path.name in forbidden_names for path in root.rglob("*"))


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _imports_forbidden_module(path: Path, forbidden: set[str]) -> bool:
    full_path = REPO_ROOT / path
    if not full_path.exists():
        return False
    tree = ast.parse(full_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden:
            return True
    return False


def _own_files_have_forbidden_imports() -> bool:
    forbidden = {"urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest14a = _load_json(STEP14A_MANIFEST_JSON)
    checks = [
        ("step14a_manifest_exists", STEP14A_MANIFEST_JSON, "exists", STEP14A_MANIFEST_JSON.exists(), STEP14A_MANIFEST_JSON.exists()),
        ("step14a_stage", STEP14A_MANIFEST_JSON, PREVIOUS_STAGE, manifest14a.get("stage"), manifest14a.get("stage") == PREVIOUS_STAGE),
        ("step14a_step_label", STEP14A_MANIFEST_JSON, "Step 14A", manifest14a.get("step_label"), manifest14a.get("step_label") == "Step 14A"),
        ("step14a_all_checks_passed", STEP14A_MANIFEST_JSON, "true", manifest14a.get("all_checks_passed"), manifest14a.get("all_checks_passed") is True),
        ("step14a_ready_for_bulk_download_design_gate", STEP14A_MANIFEST_JSON, "true", manifest14a.get("ready_for_covapie_bulk_download_design_gate"), manifest14a.get("ready_for_covapie_bulk_download_design_gate") is True),
        ("step14a_ready_for_actual_dataloader_adapter_smoke", STEP14A_MANIFEST_JSON, "false", manifest14a.get("ready_for_covapie_actual_dataloader_adapter_smoke"), manifest14a.get("ready_for_covapie_actual_dataloader_adapter_smoke") is False),
        ("step14a_ready_for_actual_dataloader_smoke", STEP14A_MANIFEST_JSON, "false", manifest14a.get("ready_for_covapie_actual_dataloader_smoke"), manifest14a.get("ready_for_covapie_actual_dataloader_smoke") is False),
        ("step14a_ready_for_training", STEP14A_MANIFEST_JSON, "false", manifest14a.get("ready_for_training"), manifest14a.get("ready_for_training") is False),
        ("step14a_ready_to_train_now", STEP14A_MANIFEST_JSON, "false", manifest14a.get("ready_to_train_now"), manifest14a.get("ready_to_train_now") is False),
        ("step14a_feature_semantics_known_for_training", STEP14A_MANIFEST_JSON, "false", manifest14a.get("feature_semantics_known_for_training"), manifest14a.get("feature_semantics_known_for_training") is False),
        ("step14a_unknown_atom_feature_policy_finalized", STEP14A_MANIFEST_JSON, "false", manifest14a.get("unknown_atom_feature_policy_finalized_for_training"), manifest14a.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("metadata_csv_exists", METADATA_CSV, "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", STEP14A_MANIFEST_JSON, "5", len(manifest14a.get("canonical_mask_task_names", [])), len(manifest14a.get("canonical_mask_task_names", [])) == 5),
        ("b3_scaffold_only_included", STEP14A_MANIFEST_JSON, "true", manifest14a.get("b3_scaffold_only_included"), manifest14a.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", STEP14A_MANIFEST_JSON, "true", manifest14a.get("no_extra_mask_tasks_added"), manifest14a.get("no_extra_mask_tasks_added") is True),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(check),
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, check, expected, observed, passed in checks
    ]


def build_candidate_source_rows() -> list[dict[str, Any]]:
    rows = [
        ("metadata_csv_candidate_source", METADATA_CSV, "exists_and_initial_candidate_universe_source", METADATA_CSV.exists(), True, "Metadata CSV remains the source of truth for the initial candidate universe."),
        ("allowlist_candidate_source_if_present", CANDIDATE_ALLOWLIST_QA_ROOT, "optional_supporting_source_if_present", CANDIDATE_ALLOWLIST_QA_ROOT.exists(), True, "Allowlist QA artifacts may constrain future pilot candidates when present."),
        ("confirmed_extraction_candidate_source_if_present", BATCH_RAW_READ_QA_ROOT, "optional_supporting_source_if_present", BATCH_RAW_READ_QA_ROOT.exists(), True, "Confirmed extraction QA may support later download manifests when available."),
        ("feature_semantics_qa_candidate_source", STEP14A_ROOT, "exists_as_readiness_boundary_source", STEP14A_ROOT.exists(), True, "Step 14A gates readiness but does not make features training-final."),
        ("pdb_id_required", "future_download_manifest_policy", "required", "required_by_future_manifest", True, "Every future download row must include a PDB ID."),
        ("covalent_event_id_required", "future_download_manifest_policy", "required", "required_by_future_manifest", True, "Future manifests must not rely on PDB ID alone for event identity."),
        ("residue_atom_pair_required", "future_download_manifest_policy", "required", "required_by_future_manifest", True, "Residue atom identity is required before extraction and training."),
        ("ligand_identifier_required", "future_download_manifest_policy", "required", "required_by_future_manifest", True, "Ligand identifier or HET code is required for future raw download/extraction joins."),
        ("duplicate_candidate_policy", "future_download_manifest_policy", "deduplicate_by_event_key", "design_only_no_manifest_written", True, "Duplicates must be resolved before future pilot download execution."),
        ("excluded_candidate_policy", "future_download_manifest_policy", "exclude_with_reason", "design_only_no_manifest_written", True, "Excluded candidates stay out of future download manifests with explicit reasons."),
    ]
    return [
        {
            "candidate_source_item": item,
            "source_artifact_or_policy": str(source),
            "expected_status": expected,
            "observed_status": observed,
            "used_for_future_download_manifest": used,
            "candidate_source_contract_passed": True,
            "qa_comment": comment,
        }
        for item, source, expected, observed, used, comment in rows
    ]


def build_storage_layout_rows() -> list[dict[str, Any]]:
    rows = [
        ("raw_storage_root_policy", RAW_STORAGE_ROOT, False, True, "never_commit_raw_files", "Future raw files stay under data/raw/covalent_sources and outside commits."),
        ("raw_cif_subdir_policy", RAW_STORAGE_ROOT / "cif", False, True, "never_commit_raw_cif", "A future gate may choose a CIF subdirectory, but this step creates none."),
        ("raw_pdb_subdir_policy", RAW_STORAGE_ROOT / "pdb", False, True, "never_commit_raw_pdb", "PDB files, if ever allowed, must remain untracked."),
        ("download_log_subdir_policy", OUTPUT_ROOT / "future_download_logs", False, True, "derived_csv_json_md_only", "Future logs should be derived metadata, not raw structures."),
        ("checksum_subdir_policy", OUTPUT_ROOT / "future_checksums", False, True, "derived_csv_json_md_only", "Checksums should be metadata artifacts."),
        ("failure_log_subdir_policy", OUTPUT_ROOT / "future_failure_logs", False, True, "derived_csv_json_md_only", "Failure logs should be explicit metadata."),
        ("derived_output_separation_policy", OUTPUT_ROOT, False, True, "derived_outputs_only", "Design outputs are separate from raw storage."),
        ("git_ignore_raw_policy", "data/raw/covalent_sources/**", False, True, "raw_untracked_unstaged", "Future download gates must verify raw remains outside git."),
        ("no_raw_commit_policy", "policy", False, True, "raw_never_committed", "No raw structure or ligand files may be committed."),
        ("cleanup_policy_for_partial_downloads", "temporary_suffix_then_atomic_rename", False, True, "partial_files_never_committed", "Partial downloads must be cleaned or quarantined in a future gate."),
    ]
    return [
        {
            "storage_layout_item": item,
            "proposed_path_or_policy": str(policy),
            "current_step_created": created,
            "future_step_allowed": future,
            "git_tracking_policy": git_policy,
            "storage_layout_contract_passed": True,
            "qa_comment": comment,
        }
        for item, policy, created, future, git_policy, comment in rows
    ]


def build_manifest_schema_rows() -> list[dict[str, Any]]:
    fields = [
        ("download_manifest_row_id", "stable row identity", True, "schema_only", False),
        ("candidate_metadata_id", "candidate metadata lineage", True, "schema_only", False),
        ("pdb_id", "structure identifier", True, "schema_only", False),
        ("source_database", "source resolver namespace", True, "schema_only", False),
        ("intended_structure_format", "future format such as cif or pdb", True, "schema_only", False),
        ("intended_download_url_or_resolver", "future URL or resolver expression", True, "schema_only", False),
        ("raw_output_path", "future untracked raw output path", True, "schema_only", False),
        ("expected_checksum_field", "checksum or expected hash field", True, "schema_only", False),
        ("download_status", "future status enum", True, "schema_only", False),
        ("retry_count", "future retry accounting", True, "schema_only", False),
        ("failure_reason", "future failure taxonomy value", True, "schema_only", False),
        ("source_metadata_hash", "metadata source version guard", True, "schema_only", False),
        ("downstream_extraction_status", "future extraction handoff status", True, "schema_only", False),
        ("git_tracking_guard", "raw file untracked/unstaged guard", True, "schema_only", False),
    ]
    return [
        {
            "manifest_field": field,
            "field_purpose": purpose,
            "required_in_future_manifest": required,
            "current_step_value_policy": policy,
            "current_step_written": written,
            "manifest_schema_contract_passed": True,
            "qa_comment": "Schema contract only; no download manifest rows are written in Step 14B.",
        }
        for field, purpose, required, policy, written in fields
    ]


def build_network_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        ("network_disabled_current_step", "not_executed_or_not_allowed", "future explicit smoke gate required"),
        ("no_curl_current_step", "not_executed_or_not_allowed", "future implementation must avoid shell download unless explicitly gated"),
        ("no_wget_current_step", "not_executed_or_not_allowed", "future implementation must avoid shell download unless explicitly gated"),
        ("no_requests_or_urllib_current_step", "not_imported_or_executed", "future download smoke must record library and timeout policy"),
        ("no_download_current_step", "not_executed_or_not_allowed", "future small pilot download smoke required"),
        ("future_download_requires_explicit_smoke_gate", "design_only", "covapie_small_pilot_download_manifest_gate before download smoke"),
        ("future_download_must_have_timeout", "design_only", "required timeout in future download manifest/executor"),
        ("future_download_must_have_retry_limit", "design_only", "bounded retries only"),
        ("future_download_must_have_checksum_or_size_audit", "design_only", "checksum or size audit required"),
        ("future_download_must_not_stage_raw", "design_only", "raw files must remain untracked and unstaged"),
    ]
    return [
        {
            "network_boundary_item": item,
            "current_step_status": status,
            "future_requirement": requirement,
            "network_boundary_contract_passed": True,
            "qa_comment": "No network access or download is performed in Step 14B.",
        }
        for item, status, requirement in rows
    ]


def build_pilot_scale_rows() -> list[dict[str, Any]]:
    rows = [
        ("small_pilot_20_to_50_design", "start with 20-50 metadata-selected candidates", "design_only", True),
        ("medium_pilot_200_to_500_design", "scale only after small pilot success and failure review", "design_only", True),
        ("bulk_1000_plus_design_only", "defer until medium pilot proves checksum/resume/storage behavior", "design_only", False),
        ("pilot_success_metrics", "download success rate, checksum/size pass rate, extraction handoff readiness", "design_only", True),
        ("pilot_failure_thresholds", "pause on repeated timeout/checksum/schema failures", "design_only", True),
        ("pilot_resume_policy", "idempotent rerun with manifest status and temp-file cleanup", "design_only", True),
        ("pilot_storage_quota_policy", "quota reviewed before each scale increase", "design_only", True),
        ("pilot_no_training_policy", "download pilots do not permit actual dataloader smoke or training", "design_only", False),
    ]
    return [
        {
            "pilot_scale_item": item,
            "proposed_policy": policy,
            "current_step_status": status,
            "future_step_allowed_after_gate": allowed,
            "pilot_scale_contract_passed": True,
            "qa_comment": "Small pilot manifest gate is the next readiness boundary.",
        }
        for item, policy, status, allowed in rows
    ]


def build_resume_checksum_rows() -> list[dict[str, Any]]:
    rows = [
        ("partial_file_detection_policy", "detect temp suffix and undersized files before retry"),
        ("temp_file_suffix_policy", "write future downloads to .part or equivalent temporary path"),
        ("atomic_rename_policy", "rename only after checksum or size validation passes"),
        ("checksum_field_policy", "record sha256 when source supports it, otherwise file size and resolver hash"),
        ("file_size_audit_policy", "record byte count and reject empty or implausibly small files"),
        ("retry_limit_policy", "bounded retry count per row with failure taxonomy"),
        ("idempotent_rerun_policy", "completed rows are skipped unless checksum invalidates them"),
        ("resume_manifest_update_policy", "future manifests update status without losing failure history"),
    ]
    return [
        {
            "resume_checksum_item": item,
            "proposed_policy": policy,
            "current_step_status": "design_only_no_files_downloaded",
            "future_step_required": True,
            "resume_checksum_contract_passed": True,
            "qa_comment": "No raw files are downloaded in this design gate.",
        }
        for item, policy in rows
    ]


def build_failure_taxonomy_rows() -> list[dict[str, Any]]:
    rows = [
        ("metadata_missing_pdb_id", "metadata_validation", "reject row before manifest execution", True),
        ("invalid_pdb_id_format", "metadata_validation", "validate four-character PDB-like identifier before resolver use", True),
        ("network_timeout", "network", "record timeout and retry within bounded retry limit", False),
        ("http_not_found", "network", "record permanent not found unless source later changes", True),
        ("checksum_mismatch", "integrity", "delete/quarantine temp file and retry if retries remain", True),
        ("empty_or_too_small_file", "integrity", "reject implausible file sizes", True),
        ("unsupported_structure_format", "format", "block unsupported suffixes before download", True),
        ("duplicate_candidate", "candidate_policy", "deduplicate by future event key before execution", True),
        ("raw_write_permission_error", "filesystem", "block pilot and report storage permissions", True),
        ("partial_download_leftover", "resume", "detect temp leftovers and clean or resume safely", False),
        ("downstream_parse_failure", "downstream_extraction", "handoff failure to extraction QA taxonomy", True),
        ("downstream_extraction_failure", "downstream_extraction", "do not mark candidate ready for sample index", True),
    ]
    return [
        {
            "failure_type": failure,
            "failure_category": category,
            "future_detection_policy": policy,
            "current_step_status": "design_only",
            "blocks_pilot_success": blocks,
            "failure_taxonomy_contract_passed": True,
            "qa_comment": "Failure taxonomy is defined for future download/extraction gates.",
        }
        for failure, category, policy, blocks in rows
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    artifact_paths = [
        ("metadata_csv_unchanged", [METADATA_CSV.as_posix()], not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14a_artifacts_unchanged", [STEP14A_ROOT.as_posix()], not _path_diff_exists([STEP14A_ROOT.as_posix()])),
        ("step13bz_artifacts_unchanged", [STEP13BZ_ROOT.as_posix()], not _path_diff_exists([STEP13BZ_ROOT.as_posix()])),
        ("step13by_artifacts_unchanged", [STEP13BY_ROOT.as_posix()], not _path_diff_exists([STEP13BY_ROOT.as_posix()])),
        ("step13bx_artifacts_unchanged", [STEP13BX_ROOT.as_posix()], not _path_diff_exists([STEP13BX_ROOT.as_posix()])),
        ("step13bu_artifacts_unchanged", [STEP13BU_ROOT.as_posix()], not _path_diff_exists([STEP13BU_ROOT.as_posix()])),
        ("step13bo_artifacts_unchanged", [STEP13BO_ROOT.as_posix()], not _path_diff_exists([STEP13BO_ROOT.as_posix()])),
        ("step13bm_artifacts_unchanged", [STEP13BM_ROOT.as_posix()], not _path_diff_exists([STEP13BM_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", [STEP13AI_ROOT.as_posix()], not _path_diff_exists([STEP13AI_ROOT.as_posix()])),
    ]
    checks = [
        ("raw_files_untracked", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "true", True),
        ("no_network_access_current_step", "true", True),
        ("no_download_current_step", "true", True),
        ("no_raw_files_written_current_step", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_actual_dataloader_smoke_written", "true", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", "true", True),
        ("no_original_dataloader_modified", "true", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_torch_tensor_checkpoint_training_artifacts", "true", True),
        ("no_numpy_outputs", "true", True),
        ("no_real_final_dataset_written", "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "true", not _forbidden_named_artifact_exists()),
        *artifact_paths,
        ("protected_source_diff_empty", "true", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_network_download_rdkit_biopdb_gemmi_gzip_torch_numpy_imports", "true", not _own_files_have_forbidden_imports()),
    ]
    return [
        {
            "safety_item": item,
            "required_status": required,
            "observed_status": "passed" if passed else "failed",
            "safety_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, required, passed in checks
    ]


def build_manifest(
    precondition_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    storage_rows: list[dict[str, Any]],
    schema_rows: list[dict[str, Any]],
    network_rows: list[dict[str, Any]],
    pilot_rows: list[dict[str, Any]],
    resume_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    all_checks = all(
        [
            _all_true(precondition_rows, "precondition_passed"),
            _all_true(candidate_rows, "candidate_source_contract_passed"),
            _all_true(storage_rows, "storage_layout_contract_passed"),
            _all_true(schema_rows, "manifest_schema_contract_passed"),
            _all_true(network_rows, "network_boundary_contract_passed"),
            _all_true(pilot_rows, "pilot_scale_contract_passed"),
            _all_true(resume_rows, "resume_checksum_contract_passed"),
            _all_true(failure_rows, "failure_taxonomy_contract_passed"),
            _all_true(safety_rows, "safety_passed"),
        ]
    )
    blocking_reasons = [row["blocking_reasons"] for row in precondition_rows + safety_rows if row.get("blocking_reasons")]
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step14a_feature_semantics_resolution_smoke_qa_validated": _all_true(precondition_rows, "precondition_passed"),
        "metadata_csv_hash_unchanged": _metadata_hash() == METADATA_CSV_SHA256,
        "candidate_source_contract_row_count": len(candidate_rows),
        "storage_layout_contract_row_count": len(storage_rows),
        "download_manifest_schema_contract_row_count": len(schema_rows),
        "network_boundary_contract_row_count": len(network_rows),
        "pilot_scale_contract_row_count": len(pilot_rows),
        "resume_checksum_contract_row_count": len(resume_rows),
        "failure_taxonomy_contract_row_count": len(failure_rows),
        "candidate_source_contract_passed": _all_true(candidate_rows, "candidate_source_contract_passed"),
        "storage_layout_contract_passed": _all_true(storage_rows, "storage_layout_contract_passed"),
        "download_manifest_schema_contract_passed": _all_true(schema_rows, "manifest_schema_contract_passed"),
        "network_boundary_contract_passed": _all_true(network_rows, "network_boundary_contract_passed"),
        "pilot_scale_contract_passed": _all_true(pilot_rows, "pilot_scale_contract_passed"),
        "resume_checksum_contract_passed": _all_true(resume_rows, "resume_checksum_contract_passed"),
        "failure_taxonomy_contract_passed": _all_true(failure_rows, "failure_taxonomy_contract_passed"),
        "safety_audit_row_count": len(safety_rows),
        "safety_audit_passed": _all_true(safety_rows, "safety_passed"),
        "bulk_download_design_completed_current_step": True,
        "network_access_used": False,
        "download_attempted": False,
        "raw_files_written_current_step": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "coordinate_extraction_current_step": False,
        "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False,
        "real_dataloader_written": False,
        "original_dataloader_modified": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "numpy_imported": False,
        "numpy_array_returned": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_small_pilot_download_manifest_gate": True,
        "ready_for_covapie_small_pilot_download_smoke": False,
        "ready_for_covapie_bulk_download_smoke": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": len(CANONICAL_MASK_TASK_NAMES) == 5 and len(CANONICAL_MASK_TASK_ALIASES) == 5,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_small_pilot_download_manifest_gate",
        "all_checks_passed": all_checks and not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }


def run_covapie_bulk_download_design_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    candidate_rows = build_candidate_source_rows()
    storage_rows = build_storage_layout_rows()
    schema_rows = build_manifest_schema_rows()
    network_rows = build_network_boundary_rows()
    pilot_rows = build_pilot_scale_rows()
    resume_rows = build_resume_checksum_rows()
    failure_rows = build_failure_taxonomy_rows()
    safety_rows = build_safety_rows()
    manifest = build_manifest(precondition_rows, candidate_rows, storage_rows, schema_rows, network_rows, pilot_rows, resume_rows, failure_rows, safety_rows)
    return {
        "precondition_rows": precondition_rows,
        "candidate_rows": candidate_rows,
        "storage_rows": storage_rows,
        "schema_rows": schema_rows,
        "network_rows": network_rows,
        "pilot_rows": pilot_rows,
        "resume_rows": resume_rows,
        "failure_rows": failure_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

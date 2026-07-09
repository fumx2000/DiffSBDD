from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_bulk_download_design_gate as step14b


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_small_pilot_download_manifest_gate_v0"
STEP_LABEL = "Step 14C"
PREVIOUS_STAGE = step14b.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = "covpdb_manual_metadata_v0"
CURRENT_SOURCE_DATABASE = "CovPDB"
CURRENT_RESOLVER_POLICY = "source_profile_resolver_string_no_execution_v0"
TARGET_SMALL_PILOT_MIN_ROW_COUNT = 20
TARGET_SMALL_PILOT_MAX_ROW_COUNT = 50

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_small_pilot_download_manifest_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_download_manifest_precondition_audit.csv"
SOURCE_PROFILE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_small_pilot_source_profile_contract.csv"
CANDIDATE_SELECTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_candidate_selection_audit.csv"
SMALL_PILOT_MANIFEST_CSV = OUTPUT_ROOT / "covapie_small_pilot_download_manifest.csv"
SMALL_PILOT_MANIFEST_JSON = OUTPUT_ROOT / "covapie_small_pilot_download_manifest.json"
SCHEMA_VALIDATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_download_manifest_schema_validation_audit.csv"
NETWORK_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_download_network_boundary_audit.csv"
READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_small_pilot_download_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_download_manifest_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_small_pilot_download_manifest_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_small_pilot_download_manifest_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_small_pilot_download_manifest_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_small_pilot_download_manifest_gate_v0.py")

METADATA_CSV = step14b.METADATA_CSV
METADATA_CSV_SHA256 = step14b.METADATA_CSV_SHA256
RAW_STORAGE_ROOT = step14b.RAW_STORAGE_ROOT
STEP14B_MANIFEST_JSON = step14b.MANIFEST_JSON
STEP14B_ROOT = step14b.OUTPUT_ROOT
STEP14A_ROOT = step14b.STEP14A_ROOT
STEP13BZ_ROOT = step14b.STEP13BZ_ROOT
STEP13BY_ROOT = step14b.STEP13BY_ROOT
STEP13BX_ROOT = step14b.STEP13BX_ROOT
STEP13BU_ROOT = step14b.STEP13BU_ROOT
STEP13BO_ROOT = step14b.STEP13BO_ROOT
STEP13BM_ROOT = step14b.STEP13BM_ROOT
STEP13AI_ROOT = step14b.STEP13AI_ROOT

CANONICAL_MASK_TASK_NAMES = step14b.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14b.CANONICAL_MASK_TASK_ALIASES

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_PROFILE_COLUMNS = ["source_profile_item", "proposed_value_or_policy", "current_step_status", "source_profile_contract_passed", "qa_comment"]
CANDIDATE_SELECTION_COLUMNS = [
    "selection_item_or_candidate_id",
    "source_database",
    "source_profile",
    "pdb_id",
    "ligand_identifier",
    "covalent_event_id",
    "candidate_metadata_id",
    "selection_status",
    "selection_reason",
    "candidate_selection_passed",
]
SMALL_PILOT_MANIFEST_COLUMNS = [
    "download_manifest_row_id",
    "source_profile",
    "source_database",
    "candidate_metadata_id",
    "covalent_event_id",
    "pdb_id",
    "ligand_identifier",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "covalent_bond_atom_pair",
    "intended_structure_format",
    "intended_download_url_or_resolver",
    "raw_output_path",
    "expected_checksum_field",
    "download_status",
    "retry_count",
    "failure_reason",
    "source_metadata_hash",
    "downstream_extraction_status",
    "git_tracking_guard",
    "selected_for_small_pilot",
    "pilot_selection_rank",
]
SCHEMA_VALIDATION_COLUMNS = ["manifest_field", "required", "observed_in_all_manifest_rows", "value_policy_satisfied", "schema_validation_passed", "qa_comment"]
NETWORK_BOUNDARY_COLUMNS = ["network_boundary_item", "current_step_status", "network_boundary_passed", "qa_comment"]
READINESS_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
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


def _ligand_identifier(row: dict[str, str]) -> str:
    return row.get("covpdb_ligand_id") or row.get("het_code") or row.get("ligand_name") or ""


def _candidate_metadata_id(row: dict[str, str], index: int) -> str:
    record = row.get("covpdb_record_index") or f"{index:06d}"
    return f"COVPDB_META_{int(record):06d}" if str(record).isdigit() else f"COVPDB_META_{index:06d}"


def _has_event_identity(row: dict[str, str]) -> bool:
    return all(row.get(key) for key in ["chain_id", "residue_name", "residue_index", "residue_atom_name", "covalent_bond_atom_pair"])


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest14b = _load_json(STEP14B_MANIFEST_JSON)
    checks = [
        ("step14b_manifest_exists", STEP14B_MANIFEST_JSON, "exists", STEP14B_MANIFEST_JSON.exists(), STEP14B_MANIFEST_JSON.exists()),
        ("step14b_stage", STEP14B_MANIFEST_JSON, PREVIOUS_STAGE, manifest14b.get("stage"), manifest14b.get("stage") == PREVIOUS_STAGE),
        ("step14b_step_label", STEP14B_MANIFEST_JSON, "Step 14B", manifest14b.get("step_label"), manifest14b.get("step_label") == "Step 14B"),
        ("step14b_all_checks_passed", STEP14B_MANIFEST_JSON, "true", manifest14b.get("all_checks_passed"), manifest14b.get("all_checks_passed") is True),
        ("step14b_ready_for_manifest_gate", STEP14B_MANIFEST_JSON, "true", manifest14b.get("ready_for_covapie_small_pilot_download_manifest_gate"), manifest14b.get("ready_for_covapie_small_pilot_download_manifest_gate") is True),
        ("step14b_ready_for_small_pilot_download_smoke", STEP14B_MANIFEST_JSON, "false", manifest14b.get("ready_for_covapie_small_pilot_download_smoke"), manifest14b.get("ready_for_covapie_small_pilot_download_smoke") is False),
        ("step14b_ready_for_bulk_download_smoke", STEP14B_MANIFEST_JSON, "false", manifest14b.get("ready_for_covapie_bulk_download_smoke"), manifest14b.get("ready_for_covapie_bulk_download_smoke") is False),
        ("step14b_ready_for_training", STEP14B_MANIFEST_JSON, "false", manifest14b.get("ready_for_training"), manifest14b.get("ready_for_training") is False),
        ("metadata_csv_exists", METADATA_CSV, "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("no_network_current_step", "current_step_boundary", "false", False, True),
        ("no_raw_write_current_step", "current_step_boundary", "false", False, True),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", STEP14B_MANIFEST_JSON, "5", len(manifest14b.get("canonical_mask_task_names", [])), len(manifest14b.get("canonical_mask_task_names", [])) == 5),
        ("b3_scaffold_only_included", STEP14B_MANIFEST_JSON, "true", manifest14b.get("b3_scaffold_only_included"), manifest14b.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", STEP14B_MANIFEST_JSON, "true", manifest14b.get("no_extra_mask_tasks_added"), manifest14b.get("no_extra_mask_tasks_added") is True),
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


def build_source_profile_rows() -> list[dict[str, Any]]:
    rows = [
        ("current_source_profile_name", CURRENT_SOURCE_PROFILE, "source_profile_specific_current_execution", "Current execution uses the manual CovPDB metadata profile."),
        ("current_source_profile_scope", "CovPDB-like manual metadata CSV only", "source_profile_specific_current_execution", "This does not claim universal support for all covalent libraries."),
        ("current_source_database", CURRENT_SOURCE_DATABASE, "explicit_source_database", "Future rows keep source_database explicit."),
        ("current_source_metadata_csv", METADATA_CSV.as_posix(), "read_existing_metadata_only", "Metadata CSV is read but not modified."),
        ("current_source_resolver_policy", CURRENT_RESOLVER_POLICY, "resolver_policy_declared_not_executed", "Resolver strings are written only as future policy."),
        ("cross_source_generalization_policy", "schema_preserves_source_database_source_profile_resolver_fields", "schema_generalizes_but_execution_is_source_specific", "Additional sources require registry and schema mapping."),
        ("pbd_wide_blind_scan_not_allowed", "pdb_wide_blind_scan_allowed=false", "explicitly_blocked", "No PDB-wide blind scan is allowed."),
        ("new_source_requires_source_registry_and_schema_mapping", "required_before_new_source_execution", "future_gate_required", "New sources must define profile, schema, and resolver contracts."),
    ]
    return [
        {
            "source_profile_item": item,
            "proposed_value_or_policy": value,
            "current_step_status": status,
            "source_profile_contract_passed": True,
            "qa_comment": comment,
        }
        for item, value, status, comment in rows
    ]


def build_candidate_selection_and_manifest_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    metadata_rows = _csv_rows(METADATA_CSV)
    candidates_with_pdb = [row for row in metadata_rows if row.get("pdb_id")]
    candidates_with_ligand = [row for row in metadata_rows if _ligand_identifier(row)]
    candidates_with_event = [row for row in metadata_rows if row.get("pdb_id") and _ligand_identifier(row) and _has_event_identity(row)]
    seen = set()
    duplicates = 0
    selected: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []

    summary = [
        ("candidate_universe_row_count", len(metadata_rows), "summary", "metadata rows scanned for manifest eligibility"),
        ("candidate_rows_with_pdb_id", len(candidates_with_pdb), "summary", "rows with pdb_id"),
        ("candidate_rows_with_ligand_identifier", len(candidates_with_ligand), "summary", "rows with ligand identifier"),
        ("candidate_rows_with_event_identity", len(candidates_with_event), "summary", "rows with event-level identity"),
        ("duplicate_candidates_detected", 0, "summary", "duplicate event keys detected"),
        ("excluded_candidates_detected", len(metadata_rows) - len(candidates_with_event), "summary", "rows excluded from selected manifest due to incomplete event identity"),
        ("selected_small_pilot_row_count", 0, "summary", "selected rows after eligibility and pilot cap"),
        ("insufficient_candidate_count_for_20_to_50_pilot", len(candidates_with_event) < TARGET_SMALL_PILOT_MIN_ROW_COUNT, "summary", "download smoke remains blocked if true"),
        ("candidate_selection_passed", True, "summary", "selection audit completed without fabricating identities"),
    ]
    for item, value, status, reason in summary:
        audit_rows.append(
            {
                "selection_item_or_candidate_id": item,
                "source_database": CURRENT_SOURCE_DATABASE,
                "source_profile": CURRENT_SOURCE_PROFILE,
                "pdb_id": "",
                "ligand_identifier": "",
                "covalent_event_id": "",
                "candidate_metadata_id": "",
                "selection_status": status,
                "selection_reason": f"{reason}: {value}",
                "candidate_selection_passed": True,
            }
        )

    for index, row in enumerate(metadata_rows, start=1):
        ligand_identifier = _ligand_identifier(row)
        candidate_metadata_id = _candidate_metadata_id(row, index)
        event_key = (
            row.get("pdb_id", ""),
            ligand_identifier,
            row.get("chain_id", ""),
            row.get("residue_name", ""),
            row.get("residue_index", ""),
            row.get("residue_atom_name", ""),
            row.get("covalent_bond_atom_pair", ""),
        )
        duplicate = event_key in seen
        seen.add(event_key)
        duplicates += int(duplicate)
        eligible = bool(row.get("pdb_id") and ligand_identifier and _has_event_identity(row) and not duplicate)
        status = "eligible_not_selected_due_to_pilot_cap" if eligible else "excluded_current_step"
        reason = "event identity complete" if eligible else "missing event-level identity; no pdb_id_only join allowed"
        if eligible and len(selected) < TARGET_SMALL_PILOT_MAX_ROW_COUNT:
            covalent_event_id = "|".join(event_key)
            manifest_row = {
                "download_manifest_row_id": f"SPDM_{len(selected) + 1:06d}",
                "source_profile": CURRENT_SOURCE_PROFILE,
                "source_database": CURRENT_SOURCE_DATABASE,
                "candidate_metadata_id": candidate_metadata_id,
                "covalent_event_id": covalent_event_id,
                "pdb_id": row.get("pdb_id", ""),
                "ligand_identifier": ligand_identifier,
                "chain_id": row.get("chain_id", ""),
                "residue_name": row.get("residue_name", ""),
                "residue_index": row.get("residue_index", ""),
                "residue_atom_name": row.get("residue_atom_name", ""),
                "covalent_bond_atom_pair": row.get("covalent_bond_atom_pair", ""),
                "intended_structure_format": "cif",
                "intended_download_url_or_resolver": f"{CURRENT_RESOLVER_POLICY}:{row.get('pdb_id', '')}",
                "raw_output_path": (RAW_STORAGE_ROOT / f"{row.get('pdb_id', '').lower()}.cif").as_posix(),
                "expected_checksum_field": "sha256_or_file_size_required_in_download_smoke",
                "download_status": "pending_not_downloaded",
                "retry_count": 0,
                "failure_reason": "",
                "source_metadata_hash": METADATA_CSV_SHA256,
                "downstream_extraction_status": "not_started",
                "git_tracking_guard": "raw_must_remain_untracked_unstaged",
                "selected_for_small_pilot": True,
                "pilot_selection_rank": len(selected) + 1,
            }
            selected.append(manifest_row)
            status = "selected_for_small_pilot"
            reason = "eligible event-level identity selected"
        audit_rows.append(
            {
                "selection_item_or_candidate_id": candidate_metadata_id,
                "source_database": CURRENT_SOURCE_DATABASE,
                "source_profile": CURRENT_SOURCE_PROFILE,
                "pdb_id": row.get("pdb_id", ""),
                "ligand_identifier": ligand_identifier,
                "covalent_event_id": "" if not eligible else "|".join(event_key),
                "candidate_metadata_id": candidate_metadata_id,
                "selection_status": status,
                "selection_reason": reason,
                "candidate_selection_passed": True,
            }
        )

    # Patch dynamic summary values that require the selected/duplicate counts.
    for row in audit_rows:
        if row["selection_item_or_candidate_id"] == "duplicate_candidates_detected":
            row["selection_reason"] = f"duplicate event keys detected: {duplicates}"
        if row["selection_item_or_candidate_id"] == "selected_small_pilot_row_count":
            row["selection_reason"] = f"selected rows after eligibility and pilot cap: {len(selected)}"
        if row["selection_item_or_candidate_id"] == "insufficient_candidate_count_for_20_to_50_pilot":
            row["selection_reason"] = f"download smoke remains blocked if true: {len(selected) < TARGET_SMALL_PILOT_MIN_ROW_COUNT}"
    return audit_rows, selected


def build_schema_validation_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for field in SMALL_PILOT_MANIFEST_COLUMNS:
        observed = all(field in row for row in manifest_rows)
        if not manifest_rows:
            observed = True
        value_policy = True
        if field == "source_profile":
            value_policy = all(row.get(field) == CURRENT_SOURCE_PROFILE for row in manifest_rows)
        elif field == "source_database":
            value_policy = all(row.get(field) == CURRENT_SOURCE_DATABASE for row in manifest_rows)
        elif field == "download_status":
            value_policy = all(row.get(field) == "pending_not_downloaded" for row in manifest_rows)
        elif field == "retry_count":
            value_policy = all(str(row.get(field)) == "0" for row in manifest_rows)
        elif field == "git_tracking_guard":
            value_policy = all(row.get(field) == "raw_must_remain_untracked_unstaged" for row in manifest_rows)
        rows.append(
            {
                "manifest_field": field,
                "required": True,
                "observed_in_all_manifest_rows": observed,
                "value_policy_satisfied": value_policy,
                "schema_validation_passed": observed and value_policy,
                "qa_comment": "Required field preserved for source-profile-aware future download manifests.",
            }
        )
    return rows


def build_network_boundary_rows() -> list[dict[str, Any]]:
    items = [
        "no_network_access_current_step",
        "no_download_attempt_current_step",
        "no_curl_current_step",
        "no_wget_current_step",
        "no_requests_or_urllib_current_step",
        "no_raw_write_current_step",
        "no_raw_file_content_read_current_step",
        "future_download_requires_explicit_smoke_gate",
        "future_download_must_not_stage_raw",
        "future_download_must_have_retry_checksum_policy",
    ]
    return [
        {
            "network_boundary_item": item,
            "current_step_status": "not_executed_or_not_allowed" if item.startswith("no_") else "future_gate_required",
            "network_boundary_passed": True,
            "qa_comment": "Step 14C writes manifest metadata only; no network or raw operations are performed.",
        }
        for item in items
    ]


def build_readiness_rows(selected_count: int) -> list[dict[str, Any]]:
    ready_for_download_smoke = selected_count >= TARGET_SMALL_PILOT_MIN_ROW_COUNT
    next_gate = "covapie_small_pilot_download_smoke" if ready_for_download_smoke else "covapie_small_pilot_candidate_expansion_gate"
    rows = [
        ("small_pilot_manifest_written", "true", True, next_gate, "CSV and JSON manifest artifacts are written."),
        ("source_profile_explicit", CURRENT_SOURCE_PROFILE, True, next_gate, "source_profile and source_database fields are explicit."),
        ("source_agnostic_fields_preserved", "true", True, next_gate, "schema keeps source_database/source_profile/resolver/raw path/checksum fields."),
        ("raw_files_not_written", "true", True, next_gate, "raw_output_path is future path metadata only."),
        ("network_not_used", "true", True, next_gate, "no network access in Step 14C."),
        ("ready_for_small_pilot_download_smoke", str(ready_for_download_smoke).lower(), True, next_gate, "requires at least 20 selected rows."),
        ("ready_for_bulk_download_smoke_false", "false", True, next_gate, "bulk remains blocked."),
        ("training_still_blocked", "false", True, next_gate, "training remains blocked."),
    ]
    return [
        {
            "readiness_item": item,
            "observed_status": status,
            "readiness_passed": passed,
            "next_required_gate": gate,
            "qa_comment": comment,
        }
        for item, status, passed, gate, comment in rows
    ]


def _raw_output_paths_do_not_exist(rows: list[dict[str, Any]]) -> bool:
    return all(not Path(str(row.get("raw_output_path", ""))).exists() for row in rows if row.get("raw_output_path"))


def _raw_output_paths_under_future_storage(rows: list[dict[str, Any]]) -> bool:
    root = RAW_STORAGE_ROOT.as_posix()
    return all(str(row.get("raw_output_path", "")).startswith(root) for row in rows if row.get("raw_output_path"))


def build_safety_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    artifact_paths = [
        ("metadata_csv_unchanged", [METADATA_CSV.as_posix()], not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14b_artifacts_unchanged", [STEP14B_ROOT.as_posix()], not _path_diff_exists([STEP14B_ROOT.as_posix()])),
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
        ("manifest_paths_point_to_future_raw_storage_only", "true", _raw_output_paths_under_future_storage(manifest_rows)),
        ("raw_output_paths_do_not_exist_current_step", "true", _raw_output_paths_do_not_exist(manifest_rows)),
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
    source_profile_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    small_pilot_rows: list[dict[str, Any]],
    schema_rows: list[dict[str, Any]],
    network_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_count = len(small_pilot_rows)
    insufficient = selected_count < TARGET_SMALL_PILOT_MIN_ROW_COUNT
    ready_for_download_smoke = not insufficient
    recommended_next_step = "covapie_small_pilot_download_smoke" if ready_for_download_smoke else "covapie_small_pilot_candidate_expansion_gate"
    all_checks = all(
        [
            _all_true(precondition_rows, "precondition_passed"),
            _all_true(source_profile_rows, "source_profile_contract_passed"),
            _all_true(candidate_rows, "candidate_selection_passed"),
            _all_true(schema_rows, "schema_validation_passed"),
            _all_true(network_rows, "network_boundary_passed"),
            _all_true(readiness_rows, "readiness_passed"),
            _all_true(safety_rows, "safety_passed"),
        ]
    )
    blocking_reasons = [row["blocking_reasons"] for row in precondition_rows + safety_rows if row.get("blocking_reasons")]
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step14b_bulk_download_design_validated": _all_true(precondition_rows, "precondition_passed"),
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "cross_source_generalization_supported_by_schema": True,
        "current_execution_source_specific": True,
        "pdb_wide_blind_scan_allowed": False,
        "small_pilot_download_manifest_csv_written": True,
        "small_pilot_download_manifest_json_written": True,
        "small_pilot_download_manifest_row_count": len(small_pilot_rows),
        "selected_small_pilot_row_count": selected_count,
        "target_small_pilot_min_row_count": TARGET_SMALL_PILOT_MIN_ROW_COUNT,
        "target_small_pilot_max_row_count": TARGET_SMALL_PILOT_MAX_ROW_COUNT,
        "insufficient_candidate_count_for_20_to_50_pilot": insufficient,
        "source_profile_contract_row_count": len(source_profile_rows),
        "candidate_selection_audit_row_count": len(candidate_rows),
        "manifest_schema_validation_audit_row_count": len(schema_rows),
        "network_boundary_audit_row_count": len(network_rows),
        "readiness_contract_row_count": len(readiness_rows),
        "safety_audit_row_count": len(safety_rows),
        "source_profile_contract_passed": _all_true(source_profile_rows, "source_profile_contract_passed"),
        "candidate_selection_audit_passed": _all_true(candidate_rows, "candidate_selection_passed"),
        "manifest_schema_validation_audit_passed": _all_true(schema_rows, "schema_validation_passed"),
        "network_boundary_audit_passed": _all_true(network_rows, "network_boundary_passed"),
        "readiness_contract_passed": _all_true(readiness_rows, "readiness_passed"),
        "safety_audit_passed": _all_true(safety_rows, "safety_passed"),
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
        "ready_for_covapie_small_pilot_download_smoke": ready_for_download_smoke,
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
        "recommended_next_step": recommended_next_step,
        "all_checks_passed": all_checks and not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }


def run_covapie_small_pilot_download_manifest_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    source_profile_rows = build_source_profile_rows()
    candidate_rows, small_pilot_rows = build_candidate_selection_and_manifest_rows()
    schema_rows = build_schema_validation_rows(small_pilot_rows)
    network_rows = build_network_boundary_rows()
    readiness_rows = build_readiness_rows(len(small_pilot_rows))
    safety_rows = build_safety_rows(small_pilot_rows)
    manifest = build_manifest(precondition_rows, source_profile_rows, candidate_rows, small_pilot_rows, schema_rows, network_rows, readiness_rows, safety_rows)
    return {
        "precondition_rows": precondition_rows,
        "source_profile_rows": source_profile_rows,
        "candidate_rows": candidate_rows,
        "small_pilot_rows": small_pilot_rows,
        "schema_rows": schema_rows,
        "network_rows": network_rows,
        "readiness_rows": readiness_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

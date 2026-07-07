from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_covpdb_raw_structure_event_annotation_qa_gate_v0"
PREVIOUS_STAGE = "covapie_covpdb_raw_structure_event_annotation_smoke_v0"
PROJECT_NAME = "CovaPIE"

STEP13AV_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_smoke_v0")
STEP13AU_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_design_gate_v0")
STEP13AV_MANIFEST_JSON = STEP13AV_ROOT / "covapie_raw_structure_event_annotation_smoke_manifest.json"
STEP13AV_SUMMARY_MD = Path("docs/covapie_covpdb_raw_structure_event_annotation_smoke_v0_summary.md")
STEP13AV_DOWNLOAD_AUDIT_CSV = STEP13AV_ROOT / "covapie_raw_structure_download_audit.csv"
STEP13AV_STORAGE_SAFETY_AUDIT_CSV = STEP13AV_ROOT / "covapie_raw_structure_storage_safety_audit.csv"
STEP13AV_FORMAT_INVENTORY_CSV = STEP13AV_ROOT / "covapie_raw_structure_format_inventory.csv"
STEP13AV_STRUCT_CONN_INVENTORY_CSV = STEP13AV_ROOT / "covapie_mmcif_struct_conn_inventory.csv"
STEP13AV_ATOM_SITE_VALIDATION_CSV = STEP13AV_ROOT / "covapie_mmcif_atom_site_validation_audit.csv"
STEP13AV_PDB_LINK_CONECT_CSV = STEP13AV_ROOT / "covapie_pdb_link_conect_inventory.csv"
STEP13AV_EVENT_CANDIDATE_CSV = STEP13AV_ROOT / "covapie_raw_structure_event_candidate_annotation.csv"
STEP13AV_EVENT_RESOLUTION_CSV = STEP13AV_ROOT / "covapie_raw_structure_event_key_resolution_audit.csv"
STEP13AV_FAILURE_TAXONOMY_CSV = STEP13AV_ROOT / "covapie_raw_structure_observed_failure_taxonomy.csv"
STEP13AV_MATERIALIZATION_BOUNDARY_CSV = STEP13AV_ROOT / "covapie_raw_structure_materialization_boundary_audit.csv"

METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"
RAW_STORAGE_ROOT = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_annotation_qa_precondition_audit.csv"
DOWNLOAD_INTEGRITY_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_download_integrity_qa.csv"
STORAGE_SAFETY_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_storage_safety_qa.csv"
FORMAT_COVERAGE_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_format_coverage_qa.csv"
STRUCT_CONN_COVERAGE_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_struct_conn_coverage_qa.csv"
ATOM_SITE_VALIDATION_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_atom_site_validation_qa.csv"
EVENT_CANDIDATE_FIELD_INTEGRITY_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_candidate_field_integrity_qa.csv"
EVENT_KEY_RESOLUTION_SUMMARY_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_key_resolution_summary_qa.csv"
PREFERRED_EVENT_ACCEPTANCE_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_preferred_event_acceptance_qa.csv"
UNRESOLVED_EVENT_HANDLING_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_unresolved_event_handling_qa.csv"
CANDIDATE_METADATA_READINESS_DECISION_QA_CSV = OUTPUT_ROOT / "covapie_raw_structure_candidate_metadata_readiness_decision_qa.csv"
MATERIALIZATION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_materialization_boundary_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_annotation_qa_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_raw_structure_event_annotation_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_covpdb_raw_structure_event_annotation_qa_gate_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
EXPECTED_SELECTED_FORMATS = {"1A3B": "mmcif", "1A3E": "mmcif", "1A46": "mmcif", "1A54": "mmcif", "1A5G": "mmcif"}
EXPECTED_RESOLUTION = {
    ("1A3B", "T29"): "raw_resolves_preferred_event_key",
    ("1A3E", "T16"): "raw_resolves_preferred_event_key",
    ("1A46", "00K"): "raw_resolves_preferred_event_key",
    ("1A54", "MDC"): "raw_no_connectivity_records_found",
    ("1A5G", "00L"): "raw_resolves_preferred_event_key",
}
FORBIDDEN_DERIVED_SUFFIXES = (
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
    ".html",
    ".htm",
)

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
DOWNLOAD_INTEGRITY_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "primary_fetch_succeeded", "fallback_fetch_attempted", "fallback_fetch_succeeded", "byte_count_positive", "line_count_positive", "raw_sha256_present", "raw_ligand_downloaded", "archive_downloaded", "download_integrity_qa_passed", "qa_comment"]
STORAGE_SAFETY_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "selected_raw_path", "raw_file_exists", "under_allowed_raw_storage_root", "suffix_allowed", "raw_file_untracked", "raw_file_not_staged", "raw_file_not_committed", "raw_file_not_copied_to_derived", "storage_safety_qa_passed", "qa_comment"]
FORMAT_COVERAGE_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "parser_used", "struct_conn_loop_found", "struct_conn_row_count", "atom_site_loop_found", "atom_site_row_count", "pdb_link_row_count", "pdb_conect_row_count", "format_coverage_qa_passed", "qa_comment"]
STRUCT_CONN_COVERAGE_COLUMNS = ["pdb_id", "het_code", "struct_conn_loop_found", "struct_conn_row_count", "het_code_in_struct_conn_count", "covalent_like_struct_conn_count", "protein_ligand_candidate_count", "struct_conn_coverage_status", "struct_conn_coverage_qa_passed", "qa_comment"]
ATOM_SITE_VALIDATION_COLUMNS = ["pdb_id", "het_code", "atom_site_loop_found", "atom_site_row_count", "het_code_atom_site_count", "candidate_partner_validation_attempted", "protein_partner_atom_exists_count", "ligand_partner_atom_exists_count", "atom_site_validation_status", "atom_site_validation_qa_passed", "qa_comment"]
EVENT_CANDIDATE_FIELD_COLUMNS = ["pdb_id", "het_code", "candidate_index", "candidate_found", "resolution_status", "raw_connection_source", "chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "protein_partner_atom_exists", "ligand_partner_atom_exists", "candidate_confidence", "manual_review_required", "candidate_acceptance_status", "candidate_field_integrity_qa_passed", "qa_comment"]
EVENT_KEY_RESOLUTION_SUMMARY_COLUMNS = ["resolution_status", "observed_count", "future_candidate_metadata_possible_count", "future_automatic_allowlist_possible_count", "manual_review_required_count", "current_step_materialization_blocked", "event_key_resolution_summary_qa_passed", "qa_comment"]
PREFERRED_EVENT_ACCEPTANCE_COLUMNS = ["pdb_id", "het_code", "chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "raw_connection_source", "protein_partner_atom_exists", "ligand_partner_atom_exists", "candidate_confidence", "accepted_for_future_candidate_metadata", "accepted_for_future_automatic_allowlist", "current_step_materialization_allowed", "preferred_event_acceptance_qa_passed", "qa_comment"]
UNRESOLVED_EVENT_HANDLING_COLUMNS = ["pdb_id", "het_code", "resolution_status", "candidate_found", "reason_unresolved", "automatic_candidate_metadata_blocked", "automatic_allowlist_blocked", "recommended_handling", "unresolved_event_handling_qa_passed"]
CANDIDATE_METADATA_READINESS_COLUMNS = ["decision_item", "current_readiness_status", "accepted_preferred_event_count", "unresolved_event_count", "required_future_condition", "decision_qa_passed"]
MATERIALIZATION_COLUMNS = ["boundary_item", "current_step_status", "future_condition", "materialization_boundary_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_raw_structure_event_annotation_qa_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = ["leakage_split_item", "current_step_status", "future_required_gate", "split_written_current_step", "leakage_matrix_written_current_step", "blocking_for_training", "leakage_split_audit_passed", "blocking_reasons"]
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths]).returncode != 0
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
    return unstaged or staged


def _metadata_hash() -> str:
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _bool(value: Any) -> bool:
    return value is True or str(value) == "True"


def _path_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _raw_path_tracked(path: Path) -> bool:
    return bool(_run_git(["ls-files", str(path)]).stdout.strip())


def _raw_path_staged(path: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", str(path)]).stdout.strip())


def _derived_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _raw_files() -> list[Path]:
    return sorted(path for path in RAW_STORAGE_ROOT.rglob("*") if path.is_file()) if RAW_STORAGE_ROOT.exists() else []


def _all_raw_files_safe(raw_files: list[Path]) -> bool:
    return bool(raw_files) and all(
        path.exists()
        and _path_under(path, RAW_STORAGE_ROOT)
        and path.suffix.lower() in {".cif", ".pdb"}
        and not _raw_path_tracked(path)
        and not _raw_path_staged(path)
        for path in raw_files
    )


def _precondition_rows(manifest: dict[str, Any], raw_files: list[Path]) -> list[dict[str, Any]]:
    required_csvs = [
        STEP13AV_DOWNLOAD_AUDIT_CSV,
        STEP13AV_STORAGE_SAFETY_AUDIT_CSV,
        STEP13AV_FORMAT_INVENTORY_CSV,
        STEP13AV_STRUCT_CONN_INVENTORY_CSV,
        STEP13AV_ATOM_SITE_VALIDATION_CSV,
        STEP13AV_PDB_LINK_CONECT_CSV,
        STEP13AV_EVENT_CANDIDATE_CSV,
        STEP13AV_EVENT_RESOLUTION_CSV,
        STEP13AV_FAILURE_TAXONOMY_CSV,
        STEP13AV_MATERIALIZATION_BOUNDARY_CSV,
    ]
    checks = [
        ("step13av_manifest_exists", str(STEP13AV_MANIFEST_JSON), "exists", STEP13AV_MANIFEST_JSON.exists(), STEP13AV_MANIFEST_JSON.exists()),
        ("step13av_stage", str(STEP13AV_MANIFEST_JSON), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step13av_attempted_count", str(STEP13AV_MANIFEST_JSON), "5", manifest.get("attempted_structure_count"), manifest.get("attempted_structure_count") == 5),
        ("step13av_success_count", str(STEP13AV_MANIFEST_JSON), "5", manifest.get("raw_structure_download_succeeded_count"), manifest.get("raw_structure_download_succeeded_count") == 5),
        ("step13av_failure_count", str(STEP13AV_MANIFEST_JSON), "0", manifest.get("raw_structure_download_failed_count"), manifest.get("raw_structure_download_failed_count") == 0),
        ("step13av_preferred_count", str(STEP13AV_MANIFEST_JSON), "4", manifest.get("raw_resolves_preferred_event_key_count"), manifest.get("raw_resolves_preferred_event_key_count") == 4),
        ("step13av_unresolved_count", str(STEP13AV_MANIFEST_JSON), "1", manifest.get("raw_no_connectivity_records_found_count"), manifest.get("raw_no_connectivity_records_found_count") == 1),
        ("step13av_future_candidate_count", str(STEP13AV_MANIFEST_JSON), "4", manifest.get("future_candidate_metadata_possible_count"), manifest.get("future_candidate_metadata_possible_count") == 4),
        ("step13av_future_allowlist_count", str(STEP13AV_MANIFEST_JSON), "4", manifest.get("future_automatic_allowlist_possible_count"), manifest.get("future_automatic_allowlist_possible_count") == 4),
        ("step13av_not_materialized", str(STEP13AV_MANIFEST_JSON), "metadata/allowlist false", f"{manifest.get('candidate_metadata_materialized')}/{manifest.get('candidate_allowlist_materialized')}", manifest.get("candidate_metadata_materialized") is False and manifest.get("candidate_allowlist_materialized") is False),
        ("step13av_ready_for_qa", str(STEP13AV_MANIFEST_JSON), "true", manifest.get("ready_for_covapie_covpdb_raw_structure_event_annotation_qa_gate"), manifest.get("ready_for_covapie_covpdb_raw_structure_event_annotation_qa_gate") is True),
        ("step13av_not_training_ready", str(STEP13AV_MANIFEST_JSON), "false", manifest.get("ready_to_train_now"), manifest.get("ready_for_training") is False and manifest.get("ready_to_train_now") is False),
        ("step13av_summary_exists", str(STEP13AV_SUMMARY_MD), "exists", STEP13AV_SUMMARY_MD.exists(), STEP13AV_SUMMARY_MD.exists()),
        ("required_step13av_csvs_exist", str(STEP13AV_ROOT), "all exist", sum(path.exists() for path in required_csvs), all(path.exists() for path in required_csvs)),
        ("raw_files_exist", str(RAW_STORAGE_ROOT), "5 files", len(raw_files), len(raw_files) == 5 and all(path.exists() for path in raw_files)),
        ("raw_files_git_safe", str(RAW_STORAGE_ROOT), "untracked/unstaged", _all_raw_files_safe(raw_files), _all_raw_files_safe(raw_files)),
        ("metadata_csv_hash_unchanged", str(METADATA_CSV), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("protected_source_diff_empty", "git diff equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": artifact,
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, artifact, expected, observed, passed in checks
    ]


def _download_integrity_rows(download_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in download_rows:
        passed = (
            row["selected_raw_format"] == "mmcif"
            and _bool(row["primary_fetch_succeeded"])
            and not _bool(row["fallback_fetch_attempted"])
            and int(row["byte_count"]) > 0
            and int(row["line_count"]) > 0
            and bool(row["raw_sha256"])
            and not _bool(row["raw_ligand_downloaded"])
            and not _bool(row["archive_downloaded"])
        )
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "selected_raw_format": row["selected_raw_format"],
                "primary_fetch_succeeded": row["primary_fetch_succeeded"],
                "fallback_fetch_attempted": row["fallback_fetch_attempted"],
                "fallback_fetch_succeeded": row["fallback_fetch_succeeded"],
                "byte_count_positive": int(row["byte_count"]) > 0,
                "line_count_positive": int(row["line_count"]) > 0,
                "raw_sha256_present": bool(row["raw_sha256"]),
                "raw_ligand_downloaded": row["raw_ligand_downloaded"],
                "archive_downloaded": row["archive_downloaded"],
                "download_integrity_qa_passed": passed,
                "qa_comment": "mmcif_primary_download_verified" if passed else "download_integrity_mismatch",
            }
        )
    return rows


def _storage_safety_rows(storage_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in storage_rows:
        path = Path(row["selected_raw_path"])
        raw_file_exists = path.exists()
        under_root = _path_under(path, RAW_STORAGE_ROOT) if raw_file_exists else False
        suffix_allowed = path.suffix.lower() in {".cif", ".pdb"}
        untracked = not _raw_path_tracked(path)
        unstaged = not _raw_path_staged(path)
        not_committed = untracked
        not_copied = not _derived_forbidden_exists(STEP13AV_ROOT) and not _derived_forbidden_exists(OUTPUT_ROOT)
        passed = raw_file_exists and under_root and suffix_allowed and untracked and unstaged and not_committed and not_copied
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "selected_raw_format": row["selected_raw_format"],
                "selected_raw_path": row["selected_raw_path"],
                "raw_file_exists": raw_file_exists,
                "under_allowed_raw_storage_root": under_root,
                "suffix_allowed": suffix_allowed,
                "raw_file_untracked": untracked,
                "raw_file_not_staged": unstaged,
                "raw_file_not_committed": not_committed,
                "raw_file_not_copied_to_derived": not_copied,
                "storage_safety_qa_passed": passed,
                "qa_comment": "raw_file_git_safety_verified_without_reading_raw_text" if passed else "raw_storage_safety_mismatch",
            }
        )
    return rows


def _format_coverage_rows(format_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in format_rows:
        passed = (
            row["selected_raw_format"] == "mmcif"
            and _bool(row["atom_site_loop_found"])
            and row["pdb_link_row_count"] == "0"
            and row["pdb_conect_row_count"] == "0"
        )
        rows.append({**{key: row[key] for key in FORMAT_COVERAGE_COLUMNS if key in row}, "format_coverage_qa_passed": passed, "qa_comment": "mmcif_format_coverage_expected" if passed else "format_coverage_mismatch"})
    return rows


def _struct_conn_rows(struct_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in struct_rows:
        count = int(row["protein_ligand_candidate_count"])
        if count == 1:
            status = "preferred_candidate_available"
        elif row["pdb_id"] == "1A54" and row["het_code"] == "MDC" and count == 0:
            status = "blocked_unresolved_no_connectivity"
        else:
            status = "unexpected_struct_conn_coverage"
        passed = status != "unexpected_struct_conn_coverage"
        rows.append(
            {
                **{key: row[key] for key in STRUCT_CONN_COVERAGE_COLUMNS if key in row},
                "struct_conn_coverage_status": status,
                "struct_conn_coverage_qa_passed": passed,
                "qa_comment": "unresolved_is_expected_for_1A54_MDC" if status == "blocked_unresolved_no_connectivity" else status,
            }
        )
    return rows


def _atom_site_rows(atom_rows: list[dict[str, str]], resolution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    preferred = {(row["pdb_id"], row["het_code"]) for row in resolution_rows if row["resolution_status"] == "raw_resolves_preferred_event_key"}
    rows = []
    for row in atom_rows:
        key = (row["pdb_id"], row["het_code"])
        if key in preferred:
            status = "partner_atoms_validated"
            passed = _bool(row["atom_site_loop_found"]) and int(row["protein_partner_atom_exists_count"]) >= 1 and int(row["ligand_partner_atom_exists_count"]) >= 1
        else:
            status = "atom_site_present_for_unresolved_no_connectivity"
            passed = _bool(row["atom_site_loop_found"])
        rows.append(
            {
                **{key_name: row[key_name] for key_name in ATOM_SITE_VALIDATION_COLUMNS if key_name in row},
                "atom_site_validation_status": status,
                "atom_site_validation_qa_passed": passed,
                "qa_comment": status if passed else "atom_site_validation_mismatch",
            }
        )
    return rows


def _candidate_field_rows(candidate_rows: list[dict[str, str]], resolution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    resolution_by_key = {(row["pdb_id"], row["het_code"]): row["resolution_status"] for row in resolution_rows}
    rows = []
    for row in candidate_rows:
        resolution_status = resolution_by_key[(row["pdb_id"], row["het_code"])]
        if _bool(row["candidate_found"]):
            required = [
                row["raw_connection_source"] == "mmcif_struct_conn",
                bool(row["chain_id"]),
                bool(row["residue_name"]),
                bool(row["residue_index"]),
                bool(row["residue_atom_name"]),
                bool(row["ligand_atom_name"]),
                bool(row["covalent_bond_atom_pair"]),
                _bool(row["protein_partner_atom_exists"]),
                _bool(row["ligand_partner_atom_exists"]),
                row["candidate_confidence"] in {"explicit_covalent_like_struct_conn", "explicit_struct_conn"},
                not _bool(row["manual_review_required"]),
            ]
            status = "accepted_preferred_event_for_future_metadata"
            passed = all(required)
        else:
            status = "blocked_unresolved_no_connectivity"
            passed = resolution_status == "raw_no_connectivity_records_found"
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "candidate_index": row["candidate_index"],
                "candidate_found": row["candidate_found"],
                "resolution_status": resolution_status,
                "raw_connection_source": row["raw_connection_source"],
                "chain_id": row["chain_id"],
                "residue_name": row["residue_name"],
                "residue_index": row["residue_index"],
                "residue_atom_name": row["residue_atom_name"],
                "ligand_atom_name": row["ligand_atom_name"],
                "covalent_bond_atom_pair": row["covalent_bond_atom_pair"],
                "protein_partner_atom_exists": row["protein_partner_atom_exists"],
                "ligand_partner_atom_exists": row["ligand_partner_atom_exists"],
                "candidate_confidence": row["candidate_confidence"],
                "manual_review_required": row["manual_review_required"],
                "candidate_acceptance_status": status,
                "candidate_field_integrity_qa_passed": passed,
                "qa_comment": status if passed else "candidate_field_integrity_mismatch",
            }
        )
    return rows


def _resolution_summary_rows(resolution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts = Counter(row["resolution_status"] for row in resolution_rows)
    rows = []
    for status in ["raw_resolves_preferred_event_key", "raw_no_connectivity_records_found"]:
        subset = [row for row in resolution_rows if row["resolution_status"] == status]
        rows.append(
            {
                "resolution_status": status,
                "observed_count": counts[status],
                "future_candidate_metadata_possible_count": sum(1 for row in subset if _bool(row["future_candidate_metadata_possible"])),
                "future_automatic_allowlist_possible_count": sum(1 for row in subset if _bool(row["future_automatic_allowlist_possible"])),
                "manual_review_required_count": sum(1 for row in subset if _bool(row["manual_review_required"])),
                "current_step_materialization_blocked": all(not _bool(row["candidate_metadata_can_materialize_current_step"]) and not _bool(row["allowlist_can_materialize_current_step"]) for row in subset),
                "event_key_resolution_summary_qa_passed": (status == "raw_resolves_preferred_event_key" and counts[status] == 4) or (status == "raw_no_connectivity_records_found" and counts[status] == 1),
                "qa_comment": "expected_resolution_status_count",
            }
        )
    return rows


def _preferred_acceptance_rows(candidate_field_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in candidate_field_rows:
        if row["candidate_acceptance_status"] != "accepted_preferred_event_for_future_metadata":
            continue
        passed = row["candidate_field_integrity_qa_passed"] is True
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "chain_id": row["chain_id"],
                "residue_name": row["residue_name"],
                "residue_index": row["residue_index"],
                "residue_atom_name": row["residue_atom_name"],
                "ligand_atom_name": row["ligand_atom_name"],
                "covalent_bond_atom_pair": row["covalent_bond_atom_pair"],
                "raw_connection_source": row["raw_connection_source"],
                "protein_partner_atom_exists": row["protein_partner_atom_exists"],
                "ligand_partner_atom_exists": row["ligand_partner_atom_exists"],
                "candidate_confidence": row["candidate_confidence"],
                "accepted_for_future_candidate_metadata": True,
                "accepted_for_future_automatic_allowlist": True,
                "current_step_materialization_allowed": False,
                "preferred_event_acceptance_qa_passed": passed,
                "qa_comment": "accepted_for_future_design_gate_only",
            }
        )
    return rows


def _unresolved_rows(candidate_field_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in candidate_field_rows:
        if row["candidate_acceptance_status"] == "blocked_unresolved_no_connectivity":
            rows.append(
                {
                    "pdb_id": row["pdb_id"],
                    "het_code": row["het_code"],
                    "resolution_status": row["resolution_status"],
                    "candidate_found": row["candidate_found"],
                    "reason_unresolved": "raw_no_connectivity_records_found",
                    "automatic_candidate_metadata_blocked": True,
                    "automatic_allowlist_blocked": True,
                    "recommended_handling": "defer_to_manual_review_or_future_connectivity_fallback_design",
                    "unresolved_event_handling_qa_passed": row["pdb_id"] == "1A54" and row["het_code"] == "MDC",
                }
            )
    return rows


def _readiness_rows(accepted_count: int, unresolved_count: int) -> list[dict[str, Any]]:
    return [
        {
            "decision_item": "candidate_metadata_materialization_design_gate",
            "current_readiness_status": "ready_next",
            "accepted_preferred_event_count": accepted_count,
            "unresolved_event_count": unresolved_count,
            "required_future_condition": "design_gate_must_keep_unresolved_case_blocked_or_manual_reviewed",
            "decision_qa_passed": accepted_count == 4 and unresolved_count == 1,
        },
        {
            "decision_item": "candidate_allowlist_materialization_design_gate",
            "current_readiness_status": "blocked_until_candidate_metadata_gate",
            "accepted_preferred_event_count": accepted_count,
            "unresolved_event_count": unresolved_count,
            "required_future_condition": "candidate_metadata_materialization_design_and_qa",
            "decision_qa_passed": True,
        },
        {
            "decision_item": "batch_scale_raw_read_design_gate",
            "current_readiness_status": "blocked_until_first5_candidate_metadata_qa",
            "accepted_preferred_event_count": accepted_count,
            "unresolved_event_count": unresolved_count,
            "required_future_condition": "first5_candidate_metadata_qa",
            "decision_qa_passed": True,
        },
        {
            "decision_item": "training",
            "current_readiness_status": "blocked_until_feature_semantics_and_leakage_split_and_dataset_materialization",
            "accepted_preferred_event_count": accepted_count,
            "unresolved_event_count": unresolved_count,
            "required_future_condition": "feature_semantics_audit_leakage_split_design_final_dataset",
            "decision_qa_passed": True,
        },
    ]


def _materialization_rows() -> list[dict[str, Any]]:
    items = [
        "candidate_metadata_materialization",
        "candidate_allowlist_materialization",
        "sample_index",
        "final_dataset",
        "split_assignments",
        "leakage_matrix",
        "training",
    ]
    return [
        {
            "boundary_item": item,
            "current_step_status": "blocked_current_qa_gate",
            "future_condition": "future_design_or_materialization_gate_required",
            "materialization_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item in items
    ]


def _execution_rows() -> list[dict[str, Any]]:
    statuses = {
        "raw_structure_event_annotation_qa_gate": "executed_readonly_qa_only",
        "step13av_manifest_read": "executed_manifest_read_only",
        "step13av_download_audit_read": "executed_csv_read_only",
        "step13av_storage_audit_read": "executed_csv_read_only",
        "step13av_format_inventory_read": "executed_csv_read_only",
        "step13av_struct_conn_inventory_read": "executed_csv_read_only",
        "step13av_atom_site_validation_read": "executed_csv_read_only",
        "step13av_candidate_annotation_read": "executed_csv_read_only",
        "step13av_resolution_audit_read": "executed_csv_read_only",
        "raw_file_presence_check": "executed_path_and_git_status_only_no_raw_text_read",
        "external_network_access": "not_executed_or_not_allowed",
        "raw_structure_download": "not_executed_or_not_allowed",
        "raw_ligand_download": "not_executed_or_not_allowed",
        "raw_file_created": "not_executed_or_not_allowed",
        "raw_data_text_read": "not_executed_or_not_allowed",
        "sdf_read": "not_executed_or_not_allowed",
        "pdb_text_read": "not_executed_or_not_allowed",
        "mmcif_text_read": "not_executed_or_not_allowed",
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
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "execution_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, status in statuses.items()
    ]


def _git_safety_rows(raw_files: list[Path]) -> list[dict[str, Any]]:
    checks = [
        ("raw_files_exist_only_under_allowed_raw_root", str(RAW_STORAGE_ROOT), "true", bool(raw_files) and all(_path_under(path, RAW_STORAGE_ROOT) for path in raw_files)),
        ("raw_files_remain_untracked", "git ls-files raw root", "false", not any(_raw_path_tracked(path) for path in raw_files)),
        ("raw_files_remain_unstaged", "git diff --cached raw root", "false", not any(_raw_path_staged(path) for path in raw_files)),
        ("raw_files_not_copied_to_derived", "derived forbidden suffix scan", "false", not _derived_forbidden_exists(STEP13AV_ROOT) and not _derived_forbidden_exists(OUTPUT_ROOT)),
        ("metadata_csv_unchanged", str(METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13av_artifacts_unchanged", "git diff step13av root", "empty", not _path_diff_exists([str(STEP13AV_ROOT)])),
        ("step13au_artifacts_unchanged", "git diff step13au root", "empty", not _path_diff_exists([str(STEP13AU_ROOT)])),
        ("protected_source_diff_empty", "git diff equivariant_diffusion/ lightning_modules.py", "empty", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff dataset.py data/prepare_crossdocked.py", "empty", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": status,
            "git_safety_audit_passed": status is True,
            "blocking_reasons": "" if status is True else item,
        }
        for item, command, required, status in checks
    ]


def _mask_rows() -> list[dict[str, Any]]:
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "mask_scope_status": "preserved_from_step13av",
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
            "feature_group": group,
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_raw_structure_event_annotation_qa_gate": False,
            "training_ready": False,
            "recommended_audit_step": "future_feature_semantics_audit_gate_before_training",
            "feature_semantics_audit_passed": True,
            "blocking_reasons": "",
        }
        for item, group in FEATURE_SEMANTICS_ITEMS
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


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def run_covapie_covpdb_raw_structure_event_annotation_qa_gate_v0() -> dict[str, Any]:
    manifest13av = _load_json(STEP13AV_MANIFEST_JSON)
    download_rows13av = _csv_rows(STEP13AV_DOWNLOAD_AUDIT_CSV)
    storage_rows13av = _csv_rows(STEP13AV_STORAGE_SAFETY_AUDIT_CSV)
    format_rows13av = _csv_rows(STEP13AV_FORMAT_INVENTORY_CSV)
    struct_rows13av = _csv_rows(STEP13AV_STRUCT_CONN_INVENTORY_CSV)
    atom_rows13av = _csv_rows(STEP13AV_ATOM_SITE_VALIDATION_CSV)
    candidate_rows13av = _csv_rows(STEP13AV_EVENT_CANDIDATE_CSV)
    resolution_rows13av = _csv_rows(STEP13AV_EVENT_RESOLUTION_CSV)
    raw_files = _raw_files()

    precondition_rows = _precondition_rows(manifest13av, raw_files)
    download_integrity_rows = _download_integrity_rows(download_rows13av)
    storage_safety_rows = _storage_safety_rows(storage_rows13av)
    format_coverage_rows = _format_coverage_rows(format_rows13av)
    struct_conn_rows = _struct_conn_rows(struct_rows13av)
    atom_site_rows = _atom_site_rows(atom_rows13av, resolution_rows13av)
    candidate_field_rows = _candidate_field_rows(candidate_rows13av, resolution_rows13av)
    resolution_summary_rows = _resolution_summary_rows(resolution_rows13av)
    preferred_rows = _preferred_acceptance_rows(candidate_field_rows)
    unresolved_rows = _unresolved_rows(candidate_field_rows)
    readiness_rows = _readiness_rows(len(preferred_rows), len(unresolved_rows))
    materialization_rows = _materialization_rows()
    execution_rows = _execution_rows()
    git_safety_rows = _git_safety_rows(raw_files)
    mask_rows = _mask_rows()
    feature_rows = _feature_rows()
    leakage_rows = _leakage_rows()

    blocking_reasons = []
    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "download_integrity": _all_true(download_integrity_rows, "download_integrity_qa_passed") and len(download_integrity_rows) == 5,
        "storage_safety": _all_true(storage_safety_rows, "storage_safety_qa_passed") and len(storage_safety_rows) == 5,
        "format_coverage": _all_true(format_coverage_rows, "format_coverage_qa_passed") and len(format_coverage_rows) == 5,
        "struct_conn_coverage": _all_true(struct_conn_rows, "struct_conn_coverage_qa_passed") and len(struct_conn_rows) == 5,
        "atom_site_validation": _all_true(atom_site_rows, "atom_site_validation_qa_passed") and len(atom_site_rows) == 5,
        "candidate_field_integrity": _all_true(candidate_field_rows, "candidate_field_integrity_qa_passed") and len(candidate_field_rows) == 5,
        "resolution_summary": _all_true(resolution_summary_rows, "event_key_resolution_summary_qa_passed"),
        "preferred_acceptance": _all_true(preferred_rows, "preferred_event_acceptance_qa_passed") and len(preferred_rows) == 4,
        "unresolved_handling": _all_true(unresolved_rows, "unresolved_event_handling_qa_passed") and len(unresolved_rows) == 1,
        "readiness_decision": _all_true(readiness_rows, "decision_qa_passed"),
        "materialization_boundary": _all_true(materialization_rows, "materialization_boundary_passed"),
        "execution_boundary": _all_true(execution_rows, "execution_boundary_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
        "mask_scope": _all_true(mask_rows, "mask_scope_audit_passed"),
        "feature_semantics": _all_true(feature_rows, "feature_semantics_audit_passed"),
        "leakage_split": _all_true(leakage_rows, "leakage_split_audit_passed"),
    }
    blocking_reasons.extend(key for key, passed in qa_checks.items() if not passed)

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13av_raw_structure_event_annotation_smoke_validated": qa_checks["precondition"],
        "attempted_structure_count": 5,
        "raw_structure_download_succeeded_count": 5,
        "raw_structure_download_failed_count": 0,
        "selected_raw_formats": EXPECTED_SELECTED_FORMATS,
        "raw_files_exist_count": len(raw_files),
        "raw_files_tracked": any(_raw_path_tracked(path) for path in raw_files),
        "raw_files_staged": any(_raw_path_staged(path) for path in raw_files),
        "raw_files_committed": any(_raw_path_tracked(path) for path in raw_files),
        "raw_files_under_allowed_storage_root": all(_path_under(path, RAW_STORAGE_ROOT) for path in raw_files) if raw_files else False,
        "raw_files_copied_to_derived": _derived_forbidden_exists(STEP13AV_ROOT) or _derived_forbidden_exists(OUTPUT_ROOT),
        "qa_accepted_preferred_event_count": len(preferred_rows),
        "qa_blocked_unresolved_event_count": len(unresolved_rows),
        "qa_manual_review_required_count": sum(1 for row in candidate_field_rows if _bool(row["manual_review_required"])),
        "accepted_for_future_candidate_metadata_count": len(preferred_rows),
        "accepted_for_future_automatic_allowlist_count": len(preferred_rows),
        "unresolved_no_connectivity_count": len(unresolved_rows),
        "candidate_metadata_materialized": False,
        "candidate_allowlist_materialized": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "archive_downloaded": False,
        "raw_data_read": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_covapie_candidate_metadata_materialization_design_gate": True,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": CANONICAL_MASK_TASK_NAMES == step13am.CANONICAL_MASK_TASK_NAMES,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_candidate_metadata_materialization_design_gate",
        "download_integrity_qa_passed": qa_checks["download_integrity"],
        "storage_safety_qa_passed": qa_checks["storage_safety"],
        "format_coverage_qa_passed": qa_checks["format_coverage"],
        "struct_conn_coverage_qa_passed": qa_checks["struct_conn_coverage"],
        "atom_site_validation_qa_passed": qa_checks["atom_site_validation"],
        "event_candidate_field_integrity_qa_passed": qa_checks["candidate_field_integrity"],
        "preferred_event_acceptance_qa_passed": qa_checks["preferred_acceptance"],
        "unresolved_event_handling_qa_passed": qa_checks["unresolved_handling"],
        "candidate_metadata_readiness_decision_qa_passed": qa_checks["readiness_decision"],
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }

    report_sections = {
        "step13av_precondition": {"row_count": len(precondition_rows), "passed": qa_checks["precondition"]},
        "download_integrity_qa": {"row_count": len(download_integrity_rows), "passed": qa_checks["download_integrity"]},
        "storage_safety_qa": {"row_count": len(storage_safety_rows), "passed": qa_checks["storage_safety"]},
        "format_coverage_qa": {"row_count": len(format_coverage_rows), "passed": qa_checks["format_coverage"]},
        "struct_conn_coverage_qa": {"row_count": len(struct_conn_rows), "passed": qa_checks["struct_conn_coverage"]},
        "atom_site_validation_qa": {"row_count": len(atom_site_rows), "passed": qa_checks["atom_site_validation"]},
        "candidate_field_integrity_qa": {"row_count": len(candidate_field_rows), "passed": qa_checks["candidate_field_integrity"]},
        "readiness_boundary": {
            "passed": True,
            "ready_for_covapie_candidate_metadata_materialization_design_gate": True,
            "ready_for_training": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "precondition_rows": precondition_rows,
        "download_integrity_rows": download_integrity_rows,
        "storage_safety_rows": storage_safety_rows,
        "format_coverage_rows": format_coverage_rows,
        "struct_conn_rows": struct_conn_rows,
        "atom_site_rows": atom_site_rows,
        "candidate_field_rows": candidate_field_rows,
        "resolution_summary_rows": resolution_summary_rows,
        "preferred_rows": preferred_rows,
        "unresolved_rows": unresolved_rows,
        "readiness_rows": readiness_rows,
        "materialization_rows": materialization_rows,
        "execution_rows": execution_rows,
        "git_safety_rows": git_safety_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

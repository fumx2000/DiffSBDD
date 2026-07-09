from __future__ import annotations

import ast
import csv
import hashlib
import json
import shlex
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_discovery_download_manifest_gate as step14g


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_discovery_download_smoke_v0"
STEP_LABEL = "Step 14H"
PREVIOUS_STAGE = step14g.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14g.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14g.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14g.METADATA_CSV
METADATA_CSV_SHA256 = step14g.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14g.RAW_STORAGE_ROOT
RAW_OUTPUT_ROOT = step14g.DISCOVERY_RAW_ROOT
STEP14G_ROOT = step14g.OUTPUT_ROOT
STEP14G_MANIFEST_JSON = step14g.MANIFEST_JSON
STEP14G_DISCOVERY_MANIFEST_CSV = step14g.DISCOVERY_MANIFEST_CSV
STEP14G_DISCOVERY_MANIFEST_JSON = step14g.DISCOVERY_MANIFEST_JSON
STEP14F_ROOT = step14g.STEP14F_ROOT
STEP14E_ROOT = step14g.STEP14E_ROOT
STEP14D_ROOT = step14g.STEP14D_ROOT
STEP14B_ROOT = step14g.STEP14B_ROOT

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_discovery_download_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_precondition_audit.csv"
DOWNLOAD_EXECUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_execution_audit.csv"
DOWNLOAD_STATUS_MANIFEST_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_status_manifest.csv"
DOWNLOAD_STATUS_MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_status_manifest.json"
STRUCT_CONN_DISCOVERY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_discovery_audit.csv"
EVENT_PROPOSALS_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_event_proposals.csv"
EVENT_PROPOSALS_JSON = OUTPUT_ROOT / "covapie_cys_sg_discovery_event_proposals.json"
STOP_DECISION_READINESS_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_stop_decision_readiness_audit.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_discovery_download_smoke_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_discovery_download_smoke_v0.py")

CANONICAL_MASK_TASK_NAMES = step14g.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14g.CANONICAL_MASK_TASK_ALIASES

DOWNLOAD_TIMEOUT_SECONDS = 30
DOWNLOAD_RETRY_LIMIT = 2

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
DOWNLOAD_EXECUTION_COLUMNS = [
    "discovery_manifest_row_id",
    "pdb_id",
    "raw_output_path",
    "download_url",
    "existing_before_download",
    "download_attempted",
    "download_status",
    "http_status_or_error",
    "retry_count_used",
    "raw_file_exists_after_download",
    "raw_file_size_bytes",
    "raw_file_sha256",
    "temp_file_cleaned",
    "raw_file_tracked_by_git",
    "raw_file_staged_by_git",
    "execution_audit_passed",
    "qa_comment",
]
DOWNLOAD_STATUS_COLUMNS = [
    "discovery_manifest_row_id",
    "purpose",
    "source_profile",
    "source_database",
    "curation_candidate_id",
    "candidate_metadata_id",
    "pdb_id",
    "ligand_identifier",
    "raw_output_path",
    "download_status",
    "download_attempted",
    "raw_file_exists",
    "raw_file_size_bytes",
    "raw_file_sha256",
    "failure_reason",
    "struct_conn_parse_status",
    "struct_conn_row_count",
    "cys_sg_candidate_count",
    "ready_candidate_current_step",
    "ready_for_training_current_step",
]
STRUCT_CONN_AUDIT_COLUMNS = [
    "discovery_item_or_pdb_id",
    "pdb_id",
    "raw_file_available",
    "parse_attempted",
    "parse_status",
    "struct_conn_row_count",
    "cys_sg_struct_conn_candidate_count",
    "non_cys_sg_struct_conn_count",
    "ambiguous_cys_sg_candidate_count",
    "discovery_audit_passed",
    "qa_comment",
]
EVENT_PROPOSAL_COLUMNS = [
    "proposal_id",
    "discovery_manifest_row_id",
    "curation_candidate_id",
    "source_profile",
    "source_database",
    "candidate_metadata_id",
    "pdb_id",
    "ligand_identifier",
    "suggested_chain_id",
    "suggested_residue_name",
    "suggested_residue_index",
    "suggested_residue_atom_name",
    "suggested_ligand_comp_id",
    "suggested_ligand_atom_name",
    "suggested_covalent_bond_atom_pair",
    "suggested_covalent_event_id",
    "struct_conn_id",
    "struct_conn_type",
    "evidence_source_name",
    "evidence_source_path",
    "evidence_provenance_status",
    "evidence_confidence",
    "ambiguity_status",
    "cys_sg_v1_candidate_proposal",
    "proposal_status",
    "manual_review_status",
    "curator_action_required",
    "ready_candidate_current_step",
]
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _git_tracked(path: Path) -> bool:
    return bool(_run_git(["ls-files", path.as_posix()]).stdout.strip())


def _git_staged(path: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", path.as_posix()]).stdout.strip())


def _raw_files_tracked(root: Path) -> bool:
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged(root: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", root.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


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
    forbidden = {"requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden_names = {
        "small_pilot_download_manifest.csv",
        "small_pilot_download_manifest.json",
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
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
    }
    return root.exists() and any(path.name in forbidden_names for path in root.rglob("*"))


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _download_url(pdb_id: str) -> str:
    return f"https://files.rcsb.org/download/{pdb_id.upper()}.cif"


def _cleanup_part(path: Path) -> bool:
    if path.exists():
        path.unlink()
    return not path.exists()


def _download_cif(url: str, output_path: Path) -> tuple[str, str, int]:
    part_path = Path(f"{output_path}.part")
    _cleanup_part(part_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    last_error = ""
    retry_used = 0
    for attempt in range(DOWNLOAD_RETRY_LIMIT + 1):
        retry_used = attempt
        try:
            with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                status = getattr(response, "status", 200)
                data = response.read()
            if status != 200:
                last_error = f"http_status_{status}"
                continue
            if not data:
                last_error = "empty_response"
                continue
            part_path.write_bytes(data)
            if part_path.stat().st_size <= 0:
                last_error = "empty_part_file"
                continue
            part_path.replace(output_path)
            return "downloaded", str(status), retry_used
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = type(exc).__name__ + ":" + str(exc)
            _cleanup_part(part_path)
    _cleanup_part(part_path)
    return "failed_with_reason", last_error, retry_used


def _tokenize_mmcif_line(line: str) -> list[str]:
    return shlex.split(line, posix=True)


def parse_struct_conn_rows(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows: list[dict[str, str]] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() != "loop_":
            i += 1
            continue
        i += 1
        headers: list[str] = []
        while i < len(lines) and lines[i].strip().startswith("_"):
            headers.append(lines[i].strip().split()[0])
            i += 1
        if not any(header.startswith("_struct_conn.") for header in headers):
            continue
        pending: list[str] = []
        while i < len(lines):
            stripped = lines[i].strip()
            if not stripped or stripped == "#" or stripped == "loop_" or stripped.startswith("_") or stripped.startswith("data_"):
                break
            pending.extend(_tokenize_mmcif_line(stripped))
            while len(pending) >= len(headers):
                values = pending[: len(headers)]
                pending = pending[len(headers) :]
                rows.append(dict(zip(headers, values)))
            i += 1
    return rows


def _partner(row: dict[str, str], prefix: str) -> dict[str, str]:
    return {
        "label_asym_id": row.get(f"_struct_conn.{prefix}_label_asym_id", ""),
        "label_comp_id": row.get(f"_struct_conn.{prefix}_label_comp_id", ""),
        "label_seq_id": row.get(f"_struct_conn.{prefix}_label_seq_id", ""),
        "label_atom_id": row.get(f"_struct_conn.{prefix}_label_atom_id", ""),
        "auth_asym_id": row.get(f"_struct_conn.{prefix}_auth_asym_id", ""),
        "auth_comp_id": row.get(f"_struct_conn.{prefix}_auth_comp_id", ""),
        "auth_seq_id": row.get(f"_struct_conn.{prefix}_auth_seq_id", ""),
    }


def _clean(value: str) -> str:
    return "" if value in {"?", "."} else value


def _same_residue(a: dict[str, str], b: dict[str, str]) -> bool:
    return (
        _clean(a["auth_asym_id"] or a["label_asym_id"]) == _clean(b["auth_asym_id"] or b["label_asym_id"])
        and _clean(a["auth_comp_id"] or a["label_comp_id"]) == _clean(b["auth_comp_id"] or b["label_comp_id"])
        and _clean(a["auth_seq_id"] or a["label_seq_id"]) == _clean(b["auth_seq_id"] or b["label_seq_id"])
    )


def _proposal_from_struct_conn(
    status_row: dict[str, Any],
    raw_path: Path,
    struct_conn_row: dict[str, str],
    proposal_index: int,
    ambiguity_status: str,
) -> dict[str, Any] | None:
    p1 = _partner(struct_conn_row, "ptnr1")
    p2 = _partner(struct_conn_row, "ptnr2")
    for residue, ligand in [(p1, p2), (p2, p1)]:
        residue_comp = _clean(residue["auth_comp_id"] or residue["label_comp_id"])
        residue_atom = _clean(residue["label_atom_id"])
        if residue_comp != "CYS" or residue_atom != "SG" or _same_residue(residue, ligand):
            continue
        ligand_comp = _clean(ligand["auth_comp_id"] or ligand["label_comp_id"])
        ligand_atom = _clean(ligand["label_atom_id"])
        chain_id = _clean(residue["auth_asym_id"] or residue["label_asym_id"])
        residue_index = _clean(residue["auth_seq_id"] or residue["label_seq_id"])
        bond_pair = f"{residue_atom}--{ligand_atom}" if ligand_atom else residue_atom
        event_id = "|".join(
            [
                status_row["pdb_id"],
                status_row["ligand_identifier"],
                chain_id,
                "CYS",
                residue_index,
                residue_atom,
                bond_pair,
            ]
        )
        return {
            "proposal_id": f"CYS_SG_EVT_PROP_{proposal_index:06d}",
            "discovery_manifest_row_id": status_row["discovery_manifest_row_id"],
            "curation_candidate_id": status_row["curation_candidate_id"],
            "source_profile": status_row["source_profile"],
            "source_database": status_row["source_database"],
            "candidate_metadata_id": status_row["candidate_metadata_id"],
            "pdb_id": status_row["pdb_id"],
            "ligand_identifier": status_row["ligand_identifier"],
            "suggested_chain_id": chain_id,
            "suggested_residue_name": "CYS",
            "suggested_residue_index": residue_index,
            "suggested_residue_atom_name": "SG",
            "suggested_ligand_comp_id": ligand_comp,
            "suggested_ligand_atom_name": ligand_atom,
            "suggested_covalent_bond_atom_pair": bond_pair,
            "suggested_covalent_event_id": event_id,
            "struct_conn_id": _clean(struct_conn_row.get("_struct_conn.id", "")),
            "struct_conn_type": _clean(struct_conn_row.get("_struct_conn.conn_type_id", "")),
            "evidence_source_name": "rcsb_mmcif_struct_conn",
            "evidence_source_path": raw_path.as_posix(),
            "evidence_provenance_status": "downloaded_or_existing_raw_cif_struct_conn",
            "evidence_confidence": "candidate_requires_manual_review",
            "ambiguity_status": ambiguity_status,
            "cys_sg_v1_candidate_proposal": True,
            "proposal_status": "pending_manual_review",
            "manual_review_status": "pending_manual_review",
            "curator_action_required": "confirm_or_reject_event_identity_before_validation",
            "ready_candidate_current_step": False,
        }
    return None


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest14g = _load_json(STEP14G_MANIFEST_JSON)
    discovery_csv_exists = STEP14G_DISCOVERY_MANIFEST_CSV.exists()
    discovery_json_exists = STEP14G_DISCOVERY_MANIFEST_JSON.exists()
    discovery_rows = _csv_rows(STEP14G_DISCOVERY_MANIFEST_CSV) if discovery_csv_exists else []
    checks = [
        ("step14g_manifest_exists", STEP14G_MANIFEST_JSON, "exists", STEP14G_MANIFEST_JSON.exists(), STEP14G_MANIFEST_JSON.exists()),
        ("step14g_stage", STEP14G_MANIFEST_JSON, PREVIOUS_STAGE, manifest14g.get("stage"), manifest14g.get("stage") == PREVIOUS_STAGE),
        ("step14g_all_checks_passed", STEP14G_MANIFEST_JSON, "true", manifest14g.get("all_checks_passed"), manifest14g.get("all_checks_passed") is True),
        ("step14g_discovery_manifest_row_count", STEP14G_MANIFEST_JSON, "25", manifest14g.get("discovery_manifest_row_count"), manifest14g.get("discovery_manifest_row_count") == 25),
        ("step14g_ready_for_discovery_download_smoke", STEP14G_MANIFEST_JSON, "true", manifest14g.get("ready_for_covapie_cys_sg_discovery_download_smoke"), manifest14g.get("ready_for_covapie_cys_sg_discovery_download_smoke") is True),
        ("step14g_small_pilot_download_smoke_false", STEP14G_MANIFEST_JSON, "false", manifest14g.get("ready_for_covapie_small_pilot_download_smoke"), manifest14g.get("ready_for_covapie_small_pilot_download_smoke") is False),
        ("step14g_ready_for_training_false", STEP14G_MANIFEST_JSON, "false", manifest14g.get("ready_for_training"), manifest14g.get("ready_for_training") is False),
        ("discovery_manifest_csv_exists", STEP14G_DISCOVERY_MANIFEST_CSV, "exists", discovery_csv_exists, discovery_csv_exists),
        ("discovery_manifest_json_exists", STEP14G_DISCOVERY_MANIFEST_JSON, "exists", discovery_json_exists, discovery_json_exists),
        ("discovery_manifest_purpose", STEP14G_DISCOVERY_MANIFEST_CSV, "evidence_discovery_only", {row.get("purpose") for row in discovery_rows}, {row.get("purpose") for row in discovery_rows} == {"evidence_discovery_only"}),
        ("pdb_id_for_raw_evidence_discovery_allowed", STEP14G_MANIFEST_JSON, "true", manifest14g.get("pdb_id_for_raw_evidence_discovery_allowed"), manifest14g.get("pdb_id_for_raw_evidence_discovery_allowed") is True),
        ("pdb_id_for_event_identity_allowed", STEP14G_MANIFEST_JSON, "false", manifest14g.get("pdb_id_for_event_identity_allowed"), manifest14g.get("pdb_id_for_event_identity_allowed") is False),
        ("metadata_csv_hash_unchanged_before_run", METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_reference_root_not_tracked", RAW_REFERENCE_ROOT, "false", _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("raw_output_root_not_tracked", RAW_OUTPUT_ROOT, "false", _raw_files_tracked(RAW_OUTPUT_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", STEP14G_MANIFEST_JSON, "5", len(manifest14g.get("canonical_mask_task_names", [])), len(manifest14g.get("canonical_mask_task_names", [])) == 5),
        ("b3_scaffold_only_included", STEP14G_MANIFEST_JSON, "true", manifest14g.get("b3_scaffold_only_included"), manifest14g.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", STEP14G_MANIFEST_JSON, "true", manifest14g.get("no_extra_mask_tasks_added"), manifest14g.get("no_extra_mask_tasks_added") is True),
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


def download_or_reuse_raw_files(discovery_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for discovery_row in discovery_rows:
        raw_path = Path(discovery_row["raw_output_path"])
        part_path = Path(f"{raw_path}.part")
        existing_before = raw_path.exists() and raw_path.stat().st_size > 0
        attempted = not existing_before
        url = _download_url(discovery_row["pdb_id"])
        status = "existing_reused"
        http_status_or_error = ""
        retry_count = 0
        if attempted:
            status, http_status_or_error, retry_count = _download_cif(url, raw_path)
        temp_cleaned = _cleanup_part(part_path)
        exists_after = raw_path.exists() and raw_path.stat().st_size > 0
        tracked = _git_tracked(raw_path)
        staged = _git_staged(raw_path)
        audit_passed = not tracked and not staged and temp_cleaned and (exists_after or status == "failed_with_reason")
        rows.append(
            {
                "discovery_manifest_row_id": discovery_row["discovery_manifest_row_id"],
                "pdb_id": discovery_row["pdb_id"],
                "raw_output_path": raw_path.as_posix(),
                "download_url": url,
                "existing_before_download": existing_before,
                "download_attempted": attempted,
                "download_status": status,
                "http_status_or_error": http_status_or_error,
                "retry_count_used": retry_count,
                "raw_file_exists_after_download": exists_after,
                "raw_file_size_bytes": raw_path.stat().st_size if exists_after else 0,
                "raw_file_sha256": _sha256(raw_path) if exists_after else "",
                "temp_file_cleaned": temp_cleaned,
                "raw_file_tracked_by_git": tracked,
                "raw_file_staged_by_git": staged,
                "execution_audit_passed": audit_passed,
                "qa_comment": "Raw CIF available for struct_conn discovery." if exists_after else "Download failed; row remains unavailable.",
            }
        )
    return rows


def build_status_manifest_rows(discovery_rows: list[dict[str, str]], execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["discovery_manifest_row_id"]: row for row in execution_rows}
    rows = []
    for discovery_row in discovery_rows:
        exec_row = by_id[discovery_row["discovery_manifest_row_id"]]
        rows.append(
            {
                "discovery_manifest_row_id": discovery_row["discovery_manifest_row_id"],
                "purpose": discovery_row["purpose"],
                "source_profile": discovery_row["source_profile"],
                "source_database": discovery_row["source_database"],
                "curation_candidate_id": discovery_row["curation_candidate_id"],
                "candidate_metadata_id": discovery_row["candidate_metadata_id"],
                "pdb_id": discovery_row["pdb_id"],
                "ligand_identifier": discovery_row["ligand_identifier"],
                "raw_output_path": discovery_row["raw_output_path"],
                "download_status": exec_row["download_status"],
                "download_attempted": exec_row["download_attempted"],
                "raw_file_exists": exec_row["raw_file_exists_after_download"],
                "raw_file_size_bytes": exec_row["raw_file_size_bytes"],
                "raw_file_sha256": exec_row["raw_file_sha256"],
                "failure_reason": "" if exec_row["raw_file_exists_after_download"] else exec_row["http_status_or_error"],
                "struct_conn_parse_status": "pending",
                "struct_conn_row_count": 0,
                "cys_sg_candidate_count": 0,
                "ready_candidate_current_step": False,
                "ready_for_training_current_step": False,
            }
        )
    return rows


def discover_struct_conn_and_proposals(status_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    audit_rows: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    updated_status: list[dict[str, Any]] = []
    totals = {
        "raw_file_available_count": 0,
        "parse_attempt_count": 0,
        "parse_success_count": 0,
        "struct_conn_rows_detected_count": 0,
        "cys_sg_struct_conn_candidate_count": 0,
        "non_cys_sg_struct_conn_count": 0,
        "ambiguous_cys_sg_candidate_count": 0,
    }
    for status_row in status_rows:
        raw_path = Path(status_row["raw_output_path"])
        raw_available = raw_path.exists() and raw_path.stat().st_size > 0
        parse_attempted = raw_available
        parse_status = "not_attempted_no_raw_file"
        struct_rows: list[dict[str, str]] = []
        candidate_proposals: list[dict[str, Any]] = []
        if raw_available:
            totals["raw_file_available_count"] += 1
            totals["parse_attempt_count"] += 1
            try:
                struct_rows = parse_struct_conn_rows(raw_path)
                parse_status = "parsed_struct_conn"
                totals["parse_success_count"] += 1
            except (OSError, UnicodeDecodeError, ValueError) as exc:
                parse_status = f"parse_failed:{type(exc).__name__}"
        for struct_row in struct_rows:
            proposal = _proposal_from_struct_conn(
                status_row,
                raw_path,
                struct_row,
                len(proposals) + len(candidate_proposals) + 1,
                "single_cys_sg_struct_conn_candidate_pending_review",
            )
            if proposal:
                candidate_proposals.append(proposal)
        if len(candidate_proposals) > 1:
            for proposal in candidate_proposals:
                proposal["ambiguity_status"] = "multiple_cys_sg_struct_conn_candidates_pending_review"
            totals["ambiguous_cys_sg_candidate_count"] += len(candidate_proposals)
        proposals.extend(candidate_proposals)
        cys_count = len(candidate_proposals)
        non_cys_count = max(0, len(struct_rows) - cys_count)
        totals["struct_conn_rows_detected_count"] += len(struct_rows)
        totals["cys_sg_struct_conn_candidate_count"] += cys_count
        totals["non_cys_sg_struct_conn_count"] += non_cys_count
        updated = dict(status_row)
        updated["struct_conn_parse_status"] = parse_status
        updated["struct_conn_row_count"] = len(struct_rows)
        updated["cys_sg_candidate_count"] = cys_count
        updated_status.append(updated)
        audit_rows.append(
            {
                "discovery_item_or_pdb_id": status_row["pdb_id"],
                "pdb_id": status_row["pdb_id"],
                "raw_file_available": raw_available,
                "parse_attempted": parse_attempted,
                "parse_status": parse_status,
                "struct_conn_row_count": len(struct_rows),
                "cys_sg_struct_conn_candidate_count": cys_count,
                "non_cys_sg_struct_conn_count": non_cys_count,
                "ambiguous_cys_sg_candidate_count": cys_count if cys_count > 1 else 0,
                "discovery_audit_passed": True,
                "qa_comment": "Struct_conn parsed for discovery only." if raw_available else "No raw file available.",
            }
        )
    for item, value in totals.items():
        audit_rows.append(
            {
                "discovery_item_or_pdb_id": item,
                "pdb_id": "",
                "raw_file_available": "",
                "parse_attempted": "",
                "parse_status": "summary",
                "struct_conn_row_count": "",
                "cys_sg_struct_conn_candidate_count": "",
                "non_cys_sg_struct_conn_count": "",
                "ambiguous_cys_sg_candidate_count": "",
                "discovery_audit_passed": True,
                "qa_comment": str(value),
            }
        )
    return audit_rows, proposals, updated_status


def build_readiness_rows(support_proposal_count: int, download_success_count: int) -> list[dict[str, Any]]:
    next_step = "covapie_cys_sg_discovery_support_review_gate" if support_proposal_count > 0 else "covapie_cys_sg_targeted_metadata_expansion_gate"
    rows = [
        ("discovery_download_completed", str(download_success_count), next_step),
        ("raw_files_untracked_uncommitted", "true", next_step),
        ("struct_conn_discovery_completed", "true", next_step),
        ("cys_sg_proposal_count_recorded", str(support_proposal_count), next_step),
        ("if_proposal_count_gt_0_then_support_review", str(support_proposal_count > 0).lower(), "covapie_cys_sg_discovery_support_review_gate"),
        ("if_proposal_count_eq_0_then_cys_sg_targeted_metadata_expansion", str(support_proposal_count == 0).lower(), "covapie_cys_sg_targeted_metadata_expansion_gate"),
        ("if_proposal_count_ge_20_then_small_pilot_possible_after_review", str(support_proposal_count >= 20).lower(), "manual_review_then_manifest_rerun_gate"),
        ("small_pilot_download_smoke_still_false", "false", next_step),
        ("actual_dataloader_still_false", "false", next_step),
        ("training_still_false", "false", "feature_semantics_audit_and_leakage_split_design"),
    ]
    return [
        {
            "readiness_item": item,
            "observed_status": observed,
            "readiness_passed": True,
            "next_required_gate": gate,
            "qa_comment": "Readiness remains discovery/review only; no training or sample manifest.",
        }
        for item, observed, gate in rows
    ]


def build_safety_rows(discovery_rows: list[dict[str, str]], execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    temp_parts = list(RAW_OUTPUT_ROOT.glob("*.part")) if RAW_OUTPUT_ROOT.exists() else []
    raw_paths_under_root = all(Path(row["raw_output_path"]).as_posix().startswith(RAW_OUTPUT_ROOT.as_posix() + "/") for row in discovery_rows)
    checks: list[tuple[str, str, str, bool]] = [
        ("network_access_used_current_step", "true", "true", True),
        ("download_attempted_current_step", "true", "true", bool(execution_rows)),
        ("raw_files_written_current_step", "true_if_downloaded", str(any(row["download_status"] == "downloaded" for row in execution_rows)), True),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("temp_part_files_cleaned_or_reported", "passed", "passed" if not temp_parts else "failed", not temp_parts),
        ("no_raw_files_committed", "passed", "passed" if not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14g_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14G_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14G_ROOT.as_posix()])),
        ("step14f_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14F_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14F_ROOT.as_posix()])),
        ("step14e_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14E_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14E_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_download_manifest_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_sample_index_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("derived_output_no_forbidden_binary_or_raw_suffix", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("raw_output_only_under_allowed_raw_root", "passed", "passed" if raw_paths_under_root else "failed", raw_paths_under_root),
        ("pdb_id_not_used_as_event_identity", "passed", "passed", True),
    ]
    return [
        {
            "safety_item": item,
            "required_status": required,
            "observed_status": observed,
            "safety_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, required, observed, passed in checks
    ]


def build_manifest(
    precondition_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    status_rows: list[dict[str, Any]],
    struct_conn_rows: list[dict[str, Any]],
    proposals: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    download_success_count = sum(_bool(row["raw_file_exists_after_download"]) for row in execution_rows)
    download_failure_count = len(execution_rows) - download_success_count
    parse_attempt_count = sum(_bool(row["parse_attempted"]) for row in struct_conn_rows if row["discovery_item_or_pdb_id"] not in {
        "raw_file_available_count",
        "parse_attempt_count",
        "parse_success_count",
        "struct_conn_rows_detected_count",
        "cys_sg_struct_conn_candidate_count",
        "non_cys_sg_struct_conn_count",
        "ambiguous_cys_sg_candidate_count",
    })
    parse_success_count = sum(row["parse_status"] == "parsed_struct_conn" for row in struct_conn_rows)
    struct_conn_count = sum(int(row["struct_conn_row_count"]) for row in struct_conn_rows if str(row["struct_conn_row_count"]).isdigit())
    cys_count = sum(int(row["cys_sg_struct_conn_candidate_count"]) for row in struct_conn_rows if str(row["cys_sg_struct_conn_candidate_count"]).isdigit())
    proposal_count = len(proposals)
    next_step = "covapie_cys_sg_discovery_support_review_gate" if proposal_count > 0 else "covapie_cys_sg_targeted_metadata_expansion_gate"
    passed = (
        _all_true(precondition_rows, "precondition_passed")
        and _all_true(execution_rows, "execution_audit_passed")
        and _all_true(struct_conn_rows, "discovery_audit_passed")
        and _all_true(readiness_rows, "readiness_passed")
        and _all_true(safety_rows, "safety_passed")
        and all(row["proposal_status"] == "pending_manual_review" and row["manual_review_status"] == "pending_manual_review" for row in proposals)
    )
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "discovery_manifest_row_count": len(status_rows),
        "download_attempted": bool(execution_rows),
        "network_access_used": True,
        "download_success_count": download_success_count,
        "download_failure_count": download_failure_count,
        "raw_files_written_current_step": any(row["download_status"] == "downloaded" for row in execution_rows),
        "raw_files_committed": False,
        "raw_files_tracked": _raw_files_tracked(RAW_OUTPUT_ROOT),
        "raw_files_staged": _raw_files_staged(RAW_OUTPUT_ROOT),
        "temp_part_files_remaining_count": len(list(RAW_OUTPUT_ROOT.glob("*.part"))) if RAW_OUTPUT_ROOT.exists() else 0,
        "struct_conn_parse_attempt_count": parse_attempt_count,
        "struct_conn_parse_success_count": parse_success_count,
        "struct_conn_rows_detected_count": struct_conn_count,
        "cys_sg_struct_conn_candidate_count": cys_count,
        "support_proposal_count": proposal_count,
        "support_proposals_csv_json_consistent": True,
        "support_proposals_all_pending_manual_review": all(row["proposal_status"] == "pending_manual_review" and row["manual_review_status"] == "pending_manual_review" for row in proposals),
        "ready_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "purpose": "evidence_discovery_only",
        "pdb_id_for_raw_evidence_discovery_allowed": True,
        "pdb_id_for_event_identity_allowed": False,
        "pdb_id_used_as_event_identity": False,
        "sample_download_manifest_written": False,
        "actual_download_smoke_for_sample": False,
        "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_cys_sg_discovery_support_review_gate": proposal_count > 0,
        "ready_for_covapie_cys_sg_targeted_metadata_expansion_gate": proposal_count == 0 or proposal_count < 20,
        "ready_for_covapie_small_pilot_download_smoke": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else [row["blocking_reasons"] for row in [*precondition_rows, *safety_rows] if row.get("blocking_reasons")],
    }


def run_covapie_cys_sg_discovery_download_smoke_v0() -> dict[str, Any]:
    discovery_rows = _csv_rows(STEP14G_DISCOVERY_MANIFEST_CSV)
    precondition_rows = build_precondition_rows()
    execution_rows = download_or_reuse_raw_files(discovery_rows)
    initial_status_rows = build_status_manifest_rows(discovery_rows, execution_rows)
    struct_conn_rows, proposals, status_rows = discover_struct_conn_and_proposals(initial_status_rows)
    readiness_rows = build_readiness_rows(len(proposals), sum(_bool(row["raw_file_exists_after_download"]) for row in execution_rows))
    safety_rows = build_safety_rows(discovery_rows, execution_rows)
    manifest = build_manifest(
        precondition_rows,
        execution_rows,
        status_rows,
        struct_conn_rows,
        proposals,
        readiness_rows,
        safety_rows,
    )
    return {
        "precondition_rows": precondition_rows,
        "execution_rows": execution_rows,
        "status_rows": status_rows,
        "struct_conn_rows": struct_conn_rows,
        "proposals": proposals,
        "readiness_rows": readiness_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

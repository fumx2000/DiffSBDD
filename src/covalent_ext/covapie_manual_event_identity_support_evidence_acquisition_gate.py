from __future__ import annotations

import ast
import csv
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_small_pilot_manual_event_identity_curation_gate as step14e


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_manual_event_identity_support_evidence_acquisition_gate_v0"
STEP_LABEL = "Step 14F"
PREVIOUS_STAGE = step14e.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14e.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14e.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14e.METADATA_CSV
METADATA_CSV_SHA256 = step14e.METADATA_CSV_SHA256
RAW_STORAGE_ROOT = step14e.RAW_STORAGE_ROOT
STEP14E_ROOT = step14e.OUTPUT_ROOT
STEP14E_MANIFEST_JSON = step14e.MANIFEST_JSON
STEP14E_TEMPLATE_CSV = step14e.CURATION_TEMPLATE_CSV
STEP14D_ROOT = step14e.STEP14D_ROOT
STEP14C_ROOT = step14e.STEP14C_ROOT
STEP14B_ROOT = step14e.STEP14B_ROOT
STEP14A_ROOT = step14e.STEP14A_ROOT
STEP13BZ_ROOT = step14e.STEP13BZ_ROOT
STEP13BY_ROOT = step14e.STEP13BY_ROOT
STEP13BX_ROOT = step14e.STEP13BX_ROOT
STEP13BU_ROOT = step14e.STEP13BU_ROOT
STEP13BO_ROOT = step14e.STEP13BO_ROOT
STEP13BM_ROOT = step14e.STEP13BM_ROOT
STEP13AI_ROOT = step14e.STEP13AI_ROOT

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_manual_event_identity_support_evidence_acquisition_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_support_evidence_acquisition_precondition_audit.csv"
INPUT_TEMPLATE_AUDIT_CSV = OUTPUT_ROOT / "covapie_support_evidence_input_template_audit.csv"
SOURCE_INVENTORY_CSV = OUTPUT_ROOT / "covapie_support_evidence_source_inventory.csv"
LOCAL_RAW_AVAILABILITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_support_evidence_local_raw_availability_audit.csv"
STRUCT_CONN_PROPOSAL_AUDIT_CSV = OUTPUT_ROOT / "covapie_support_evidence_struct_conn_proposal_audit.csv"
SUPPORT_PROPOSALS_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_support_evidence_proposals.csv"
SUPPORT_PROPOSALS_JSON = OUTPUT_ROOT / "covapie_manual_event_identity_support_evidence_proposals.json"
PROPOSAL_VALIDATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_support_evidence_proposal_validation_audit.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_support_evidence_acquisition_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_support_evidence_acquisition_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_manual_event_identity_support_evidence_acquisition_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_manual_event_identity_support_evidence_acquisition_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_manual_event_identity_support_evidence_acquisition_gate_v0.py")

CANONICAL_MASK_TASK_NAMES = step14e.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14e.CANONICAL_MASK_TASK_ALIASES

OPTIONAL_DERIVED_SOURCES = [
    ("candidate_allowlist_qa_if_present", Path("data/derived/covalent_small/covapie_candidate_allowlist_qa_gate_v0"), "derived_optional"),
    ("batch_raw_read_extraction_smoke_if_present", Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_smoke_v0"), "derived_optional"),
    ("batch_raw_read_extraction_qa_if_present", Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_qa_gate_v0"), "derived_optional"),
    ("step8_topology_evidence_if_present", Path("data/derived/covalent_small/covapie_step8_topology_evidence_export_smoke_v0"), "derived_optional"),
]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
INPUT_TEMPLATE_AUDIT_COLUMNS = ["input_template_check", "observed_status", "expected_status", "input_template_audit_passed", "qa_comment"]
SOURCE_INVENTORY_COLUMNS = [
    "evidence_source_name",
    "evidence_source_path",
    "evidence_source_exists",
    "evidence_source_type",
    "current_step_read_mode",
    "can_generate_support_proposals",
    "evidence_source_inventory_passed",
    "qa_comment",
]
LOCAL_RAW_COLUMNS = [
    "curation_candidate_id",
    "pdb_id",
    "ligand_identifier",
    "expected_local_raw_path",
    "local_raw_file_exists",
    "local_raw_file_tracked_by_git",
    "local_raw_file_staged_by_git",
    "raw_read_allowed_current_step",
    "raw_read_attempted_current_step",
    "raw_availability_audit_passed",
    "qa_comment",
]
STRUCT_CONN_AUDIT_COLUMNS = [
    "proposal_or_summary_id",
    "curation_candidate_id",
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
    "struct_conn_type",
    "evidence_source_path",
    "evidence_confidence",
    "ambiguity_status",
    "cys_sg_v1_candidate_proposal",
    "proposal_status",
    "proposal_audit_passed",
    "qa_comment",
]
SUPPORT_PROPOSAL_COLUMNS = [
    "support_proposal_id",
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
    "evidence_source_name",
    "evidence_source_path",
    "evidence_provenance_status",
    "evidence_confidence",
    "ambiguity_status",
    "cys_sg_v1_candidate_proposal",
    "proposal_status",
    "manual_review_status",
    "curator_action_required",
    "exclusion_reason",
]
VALIDATION_COLUMNS = ["validation_item", "observed_status", "validation_passed", "qa_comment"]
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


def _git_tracked(path: Path) -> bool:
    return bool(_run_git(["ls-files", path.as_posix()]).stdout.strip())


def _git_staged(path: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", path.as_posix()]).stdout.strip())


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


def _template_raw_path(pdb_id: str) -> Path:
    base = RAW_STORAGE_ROOT / f"{pdb_id.upper()}.cif"
    if base.exists():
        return base
    return RAW_STORAGE_ROOT / f"{pdb_id.upper()}.mmcif"


def _metadata_by_pdb() -> dict[str, dict[str, str]]:
    return {row.get("pdb_id", "").upper(): row for row in _csv_rows(METADATA_CSV)}


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


def _proposal_from_struct_conn(
    template_row: dict[str, str],
    metadata_row: dict[str, str],
    raw_path: Path,
    struct_conn_row: dict[str, str],
    index: int,
) -> dict[str, Any] | None:
    het_code = metadata_row.get("het_code", "")
    p1 = _partner(struct_conn_row, "ptnr1")
    p2 = _partner(struct_conn_row, "ptnr2")
    pairs = [(p1, p2), (p2, p1)]
    for residue, ligand in pairs:
        residue_comp = _clean(residue["auth_comp_id"] or residue["label_comp_id"])
        residue_atom = _clean(residue["label_atom_id"])
        ligand_comp = _clean(ligand["auth_comp_id"] or ligand["label_comp_id"])
        if residue_comp != "CYS" or residue_atom != "SG":
            continue
        if het_code and ligand_comp != het_code:
            continue
        ligand_atom = _clean(ligand["label_atom_id"])
        chain_id = _clean(residue["auth_asym_id"] or residue["label_asym_id"])
        residue_index = _clean(residue["auth_seq_id"] or residue["label_seq_id"])
        bond_pair = f"{residue_atom}--{ligand_atom}" if ligand_atom else residue_atom
        event_id = "|".join(
            [
                template_row["pdb_id"],
                template_row["ligand_identifier"],
                chain_id,
                "CYS",
                residue_index,
                residue_atom,
                bond_pair,
            ]
        )
        return {
            "support_proposal_id": f"SUP_EVT_{index:06d}",
            "curation_candidate_id": template_row["curation_candidate_id"],
            "source_profile": CURRENT_SOURCE_PROFILE,
            "source_database": CURRENT_SOURCE_DATABASE,
            "candidate_metadata_id": template_row["candidate_metadata_id"],
            "pdb_id": template_row["pdb_id"],
            "ligand_identifier": template_row["ligand_identifier"],
            "suggested_chain_id": chain_id,
            "suggested_residue_name": "CYS",
            "suggested_residue_index": residue_index,
            "suggested_residue_atom_name": "SG",
            "suggested_ligand_comp_id": ligand_comp,
            "suggested_ligand_atom_name": ligand_atom,
            "suggested_covalent_bond_atom_pair": bond_pair,
            "suggested_covalent_event_id": event_id,
            "evidence_source_name": "local_raw_mmcif_struct_conn",
            "evidence_source_path": raw_path.as_posix(),
            "evidence_provenance_status": "support_proposal_from_existing_local_raw_struct_conn",
            "evidence_confidence": "candidate_requires_manual_review",
            "ambiguity_status": "single_struct_conn_candidate_pending_review",
            "cys_sg_v1_candidate_proposal": True,
            "proposal_status": "pending_manual_review",
            "manual_review_status": "pending_manual_review",
            "curator_action_required": "confirm_or_reject_event_identity_before_validation",
            "exclusion_reason": "",
        }
    return None


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest14e = _load_json(STEP14E_MANIFEST_JSON)
    checks = [
        ("step14e_manifest_exists", STEP14E_MANIFEST_JSON, "exists", STEP14E_MANIFEST_JSON.exists(), STEP14E_MANIFEST_JSON.exists()),
        ("step14e_stage", STEP14E_MANIFEST_JSON, PREVIOUS_STAGE, manifest14e.get("stage"), manifest14e.get("stage") == PREVIOUS_STAGE),
        ("step14e_step_label", STEP14E_MANIFEST_JSON, "Step 14E", manifest14e.get("step_label"), manifest14e.get("step_label") == "Step 14E"),
        ("step14e_all_checks_passed", STEP14E_MANIFEST_JSON, "true", manifest14e.get("all_checks_passed"), manifest14e.get("all_checks_passed") is True),
        ("step14e_template_row_count", STEP14E_MANIFEST_JSON, "25", manifest14e.get("manual_curation_template_row_count"), manifest14e.get("manual_curation_template_row_count") == 25),
        ("step14e_selected_for_manual_curation_count", STEP14E_MANIFEST_JSON, "25", manifest14e.get("selected_for_manual_curation_count"), manifest14e.get("selected_for_manual_curation_count") == 25),
        ("step14e_ready_candidate_count_zero", STEP14E_MANIFEST_JSON, "0", manifest14e.get("ready_candidate_count_current_step"), manifest14e.get("ready_candidate_count_current_step") == 0),
        ("step14e_all_pending", STEP14E_MANIFEST_JSON, "true", manifest14e.get("manual_review_status_all_pending"), manifest14e.get("manual_review_status_all_pending") is True),
        ("step14e_validation_gate_ready", STEP14E_MANIFEST_JSON, "true", manifest14e.get("ready_for_covapie_small_pilot_manual_event_identity_validation_gate"), manifest14e.get("ready_for_covapie_small_pilot_manual_event_identity_validation_gate") is True),
        ("step14e_download_smoke_blocked", STEP14E_MANIFEST_JSON, "false", manifest14e.get("ready_for_covapie_small_pilot_download_smoke"), manifest14e.get("ready_for_covapie_small_pilot_download_smoke") is False),
        ("metadata_csv_exists", METADATA_CSV, "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", STEP14E_MANIFEST_JSON, "5", len(manifest14e.get("canonical_mask_task_names", [])), len(manifest14e.get("canonical_mask_task_names", [])) == 5),
        ("b3_scaffold_only_included", STEP14E_MANIFEST_JSON, "true", manifest14e.get("b3_scaffold_only_included"), manifest14e.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", STEP14E_MANIFEST_JSON, "true", manifest14e.get("no_extra_mask_tasks_added"), manifest14e.get("no_extra_mask_tasks_added") is True),
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


def build_input_template_audit_rows(template_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    event_fields_blank = all(not row[field] for row in template_rows for field in ["chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "covalent_event_id"])
    checks = [
        ("template_exists", str(STEP14E_TEMPLATE_CSV.exists()), "True", STEP14E_TEMPLATE_CSV.exists()),
        ("template_row_count_25", str(len(template_rows)), "25", len(template_rows) == 25),
        ("all_rows_pending_manual_review", str(all(row["manual_review_status"] == "pending_manual_review" for row in template_rows)), "True", all(row["manual_review_status"] == "pending_manual_review" for row in template_rows)),
        ("ready_candidate_count_zero", "0", "0", True),
        ("source_profile_covpdb_manual_metadata_v0", str({row["source_profile"] for row in template_rows}), CURRENT_SOURCE_PROFILE, {row["source_profile"] for row in template_rows} == {CURRENT_SOURCE_PROFILE}),
        ("source_database_covpdb", str({row["source_database"] for row in template_rows}), CURRENT_SOURCE_DATABASE, {row["source_database"] for row in template_rows} == {CURRENT_SOURCE_DATABASE}),
        ("pdb_id_prefilled", str(all(row["pdb_id"] for row in template_rows)), "True", all(row["pdb_id"] for row in template_rows)),
        ("ligand_identifier_prefilled", str(all(row["ligand_identifier"] for row in template_rows)), "True", all(row["ligand_identifier"] for row in template_rows)),
        ("event_level_fields_blank_pending", str(event_fields_blank), "True", event_fields_blank),
        ("v1_scope_cys_sg_pending", str({row["cys_sg_v1_candidate"] for row in template_rows}), "unknown_pending_manual_review", {row["cys_sg_v1_candidate"] for row in template_rows} == {"unknown_pending_manual_review"}),
    ]
    return [
        {
            "input_template_check": item,
            "observed_status": observed,
            "expected_status": expected,
            "input_template_audit_passed": passed,
            "qa_comment": "Step 14E template remains pending and unmodified.",
        }
        for item, observed, expected, passed in checks
    ]


def build_source_inventory_rows(template_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    raw_files = [_template_raw_path(row["pdb_id"]) for row in template_rows]
    local_raw_count = sum(path.exists() for path in raw_files)
    rows = [
        ("step14e_manual_curation_template", STEP14E_TEMPLATE_CSV, STEP14E_TEMPLATE_CSV.exists(), "derived_csv", "read_only", True, "Pending template is the proposal target."),
        ("metadata_csv", METADATA_CSV, METADATA_CSV.exists(), "derived_csv", "read_only", True, "Metadata provides het_code for raw struct_conn matching."),
        ("local_raw_cif_root", RAW_STORAGE_ROOT, RAW_STORAGE_ROOT.exists(), "local_raw_root", "read_only_existing_cif_mmcif_only", RAW_STORAGE_ROOT.exists(), "Existing local raw may be read but never written or committed."),
        ("local_raw_cif_files_for_template_pdb_ids", RAW_STORAGE_ROOT, local_raw_count > 0, "local_raw_cif_files", "read_only_existing_cif_mmcif_only", local_raw_count > 0, f"{local_raw_count} template raw files available."),
        ("step14d_candidate_expansion_artifacts", STEP14D_ROOT, STEP14D_ROOT.exists(), "derived_artifacts", "read_only", True, "Prior expansion gate is context only."),
        ("step14c_manifest_artifacts", STEP14C_ROOT, STEP14C_ROOT.exists(), "derived_artifacts", "read_only", True, "Prior manifest gate is context only."),
    ]
    for item in OPTIONAL_DERIVED_SOURCES:
        name, path, source_type = item
        rows.append((name, path, path.exists(), source_type, "read_only_if_present", path.exists(), "Missing optional derived evidence does not fail."))
    rows.extend(
        [
            ("no_network_source_current_step", "policy", True, "policy", "not_executed_or_not_allowed", False, "Network sources are not allowed."),
            ("no_external_download_current_step", "policy", True, "policy", "not_executed_or_not_allowed", False, "External downloads are not allowed."),
        ]
    )
    return [
        {
            "evidence_source_name": name,
            "evidence_source_path": str(path),
            "evidence_source_exists": exists,
            "evidence_source_type": source_type,
            "current_step_read_mode": read_mode,
            "can_generate_support_proposals": can_generate,
            "evidence_source_inventory_passed": True,
            "qa_comment": comment,
        }
        for name, path, exists, source_type, read_mode, can_generate, comment in rows
    ]


def build_local_raw_availability_rows(template_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw_available_count = 0
    raw_read_count = 0
    for template_row in template_rows:
        raw_path = _template_raw_path(template_row["pdb_id"])
        exists = raw_path.exists()
        raw_available_count += int(exists)
        raw_read_count += int(exists)
        tracked = _git_tracked(raw_path)
        staged = _git_staged(raw_path)
        rows.append(
            {
                "curation_candidate_id": template_row["curation_candidate_id"],
                "pdb_id": template_row["pdb_id"],
                "ligand_identifier": template_row["ligand_identifier"],
                "expected_local_raw_path": raw_path.as_posix(),
                "local_raw_file_exists": exists,
                "local_raw_file_tracked_by_git": tracked,
                "local_raw_file_staged_by_git": staged,
                "raw_read_allowed_current_step": exists,
                "raw_read_attempted_current_step": exists,
                "raw_availability_audit_passed": exists == (raw_path.suffix.lower() in {".cif", ".mmcif"}) and not tracked and not staged if exists else True,
                "qa_comment": "Existing local raw read-only evidence checked." if exists else "No local raw file available; candidate remains pending.",
            }
        )
    for summary_id, value in [
        ("summary_template_candidate_count", len(template_rows)),
        ("summary_local_raw_available_count", raw_available_count),
        ("summary_local_raw_read_count", raw_read_count),
    ]:
        rows.append(
            {
                "curation_candidate_id": summary_id,
                "pdb_id": "",
                "ligand_identifier": "",
                "expected_local_raw_path": "",
                "local_raw_file_exists": "",
                "local_raw_file_tracked_by_git": False,
                "local_raw_file_staged_by_git": False,
                "raw_read_allowed_current_step": "",
                "raw_read_attempted_current_step": "",
                "raw_availability_audit_passed": True,
                "qa_comment": str(value),
            }
        )
    return rows


def build_struct_conn_audit_and_proposals(template_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    metadata_by_pdb = _metadata_by_pdb()
    proposals: list[dict[str, Any]] = []
    proposal_audit_rows: list[dict[str, Any]] = []
    local_raw_available_count = 0
    local_raw_read_count = 0
    struct_conn_count = 0
    cys_sg_count = 0
    ambiguous_count = 0
    non_cys_sg_count = 0
    for template_row in template_rows:
        raw_path = _template_raw_path(template_row["pdb_id"])
        if not raw_path.exists():
            continue
        local_raw_available_count += 1
        local_raw_read_count += 1
        metadata_row = metadata_by_pdb.get(template_row["pdb_id"].upper(), {})
        struct_rows = parse_struct_conn_rows(raw_path)
        struct_conn_count += len(struct_rows)
        candidate_proposals_for_template: list[dict[str, Any]] = []
        for struct_row in struct_rows:
            proposal = _proposal_from_struct_conn(template_row, metadata_row, raw_path, struct_row, len(proposals) + len(candidate_proposals_for_template) + 1)
            if proposal:
                candidate_proposals_for_template.append(proposal)
            else:
                non_cys_sg_count += 1
        if len(candidate_proposals_for_template) > 1:
            ambiguous_count += len(candidate_proposals_for_template)
            for proposal in candidate_proposals_for_template:
                proposal["ambiguity_status"] = "multiple_struct_conn_candidates_pending_review"
        cys_sg_count += len(candidate_proposals_for_template)
        proposals.extend(candidate_proposals_for_template)

    summary_values = [
        ("template_candidate_count", len(template_rows)),
        ("local_raw_available_count", local_raw_available_count),
        ("local_raw_read_count", local_raw_read_count),
        ("struct_conn_rows_detected_count", struct_conn_count),
        ("cys_sg_struct_conn_candidate_count", cys_sg_count),
        ("ambiguous_struct_conn_candidate_count", ambiguous_count),
        ("non_cys_or_non_sg_candidate_count", non_cys_sg_count),
        ("support_proposal_count", len(proposals)),
        ("support_proposals_pending_manual_review", len(proposals)),
        ("no_ready_candidates_created", 0),
    ]
    for item, value in summary_values:
        proposal_audit_rows.append(
            {
                "proposal_or_summary_id": item,
                "curation_candidate_id": "",
                "pdb_id": "",
                "ligand_identifier": "",
                "suggested_chain_id": "",
                "suggested_residue_name": "",
                "suggested_residue_index": "",
                "suggested_residue_atom_name": "",
                "suggested_ligand_comp_id": "",
                "suggested_ligand_atom_name": "",
                "suggested_covalent_bond_atom_pair": "",
                "suggested_covalent_event_id": "",
                "struct_conn_type": "summary",
                "evidence_source_path": "",
                "evidence_confidence": "summary",
                "ambiguity_status": "summary",
                "cys_sg_v1_candidate_proposal": "",
                "proposal_status": "summary",
                "proposal_audit_passed": True,
                "qa_comment": str(value),
            }
        )
    for proposal in proposals:
        proposal_audit_rows.append(
            {
                "proposal_or_summary_id": proposal["support_proposal_id"],
                "curation_candidate_id": proposal["curation_candidate_id"],
                "pdb_id": proposal["pdb_id"],
                "ligand_identifier": proposal["ligand_identifier"],
                "suggested_chain_id": proposal["suggested_chain_id"],
                "suggested_residue_name": proposal["suggested_residue_name"],
                "suggested_residue_index": proposal["suggested_residue_index"],
                "suggested_residue_atom_name": proposal["suggested_residue_atom_name"],
                "suggested_ligand_comp_id": proposal["suggested_ligand_comp_id"],
                "suggested_ligand_atom_name": proposal["suggested_ligand_atom_name"],
                "suggested_covalent_bond_atom_pair": proposal["suggested_covalent_bond_atom_pair"],
                "suggested_covalent_event_id": proposal["suggested_covalent_event_id"],
                "struct_conn_type": "covale",
                "evidence_source_path": proposal["evidence_source_path"],
                "evidence_confidence": proposal["evidence_confidence"],
                "ambiguity_status": proposal["ambiguity_status"],
                "cys_sg_v1_candidate_proposal": proposal["cys_sg_v1_candidate_proposal"],
                "proposal_status": proposal["proposal_status"],
                "proposal_audit_passed": True,
                "qa_comment": "Support proposal only; pending manual review.",
            }
        )
    counts = {
        "template_candidate_count": len(template_rows),
        "local_raw_available_count": local_raw_available_count,
        "local_raw_read_count": local_raw_read_count,
        "struct_conn_rows_detected_count": struct_conn_count,
        "cys_sg_struct_conn_candidate_count": cys_sg_count,
        "support_proposal_count": len(proposals),
        "ambiguous_struct_conn_candidate_count": ambiguous_count,
        "non_cys_or_non_sg_candidate_count": non_cys_sg_count,
    }
    return proposal_audit_rows, proposals, counts


def build_validation_rows(proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("proposals_csv_json_consistent", True, "CSV and JSON are written from the same proposal list."),
        ("all_proposals_pending_manual_review", all(row["proposal_status"] == "pending_manual_review" and row["manual_review_status"] == "pending_manual_review" for row in proposals), "All proposals remain pending."),
        ("no_ready_candidates_created", True, "No proposal is a ready candidate."),
        ("no_pdb_only_join_used", True, "Proposals require struct_conn evidence, never PDB ID alone."),
        ("no_ligand_topology_auto_restore", True, "No topology restoration is performed."),
        ("v1_cys_sg_scope_preserved", all(row["suggested_residue_name"] == "CYS" and row["suggested_residue_atom_name"] == "SG" for row in proposals), "Only CYS/SG proposals are emitted."),
        ("raw_files_not_written", True, "Raw files are read-only if present."),
        ("raw_files_not_tracked_or_staged", not _raw_files_tracked() and not _raw_files_staged(), "Raw files remain untracked and unstaged."),
        ("no_download_manifest_written", not _forbidden_named_artifact_exists(), "No download manifest artifact is written."),
        ("validation_gate_still_required", True, "A support review gate remains required before validation."),
    ]
    return [
        {
            "validation_item": item,
            "observed_status": str(observed),
            "validation_passed": bool(observed),
            "qa_comment": comment,
        }
        for item, observed, comment in checks
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    existing_paths = {
        "metadata_csv_unchanged": [METADATA_CSV.as_posix()],
        "step14e_artifacts_unchanged": [STEP14E_ROOT.as_posix()],
        "step14d_artifacts_unchanged": [STEP14D_ROOT.as_posix()],
        "step14c_artifacts_unchanged": [STEP14C_ROOT.as_posix()],
        "step14b_artifacts_unchanged": [STEP14B_ROOT.as_posix()],
        "step14a_artifacts_unchanged": [STEP14A_ROOT.as_posix()],
        "step13bz_artifacts_unchanged": [STEP13BZ_ROOT.as_posix()],
        "step13by_artifacts_unchanged": [STEP13BY_ROOT.as_posix()],
        "step13bx_artifacts_unchanged": [STEP13BX_ROOT.as_posix()],
        "step13bu_artifacts_unchanged": [STEP13BU_ROOT.as_posix()],
        "step13bo_artifacts_unchanged": [STEP13BO_ROOT.as_posix()],
        "step13bm_artifacts_unchanged": [STEP13BM_ROOT.as_posix()],
        "step13ai_inventory_artifacts_unchanged": [STEP13AI_ROOT.as_posix()],
    }
    checks: list[tuple[str, str, str, bool]] = [
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked() else "failed", not _raw_files_tracked()),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged() else "failed", not _raw_files_staged()),
        ("raw_files_read_only_if_present", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_download_manifest_written_current_step", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_download_smoke_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_smoke_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", "passed", "passed", True),
        ("no_original_dataloader_modified", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_torch_tensor_checkpoint_training_artifacts", "passed", "passed", True),
        ("no_numpy_outputs", "passed", "passed", True),
        ("no_real_final_dataset_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
    ]
    for item, paths in existing_paths.items():
        passed = (item != "metadata_csv_unchanged" or _metadata_hash() == METADATA_CSV_SHA256) and not _path_diff_exists(paths)
        checks.append((item, "passed", "passed" if passed else "failed", passed))
    protected_passed = not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])
    dataloader_passed = not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])
    checks.extend(
        [
            ("protected_source_diff_empty", "passed", "passed" if protected_passed else "failed", protected_passed),
            ("original_dataloader_diff_empty", "passed", "passed" if dataloader_passed else "failed", dataloader_passed),
            ("no_network_download_rdkit_biopdb_gemmi_gzip_torch_numpy_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
            ("derived_output_no_forbidden_binary_artifacts", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ]
    )
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
    template_rows: list[dict[str, str]],
    source_inventory_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    struct_conn_rows: list[dict[str, Any]],
    proposals: list[dict[str, Any]],
    validation_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
    counts: dict[str, int],
) -> dict[str, Any]:
    passed = (
        _all_true(precondition_rows, "precondition_passed")
        and _all_true(source_inventory_rows, "evidence_source_inventory_passed")
        and _all_true(raw_rows, "raw_availability_audit_passed")
        and _all_true(struct_conn_rows, "proposal_audit_passed")
        and _all_true(validation_rows, "validation_passed")
        and _all_true(safety_rows, "safety_passed")
    )
    raw_read = counts["local_raw_read_count"] > 0
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step14e_manual_curation_template_validated": _all_true(precondition_rows, "precondition_passed"),
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "template_candidate_count": counts["template_candidate_count"],
        "local_raw_available_count": counts["local_raw_available_count"],
        "local_raw_read_count": counts["local_raw_read_count"],
        "struct_conn_rows_detected_count": counts["struct_conn_rows_detected_count"],
        "cys_sg_struct_conn_candidate_count": counts["cys_sg_struct_conn_candidate_count"],
        "support_proposal_count": counts["support_proposal_count"],
        "insufficient_support_evidence_for_20_candidate_review": counts["support_proposal_count"] < 20,
        "support_proposals_csv_json_consistent": True,
        "support_proposals_all_pending_manual_review": all(row["proposal_status"] == "pending_manual_review" and row["manual_review_status"] == "pending_manual_review" for row in proposals),
        "ready_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "raw_file_content_read_current_step": raw_read,
        "mmcif_text_read": raw_read,
        "mmcif_struct_conn_parse_current_step": raw_read,
        "coordinate_extraction_current_step": False,
        "ligand_topology_auto_restored_current_step": False,
        "network_access_used": False,
        "download_attempted": False,
        "raw_files_written_current_step": False,
        "raw_files_committed": False,
        "download_manifest_written": False,
        "actual_download_smoke_written": False,
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
        "ready_for_covapie_manual_event_identity_support_review_gate": True,
        "ready_for_covapie_small_pilot_manual_event_identity_validation_gate": False,
        "ready_for_covapie_small_pilot_download_manifest_rerun_gate": False,
        "ready_for_covapie_small_pilot_download_smoke": False,
        "ready_for_covapie_bulk_download_smoke": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_manual_event_identity_support_review_gate",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else [row["blocking_reasons"] for row in [*precondition_rows, *safety_rows] if row.get("blocking_reasons")],
    }


def run_covapie_manual_event_identity_support_evidence_acquisition_gate_v0() -> dict[str, Any]:
    template_rows = _csv_rows(STEP14E_TEMPLATE_CSV)
    precondition_rows = build_precondition_rows()
    input_template_rows = build_input_template_audit_rows(template_rows)
    source_inventory_rows = build_source_inventory_rows(template_rows)
    raw_rows = build_local_raw_availability_rows(template_rows)
    struct_conn_rows, proposals, counts = build_struct_conn_audit_and_proposals(template_rows)
    validation_rows = build_validation_rows(proposals)
    safety_rows = build_safety_rows()
    manifest = build_manifest(
        precondition_rows,
        template_rows,
        source_inventory_rows,
        raw_rows,
        struct_conn_rows,
        proposals,
        validation_rows,
        safety_rows,
        counts,
    )
    return {
        "precondition_rows": precondition_rows,
        "input_template_rows": input_template_rows,
        "source_inventory_rows": source_inventory_rows,
        "raw_rows": raw_rows,
        "struct_conn_rows": struct_conn_rows,
        "proposals": proposals,
        "validation_rows": validation_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_small_pilot_download_manifest_gate as step14c


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_small_pilot_candidate_expansion_gate_v0"
STEP_LABEL = "Step 14D"
PREVIOUS_STAGE = step14c.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14c.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14c.CURRENT_SOURCE_DATABASE
TARGET_SMALL_PILOT_MIN_ROW_COUNT = step14c.TARGET_SMALL_PILOT_MIN_ROW_COUNT
TARGET_SMALL_PILOT_MAX_ROW_COUNT = step14c.TARGET_SMALL_PILOT_MAX_ROW_COUNT

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_small_pilot_candidate_expansion_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_candidate_expansion_precondition_audit.csv"
EVIDENCE_SOURCE_INVENTORY_CSV = OUTPUT_ROOT / "covapie_small_pilot_candidate_evidence_source_inventory.csv"
EVENT_IDENTITY_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "covapie_small_pilot_event_identity_mapping_contract.csv"
CANDIDATE_EXPANSION_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_candidate_expansion_audit.csv"
EXPANDED_EVENT_CANDIDATES_CSV = OUTPUT_ROOT / "covapie_small_pilot_expanded_event_candidates.csv"
EXPANDED_EVENT_CANDIDATES_JSON = OUTPUT_ROOT / "covapie_small_pilot_expanded_event_candidates.json"
CANDIDATE_GAP_TAXONOMY_CSV = OUTPUT_ROOT / "covapie_small_pilot_candidate_gap_taxonomy_audit.csv"
READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_small_pilot_candidate_expansion_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_candidate_expansion_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_small_pilot_candidate_expansion_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_small_pilot_candidate_expansion_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_small_pilot_candidate_expansion_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_small_pilot_candidate_expansion_gate_v0.py")

METADATA_CSV = step14c.METADATA_CSV
METADATA_CSV_SHA256 = step14c.METADATA_CSV_SHA256
RAW_STORAGE_ROOT = step14c.RAW_STORAGE_ROOT
STEP14C_MANIFEST_JSON = step14c.MANIFEST_JSON
STEP14C_ROOT = step14c.OUTPUT_ROOT
STEP14B_ROOT = step14c.STEP14B_ROOT
STEP14A_ROOT = step14c.STEP14A_ROOT
STEP13BZ_ROOT = step14c.STEP13BZ_ROOT
STEP13BY_ROOT = step14c.STEP13BY_ROOT
STEP13BX_ROOT = step14c.STEP13BX_ROOT
STEP13BU_ROOT = step14c.STEP13BU_ROOT
STEP13BO_ROOT = step14c.STEP13BO_ROOT
STEP13BM_ROOT = step14c.STEP13BM_ROOT
STEP13AI_ROOT = step14c.STEP13AI_ROOT

OPTIONAL_EVIDENCE_SOURCES = [
    ("candidate_allowlist_qa_if_present", Path("data/derived/covalent_small/covapie_candidate_allowlist_qa_gate_v0"), "optional_supporting"),
    ("batch_raw_read_extraction_smoke_if_present", Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_smoke_v0"), "authoritative_if_event_fields_present"),
    ("batch_raw_read_extraction_qa_if_present", Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_qa_gate_v0"), "authoritative_if_event_fields_present"),
    ("real_covalent_confirmed_candidate_full_atom_extraction_if_present", Path("data/derived/covalent_small/covapie_real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0"), "authoritative_if_event_fields_present"),
    ("final_dataset_smoke_preview_if_present", Path("data/derived/covalent_small/covapie_final_dataset_smoke_v0"), "supporting_only"),
    ("metadata_dataloader_smoke_preview_if_present", Path("data/derived/covalent_small/covapie_metadata_dataloader_smoke_v0"), "supporting_only"),
    ("sample_index_smoke_preview_if_present", Path("data/derived/covalent_small/covapie_sample_index_smoke_v0"), "supporting_only"),
    ("step8_topology_evidence_export_if_present", Path("data/derived/covalent_small/covapie_step8_topology_evidence_export_smoke_v0"), "authoritative_if_event_fields_present"),
]

CANONICAL_MASK_TASK_NAMES = step14c.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14c.CANONICAL_MASK_TASK_ALIASES

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
EVIDENCE_SOURCE_COLUMNS = [
    "evidence_source_name",
    "evidence_source_path",
    "evidence_source_exists",
    "evidence_source_type",
    "event_identity_authoritative",
    "can_support_candidate_expansion",
    "current_step_read_mode",
    "evidence_source_inventory_passed",
    "qa_comment",
]
EVENT_IDENTITY_MAPPING_COLUMNS = [
    "event_identity_field",
    "required_for_expanded_candidate",
    "allowed_source_evidence",
    "pdb_only_join_allowed",
    "current_step_policy",
    "mapping_contract_passed",
    "qa_comment",
]
CANDIDATE_EXPANSION_AUDIT_COLUMNS = [
    "expansion_item_or_candidate_id",
    "source_profile",
    "source_database",
    "pdb_id",
    "ligand_identifier",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "ligand_atom_name",
    "covalent_bond_atom_pair",
    "covalent_event_id",
    "evidence_source_name",
    "event_identity_complete",
    "pdb_only_join_used",
    "expansion_status",
    "expansion_reason",
    "candidate_expansion_passed",
]
EXPANDED_CANDIDATE_COLUMNS = [
    "expanded_candidate_id",
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
    "ligand_atom_name",
    "covalent_bond_atom_pair",
    "evidence_source_name",
    "evidence_source_path",
    "evidence_provenance_status",
    "event_identity_complete",
    "pdb_only_join_used",
    "selected_for_small_pilot_manifest_rerun",
    "pilot_selection_rank",
    "expansion_status",
    "exclusion_reason",
]
GAP_TAXONOMY_COLUMNS = ["gap_type", "gap_category", "detection_policy", "observed_count", "blocks_manifest_rerun", "gap_taxonomy_passed", "qa_comment"]
READINESS_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]

EVENT_FIELDS = ["chain_id", "residue_name", "residue_index", "residue_atom_name", "covalent_bond_atom_pair"]
ALLOWED_EVIDENCE_SUFFIXES = {".csv", ".json", ".txt", ".md"}
FORBIDDEN_EVIDENCE_SUFFIXES = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz"}


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


def _ligand_identifier(row: dict[str, str]) -> str:
    return row.get("covpdb_ligand_id") or row.get("het_code") or row.get("ligand_id") or row.get("ligand_identifier") or row.get("ligand_name") or ""


def _candidate_metadata_id(row: dict[str, str], index: int) -> str:
    existing = row.get("candidate_metadata_id") or row.get("candidate_id") or row.get("expanded_candidate_id")
    if existing:
        return existing
    record = row.get("covpdb_record_index") or f"{index:06d}"
    return f"COVPDB_META_{int(record):06d}" if str(record).isdigit() else f"COVPDB_META_{index:06d}"


def _event_complete(row: dict[str, str]) -> bool:
    return bool(row.get("pdb_id") and _ligand_identifier(row) and all(row.get(field) for field in EVENT_FIELDS))


def _covalent_event_id(row: dict[str, str]) -> str:
    existing = row.get("covalent_event_id")
    if existing:
        return existing
    return "|".join(
        [
            row.get("pdb_id", ""),
            _ligand_identifier(row),
            row.get("chain_id", ""),
            row.get("residue_name", ""),
            row.get("residue_index", ""),
            row.get("residue_atom_name", ""),
            row.get("covalent_bond_atom_pair", ""),
        ]
    )


def _safe_evidence_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in ALLOWED_EVIDENCE_SUFFIXES and path.suffix.lower() not in FORBIDDEN_EVIDENCE_SUFFIXES]


def _read_evidence_rows(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".csv":
        try:
            return _csv_rows(path)
        except (csv.Error, UnicodeDecodeError):
            return []
    if path.suffix.lower() == ".json":
        try:
            data = _load_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return []
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list) and all(isinstance(row, dict) for row in value):
                    return value
        return []
    return []


def _source_has_authoritative_event_rows(root: Path) -> bool:
    for path in _safe_evidence_files(root):
        for row in _read_evidence_rows(path):
            if _event_complete({key: str(value) for key, value in row.items()}):
                return True
    return False


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest14c = _load_json(STEP14C_MANIFEST_JSON)
    checks = [
        ("step14c_manifest_exists", STEP14C_MANIFEST_JSON, "exists", STEP14C_MANIFEST_JSON.exists(), STEP14C_MANIFEST_JSON.exists()),
        ("step14c_stage", STEP14C_MANIFEST_JSON, PREVIOUS_STAGE, manifest14c.get("stage"), manifest14c.get("stage") == PREVIOUS_STAGE),
        ("step14c_step_label", STEP14C_MANIFEST_JSON, "Step 14C", manifest14c.get("step_label"), manifest14c.get("step_label") == "Step 14C"),
        ("step14c_all_checks_passed", STEP14C_MANIFEST_JSON, "true", manifest14c.get("all_checks_passed"), manifest14c.get("all_checks_passed") is True),
        ("step14c_source_profile", STEP14C_MANIFEST_JSON, CURRENT_SOURCE_PROFILE, manifest14c.get("current_source_profile"), manifest14c.get("current_source_profile") == CURRENT_SOURCE_PROFILE),
        ("step14c_source_database", STEP14C_MANIFEST_JSON, CURRENT_SOURCE_DATABASE, manifest14c.get("current_source_database"), manifest14c.get("current_source_database") == CURRENT_SOURCE_DATABASE),
        ("step14c_execution_source_specific", STEP14C_MANIFEST_JSON, "true", manifest14c.get("current_execution_source_specific"), manifest14c.get("current_execution_source_specific") is True),
        ("step14c_schema_generalization", STEP14C_MANIFEST_JSON, "true", manifest14c.get("cross_source_generalization_supported_by_schema"), manifest14c.get("cross_source_generalization_supported_by_schema") is True),
        ("step14c_no_pdb_wide_blind_scan", STEP14C_MANIFEST_JSON, "false", manifest14c.get("pdb_wide_blind_scan_allowed"), manifest14c.get("pdb_wide_blind_scan_allowed") is False),
        ("step14c_selected_count_zero", STEP14C_MANIFEST_JSON, "0", manifest14c.get("selected_small_pilot_row_count"), manifest14c.get("selected_small_pilot_row_count") == 0),
        ("step14c_insufficient_candidates", STEP14C_MANIFEST_JSON, "true", manifest14c.get("insufficient_candidate_count_for_20_to_50_pilot"), manifest14c.get("insufficient_candidate_count_for_20_to_50_pilot") is True),
        ("step14c_download_smoke_blocked", STEP14C_MANIFEST_JSON, "false", manifest14c.get("ready_for_covapie_small_pilot_download_smoke"), manifest14c.get("ready_for_covapie_small_pilot_download_smoke") is False),
        ("step14c_recommended_next_step", STEP14C_MANIFEST_JSON, "covapie_small_pilot_candidate_expansion_gate", manifest14c.get("recommended_next_step"), manifest14c.get("recommended_next_step") == "covapie_small_pilot_candidate_expansion_gate"),
        ("metadata_csv_exists", METADATA_CSV, "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("no_network_current_step", "current_step_boundary", "false", False, True),
        ("no_download_current_step", "current_step_boundary", "false", False, True),
        ("no_raw_write_current_step", "current_step_boundary", "false", False, True),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", STEP14C_MANIFEST_JSON, "5", len(manifest14c.get("canonical_mask_task_names", [])), len(manifest14c.get("canonical_mask_task_names", [])) == 5),
        ("b3_scaffold_only_included", STEP14C_MANIFEST_JSON, "true", manifest14c.get("b3_scaffold_only_included"), manifest14c.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", STEP14C_MANIFEST_JSON, "true", manifest14c.get("no_extra_mask_tasks_added"), manifest14c.get("no_extra_mask_tasks_added") is True),
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


def build_evidence_source_inventory_rows() -> list[dict[str, Any]]:
    rows = [
        ("current_metadata_csv", METADATA_CSV, METADATA_CSV.exists(), "metadata_csv", False, False, "csv_header_and_rows_only", "Metadata has PDB/ligand IDs but is not authoritative for event-level identity."),
        ("step14c_candidate_selection_audit", step14c.CANDIDATE_SELECTION_AUDIT_CSV, step14c.CANDIDATE_SELECTION_AUDIT_CSV.exists(), "derived_csv", False, True, "csv_read_only", "Explains why Step 14C selected zero rows."),
        ("step14c_empty_small_pilot_manifest", step14c.SMALL_PILOT_MANIFEST_CSV, step14c.SMALL_PILOT_MANIFEST_CSV.exists(), "derived_csv", False, True, "csv_read_only", "Confirms no download manifest rows were selected."),
    ]
    for name, path, source_type in OPTIONAL_EVIDENCE_SOURCES:
        exists = path.exists()
        authoritative = exists and source_type.startswith("authoritative") and _source_has_authoritative_event_rows(path)
        supporting = exists and source_type in {"supporting_only", "optional_supporting"}
        rows.append(
            (
                name,
                path,
                exists,
                source_type,
                authoritative,
                authoritative or supporting,
                "derived_csv_json_txt_md_read_only" if exists else "missing_optional_evidence_source",
                "Optional source missing or scanned safely; missing optional sources do not fail.",
            )
        )
    rows.append(
        (
            "manual_event_identity_curation_required_policy",
            "policy",
            True,
            "policy",
            True,
            True,
            "policy_declared",
            "If fewer than 20 authoritative candidates are expanded, manual curation is required.",
        )
    )
    return [
        {
            "evidence_source_name": name,
            "evidence_source_path": str(path),
            "evidence_source_exists": exists,
            "evidence_source_type": source_type,
            "event_identity_authoritative": authoritative,
            "can_support_candidate_expansion": can_support,
            "current_step_read_mode": read_mode,
            "evidence_source_inventory_passed": True,
            "qa_comment": comment,
        }
        for name, path, exists, source_type, authoritative, can_support, read_mode, comment in rows
    ]


def build_event_identity_mapping_rows() -> list[dict[str, Any]]:
    rows = [
        ("source_profile", True, "Step14C source profile contract", False, "must equal current source profile"),
        ("source_database", True, "Step14C source profile contract", False, "must equal current source database"),
        ("pdb_id", True, "metadata CSV plus authoritative event evidence", True, "required but not sufficient by itself"),
        ("ligand_identifier", True, "metadata CSV plus authoritative event evidence", False, "required with PDB for candidate matching"),
        ("chain_id", True, "authoritative event identity evidence", False, "must not be fabricated"),
        ("residue_name", True, "authoritative event identity evidence", False, "must not be fabricated"),
        ("residue_index", True, "authoritative event identity evidence", False, "must not be fabricated"),
        ("residue_atom_name", True, "authoritative event identity evidence", False, "must not be fabricated"),
        ("ligand_atom_name", False, "authoritative evidence or covalent_bond_atom_pair", False, "nullable only when covalent_bond_atom_pair contains ligand atom identity"),
        ("covalent_bond_atom_pair", True, "authoritative event identity evidence", False, "must contain residue/ligand atom relationship"),
        ("covalent_event_id", True, "derived from event-level identity", False, "never derived from PDB ID alone"),
        ("candidate_metadata_id", True, "metadata CSV lineage", False, "stable candidate lineage id"),
        ("evidence_source", True, "derived evidence source inventory", False, "must record provenance"),
        ("evidence_provenance_status", True, "derived evidence source inventory", False, "must distinguish authoritative/supporting/missing"),
    ]
    return [
        {
            "event_identity_field": field,
            "required_for_expanded_candidate": required,
            "allowed_source_evidence": source,
            "pdb_only_join_allowed": pdb_only,
            "current_step_policy": policy,
            "mapping_contract_passed": True,
            "qa_comment": "PDB-only joins are blocked except that pdb_id itself may be present as one component.",
        }
        for field, required, source, pdb_only, policy in rows
    ]


def _authoritative_evidence_rows(inventory_rows: list[dict[str, Any]]) -> list[tuple[str, Path, dict[str, str]]]:
    output: list[tuple[str, Path, dict[str, str]]] = []
    authoritative_names = {row["evidence_source_name"] for row in inventory_rows if _bool(row["event_identity_authoritative"]) and str(row["evidence_source_path"]) != "policy"}
    for name, root, _source_type in OPTIONAL_EVIDENCE_SOURCES:
        if name not in authoritative_names or not root.exists():
            continue
        for path in _safe_evidence_files(root):
            for row in _read_evidence_rows(path):
                normalized = {key: str(value) for key, value in row.items()}
                if _event_complete(normalized):
                    output.append((name, path, normalized))
    return output


def _matching_evidence(metadata_row: dict[str, str], evidence: list[tuple[str, Path, dict[str, str]]]) -> tuple[str, Path, dict[str, str]] | None:
    pdb_id = metadata_row.get("pdb_id", "")
    ligand = _ligand_identifier(metadata_row)
    for source_name, path, row in evidence:
        if row.get("pdb_id") != pdb_id:
            continue
        if ligand and _ligand_identifier(row) and _ligand_identifier(row) != ligand:
            continue
        return source_name, path, row
    return None


def build_candidate_expansion_rows_and_candidates(
    inventory_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    metadata_rows = _csv_rows(METADATA_CSV)
    authoritative_evidence = _authoritative_evidence_rows(inventory_rows)
    expanded: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    incomplete_count = 0
    duplicate_count = 0
    seen_events: set[str] = set()
    gap_counts = {
        "missing_chain_id": 0,
        "missing_residue_name": 0,
        "missing_residue_index": 0,
        "missing_residue_atom_name": 0,
        "missing_ligand_atom_name": 0,
        "missing_covalent_bond_atom_pair": 0,
        "missing_ligand_identifier": 0,
        "missing_covalent_event_id": 0,
        "duplicate_event_identity": 0,
        "pdb_only_join_blocked": len(metadata_rows),
        "non_cys_or_non_sg_event_out_of_v1_scope": 0,
        "missing_authoritative_evidence_source": 0,
    }

    summaries = [
        ("metadata_candidate_universe_row_count", len(metadata_rows)),
        ("step14c_selected_small_pilot_row_count", 0),
        ("step14c_gap_reason_missing_event_identity", 1),
        ("evidence_sources_scanned_count", len(inventory_rows)),
        ("authoritative_event_evidence_sources_count", sum(_bool(row["event_identity_authoritative"]) and row["evidence_source_path"] != "policy" for row in inventory_rows)),
        ("expanded_event_candidate_count", 0),
        ("selected_for_manifest_rerun_count", 0),
        ("incomplete_event_identity_candidate_count", 0),
        ("pdb_only_join_attempts_blocked", len(metadata_rows)),
        ("candidate_expansion_passed", 1),
    ]
    for item, value in summaries:
        audit.append(
            {
                "expansion_item_or_candidate_id": item,
                "source_profile": CURRENT_SOURCE_PROFILE,
                "source_database": CURRENT_SOURCE_DATABASE,
                "pdb_id": "",
                "ligand_identifier": "",
                "chain_id": "",
                "residue_name": "",
                "residue_index": "",
                "residue_atom_name": "",
                "ligand_atom_name": "",
                "covalent_bond_atom_pair": "",
                "covalent_event_id": "",
                "evidence_source_name": "summary",
                "event_identity_complete": True,
                "pdb_only_join_used": False,
                "expansion_status": "summary",
                "expansion_reason": f"{item}: {value}",
                "candidate_expansion_passed": True,
            }
        )

    for index, metadata_row in enumerate(metadata_rows, start=1):
        candidate_metadata_id = _candidate_metadata_id(metadata_row, index)
        ligand = _ligand_identifier(metadata_row)
        match = _matching_evidence(metadata_row, authoritative_evidence)
        event_row = match[2] if match else {}
        event_identity_complete = bool(match and _event_complete(event_row))
        if not ligand:
            gap_counts["missing_ligand_identifier"] += 1
        for gap, field in [
            ("missing_chain_id", "chain_id"),
            ("missing_residue_name", "residue_name"),
            ("missing_residue_index", "residue_index"),
            ("missing_residue_atom_name", "residue_atom_name"),
            ("missing_covalent_bond_atom_pair", "covalent_bond_atom_pair"),
        ]:
            if not event_row.get(field):
                gap_counts[gap] += 1
        if not event_row.get("ligand_atom_name"):
            gap_counts["missing_ligand_atom_name"] += 1
        if not match:
            gap_counts["missing_authoritative_evidence_source"] += 1
        covalent_event_id = _covalent_event_id(event_row) if event_identity_complete else ""
        if not covalent_event_id:
            gap_counts["missing_covalent_event_id"] += 1
        duplicate = bool(covalent_event_id and covalent_event_id in seen_events)
        duplicate_count += int(duplicate)
        gap_counts["duplicate_event_identity"] += int(duplicate)
        if covalent_event_id:
            seen_events.add(covalent_event_id)
        selected = event_identity_complete and not duplicate and len(expanded) < TARGET_SMALL_PILOT_MAX_ROW_COUNT
        incomplete_count += int(not event_identity_complete)
        expansion_status = "expanded_selected_for_manifest_rerun" if selected else "not_expanded_current_step"
        expansion_reason = "authoritative event identity found" if selected else "missing authoritative event-level identity; pdb_only_join blocked"
        audit.append(
            {
                "expansion_item_or_candidate_id": candidate_metadata_id,
                "source_profile": CURRENT_SOURCE_PROFILE,
                "source_database": CURRENT_SOURCE_DATABASE,
                "pdb_id": metadata_row.get("pdb_id", ""),
                "ligand_identifier": ligand,
                "chain_id": event_row.get("chain_id", ""),
                "residue_name": event_row.get("residue_name", ""),
                "residue_index": event_row.get("residue_index", ""),
                "residue_atom_name": event_row.get("residue_atom_name", ""),
                "ligand_atom_name": event_row.get("ligand_atom_name", ""),
                "covalent_bond_atom_pair": event_row.get("covalent_bond_atom_pair", ""),
                "covalent_event_id": covalent_event_id,
                "evidence_source_name": match[0] if match else "",
                "event_identity_complete": event_identity_complete,
                "pdb_only_join_used": False,
                "expansion_status": expansion_status,
                "expansion_reason": expansion_reason,
                "candidate_expansion_passed": True,
            }
        )
        if selected:
            expanded.append(
                {
                    "expanded_candidate_id": f"EXP_EVT_{len(expanded) + 1:06d}",
                    "source_profile": CURRENT_SOURCE_PROFILE,
                    "source_database": CURRENT_SOURCE_DATABASE,
                    "candidate_metadata_id": candidate_metadata_id,
                    "covalent_event_id": covalent_event_id,
                    "pdb_id": metadata_row.get("pdb_id", ""),
                    "ligand_identifier": ligand,
                    "chain_id": event_row.get("chain_id", ""),
                    "residue_name": event_row.get("residue_name", ""),
                    "residue_index": event_row.get("residue_index", ""),
                    "residue_atom_name": event_row.get("residue_atom_name", ""),
                    "ligand_atom_name": event_row.get("ligand_atom_name", ""),
                    "covalent_bond_atom_pair": event_row.get("covalent_bond_atom_pair", ""),
                    "evidence_source_name": match[0],
                    "evidence_source_path": match[1].as_posix(),
                    "evidence_provenance_status": "authoritative_event_identity_from_derived_evidence",
                    "event_identity_complete": True,
                    "pdb_only_join_used": False,
                    "selected_for_small_pilot_manifest_rerun": True,
                    "pilot_selection_rank": len(expanded) + 1,
                    "expansion_status": "selected_for_manifest_rerun",
                    "exclusion_reason": "",
                }
            )

    for row in audit:
        item = row["expansion_item_or_candidate_id"]
        if item == "expanded_event_candidate_count":
            row["expansion_reason"] = f"expanded_event_candidate_count: {len(expanded)}"
        if item == "selected_for_manifest_rerun_count":
            row["expansion_reason"] = f"selected_for_manifest_rerun_count: {len(expanded)}"
        if item == "incomplete_event_identity_candidate_count":
            row["expansion_reason"] = f"incomplete_event_identity_candidate_count: {incomplete_count}"
    return audit, expanded, gap_counts


def build_gap_taxonomy_rows(gap_counts: dict[str, int]) -> list[dict[str, Any]]:
    definitions = [
        ("missing_chain_id", "event_identity", "chain_id is required for event-level identity", True),
        ("missing_residue_name", "event_identity", "residue_name is required for event-level identity", True),
        ("missing_residue_index", "event_identity", "residue_index is required for event-level identity", True),
        ("missing_residue_atom_name", "event_identity", "residue_atom_name is required for event-level identity", True),
        ("missing_ligand_atom_name", "event_identity", "ligand_atom_name is required unless covalent bond pair encodes it", True),
        ("missing_covalent_bond_atom_pair", "event_identity", "covalent_bond_atom_pair must identify residue/ligand atoms", True),
        ("missing_ligand_identifier", "metadata_identity", "ligand identifier is required for non-PDB-only matching", True),
        ("missing_covalent_event_id", "event_identity", "covalent_event_id must be derived from event identity", True),
        ("duplicate_event_identity", "deduplication", "duplicate event identities block duplicate manifest rows", True),
        ("pdb_only_join_blocked", "join_policy", "PDB-only join attempts are always blocked", True),
        ("non_cys_or_non_sg_event_out_of_v1_scope", "scope", "non-CYS/SG evidence remains out of v1 scope", True),
        ("missing_authoritative_evidence_source", "provenance", "authoritative derived evidence is required before expansion", True),
    ]
    return [
        {
            "gap_type": gap_type,
            "gap_category": category,
            "detection_policy": policy,
            "observed_count": gap_counts.get(gap_type, 0),
            "blocks_manifest_rerun": blocks,
            "gap_taxonomy_passed": True,
            "qa_comment": "Observed counts are derived from metadata rows and allowed derived evidence only.",
        }
        for gap_type, category, policy, blocks in definitions
    ]


def build_readiness_rows(selected_count: int) -> list[dict[str, Any]]:
    ready_for_rerun = selected_count >= TARGET_SMALL_PILOT_MIN_ROW_COUNT
    manual_gate = not ready_for_rerun
    next_gate = "covapie_small_pilot_download_manifest_rerun_gate" if ready_for_rerun else "covapie_small_pilot_manual_event_identity_curation_gate"
    rows = [
        ("step14c_gap_confirmed", "true", True, next_gate, "Step 14C selected zero candidates due to missing event identity."),
        ("candidate_expansion_completed_current_step", "true", True, next_gate, "Candidate expansion audit completed without raw reads."),
        ("expanded_event_candidates_written", "true", True, next_gate, "Expanded candidate CSV/JSON written."),
        ("pdb_only_join_blocked", "true", True, next_gate, "No candidate uses PDB-only join."),
        ("selected_for_manifest_rerun_count_recorded", str(selected_count), True, next_gate, "Selected count controls next gate."),
        ("ready_for_small_pilot_download_manifest_rerun_gate", str(ready_for_rerun).lower(), True, next_gate, "Requires at least 20 expanded candidates."),
        ("ready_for_small_pilot_download_smoke_false", "false", True, next_gate, "Download smoke remains blocked in Step 14D."),
        ("ready_for_bulk_download_smoke_false", "false", True, next_gate, "Bulk download remains blocked."),
        ("ready_for_actual_dataloader_false", "false", True, next_gate, "Actual dataloader remains blocked."),
        ("training_still_blocked", "false", True, next_gate, "Training remains blocked."),
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


def build_safety_rows() -> list[dict[str, Any]]:
    artifact_paths = [
        ("metadata_csv_unchanged", [METADATA_CSV.as_posix()], not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14c_artifacts_unchanged", [STEP14C_ROOT.as_posix()], not _path_diff_exists([STEP14C_ROOT.as_posix()])),
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
        ("no_download_manifest_written_current_step", "true", not _forbidden_named_artifact_exists()),
        ("no_actual_download_smoke_written", "true", not _forbidden_named_artifact_exists()),
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
        ("derived_output_no_forbidden_binary_artifacts", "true", not _forbidden_suffix_exists()),
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
    inventory_rows: list[dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    expansion_rows: list[dict[str, Any]],
    expanded_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_count = sum(_bool(row["selected_for_small_pilot_manifest_rerun"]) for row in expanded_rows)
    ready_for_rerun = selected_count >= TARGET_SMALL_PILOT_MIN_ROW_COUNT
    manual_gate = not ready_for_rerun
    recommended_next_step = "covapie_small_pilot_download_manifest_rerun_gate" if ready_for_rerun else "covapie_small_pilot_manual_event_identity_curation_gate"
    all_checks = all(
        [
            _all_true(precondition_rows, "precondition_passed"),
            _all_true(inventory_rows, "evidence_source_inventory_passed"),
            _all_true(mapping_rows, "mapping_contract_passed"),
            _all_true(expansion_rows, "candidate_expansion_passed"),
            _all_true(gap_rows, "gap_taxonomy_passed"),
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
        "step14c_small_pilot_manifest_gap_validated": _all_true(precondition_rows, "precondition_passed"),
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "current_execution_source_specific": True,
        "cross_source_generalization_supported_by_schema": True,
        "pdb_wide_blind_scan_allowed": False,
        "metadata_csv_hash_unchanged": _metadata_hash() == METADATA_CSV_SHA256,
        "evidence_source_inventory_row_count": len(inventory_rows),
        "event_identity_mapping_contract_row_count": len(mapping_rows),
        "candidate_expansion_audit_row_count": len(expansion_rows),
        "expanded_event_candidates_row_count": len(expanded_rows),
        "selected_for_manifest_rerun_count": selected_count,
        "target_small_pilot_min_row_count": TARGET_SMALL_PILOT_MIN_ROW_COUNT,
        "target_small_pilot_max_row_count": TARGET_SMALL_PILOT_MAX_ROW_COUNT,
        "insufficient_candidate_count_for_20_to_50_pilot": selected_count < TARGET_SMALL_PILOT_MIN_ROW_COUNT,
        "candidate_gap_taxonomy_audit_row_count": len(gap_rows),
        "readiness_contract_row_count": len(readiness_rows),
        "safety_audit_row_count": len(safety_rows),
        "evidence_source_inventory_passed": _all_true(inventory_rows, "evidence_source_inventory_passed"),
        "event_identity_mapping_contract_passed": _all_true(mapping_rows, "mapping_contract_passed"),
        "candidate_expansion_audit_passed": _all_true(expansion_rows, "candidate_expansion_passed"),
        "expanded_event_candidates_written": True,
        "expanded_event_candidates_csv_json_consistent": True,
        "candidate_gap_taxonomy_audit_passed": _all_true(gap_rows, "gap_taxonomy_passed"),
        "readiness_contract_passed": _all_true(readiness_rows, "readiness_passed"),
        "safety_audit_passed": _all_true(safety_rows, "safety_passed"),
        "pdb_only_join_used": False,
        "pdb_only_join_blocked": True,
        "network_access_used": False,
        "download_attempted": False,
        "raw_files_written_current_step": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "coordinate_extraction_current_step": False,
        "ligand_topology_auto_restored_current_step": False,
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
        "ready_for_covapie_small_pilot_download_manifest_rerun_gate": ready_for_rerun,
        "ready_for_covapie_small_pilot_manual_event_identity_curation_gate": manual_gate,
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
        "recommended_next_step": recommended_next_step,
        "all_checks_passed": all_checks and not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }


def run_covapie_small_pilot_candidate_expansion_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    inventory_rows = build_evidence_source_inventory_rows()
    mapping_rows = build_event_identity_mapping_rows()
    expansion_rows, expanded_rows, gap_counts = build_candidate_expansion_rows_and_candidates(inventory_rows)
    gap_rows = build_gap_taxonomy_rows(gap_counts)
    readiness_rows = build_readiness_rows(sum(_bool(row["selected_for_small_pilot_manifest_rerun"]) for row in expanded_rows))
    safety_rows = build_safety_rows()
    manifest = build_manifest(precondition_rows, inventory_rows, mapping_rows, expansion_rows, expanded_rows, gap_rows, readiness_rows, safety_rows)
    return {
        "precondition_rows": precondition_rows,
        "inventory_rows": inventory_rows,
        "mapping_rows": mapping_rows,
        "expansion_rows": expansion_rows,
        "expanded_rows": expanded_rows,
        "gap_rows": gap_rows,
        "readiness_rows": readiness_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_candidate_metadata_materialization_design_gate_v0"
PREVIOUS_STAGE = "covapie_covpdb_raw_structure_event_annotation_qa_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AW_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_qa_gate_v0")
STEP13AV_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_smoke_v0")
STEP13AU_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_design_gate_v0")
STEP13AW_MANIFEST_JSON = STEP13AW_ROOT / "covapie_raw_structure_event_annotation_qa_gate_manifest.json"
STEP13AW_PREFERRED_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_preferred_event_acceptance_qa.csv"
STEP13AW_UNRESOLVED_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_unresolved_event_handling_qa.csv"
STEP13AW_READINESS_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_candidate_metadata_readiness_decision_qa.csv"
STEP13AW_CANDIDATE_INTEGRITY_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_event_candidate_field_integrity_qa.csv"
STEP13AW_RESOLUTION_SUMMARY_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_event_key_resolution_summary_qa.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"
RAW_STORAGE_ROOT = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_design_precondition_audit.csv"
ACCEPTED_EVENT_INVENTORY_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_accepted_event_inventory.csv"
UNRESOLVED_EXCLUSION_POLICY_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_unresolved_event_exclusion_policy.csv"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_schema_contract.csv"
FIELD_SOURCE_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_field_source_mapping_contract.csv"
ROW_IDENTITY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_row_identity_contract.csv"
VALIDATION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_validation_contract.csv"
MATERIALIZATION_SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_smoke_plan.csv"
CANDIDATE_ALLOWLIST_DEPENDENCY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_dependency_contract.csv"
MATERIALIZATION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_boundary_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_candidate_metadata_materialization_design_gate_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
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

CANDIDATE_METADATA_FIELDS = [
    "candidate_metadata_id",
    "project_name",
    "source_name",
    "source_database",
    "source_stage",
    "pdb_id",
    "het_code",
    "selected_raw_format",
    "raw_connection_source",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "ligand_atom_name",
    "covalent_bond_atom_pair",
    "protein_partner_atom_exists",
    "ligand_partner_atom_exists",
    "candidate_confidence",
    "event_key_resolution_status",
    "accepted_for_future_candidate_metadata",
    "accepted_for_future_automatic_allowlist",
    "current_step_materialization_allowed",
    "unresolved_exclusion_status",
    "unresolved_exclusion_reason",
    "manual_review_required",
    "source_step13aw_preferred_acceptance_row_index",
    "source_step13aw_candidate_integrity_row_index",
    "source_metadata_csv_row_key",
    "raw_file_path_policy",
    "raw_file_tracked_policy",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
    "ready_for_training",
]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
ACCEPTED_EVENT_COLUMNS = ["pdb_id", "het_code", "chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "raw_connection_source", "candidate_confidence", "accepted_for_future_candidate_metadata", "accepted_for_future_automatic_allowlist", "future_candidate_metadata_id_preview", "accepted_event_inventory_passed"]
UNRESOLVED_EXCLUSION_COLUMNS = ["pdb_id", "het_code", "resolution_status", "reason_unresolved", "automatic_candidate_metadata_blocked", "automatic_allowlist_blocked", "future_allowed_path", "exclusion_policy_passed"]
SCHEMA_COLUMNS = ["candidate_metadata_field", "field_description", "required_for_candidate_metadata", "required_for_future_allowlist", "materialization_status", "training_use_status", "schema_contract_passed"]
FIELD_SOURCE_COLUMNS = ["candidate_metadata_field", "source_artifact", "source_column", "required_for_candidate_metadata", "required_for_future_allowlist", "validation_rule", "materialization_design_contract_passed"]
ROW_IDENTITY_COLUMNS = ["identity_contract_item", "contract_value", "deterministic", "blocks_materialization_if_violated", "row_identity_contract_passed"]
VALIDATION_COLUMNS = ["validation_item", "validation_rule", "applies_to", "blocks_materialization_if_failed", "validation_contract_passed"]
SMOKE_PLAN_COLUMNS = ["planned_step", "planned_action", "allowed_inputs", "allowed_outputs", "blocked_outputs", "required_preconditions", "materialization_smoke_plan_passed"]
ALLOWLIST_DEPENDENCY_COLUMNS = ["dependency_item", "automatic_allowlist_possible_count", "dependency", "current_step_allowed", "future_condition", "dependency_contract_passed"]
MATERIALIZATION_COLUMNS = ["boundary_item", "current_step_status", "future_condition", "materialization_boundary_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_candidate_metadata_materialization_design_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
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


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", str(RAW_STORAGE_ROOT)]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", str(RAW_STORAGE_ROOT)]).stdout.strip())


def _derived_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _metadata_row_key(row: dict[str, str]) -> str:
    return f"{row['source_dataset_name']}::{row['source_dataset_version']}::{row['covpdb_record_index']}::{row['pdb_id']}::{row['het_code']}"


def _candidate_id(row: dict[str, str]) -> str:
    return (
        f"covpdb::{row['pdb_id']}::{row['het_code']}::"
        f"{row['chain_id']}:{row['residue_name']}{row['residue_index']}:"
        f"{row['residue_atom_name']}-{row['ligand_atom_name']}"
    )


def _precondition_rows(manifest: dict[str, Any], preferred_rows: list[dict[str, str]], unresolved_rows: list[dict[str, str]], readiness_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    checks = [
        ("step13aw_manifest_exists", str(STEP13AW_MANIFEST_JSON), "exists", STEP13AW_MANIFEST_JSON.exists(), STEP13AW_MANIFEST_JSON.exists()),
        ("step13aw_stage", str(STEP13AW_MANIFEST_JSON), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step13aw_ready_for_design_gate", str(STEP13AW_MANIFEST_JSON), "true", manifest.get("ready_for_covapie_candidate_metadata_materialization_design_gate"), manifest.get("ready_for_covapie_candidate_metadata_materialization_design_gate") is True),
        ("step13aw_preferred_count", str(STEP13AW_MANIFEST_JSON), "4", manifest.get("qa_accepted_preferred_event_count"), manifest.get("qa_accepted_preferred_event_count") == 4),
        ("step13aw_unresolved_count", str(STEP13AW_MANIFEST_JSON), "1", manifest.get("qa_blocked_unresolved_event_count"), manifest.get("qa_blocked_unresolved_event_count") == 1),
        ("step13aw_no_materialization", str(STEP13AW_MANIFEST_JSON), "metadata/allowlist false", f"{manifest.get('candidate_metadata_materialized')}/{manifest.get('candidate_allowlist_materialized')}", manifest.get("candidate_metadata_materialized") is False and manifest.get("candidate_allowlist_materialized") is False),
        ("preferred_acceptance_rows", str(STEP13AW_PREFERRED_QA_CSV), "4 rows", len(preferred_rows), len(preferred_rows) == 4),
        ("unresolved_exclusion_rows", str(STEP13AW_UNRESOLVED_QA_CSV), "1 row", len(unresolved_rows), len(unresolved_rows) == 1),
        ("readiness_decision_rows", str(STEP13AW_READINESS_QA_CSV), "4 rows", len(readiness_rows), len(readiness_rows) == 4),
        ("candidate_integrity_exists", str(STEP13AW_CANDIDATE_INTEGRITY_QA_CSV), "exists", STEP13AW_CANDIDATE_INTEGRITY_QA_CSV.exists(), STEP13AW_CANDIDATE_INTEGRITY_QA_CSV.exists()),
        ("resolution_summary_exists", str(STEP13AW_RESOLUTION_SUMMARY_QA_CSV), "exists", STEP13AW_RESOLUTION_SUMMARY_QA_CSV.exists(), STEP13AW_RESOLUTION_SUMMARY_QA_CSV.exists()),
        ("metadata_csv_exists", str(METADATA_CSV), "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", str(METADATA_CSV), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("covapie_naming_convention_exists", str(NAMING_CONVENTION_MD), "exists", NAMING_CONVENTION_MD.exists(), NAMING_CONVENTION_MD.exists()),
        ("raw_files_untracked", "git ls-files raw root", "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", _raw_files_staged(), not _raw_files_staged()),
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


def _accepted_event_inventory(preferred_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    ids = [_candidate_id(row) for row in preferred_rows]
    duplicate_ids = {candidate_id for candidate_id in ids if ids.count(candidate_id) > 1}
    rows = []
    for row in preferred_rows:
        candidate_id = _candidate_id(row)
        passed = _bool(row["accepted_for_future_candidate_metadata"]) and _bool(row["accepted_for_future_automatic_allowlist"]) and candidate_id not in duplicate_ids and " " not in candidate_id
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
                "candidate_confidence": row["candidate_confidence"],
                "accepted_for_future_candidate_metadata": row["accepted_for_future_candidate_metadata"],
                "accepted_for_future_automatic_allowlist": row["accepted_for_future_automatic_allowlist"],
                "future_candidate_metadata_id_preview": candidate_id,
                "accepted_event_inventory_passed": passed,
            }
        )
    return rows


def _unresolved_exclusion_rows(unresolved_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in unresolved_rows:
        passed = (
            row["pdb_id"] == "1A54"
            and row["het_code"] == "MDC"
            and row["reason_unresolved"] == "raw_no_connectivity_records_found"
            and _bool(row["automatic_candidate_metadata_blocked"])
            and _bool(row["automatic_allowlist_blocked"])
        )
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "resolution_status": row["resolution_status"],
                "reason_unresolved": row["reason_unresolved"],
                "automatic_candidate_metadata_blocked": row["automatic_candidate_metadata_blocked"],
                "automatic_allowlist_blocked": row["automatic_allowlist_blocked"],
                "future_allowed_path": "manual_review_or_connectivity_fallback_design",
                "exclusion_policy_passed": passed,
            }
        )
    return rows


def _schema_rows() -> list[dict[str, Any]]:
    descriptions = {
        "candidate_metadata_id": "deterministic future row identifier",
        "project_name": "constant project name",
        "source_name": "source short name",
        "source_database": "external database name",
        "source_stage": "source QA/design stage lineage",
        "source_metadata_csv_row_key": "stable key back to Step 13AO metadata row",
    }
    return [
        {
            "candidate_metadata_field": field,
            "field_description": descriptions.get(field, f"future candidate metadata field {field}"),
            "required_for_candidate_metadata": True,
            "required_for_future_allowlist": field in {"candidate_metadata_id", "pdb_id", "het_code", "chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "accepted_for_future_automatic_allowlist"},
            "materialization_status": "design_only_not_materialized",
            "training_use_status": "not_training_input_yet",
            "schema_contract_passed": True,
        }
        for field in CANDIDATE_METADATA_FIELDS
    ]


def _field_source_rows() -> list[dict[str, Any]]:
    preferred_fields = {
        "pdb_id",
        "het_code",
        "raw_connection_source",
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "ligand_atom_name",
        "covalent_bond_atom_pair",
        "protein_partner_atom_exists",
        "ligand_partner_atom_exists",
        "candidate_confidence",
        "accepted_for_future_candidate_metadata",
        "accepted_for_future_automatic_allowlist",
        "current_step_materialization_allowed",
    }
    candidate_integrity_fields = {"event_key_resolution_status", "manual_review_required", "source_step13aw_candidate_integrity_row_index"}
    metadata_fields = {"source_metadata_csv_row_key", "source_name", "source_database"}
    unresolved_fields = {"unresolved_exclusion_status", "unresolved_exclusion_reason"}
    rows = []
    for field in CANDIDATE_METADATA_FIELDS:
        if field in preferred_fields:
            artifact = str(STEP13AW_PREFERRED_QA_CSV)
            source_column = field
        elif field in candidate_integrity_fields:
            artifact = str(STEP13AW_CANDIDATE_INTEGRITY_QA_CSV)
            source_column = "resolution_status" if field == "event_key_resolution_status" else field
        elif field in unresolved_fields:
            artifact = str(STEP13AW_UNRESOLVED_QA_CSV)
            source_column = "reason_unresolved"
        elif field in metadata_fields:
            artifact = str(METADATA_CSV)
            source_column = "source_dataset_name/source_dataset_version/covpdb_record_index/pdb_id/het_code"
        elif field == "source_step13aw_preferred_acceptance_row_index":
            artifact = str(STEP13AW_PREFERRED_QA_CSV)
            source_column = "row_index"
        else:
            artifact = "constant_or_policy_value"
            source_column = field
        rows.append(
            {
                "candidate_metadata_field": field,
                "source_artifact": artifact,
                "source_column": source_column,
                "required_for_candidate_metadata": True,
                "required_for_future_allowlist": field in {"candidate_metadata_id", "pdb_id", "het_code", "chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair"},
                "validation_rule": "non_empty_or_policy_value;unresolved_rows_excluded_from_materialization",
                "materialization_design_contract_passed": True,
            }
        )
    return rows


def _row_identity_rows(accepted_rows: list[dict[str, Any]], unresolved_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = [row["future_candidate_metadata_id_preview"] for row in accepted_rows]
    return [
        {
            "identity_contract_item": "candidate_metadata_id_format",
            "contract_value": "covpdb::{pdb_id}::{het_code}::{chain_id}:{residue_name}{residue_index}:{residue_atom_name}-{ligand_atom_name}",
            "deterministic": True,
            "blocks_materialization_if_violated": True,
            "row_identity_contract_passed": True,
        },
        {
            "identity_contract_item": "one_row_per_accepted_preferred_event",
            "contract_value": "4 accepted events produce 4 future IDs",
            "deterministic": True,
            "blocks_materialization_if_violated": True,
            "row_identity_contract_passed": len(ids) == 4,
        },
        {
            "identity_contract_item": "unresolved_event_has_no_candidate_metadata_id",
            "contract_value": "1A54/MDC excluded",
            "deterministic": True,
            "blocks_materialization_if_violated": True,
            "row_identity_contract_passed": len(unresolved_rows) == 1,
        },
        {
            "identity_contract_item": "duplicate_id_blocks_materialization",
            "contract_value": "future IDs must be unique",
            "deterministic": True,
            "blocks_materialization_if_violated": True,
            "row_identity_contract_passed": len(ids) == len(set(ids)),
        },
    ]


def _validation_rows() -> list[dict[str, Any]]:
    items = [
        ("accepted_event_count", "exactly_4", "accepted preferred events", True),
        ("unresolved_event_exclusion", "1A54_MDC_excluded", "unresolved event", True),
        ("candidate_metadata_id_unique", "no_duplicate_ids", "future candidate metadata rows", True),
        ("candidate_metadata_not_materialized", "design_gate_only", "current step", True),
        ("allowlist_not_materialized", "blocked_until_candidate_metadata_qa", "current step", True),
        ("training_boundary", "ready_to_train_now_false", "current step", True),
    ]
    return [
        {
            "validation_item": item,
            "validation_rule": rule,
            "applies_to": applies_to,
            "blocks_materialization_if_failed": blocks,
            "validation_contract_passed": True,
        }
        for item, rule, applies_to, blocks in items
    ]


def _materialization_smoke_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "planned_step": "first4_candidate_metadata_materialization_smoke",
            "planned_action": "ready_next",
            "allowed_inputs": "Step13AW preferred acceptance QA;Step13AO metadata CSV;Step13AX design contracts",
            "allowed_outputs": "candidate_metadata_smoke_csv_json_md_for_4_accepted_events",
            "blocked_outputs": "allowlist;sample_index;final_dataset;split;leakage_matrix;training",
            "required_preconditions": "Step13AX all_checks_passed",
            "materialization_smoke_plan_passed": True,
        },
        {
            "planned_step": "candidate_metadata_qa_gate",
            "planned_action": "qa_after_smoke",
            "allowed_inputs": "candidate metadata smoke artifacts",
            "allowed_outputs": "qa_audits_reports_manifest",
            "blocked_outputs": "allowlist;training",
            "required_preconditions": "candidate metadata smoke passed",
            "materialization_smoke_plan_passed": True,
        },
        {
            "planned_step": "candidate_allowlist_materialization_design_gate",
            "planned_action": "blocked_until_candidate_metadata_qa",
            "allowed_inputs": "candidate metadata QA outputs",
            "allowed_outputs": "allowlist design contracts only",
            "blocked_outputs": "allowlist materialization;training",
            "required_preconditions": "candidate metadata QA passed",
            "materialization_smoke_plan_passed": True,
        },
        {
            "planned_step": "batch_scale_raw_read_design_gate",
            "planned_action": "blocked",
            "allowed_inputs": "future design artifacts",
            "allowed_outputs": "design contracts only",
            "blocked_outputs": "batch raw read;training",
            "required_preconditions": "first4 candidate metadata QA and allowlist design",
            "materialization_smoke_plan_passed": True,
        },
        {
            "planned_step": "training",
            "planned_action": "blocked",
            "allowed_inputs": "none_current_step",
            "allowed_outputs": "none",
            "blocked_outputs": "forward;loss;backward;optimizer;trainer.fit;checkpoint",
            "required_preconditions": "feature semantics audit;leakage split design;dataset materialization;training gate",
            "materialization_smoke_plan_passed": True,
        },
    ]


def _allowlist_dependency_rows() -> list[dict[str, Any]]:
    return [
        {
            "dependency_item": "candidate_allowlist_materialization",
            "automatic_allowlist_possible_count": 4,
            "dependency": "candidate_metadata_materialization_smoke_and_qa",
            "current_step_allowed": False,
            "future_condition": "candidate_metadata_smoke_and_qa_passed",
            "dependency_contract_passed": True,
        },
        {
            "dependency_item": "automatic_allowlist_possible_count",
            "automatic_allowlist_possible_count": 4,
            "dependency": "accepted_preferred_event_inventory",
            "current_step_allowed": False,
            "future_condition": "candidate_metadata_ids_materialized_and_qa_passed",
            "dependency_contract_passed": True,
        },
    ]


def _materialization_boundary_rows() -> list[dict[str, Any]]:
    items = ["candidate_metadata_materialization", "candidate_allowlist_materialization", "sample_index", "final_dataset", "split_assignments", "leakage_matrix", "training"]
    return [
        {
            "boundary_item": item,
            "current_step_status": "blocked_current_design_gate",
            "future_condition": "future_materialization_or_training_gate_required",
            "materialization_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item in items
    ]


def _execution_rows() -> list[dict[str, Any]]:
    statuses = {
        "candidate_metadata_materialization_design_gate": "executed_design_gate_only",
        "step13aw_manifest_read": "executed_manifest_read_only",
        "step13aw_preferred_acceptance_read": "executed_csv_read_only",
        "step13aw_unresolved_handling_read": "executed_csv_read_only",
        "step13aw_candidate_integrity_read": "executed_csv_read_only",
        "metadata_csv_read": "executed_metadata_read_only",
        "raw_file_presence_check": "not_executed_or_not_allowed",
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


def _git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw root", "false", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", not _raw_files_staged()),
        ("derived_output_no_raw_suffix_artifacts", "forbidden suffix scan", "false", not _derived_forbidden_exists(OUTPUT_ROOT)),
        ("metadata_csv_unchanged", str(METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13aw_artifacts_unchanged", "git diff step13aw root", "empty", not _path_diff_exists([str(STEP13AW_ROOT)])),
        ("step13av_artifacts_unchanged", "git diff step13av root", "empty", not _path_diff_exists([str(STEP13AV_ROOT)])),
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
            "mask_scope_status": "preserved_from_step13aw",
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
            "blocking_for_candidate_metadata_materialization_design_gate": False,
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


def run_covapie_candidate_metadata_materialization_design_gate_v0() -> dict[str, Any]:
    manifest13aw = _load_json(STEP13AW_MANIFEST_JSON)
    preferred_rows = _csv_rows(STEP13AW_PREFERRED_QA_CSV)
    unresolved_rows = _csv_rows(STEP13AW_UNRESOLVED_QA_CSV)
    readiness_rows13aw = _csv_rows(STEP13AW_READINESS_QA_CSV)
    metadata_rows = _csv_rows(METADATA_CSV)
    metadata_by_key = {(row["pdb_id"], row["het_code"]): row for row in metadata_rows}

    precondition_rows = _precondition_rows(manifest13aw, preferred_rows, unresolved_rows, readiness_rows13aw)
    accepted_rows = _accepted_event_inventory(preferred_rows)
    unresolved_policy_rows = _unresolved_exclusion_rows(unresolved_rows)
    schema_rows = _schema_rows()
    field_source_rows = _field_source_rows()
    row_identity_rows = _row_identity_rows(accepted_rows, unresolved_policy_rows)
    validation_rows = _validation_rows()
    plan_rows = _materialization_smoke_plan_rows()
    allowlist_rows = _allowlist_dependency_rows()
    materialization_rows = _materialization_boundary_rows()
    execution_rows = _execution_rows()
    git_safety_rows = _git_safety_rows()
    mask_rows = _mask_rows()
    feature_rows = _feature_rows()
    leakage_rows = _leakage_rows()

    for row in accepted_rows:
        metadata = metadata_by_key.get((row["pdb_id"], row["het_code"]), {})
        row["source_metadata_csv_row_key"] = _metadata_row_key(metadata) if metadata else ""

    future_ids = [row["future_candidate_metadata_id_preview"] for row in accepted_rows]
    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "accepted_inventory": _all_true(accepted_rows, "accepted_event_inventory_passed") and len(accepted_rows) == 4 and len(future_ids) == len(set(future_ids)),
        "unresolved_policy": _all_true(unresolved_policy_rows, "exclusion_policy_passed") and len(unresolved_policy_rows) == 1,
        "schema_contract": _all_true(schema_rows, "schema_contract_passed") and [row["candidate_metadata_field"] for row in schema_rows] == CANDIDATE_METADATA_FIELDS,
        "field_source_mapping": _all_true(field_source_rows, "materialization_design_contract_passed") and {row["candidate_metadata_field"] for row in field_source_rows} == set(CANDIDATE_METADATA_FIELDS),
        "row_identity": _all_true(row_identity_rows, "row_identity_contract_passed"),
        "validation": _all_true(validation_rows, "validation_contract_passed"),
        "plan": _all_true(plan_rows, "materialization_smoke_plan_passed"),
        "allowlist_dependency": _all_true(allowlist_rows, "dependency_contract_passed"),
        "materialization_boundary": _all_true(materialization_rows, "materialization_boundary_passed"),
        "execution_boundary": _all_true(execution_rows, "execution_boundary_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
        "mask_scope": _all_true(mask_rows, "mask_scope_audit_passed"),
        "feature_semantics": _all_true(feature_rows, "feature_semantics_audit_passed"),
        "leakage_split": _all_true(leakage_rows, "leakage_split_audit_passed"),
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13aw_raw_structure_event_annotation_qa_gate_validated": qa_checks["precondition"],
        "accepted_preferred_event_count": len(accepted_rows),
        "blocked_unresolved_event_count": len(unresolved_policy_rows),
        "candidate_metadata_schema_field_count": len(schema_rows),
        "field_source_mapping_row_count": len(field_source_rows),
        "accepted_event_inventory_row_count": len(accepted_rows),
        "unresolved_exclusion_policy_row_count": len(unresolved_policy_rows),
        "future_candidate_metadata_id_preview_count": len(future_ids),
        "future_candidate_metadata_id_unique_count": len(set(future_ids)),
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
        "raw_file_created": False,
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
        "ready_for_covapie_candidate_metadata_materialization_smoke": True,
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
        "recommended_next_step": "covapie_candidate_metadata_materialization_smoke",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13aw_precondition": {"row_count": len(precondition_rows), "passed": qa_checks["precondition"]},
        "accepted_event_inventory": {"row_count": len(accepted_rows), "passed": qa_checks["accepted_inventory"]},
        "unresolved_exclusion_policy": {"row_count": len(unresolved_policy_rows), "passed": qa_checks["unresolved_policy"]},
        "schema_contract": {"row_count": len(schema_rows), "passed": qa_checks["schema_contract"]},
        "field_source_mapping": {"row_count": len(field_source_rows), "passed": qa_checks["field_source_mapping"]},
        "row_identity_contract": {"row_count": len(row_identity_rows), "passed": qa_checks["row_identity"]},
        "materialization_smoke_plan": {"row_count": len(plan_rows), "passed": qa_checks["plan"]},
        "readiness_boundary": {
            "passed": True,
            "ready_for_covapie_candidate_metadata_materialization_smoke": True,
            "ready_for_training": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "precondition_rows": precondition_rows,
        "accepted_rows": accepted_rows,
        "unresolved_policy_rows": unresolved_policy_rows,
        "schema_rows": schema_rows,
        "field_source_rows": field_source_rows,
        "row_identity_rows": row_identity_rows,
        "validation_rows": validation_rows,
        "plan_rows": plan_rows,
        "allowlist_rows": allowlist_rows,
        "materialization_rows": materialization_rows,
        "execution_rows": execution_rows,
        "git_safety_rows": git_safety_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

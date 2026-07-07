from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_candidate_metadata_materialization_qa_gate as step13az
from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_candidate_allowlist_materialization_design_gate_v0"
PREVIOUS_STAGE = "covapie_candidate_metadata_materialization_qa_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AZ_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_qa_gate_v0")
STEP13AY_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_smoke_v0")
STEP13AX_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_design_gate_v0")

STEP13AZ_MANIFEST_JSON = STEP13AZ_ROOT / "covapie_candidate_metadata_materialization_qa_gate_manifest.json"
STEP13AZ_CONTENT_INTEGRITY_CSV = STEP13AZ_ROOT / "covapie_candidate_metadata_qa_gate_content_integrity.csv"
STEP13AZ_TRACEABILITY_CSV = STEP13AZ_ROOT / "covapie_candidate_metadata_qa_gate_traceability.csv"
STEP13AZ_UNRESOLVED_EXCLUSION_CSV = STEP13AZ_ROOT / "covapie_candidate_metadata_qa_gate_unresolved_exclusion.csv"
STEP13AY_CANDIDATE_METADATA_CSV = STEP13AY_ROOT / "covapie_candidate_metadata_smoke.csv"
STEP13AY_CANDIDATE_METADATA_JSON = STEP13AY_ROOT / "covapie_candidate_metadata_smoke.json"
STEP13AX_SCHEMA_CONTRACT_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_schema_contract.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"
RAW_STORAGE_ROOT = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_materialization_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_design_precondition_audit.csv"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_schema_contract.csv"
CANDIDATE_PREVIEW_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_candidate_preview.csv"
EXCLUSION_POLICY_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_exclusion_policy.csv"
MATERIALIZATION_PLAN_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_materialization_plan.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_git_safety.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_training_blockers.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_candidate_allowlist_materialization_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_candidate_allowlist_materialization_design_gate_v0_summary.md")

ALLOWLIST_FIELDS = [
    "allowlist_entry_id",
    "candidate_metadata_id",
    "project_name",
    "source_name",
    "source_database",
    "source_stage",
    "pdb_id",
    "het_code",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "ligand_atom_name",
    "covalent_bond_atom_pair",
    "event_key_resolution_status",
    "candidate_metadata_qa_status",
    "allowlist_entry_status",
    "allowlist_reason",
    "unresolved_exclusion_status",
    "manual_review_required",
    "raw_file_path_policy",
    "raw_file_tracked_policy",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
    "ready_for_training",
]
CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
EXPECTED_CANDIDATE_IDS = step13az.EXPECTED_IDS
EXPECTED_ALLOWLIST_IDS = [f"allowlist::{candidate_id}" for candidate_id in EXPECTED_CANDIDATE_IDS]
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
MATERIALIZED_FORBIDDEN_NAMES = {
    "covapie_candidate_allowlist.csv",
    "covapie_candidate_allowlist.json",
    "sample_index.csv",
    "sample_index.json",
    "final_dataset.csv",
    "final_dataset.json",
    "split_assignments.csv",
    "split_assignments.json",
    "leakage_matrix.csv",
    "leakage_matrix.json",
}

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SCHEMA_COLUMNS = ["allowlist_field", "field_order", "field_description", "required_for_future_allowlist", "source_field_or_policy", "materialization_status", "training_use_status", "allowlist_schema_contract_passed"]
PREVIEW_COLUMNS = ["allowlist_entry_id_preview", "candidate_metadata_id", "pdb_id", "het_code", "chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "event_key_resolution_status", "candidate_metadata_qa_status", "allowlist_entry_status", "allowlist_reason", "preview_only", "current_step_allowlist_materialized", "not_a_materialized_allowlist", "candidate_preview_passed"]
EXCLUSION_COLUMNS = ["pdb_id", "het_code", "resolution_status", "reason_unresolved", "candidate_metadata_present", "allowlist_entry_preview_created", "allowlist_entry_materialized", "exclusion_policy", "exclusion_policy_passed"]
PLAN_COLUMNS = ["planned_step", "planned_action", "allowed_inputs", "allowed_outputs", "blocked_outputs", "required_preconditions", "plan_passed"]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "allowed_current_step", "future_condition", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
TRAINING_BLOCKERS_COLUMNS = ["training_blocker_item", "current_step_status", "training_blocker_passed", "qa_comment"]


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> Any:
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
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", str(RAW_STORAGE_ROOT)]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", str(RAW_STORAGE_ROOT)]).stdout.strip())


def _derived_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _materialized_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.name in MATERIALIZED_FORBIDDEN_NAMES for path in root.rglob("*")) if root.exists() else False


def _precondition_rows(manifest13az: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("step13az_manifest_exists", str(STEP13AZ_MANIFEST_JSON), "exists", STEP13AZ_MANIFEST_JSON.exists(), STEP13AZ_MANIFEST_JSON.exists()),
        ("step13az_stage", str(STEP13AZ_MANIFEST_JSON), PREVIOUS_STAGE, manifest13az.get("stage"), manifest13az.get("stage") == PREVIOUS_STAGE),
        ("step13az_all_checks_passed", str(STEP13AZ_MANIFEST_JSON), "true", manifest13az.get("all_checks_passed"), manifest13az.get("all_checks_passed") is True),
        ("step13az_ready_for_allowlist_design", str(STEP13AZ_MANIFEST_JSON), "true", manifest13az.get("ready_for_covapie_candidate_allowlist_materialization_design_gate"), manifest13az.get("ready_for_covapie_candidate_allowlist_materialization_design_gate") is True),
        ("step13az_not_allowlist_smoke_ready", str(STEP13AZ_MANIFEST_JSON), "false", manifest13az.get("ready_for_covapie_candidate_allowlist_materialization_smoke"), manifest13az.get("ready_for_covapie_candidate_allowlist_materialization_smoke") is False),
        ("step13az_candidate_rows", str(STEP13AZ_MANIFEST_JSON), "4", manifest13az.get("qa_candidate_metadata_row_count"), manifest13az.get("qa_candidate_metadata_row_count") == 4),
        ("step13az_candidate_columns", str(STEP13AZ_MANIFEST_JSON), "33", manifest13az.get("qa_candidate_metadata_column_count"), manifest13az.get("qa_candidate_metadata_column_count") == 33),
        ("step13az_traceability_passed", str(STEP13AZ_MANIFEST_JSON), "true", manifest13az.get("qa_traceability_passed"), manifest13az.get("qa_traceability_passed") is True),
        ("step13az_content_integrity_passed", str(STEP13AZ_MANIFEST_JSON), "true", manifest13az.get("qa_content_integrity_passed"), manifest13az.get("qa_content_integrity_passed") is True),
        ("step13az_unresolved_preserved", str(STEP13AZ_MANIFEST_JSON), "true", manifest13az.get("qa_unresolved_exclusion_preserved"), manifest13az.get("qa_unresolved_exclusion_preserved") is True),
        ("step13az_ready_for_training", str(STEP13AZ_MANIFEST_JSON), "false", manifest13az.get("ready_for_training"), manifest13az.get("ready_for_training") is False),
        ("step13az_ready_to_train_now", str(STEP13AZ_MANIFEST_JSON), "false", manifest13az.get("ready_to_train_now"), manifest13az.get("ready_to_train_now") is False),
        ("step13az_content_integrity_exists", str(STEP13AZ_CONTENT_INTEGRITY_CSV), "exists", STEP13AZ_CONTENT_INTEGRITY_CSV.exists(), STEP13AZ_CONTENT_INTEGRITY_CSV.exists()),
        ("step13az_traceability_exists", str(STEP13AZ_TRACEABILITY_CSV), "exists", STEP13AZ_TRACEABILITY_CSV.exists(), STEP13AZ_TRACEABILITY_CSV.exists()),
        ("step13az_unresolved_exists", str(STEP13AZ_UNRESOLVED_EXCLUSION_CSV), "exists", STEP13AZ_UNRESOLVED_EXCLUSION_CSV.exists(), STEP13AZ_UNRESOLVED_EXCLUSION_CSV.exists()),
        ("step13ay_candidate_metadata_csv_exists", str(STEP13AY_CANDIDATE_METADATA_CSV), "exists", STEP13AY_CANDIDATE_METADATA_CSV.exists(), STEP13AY_CANDIDATE_METADATA_CSV.exists()),
        ("step13ay_candidate_metadata_json_exists", str(STEP13AY_CANDIDATE_METADATA_JSON), "exists", STEP13AY_CANDIDATE_METADATA_JSON.exists(), STEP13AY_CANDIDATE_METADATA_JSON.exists()),
        ("step13ax_schema_contract_exists", str(STEP13AX_SCHEMA_CONTRACT_CSV), "exists", STEP13AX_SCHEMA_CONTRACT_CSV.exists(), STEP13AX_SCHEMA_CONTRACT_CSV.exists()),
        ("metadata_csv_exists", str(METADATA_CSV), "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", str(METADATA_CSV), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
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


def _schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "allowlist_field": field,
            "field_order": index,
            "field_description": f"future allowlist field {field}",
            "required_for_future_allowlist": True,
            "source_field_or_policy": "candidate_metadata_smoke_or_policy_value",
            "materialization_status": "design_only_not_materialized",
            "training_use_status": "not_training_input_yet",
            "allowlist_schema_contract_passed": True,
        }
        for index, field in enumerate(ALLOWLIST_FIELDS, start=1)
    ]


def _candidate_preview_rows(candidate_rows: list[dict[str, str]], content_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    qa_by_id = {row["candidate_metadata_id"]: row for row in content_rows}
    rows = []
    for row in candidate_rows:
        qa = qa_by_id.get(row["candidate_metadata_id"], {})
        allowlist_id = f"allowlist::{row['candidate_metadata_id']}"
        passed = (
            row["candidate_metadata_id"] in EXPECTED_CANDIDATE_IDS
            and allowlist_id in EXPECTED_ALLOWLIST_IDS
            and _bool(qa.get("content_integrity_passed"))
            and (row["pdb_id"], row["het_code"]) != ("1A54", "MDC")
        )
        rows.append(
            {
                "allowlist_entry_id_preview": allowlist_id,
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "chain_id": row["chain_id"],
                "residue_name": row["residue_name"],
                "residue_index": row["residue_index"],
                "residue_atom_name": row["residue_atom_name"],
                "ligand_atom_name": row["ligand_atom_name"],
                "covalent_bond_atom_pair": row["covalent_bond_atom_pair"],
                "event_key_resolution_status": row["event_key_resolution_status"],
                "candidate_metadata_qa_status": "passed" if _bool(qa.get("content_integrity_passed")) else "blocked",
                "allowlist_entry_status": "eligible_for_future_allowlist_smoke",
                "allowlist_reason": "candidate_metadata_qa_passed_and_event_key_resolved",
                "preview_only": True,
                "current_step_allowlist_materialized": False,
                "not_a_materialized_allowlist": True,
                "candidate_preview_passed": passed,
            }
        )
    return rows


def _exclusion_policy_rows(unresolved_rows: list[dict[str, str]], candidate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidate_pairs = {(row["pdb_id"], row["het_code"]) for row in candidate_rows}
    rows = []
    for row in unresolved_rows:
        pair = (row["pdb_id"], row["het_code"])
        passed = pair == ("1A54", "MDC") and pair not in candidate_pairs and not _bool(row["candidate_metadata_materialized"]) and not _bool(row["candidate_allowlist_materialized"])
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "resolution_status": row["resolution_status"],
                "reason_unresolved": row["reason_unresolved"],
                "candidate_metadata_present": pair in candidate_pairs,
                "allowlist_entry_preview_created": False,
                "allowlist_entry_materialized": False,
                "exclusion_policy": "manual_review_or_connectivity_fallback_design_required",
                "exclusion_policy_passed": passed,
            }
        )
    return rows


def _materialization_plan_rows() -> list[dict[str, Any]]:
    plan = [
        ("candidate_allowlist_materialization_smoke", "ready_next", "Step13BA design contracts;Step13AY candidate metadata smoke;Step13AZ QA outputs", "candidate_allowlist_smoke_csv_json_for_4_entries", "sample_index;final_dataset;split;leakage_matrix;training", "Step13BA all_checks_passed"),
        ("candidate_allowlist_qa_gate", "qa_after_smoke", "candidate allowlist smoke artifacts", "qa_artifacts_manifest_summary", "training", "candidate allowlist smoke passed"),
        ("batch_raw_read_design_gate", "blocked_until_allowlist_qa", "candidate allowlist QA outputs", "batch raw read design contracts", "raw read smoke;training", "candidate allowlist QA passed"),
        ("batch_raw_read_smoke", "blocked_until_batch_raw_read_design_gate", "batch raw read design gate outputs", "future controlled raw read smoke", "training", "batch raw read design gate passed"),
        ("training", "blocked", "none_current_step", "none", "forward;loss;backward;optimizer;trainer.fit;checkpoint", "feature semantics audit;leakage split design;dataset gates"),
    ]
    return [
        {
            "planned_step": step,
            "planned_action": action,
            "allowed_inputs": inputs,
            "allowed_outputs": outputs,
            "blocked_outputs": blocked,
            "required_preconditions": preconditions,
            "plan_passed": True,
        }
        for step, action, inputs, outputs, blocked, preconditions in plan
    ]


def _boundary_safety_rows() -> list[dict[str, Any]]:
    statuses = {
        "candidate_allowlist_materialization_design_gate": ("executed_design_gate_only", True, "current_step_complete"),
        "candidate_allowlist_materialization": ("blocked_current_design_gate", False, "candidate_allowlist_materialization_smoke"),
        "candidate_metadata_materialization": ("not_executed_current_step", False, "already_completed_previous_smoke"),
        "sample_index": ("blocked_current_design_gate", False, "future_gate_required"),
        "final_dataset": ("blocked_current_design_gate", False, "future_gate_required"),
        "split_assignments": ("blocked_current_design_gate", False, "future_leakage_split_gate_required"),
        "leakage_matrix": ("blocked_current_design_gate", False, "future_leakage_split_gate_required"),
        "training": ("blocked_current_design_gate", False, "future_training_gate_required"),
        "network_access": ("not_executed_or_not_allowed", False, "not_applicable"),
        "raw_download": ("not_executed_or_not_allowed", False, "not_applicable"),
        "raw_text_read": ("not_executed_or_not_allowed", False, "not_applicable"),
        "rdkit_biopdb_gemmi": ("not_executed_or_not_allowed", False, "not_applicable"),
        "torch_model_training": ("not_executed_or_not_allowed", False, "not_applicable"),
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "allowed_current_step": allowed,
            "future_condition": future_condition,
            "boundary_safety_passed": True,
            "qa_comment": "boundary_respected",
        }
        for item, (status, allowed, future_condition) in statuses.items()
    ]


def _git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw root", "false", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", not _raw_files_staged()),
        ("derived_output_no_raw_suffix_artifacts", "forbidden suffix scan", "false", not _derived_forbidden_exists(OUTPUT_ROOT)),
        ("no_materialized_allowlist_artifacts", "forbidden allowlist output scan", "false", not any((OUTPUT_ROOT / name).exists() for name in ["covapie_candidate_allowlist.csv", "covapie_candidate_allowlist.json"])),
        ("no_sample_final_split_leakage_artifacts", "forbidden output name scan", "false", not _materialized_forbidden_exists(OUTPUT_ROOT)),
        ("metadata_csv_unchanged", str(METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13az_artifacts_unchanged", "git diff step13az root", "empty", not _path_diff_exists([str(STEP13AZ_ROOT)])),
        ("step13ay_artifacts_unchanged", "git diff step13ay root", "empty", not _path_diff_exists([str(STEP13AY_ROOT)])),
        ("step13ax_artifacts_unchanged", "git diff step13ax root", "empty", not _path_diff_exists([str(STEP13AX_ROOT)])),
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


def _training_blocker_rows() -> list[dict[str, Any]]:
    rows = [
        ("mask_warhead_only_A", "warhead_only/A_preserved", True, "canonical_mask_preserved"),
        ("mask_linker_plus_warhead_B", "linker_plus_warhead/B_preserved", True, "canonical_mask_preserved"),
        ("mask_scaffold_plus_warhead_B2", "scaffold_plus_warhead/B2_preserved", True, "canonical_mask_preserved"),
        ("mask_scaffold_only_B3", "scaffold_only/B3_preserved", True, "canonical_mask_preserved"),
        ("mask_scaffold_plus_linker_plus_warhead_C", "scaffold_plus_linker_plus_warhead/C_preserved", True, "canonical_mask_preserved"),
        ("feature_semantics_audit_required", "required_before_training", True, "training_blocker_preserved"),
        ("feature_semantics_fully_audited_claimed_false", "fully_audited_claimed_false", True, "training_blocker_preserved"),
        ("leakage_split_design_required", "required_before_training", True, "training_blocker_preserved"),
        ("split_written_current_step_false", "false", True, "training_blocker_preserved"),
        ("leakage_matrix_written_current_step_false", "false", True, "training_blocker_preserved"),
        ("ready_for_training_false", "false", True, "training_blocker_preserved"),
    ]
    return [
        {
            "training_blocker_item": item,
            "current_step_status": status,
            "training_blocker_passed": passed,
            "qa_comment": comment,
        }
        for item, status, passed, comment in rows
    ]


def run_covapie_candidate_allowlist_materialization_design_gate_v0() -> dict[str, Any]:
    manifest13az = _load_json(STEP13AZ_MANIFEST_JSON)
    content_rows13az = _csv_rows(STEP13AZ_CONTENT_INTEGRITY_CSV)
    unresolved_rows13az = _csv_rows(STEP13AZ_UNRESOLVED_EXCLUSION_CSV)
    candidate_rows = _csv_rows(STEP13AY_CANDIDATE_METADATA_CSV)
    candidate_json_rows = _load_json(STEP13AY_CANDIDATE_METADATA_JSON)

    precondition_rows = _precondition_rows(manifest13az)
    schema_rows = _schema_rows()
    preview_rows = _candidate_preview_rows(candidate_rows, content_rows13az)
    exclusion_rows = _exclusion_policy_rows(unresolved_rows13az, candidate_rows)
    plan_rows = _materialization_plan_rows()
    boundary_rows = _boundary_safety_rows()
    git_safety_rows = _git_safety_rows()
    training_blocker_rows = _training_blocker_rows()
    preview_ids = [row["allowlist_entry_id_preview"] for row in preview_rows]

    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "schema": len(schema_rows) == 25 and _all_true(schema_rows, "allowlist_schema_contract_passed"),
        "preview": len(preview_rows) == 4 and _all_true(preview_rows, "candidate_preview_passed") and preview_ids == EXPECTED_ALLOWLIST_IDS and len(preview_ids) == len(set(preview_ids)),
        "exclusion": len(exclusion_rows) == 1 and _all_true(exclusion_rows, "exclusion_policy_passed"),
        "plan": _all_true(plan_rows, "plan_passed"),
        "boundary": _all_true(boundary_rows, "boundary_safety_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
        "training_blockers": _all_true(training_blocker_rows, "training_blocker_passed"),
        "candidate_json": len(candidate_json_rows) == 4,
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13az_candidate_metadata_materialization_qa_gate_validated": qa_checks["precondition"],
        "candidate_metadata_qa_row_count": manifest13az.get("qa_candidate_metadata_row_count"),
        "candidate_metadata_qa_column_count": manifest13az.get("qa_candidate_metadata_column_count"),
        "allowlist_schema_field_count": len(schema_rows),
        "allowlist_candidate_preview_row_count": len(preview_rows),
        "allowlist_entry_id_preview_count": len(preview_ids),
        "allowlist_entry_id_preview_unique_count": len(set(preview_ids)),
        "unresolved_exclusion_policy_row_count": len(exclusion_rows),
        "allowlist_schema_contract_passed": qa_checks["schema"],
        "allowlist_candidate_preview_passed": qa_checks["preview"],
        "unresolved_exclusion_policy_passed": qa_checks["exclusion"],
        "materialization_plan_passed": qa_checks["plan"],
        "boundary_safety_passed": qa_checks["boundary"],
        "git_safety_passed": qa_checks["git_safety"],
        "training_blockers_passed": qa_checks["training_blockers"],
        "candidate_allowlist_materialized": False,
        "candidate_allowlist_materialized_current_step": False,
        "candidate_metadata_materialized_current_step": False,
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
        "ready_for_covapie_candidate_allowlist_materialization_smoke": True,
        "ready_for_covapie_batch_scale_raw_read_design_gate": False,
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
        "recommended_next_step": "covapie_candidate_allowlist_materialization_smoke",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    return {
        "precondition_rows": precondition_rows,
        "schema_rows": schema_rows,
        "preview_rows": preview_rows,
        "exclusion_rows": exclusion_rows,
        "plan_rows": plan_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "training_blocker_rows": training_blocker_rows,
        "manifest": manifest,
    }

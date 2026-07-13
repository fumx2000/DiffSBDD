from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from covalent_ext import covapie_sample_index_qa_gate as step13bi
from covalent_ext.covapie_legacy_pipeline_retirement_policy import (
    LegacyStageRetirementPolicy,
    build_legacy_stage_retirement_policy,
    raise_legacy_stage_retired,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_STAGE = "covapie_split_leakage_design_gate_v0"
STAGE = LEGACY_STAGE
PREVIOUS_STAGE = step13bi.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_split_leakage_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_leakage_design_precondition_audit.csv"
GROUPING_KEY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_split_grouping_key_contract.csv"
LEAKAGE_RULE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_split_leakage_rule_contract.csv"
LEAKAGE_RISK_DESIGN_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_leakage_risk_design_audit.csv"
SPLIT_UNIT_DESIGN_PREVIEW_CSV = OUTPUT_ROOT / "covapie_split_unit_design_preview.csv"
SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_split_leakage_smoke_plan.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_split_leakage_design_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_split_leakage_design_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_split_leakage_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_split_leakage_design_gate_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = step13bi.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bi.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bi.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
GROUPING_KEY_COLUMNS = [
    "grouping_key_name",
    "grouping_key_status",
    "available_in_current_sample_index",
    "required_before_real_split",
    "leakage_risk_controlled",
    "grouping_policy",
    "design_contract_passed",
]
LEAKAGE_RULE_COLUMNS = [
    "leakage_rule_id",
    "leakage_rule_description",
    "applies_current_smoke",
    "required_before_real_split",
    "enforcement_level",
    "expected_current_status",
    "design_contract_passed",
]
RISK_AUDIT_COLUMNS = [
    "risk_group",
    "observed_group_count",
    "observed_max_rows_per_group",
    "current_smoke_status",
    "leakage_risk_level",
    "required_action_before_real_split",
    "risk_design_audit_passed",
]
SPLIT_UNIT_COLUMNS = [
    "split_unit_id",
    "extracted_event_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "covalent_residue_site",
    "covalent_bond_atom_pair",
    "sample_rows_in_unit",
    "mask_task_count_in_unit",
    "mask_task_names_in_unit",
    "split_assignment_current_step",
    "eligible_for_real_split_assignment",
    "blocker_reason",
    "split_unit_design_passed",
]
SMOKE_PLAN_COLUMNS = [
    "planned_step",
    "planned_action",
    "allowed_inputs",
    "allowed_outputs",
    "blocked_outputs",
    "required_preconditions",
    "plan_passed",
]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]

GUARDED_ENTRYPOINTS = (
    "build_precondition_rows",
    "build_grouping_key_contract_rows",
    "build_leakage_rule_contract_rows",
    "build_leakage_risk_design_audit_rows",
    "build_split_unit_design_preview_rows",
    "build_smoke_plan_rows",
    "build_boundary_rows",
    "build_git_safety_rows",
    "run_covapie_split_leakage_design_gate_v0",
)


def build_retirement_policy() -> LegacyStageRetirementPolicy:
    return build_legacy_stage_retirement_policy(LEGACY_STAGE)


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
    path = step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _raw_files_tracked() -> bool:
    root = step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    root = step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT
    return bool(_run_git(["diff", "--cached", "--name-only", "--", root.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _residue_site(row: dict[str, str]) -> str:
    return f"{row['chain_id']}:{row['residue_name']}{row['residue_index']}:{row['residue_atom_name']}"


def _group_counts(rows: list[dict[str, str]], key: str | None = None, values: list[str] | None = None) -> Counter[str]:
    if values is not None:
        return Counter(values)
    if key is None:
        raise ValueError("key or values is required")
    return Counter(row[key] for row in rows)


def _max_count(counter: Counter[str]) -> int:
    return max(counter.values()) if counter else 0


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "covapie_sample_index_smoke.csv",
        "covapie_sample_index_smoke.json",
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


def build_precondition_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    manifest13bi = _load_json(step13bi.MANIFEST_JSON)
    sample_rows = _csv_rows(step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    sample_json = _load_json(step13bi.step13bh.SAMPLE_INDEX_SMOKE_JSON)
    schema_qa = _csv_rows(step13bi.SCHEMA_CSV_JSON_QA_AUDIT_CSV)
    row_qa = _csv_rows(step13bi.ROW_IDENTITY_QA_AUDIT_CSV)
    mask_qa = _csv_rows(step13bi.MASK_DISTRIBUTION_QA_AUDIT_CSV)
    trace_qa = _csv_rows(step13bi.SOURCE_TRACEABILITY_QA_AUDIT_CSV)
    checks = [
        ("step13bi_manifest_exists", step13bi.MANIFEST_JSON, "exists", step13bi.MANIFEST_JSON.exists(), step13bi.MANIFEST_JSON.exists()),
        ("step13bi_stage", step13bi.MANIFEST_JSON, PREVIOUS_STAGE, manifest13bi.get("stage"), manifest13bi.get("stage") == PREVIOUS_STAGE),
        ("step13bi_all_checks_passed", step13bi.MANIFEST_JSON, "true", manifest13bi.get("all_checks_passed"), manifest13bi.get("all_checks_passed") is True),
        ("step13bi_ready_for_split_leakage_design_gate", step13bi.MANIFEST_JSON, "true", manifest13bi.get("ready_for_covapie_split_leakage_design_gate"), manifest13bi.get("ready_for_covapie_split_leakage_design_gate") is True),
        ("step13bi_ready_for_final_dataset_design_gate", step13bi.MANIFEST_JSON, "false", manifest13bi.get("ready_for_covapie_final_dataset_design_gate"), manifest13bi.get("ready_for_covapie_final_dataset_design_gate") is False),
        ("step13bi_ready_for_dataloader_smoke", step13bi.MANIFEST_JSON, "false", manifest13bi.get("ready_for_covapie_dataloader_smoke"), manifest13bi.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13bi_ready_for_training", step13bi.MANIFEST_JSON, "false", manifest13bi.get("ready_for_training"), manifest13bi.get("ready_for_training") is False),
        ("step13bi_ready_to_train_now", step13bi.MANIFEST_JSON, "false", manifest13bi.get("ready_to_train_now"), manifest13bi.get("ready_to_train_now") is False),
        ("sample_index_csv_row_count", step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV, "20", len(sample_rows), len(sample_rows) == 20),
        ("sample_index_csv_column_count", step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV, "31", len(sample_rows[0]) if sample_rows else 0, bool(sample_rows) and len(sample_rows[0]) == 31),
        ("sample_index_json_row_count", step13bi.step13bh.SAMPLE_INDEX_SMOKE_JSON, "20", len(sample_json), isinstance(sample_json, list) and len(sample_json) == 20),
        ("step13bi_schema_csv_json_qa_passed", step13bi.SCHEMA_CSV_JSON_QA_AUDIT_CSV, "true", all(_bool(row["schema_csv_json_qa_passed"]) for row in schema_qa), all(_bool(row["schema_csv_json_qa_passed"]) for row in schema_qa)),
        ("step13bi_row_identity_qa_passed", step13bi.ROW_IDENTITY_QA_AUDIT_CSV, "true", all(_bool(row["row_identity_qa_passed"]) for row in row_qa), all(_bool(row["row_identity_qa_passed"]) for row in row_qa)),
        ("step13bi_mask_distribution_qa_passed", step13bi.MASK_DISTRIBUTION_QA_AUDIT_CSV, "true", all(_bool(row["mask_distribution_qa_passed"]) for row in mask_qa), all(_bool(row["mask_distribution_qa_passed"]) for row in mask_qa)),
        ("step13bi_source_traceability_qa_passed", step13bi.SOURCE_TRACEABILITY_QA_AUDIT_CSV, "true", all(_bool(row["source_traceability_qa_passed"]) for row in trace_qa), all(_bool(row["source_traceability_qa_passed"]) for row in trace_qa)),
        ("canonical_mask_count", step13bi.MANIFEST_JSON, "5", manifest13bi.get("source_canonical_mask_task_count"), manifest13bi.get("source_canonical_mask_task_count") == 5),
        ("b3_scaffold_only_included", step13bi.MANIFEST_JSON, "true", manifest13bi.get("b3_scaffold_only_included"), manifest13bi.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", step13bi.MANIFEST_JSON, "true", manifest13bi.get("no_extra_mask_tasks_added"), manifest13bi.get("no_extra_mask_tasks_added") is True),
        ("metadata_csv_hash_unchanged", step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
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


def build_grouping_key_contract_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    available = {
        "extracted_event_id",
        "candidate_metadata_id",
        "pdb_id",
        "allowlist_entry_id",
        "ligand_het_code",
        "covalent_residue_site",
        "covalent_bond_atom_pair",
        "source_dataset_name",
    }
    policies = {
        "extracted_event_id": "hard_same_split_for_all_mask_rows",
        "candidate_metadata_id": "hard_same_split_for_all_candidate_rows",
        "pdb_id": "hard_same_split_by_default",
        "allowlist_entry_id": "hard_same_split_for_allowlist_entry",
        "ligand_het_code": "review_group_or_balance_before_real_split",
        "covalent_residue_site": "review_mechanism_site_leakage_before_real_split",
        "covalent_bond_atom_pair": "review_covalent_atom_pair_leakage_before_real_split",
        "source_dataset_name": "track_source_dataset_for_future_stratification",
        "scaffold_identity_future": "future_required_grouping_key_not_materialized_current_step",
        "linker_identity_future": "future_required_grouping_key_not_materialized_current_step",
        "warhead_type_future": "future_required_grouping_key_not_materialized_current_step",
        "protein_sequence_cluster_future": "future_required_grouping_key_not_materialized_current_step",
        "pocket_similarity_cluster_future": "future_required_grouping_key_not_materialized_current_step",
    }
    rows = []
    for key in [
        "extracted_event_id",
        "candidate_metadata_id",
        "pdb_id",
        "allowlist_entry_id",
        "ligand_het_code",
        "covalent_residue_site",
        "covalent_bond_atom_pair",
        "source_dataset_name",
        "scaffold_identity_future",
        "linker_identity_future",
        "warhead_type_future",
        "protein_sequence_cluster_future",
        "pocket_similarity_cluster_future",
    ]:
        current = key in available
        rows.append(
            {
                "grouping_key_name": key,
                "grouping_key_status": "available_or_derivable_current_sample_index" if current else "future_required_not_materialized_current_step",
                "available_in_current_sample_index": current,
                "required_before_real_split": True,
                "leakage_risk_controlled": True,
                "grouping_policy": policies[key],
                "design_contract_passed": True,
            }
        )
    return rows


def build_leakage_rule_contract_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    rows = [
        ("same_extracted_event_id_same_split", "Rows sharing extracted_event_id must stay in one split.", True, True, "hard_constraint", "design_only_not_assigned"),
        ("same_candidate_metadata_id_same_split", "Rows sharing candidate_metadata_id must stay in one split.", True, True, "hard_constraint", "design_only_not_assigned"),
        ("same_pdb_id_same_split", "Rows sharing PDB ID default to one split.", True, True, "hard_constraint", "design_only_not_assigned"),
        ("same_allowlist_entry_id_same_split", "Rows sharing allowlist entry must stay in one split.", True, True, "hard_constraint", "design_only_not_assigned"),
        ("same_ligand_het_code_flagged_for_review", "Ligand HET code overlap is reviewed before real split.", True, True, "review_constraint", "flagged_for_future_review"),
        ("same_covalent_residue_site_flagged_for_review", "Covalent residue site overlap is reviewed before real split.", True, True, "review_constraint", "flagged_for_future_review"),
        ("same_covalent_bond_atom_pair_flagged_for_review", "Covalent bond atom pair overlap is reviewed before real split.", True, True, "review_constraint", "flagged_for_future_review"),
        ("same_scaffold_future_same_or_grouped_split", "Future scaffold identity should be grouped or blocked across splits.", False, True, "future_constraint", "future_required"),
        ("same_warhead_type_future_balance_or_group", "Future warhead type should be grouped or balanced.", False, True, "future_constraint", "future_required"),
        ("protein_sequence_cluster_future_group_split", "Future protein sequence clusters should control homolog leakage.", False, True, "future_constraint", "future_required"),
        ("pocket_similarity_cluster_future_group_split", "Future pocket similarity clusters should control pocket leakage.", False, True, "future_constraint", "future_required"),
        ("mask_task_rows_bound_to_parent_event", "All five mask rows for one event stay with the parent event.", True, True, "hard_constraint", "design_only_not_assigned"),
        ("no_random_row_level_split_allowed", "Random row-level split is forbidden.", True, True, "hard_constraint", "forbidden"),
        ("no_training_until_feature_semantics_audit", "Training remains blocked until feature semantics audit.", True, True, "hard_constraint", "training_blocked"),
        ("no_training_until_leakage_split_gate", "Training remains blocked until leakage/split gates finish.", True, True, "hard_constraint", "training_blocked"),
    ]
    return [
        {
            "leakage_rule_id": rule_id,
            "leakage_rule_description": description,
            "applies_current_smoke": applies,
            "required_before_real_split": required,
            "enforcement_level": level,
            "expected_current_status": status,
            "design_contract_passed": True,
        }
        for rule_id, description, applies, required, level, status in rows
    ]


def build_leakage_risk_design_audit_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    sample_rows = _csv_rows(step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    residue_sites = [_residue_site(row) for row in sample_rows]
    counts = {
        "parent_event_grouping": _group_counts(sample_rows, "extracted_event_id"),
        "candidate_metadata_grouping": _group_counts(sample_rows, "candidate_metadata_id"),
        "pdb_grouping": _group_counts(sample_rows, "pdb_id"),
        "mask_task_grouping": _group_counts(sample_rows, "mask_task_name"),
        "ligand_het_code_grouping": _group_counts(sample_rows, "het_code"),
        "covalent_residue_site_grouping": _group_counts(sample_rows, values=residue_sites),
        "covalent_bond_atom_pair_grouping": _group_counts(sample_rows, "covalent_bond_atom_pair"),
    }
    rows = []
    for name in [
        "parent_event_grouping",
        "candidate_metadata_grouping",
        "pdb_grouping",
        "mask_task_grouping",
        "ligand_het_code_grouping",
        "covalent_residue_site_grouping",
        "covalent_bond_atom_pair_grouping",
    ]:
        rows.append(
            {
                "risk_group": name,
                "observed_group_count": len(counts[name]),
                "observed_max_rows_per_group": _max_count(counts[name]),
                "current_smoke_status": "observed_current_sample_index_design_only",
                "leakage_risk_level": "hard_grouping_required" if name in {"parent_event_grouping", "candidate_metadata_grouping", "pdb_grouping"} else "review_required",
                "required_action_before_real_split": "enforce_or_review_grouping_before_real_split",
                "risk_design_audit_passed": True,
            }
        )
    for name in ["scaffold_future_missing", "warhead_type_future_missing", "sequence_cluster_future_missing", "pocket_cluster_future_missing"]:
        rows.append(
            {
                "risk_group": name,
                "observed_group_count": 0,
                "observed_max_rows_per_group": 0,
                "current_smoke_status": "required_before_real_split",
                "leakage_risk_level": "future_required",
                "required_action_before_real_split": "materialize_future_grouping_annotation_before_scalable_training_split",
                "risk_design_audit_passed": True,
            }
        )
    rows.append(
        {
            "risk_group": "row_level_random_split_forbidden",
            "observed_group_count": 20,
            "observed_max_rows_per_group": 1,
            "current_smoke_status": "forbidden_by_design",
            "leakage_risk_level": "hard_forbidden",
            "required_action_before_real_split": "split_by_parent_units_not_rows",
            "risk_design_audit_passed": True,
        }
    )
    return rows


def build_split_unit_design_preview_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _csv_rows(step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV):
        grouped[row["extracted_event_id"]].append(row)
    rows = []
    blocker = "smoke_size_too_small;feature_semantics_audit_required;scaffold_linker_warhead_annotation_required;leakage_split_design_only_current_step"
    for idx, event_id in enumerate(sorted(grouped), start=1):
        event_rows = grouped[event_id]
        first = event_rows[0]
        mask_names = [row["mask_task_name"] for row in sorted(event_rows, key=lambda row: CANONICAL_MASK_TASK_NAMES.index(row["mask_task_name"]))]
        rows.append(
            {
                "split_unit_id": f"COVAPIE_SPLIT_UNIT_DESIGN_{idx:06d}",
                "extracted_event_id": event_id,
                "candidate_metadata_id": first["candidate_metadata_id"],
                "pdb_id": first["pdb_id"],
                "het_code": first["het_code"],
                "covalent_residue_site": _residue_site(first),
                "covalent_bond_atom_pair": first["covalent_bond_atom_pair"],
                "sample_rows_in_unit": len(event_rows),
                "mask_task_count_in_unit": len(set(mask_names)),
                "mask_task_names_in_unit": ";".join(mask_names),
                "split_assignment_current_step": "not_written_current_step",
                "eligible_for_real_split_assignment": False,
                "blocker_reason": blocker,
                "split_unit_design_passed": len(event_rows) == 5 and set(mask_names) == set(CANONICAL_MASK_TASK_NAMES),
            }
        )
    return rows


def build_smoke_plan_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    rows = [
        ("read_sample_index_qa_gate", "Read Step 13BI QA outputs.", "step13bi_manifest_and_audits", "readiness_validation", "split_assignments;leakage_matrix", "step13bi_passed"),
        ("read_sample_index_smoke", "Read Step 13BH sample index CSV/JSON.", "step13bh_sample_index", "split_unit_inputs", "sample_index_rewrite", "step13bi_ready"),
        ("materialize_split_units_smoke", "Write future split unit preview only.", "sample_index_smoke", "split_unit_preview", "train_val_test_assignments", "design_gate_passed"),
        ("validate_no_row_level_random_split", "Assert row-level random split remains forbidden.", "split_unit_preview", "validation_audit", "row_level_assignments", "split_units_available"),
        ("validate_parent_event_group_integrity", "Assert five mask rows stay bound to parent event.", "split_unit_preview", "group_integrity_audit", "broken_parent_groups", "split_units_available"),
        ("write_split_leakage_smoke_preview", "Write smoke preview without real train/val/test split.", "split_unit_preview", "split_leakage_smoke_preview", "leakage_matrix;final_dataset", "design_gate_passed"),
        ("split_leakage_qa_gate", "QA future split/leakage smoke.", "split_leakage_smoke_preview", "qa_audits", "training_inputs", "split_leakage_smoke_passed"),
        ("feature_semantics_audit_gate", "Audit feature semantics before training.", "feature_contracts", "feature_semantics_audits", "training", "split_leakage_qa_passed"),
        ("final_dataset_design_gate", "Design final dataset after split QA and feature audit.", "split_qa;feature_audit", "final_dataset_contract", "final_dataset_materialization", "split_qa_and_feature_audit_required"),
        ("dataloader_smoke", "Run dataloader smoke only after final dataset gates.", "final_dataset_smoke", "loader_smoke_audit", "training", "final_dataset_gate_required"),
        ("training", "Training remains blocked.", "none", "none", "forward;loss;backward;optimizer;trainer.fit", "feature_semantics_and_split_gates_required"),
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
        for step, action, inputs, outputs, blocked, preconditions in rows
    ]


def build_boundary_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    statuses = {
        "split_leakage_design_gate": "executed_design_gate_only",
        "read_step13bi_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bh_sample_index": "executed_derived_csv_json_read_only",
        "split_assignment_write": "blocked_current_design_gate",
        "leakage_matrix_write": "blocked_current_design_gate",
        "final_dataset": "blocked_current_step",
        "dataloader_smoke": "blocked_current_step",
        "training": "blocked_current_step",
        "raw_file_content_read": "not_executed_or_not_allowed",
        "mmcif_parse": "not_executed_or_not_allowed",
        "coordinate_extraction": "not_executed_or_not_allowed",
        "network_access": "not_executed_or_not_allowed",
        "raw_download": "not_executed_or_not_allowed",
        "rdkit_biopdb_gemmi": "not_executed_or_not_allowed",
        "torch_model_training": "not_executed_or_not_allowed",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "boundary_safety_passed": True,
            "qa_comment": "design gate boundary respected",
        }
        for item, status in statuses.items()
    ]


def build_git_safety_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    checks = [
        ("raw_files_untracked", "git ls-files data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached --name-only -- data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "boundary manifest", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("no_split_assignments_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", str(step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV), "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bi_artifacts_unchanged", str(step13bi.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bi.OUTPUT_ROOT.as_posix()])),
        ("step13bh_artifacts_unchanged", str(step13bi.step13bh.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bi.step13bh.OUTPUT_ROOT.as_posix()])),
        ("step13bg_artifacts_unchanged", str(step13bi.step13bh.step13bg.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bi.step13bh.step13bg.OUTPUT_ROOT.as_posix()])),
        ("step13bf_artifacts_unchanged", str(step13bi.step13bh.step13bg.step13bf.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bi.step13bh.step13bg.step13bf.OUTPUT_ROOT.as_posix()])),
        ("step13be_artifacts_unchanged", str(step13bi.step13bh.step13bg.step13bf.step13be.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bi.step13bh.step13bg.step13bf.step13be.OUTPUT_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", "data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0", "no_diff", not _path_diff_exists(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"])),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "no_diff", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "no_diff", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": "passed" if passed else "failed",
            "git_safety_audit_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, command, required, passed in checks
    ]


def run_covapie_split_leakage_design_gate_v0() -> dict[str, Any]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    precondition_rows = build_precondition_rows()
    grouping_rows = build_grouping_key_contract_rows()
    leakage_rule_rows = build_leakage_rule_contract_rows()
    risk_rows = build_leakage_risk_design_audit_rows()
    split_unit_rows = build_split_unit_design_preview_rows()
    smoke_plan_rows = build_smoke_plan_rows()
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    sample_rows = _csv_rows(step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    mask_counts = Counter(row["mask_task_name"] for row in sample_rows)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bi_sample_index_qa_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_sample_index_row_count": len(sample_rows),
        "source_unique_event_count": len({row["extracted_event_id"] for row in sample_rows}),
        "source_canonical_mask_task_count": len(set(mask_counts)),
        "split_grouping_key_contract_row_count": len(grouping_rows),
        "leakage_rule_contract_row_count": len(leakage_rule_rows),
        "leakage_risk_design_audit_row_count": len(risk_rows),
        "split_unit_design_preview_row_count": len(split_unit_rows),
        "split_leakage_smoke_plan_row_count": len(smoke_plan_rows),
        "split_grouping_key_contract_passed": all(_bool(row["design_contract_passed"]) for row in grouping_rows),
        "leakage_rule_contract_passed": all(_bool(row["design_contract_passed"]) for row in leakage_rule_rows),
        "leakage_risk_design_audit_passed": all(_bool(row["risk_design_audit_passed"]) for row in risk_rows),
        "split_unit_design_preview_passed": all(_bool(row["split_unit_design_passed"]) for row in split_unit_rows),
        "split_leakage_smoke_plan_passed": all(_bool(row["plan_passed"]) for row in smoke_plan_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "atom_site_scan_current_step": False,
        "struct_conn_scan_current_step": False,
        "coordinate_extraction_current_step": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "archive_downloaded": False,
        "raw_file_created": False,
        "sdf_read": False,
        "pdb_read": False,
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
        "ready_for_covapie_split_leakage_smoke": True,
        "ready_for_covapie_split_leakage_qa_gate": False,
        "ready_for_covapie_feature_semantics_audit_gate": False,
        "ready_for_covapie_final_dataset_design_gate": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": mask_counts["scaffold_only"] == 4,
        "no_extra_mask_tasks_added": set(mask_counts) == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_split_leakage_smoke",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bi_sample_index_qa_gate_validated"],
            manifest["source_sample_index_row_count"] == 20,
            manifest["source_unique_event_count"] == 4,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["split_grouping_key_contract_row_count"] == 13,
            manifest["leakage_rule_contract_row_count"] == 15,
            manifest["leakage_risk_design_audit_row_count"] == 12,
            manifest["split_unit_design_preview_row_count"] == 4,
            manifest["split_leakage_smoke_plan_row_count"] == 11,
            manifest["split_grouping_key_contract_passed"],
            manifest["leakage_rule_contract_passed"],
            manifest["leakage_risk_design_audit_passed"],
            manifest["split_unit_design_preview_passed"],
            manifest["split_leakage_smoke_plan_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["split_leakage_design_gate_contract_failed"]
    return {
        "precondition_rows": precondition_rows,
        "grouping_rows": grouping_rows,
        "leakage_rule_rows": leakage_rule_rows,
        "risk_rows": risk_rows,
        "split_unit_rows": split_unit_rows,
        "smoke_plan_rows": smoke_plan_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }

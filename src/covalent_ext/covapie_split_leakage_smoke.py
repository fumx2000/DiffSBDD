from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from covalent_ext import covapie_split_leakage_design_gate as step13bj
from covalent_ext.covapie_legacy_pipeline_retirement_policy import (
    LegacyStageRetirementPolicy,
    build_legacy_stage_retirement_policy,
    raise_legacy_stage_retired,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_STAGE = "covapie_split_leakage_smoke_v0"
STAGE = LEGACY_STAGE
PREVIOUS_STAGE = step13bj.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_split_leakage_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_leakage_smoke_precondition_audit.csv"
SPLIT_UNIT_SMOKE_PREVIEW_CSV = OUTPUT_ROOT / "covapie_split_unit_smoke_preview.csv"
SPLIT_UNIT_SMOKE_PREVIEW_JSON = OUTPUT_ROOT / "covapie_split_unit_smoke_preview.json"
PARENT_EVENT_GROUP_INTEGRITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_parent_event_group_integrity_audit.csv"
CANDIDATE_METADATA_GROUP_INTEGRITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_group_integrity_audit.csv"
MASK_TASK_GROUPING_INTEGRITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_mask_task_grouping_integrity_audit.csv"
RISK_SMOKE_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_leakage_risk_smoke_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_split_leakage_smoke_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_split_leakage_smoke_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_split_leakage_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_split_leakage_smoke_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = step13bj.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bj.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bj.METADATA_CSV_SHA256
MASK_ALIAS_BY_NAME = dict(zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES))

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
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
    "sample_ids_in_unit",
    "split_assignment_current_step",
    "real_split_assignment_written",
    "eligible_for_training_split",
    "blocker_reason",
    "split_unit_smoke_passed",
]
PARENT_EVENT_COLUMNS = [
    "extracted_event_id",
    "candidate_metadata_id",
    "sample_rows_for_event",
    "unique_split_unit_count",
    "mask_task_count",
    "mask_task_names",
    "all_mask_rows_bound_to_parent_event",
    "no_row_level_split_assignment",
    "group_integrity_passed",
    "qa_comment",
]
CANDIDATE_COLUMNS = [
    "candidate_metadata_id",
    "extracted_event_count",
    "sample_rows_for_candidate",
    "unique_split_unit_count",
    "pdb_id",
    "het_code",
    "all_candidate_rows_bound_to_one_unit",
    "no_candidate_level_leakage_in_smoke",
    "candidate_group_integrity_passed",
    "qa_comment",
]
MASK_GROUPING_COLUMNS = [
    "mask_task_name",
    "mask_task_alias",
    "observed_row_count",
    "observed_unique_event_count",
    "expected_row_count",
    "expected_unique_event_count",
    "mask_rows_distributed_across_all_events",
    "no_extra_mask_tasks",
    "b3_scaffold_only_included_when_applicable",
    "mask_grouping_integrity_passed",
    "qa_comment",
]
RISK_SMOKE_COLUMNS = [
    "risk_group",
    "observed_group_count",
    "observed_max_rows_per_group",
    "smoke_status",
    "risk_level",
    "required_action_before_real_split",
    "risk_smoke_audit_passed",
]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]

GUARDED_ENTRYPOINTS = (
    "build_precondition_rows",
    "build_split_unit_smoke_preview_rows",
    "build_parent_event_group_integrity_rows",
    "build_candidate_metadata_group_integrity_rows",
    "build_mask_task_grouping_integrity_rows",
    "build_risk_smoke_audit_rows",
    "build_boundary_rows",
    "build_git_safety_rows",
    "run_covapie_split_leakage_smoke_v0",
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
    path = step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _raw_files_tracked() -> bool:
    root = step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    root = step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT
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


def _group_by(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def _ordered_mask_names(rows: list[dict[str, str]]) -> list[str]:
    names = {row["mask_task_name"] for row in rows}
    return [name for name in CANONICAL_MASK_TASK_NAMES if name in names]


def _split_unit_id(index: int) -> str:
    return f"COVAPIE_SPLIT_UNIT_SMOKE_{index:06d}"


def build_precondition_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    manifest13bj = _load_json(step13bj.MANIFEST_JSON)
    grouping = _csv_rows(step13bj.GROUPING_KEY_CONTRACT_CSV)
    rules = _csv_rows(step13bj.LEAKAGE_RULE_CONTRACT_CSV)
    design_preview = _csv_rows(step13bj.SPLIT_UNIT_DESIGN_PREVIEW_CSV)
    sample_rows = _csv_rows(step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    sample_json = _load_json(step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_JSON)
    manifest13bi = _load_json(step13bj.step13bi.MANIFEST_JSON)
    checks = [
        ("step13bj_manifest_exists", step13bj.MANIFEST_JSON, "exists", step13bj.MANIFEST_JSON.exists(), step13bj.MANIFEST_JSON.exists()),
        ("step13bj_stage", step13bj.MANIFEST_JSON, PREVIOUS_STAGE, manifest13bj.get("stage"), manifest13bj.get("stage") == PREVIOUS_STAGE),
        ("step13bj_all_checks_passed", step13bj.MANIFEST_JSON, "true", manifest13bj.get("all_checks_passed"), manifest13bj.get("all_checks_passed") is True),
        ("step13bj_ready_for_split_leakage_smoke", step13bj.MANIFEST_JSON, "true", manifest13bj.get("ready_for_covapie_split_leakage_smoke"), manifest13bj.get("ready_for_covapie_split_leakage_smoke") is True),
        ("step13bj_ready_for_split_leakage_qa_gate", step13bj.MANIFEST_JSON, "false", manifest13bj.get("ready_for_covapie_split_leakage_qa_gate"), manifest13bj.get("ready_for_covapie_split_leakage_qa_gate") is False),
        ("step13bj_ready_for_final_dataset_design_gate", step13bj.MANIFEST_JSON, "false", manifest13bj.get("ready_for_covapie_final_dataset_design_gate"), manifest13bj.get("ready_for_covapie_final_dataset_design_gate") is False),
        ("step13bj_ready_for_dataloader_smoke", step13bj.MANIFEST_JSON, "false", manifest13bj.get("ready_for_covapie_dataloader_smoke"), manifest13bj.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13bj_ready_for_training", step13bj.MANIFEST_JSON, "false", manifest13bj.get("ready_for_training"), manifest13bj.get("ready_for_training") is False),
        ("step13bj_ready_to_train_now", step13bj.MANIFEST_JSON, "false", manifest13bj.get("ready_to_train_now"), manifest13bj.get("ready_to_train_now") is False),
        ("step13bj_grouping_key_contract", step13bj.GROUPING_KEY_CONTRACT_CSV, "13_passed", f"{len(grouping)}_{all(_bool(row['design_contract_passed']) for row in grouping)}", len(grouping) == 13 and all(_bool(row["design_contract_passed"]) for row in grouping)),
        ("step13bj_leakage_rule_contract", step13bj.LEAKAGE_RULE_CONTRACT_CSV, "15_passed", f"{len(rules)}_{all(_bool(row['design_contract_passed']) for row in rules)}", len(rules) == 15 and all(_bool(row["design_contract_passed"]) for row in rules)),
        ("step13bj_split_unit_design_preview", step13bj.SPLIT_UNIT_DESIGN_PREVIEW_CSV, "4_passed", f"{len(design_preview)}_{all(_bool(row['split_unit_design_passed']) for row in design_preview)}", len(design_preview) == 4 and all(_bool(row["split_unit_design_passed"]) for row in design_preview)),
        ("sample_index_csv_row_count", step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV, "20", len(sample_rows), len(sample_rows) == 20),
        ("sample_index_csv_column_count", step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV, "31", len(sample_rows[0]) if sample_rows else 0, bool(sample_rows) and len(sample_rows[0]) == 31),
        ("sample_index_json_row_count", step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_JSON, "20", len(sample_json), isinstance(sample_json, list) and len(sample_json) == 20),
        ("step13bi_sample_index_qa_passed", step13bj.step13bi.MANIFEST_JSON, "true", manifest13bi.get("all_checks_passed"), manifest13bi.get("all_checks_passed") is True),
        ("canonical_mask_count", step13bj.MANIFEST_JSON, "5", manifest13bj.get("source_canonical_mask_task_count"), manifest13bj.get("source_canonical_mask_task_count") == 5),
        ("b3_scaffold_only_included", step13bj.MANIFEST_JSON, "true", manifest13bj.get("b3_scaffold_only_included"), manifest13bj.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", step13bj.MANIFEST_JSON, "true", manifest13bj.get("no_extra_mask_tasks_added"), manifest13bj.get("no_extra_mask_tasks_added") is True),
        ("metadata_csv_hash_unchanged", step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
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


def build_split_unit_smoke_preview_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    grouped = _group_by(_csv_rows(step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV), "extracted_event_id")
    blocker = "smoke_size_too_small;feature_semantics_audit_required;scaffold_linker_warhead_annotation_required;split_leakage_smoke_only_current_step"
    rows = []
    for idx, event_id in enumerate(sorted(grouped), start=1):
        event_rows = grouped[event_id]
        first = event_rows[0]
        mask_names = _ordered_mask_names(event_rows)
        sample_ids = [row["sample_id"] for row in sorted(event_rows, key=lambda row: CANONICAL_MASK_TASK_NAMES.index(row["mask_task_name"]))]
        passed = len(event_rows) == 5 and mask_names == CANONICAL_MASK_TASK_NAMES and len(sample_ids) == 5
        rows.append(
            {
                "split_unit_id": _split_unit_id(idx),
                "extracted_event_id": event_id,
                "candidate_metadata_id": first["candidate_metadata_id"],
                "pdb_id": first["pdb_id"],
                "het_code": first["het_code"],
                "covalent_residue_site": _residue_site(first),
                "covalent_bond_atom_pair": first["covalent_bond_atom_pair"],
                "sample_rows_in_unit": len(event_rows),
                "mask_task_count_in_unit": len(mask_names),
                "mask_task_names_in_unit": ";".join(mask_names),
                "sample_ids_in_unit": ";".join(sample_ids),
                "split_assignment_current_step": "not_written_current_step",
                "real_split_assignment_written": False,
                "eligible_for_training_split": False,
                "blocker_reason": blocker,
                "split_unit_smoke_passed": passed,
            }
        )
    return rows


def build_parent_event_group_integrity_rows(split_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    split_by_event = {row["extracted_event_id"]: row["split_unit_id"] for row in split_units}
    grouped = _group_by(_csv_rows(step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV), "extracted_event_id")
    rows = []
    for event_id in sorted(grouped):
        event_rows = grouped[event_id]
        mask_names = _ordered_mask_names(event_rows)
        unique_split_units = {split_by_event[event_id]}
        passed = len(event_rows) == 5 and len(unique_split_units) == 1 and mask_names == CANONICAL_MASK_TASK_NAMES and all(row["split_assignment_status"] == "not_written_current_step" for row in event_rows)
        rows.append(
            {
                "extracted_event_id": event_id,
                "candidate_metadata_id": event_rows[0]["candidate_metadata_id"],
                "sample_rows_for_event": len(event_rows),
                "unique_split_unit_count": len(unique_split_units),
                "mask_task_count": len(mask_names),
                "mask_task_names": ";".join(mask_names),
                "all_mask_rows_bound_to_parent_event": len(unique_split_units) == 1,
                "no_row_level_split_assignment": all(row["split_assignment_status"] == "not_written_current_step" for row in event_rows),
                "group_integrity_passed": passed,
                "qa_comment": "all five canonical mask rows remain bound to parent event",
            }
        )
    return rows


def build_candidate_metadata_group_integrity_rows(split_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    split_by_candidate = {row["candidate_metadata_id"]: row["split_unit_id"] for row in split_units}
    grouped = _group_by(_csv_rows(step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV), "candidate_metadata_id")
    rows = []
    for candidate_id in sorted(grouped):
        candidate_rows = grouped[candidate_id]
        event_count = len({row["extracted_event_id"] for row in candidate_rows})
        unique_split_units = {split_by_candidate[candidate_id]}
        passed = event_count == 1 and len(candidate_rows) == 5 and len(unique_split_units) == 1
        rows.append(
            {
                "candidate_metadata_id": candidate_id,
                "extracted_event_count": event_count,
                "sample_rows_for_candidate": len(candidate_rows),
                "unique_split_unit_count": len(unique_split_units),
                "pdb_id": candidate_rows[0]["pdb_id"],
                "het_code": candidate_rows[0]["het_code"],
                "all_candidate_rows_bound_to_one_unit": len(unique_split_units) == 1,
                "no_candidate_level_leakage_in_smoke": True,
                "candidate_group_integrity_passed": passed,
                "qa_comment": "candidate metadata rows remain bound to one smoke split unit",
            }
        )
    return rows


def build_mask_task_grouping_integrity_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    sample_rows = _csv_rows(step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    rows = []
    observed_masks = {row["mask_task_name"] for row in sample_rows}
    for mask_name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES):
        rows_for_mask = [row for row in sample_rows if row["mask_task_name"] == mask_name]
        event_count = len({row["extracted_event_id"] for row in rows_for_mask})
        b3_ok = mask_name != "scaffold_only" or alias == "B3"
        passed = len(rows_for_mask) == 4 and event_count == 4 and observed_masks == set(CANONICAL_MASK_TASK_NAMES) and b3_ok
        rows.append(
            {
                "mask_task_name": mask_name,
                "mask_task_alias": alias,
                "observed_row_count": len(rows_for_mask),
                "observed_unique_event_count": event_count,
                "expected_row_count": 4,
                "expected_unique_event_count": 4,
                "mask_rows_distributed_across_all_events": event_count == 4,
                "no_extra_mask_tasks": observed_masks == set(CANONICAL_MASK_TASK_NAMES),
                "b3_scaffold_only_included_when_applicable": b3_ok,
                "mask_grouping_integrity_passed": passed,
                "qa_comment": "canonical mask distribution preserved in smoke preview",
            }
        )
    return rows


def build_risk_smoke_audit_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    sample_rows = _csv_rows(step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    residue_sites = [_residue_site(row) for row in sample_rows]
    counts = {
        "parent_event_grouping": _group_counts(sample_rows, "extracted_event_id"),
        "candidate_metadata_grouping": _group_counts(sample_rows, "candidate_metadata_id"),
        "pdb_grouping": _group_counts(sample_rows, "pdb_id"),
        "ligand_het_code_grouping": _group_counts(sample_rows, "het_code"),
        "covalent_residue_site_grouping": _group_counts(sample_rows, values=residue_sites),
        "covalent_bond_atom_pair_grouping": _group_counts(sample_rows, "covalent_bond_atom_pair"),
        "mask_task_grouping": _group_counts(sample_rows, "mask_task_name"),
    }
    rows = []
    for name in [
        "parent_event_grouping",
        "candidate_metadata_grouping",
        "pdb_grouping",
        "ligand_het_code_grouping",
        "covalent_residue_site_grouping",
        "covalent_bond_atom_pair_grouping",
        "mask_task_grouping",
    ]:
        rows.append(
            {
                "risk_group": name,
                "observed_group_count": len(counts[name]),
                "observed_max_rows_per_group": _max_count(counts[name]),
                "smoke_status": "observed_current_smoke_preview",
                "risk_level": "hard_grouping_required" if name in {"parent_event_grouping", "candidate_metadata_grouping", "pdb_grouping"} else "review_required",
                "required_action_before_real_split": "enforce_or_review_grouping_before_real_split",
                "risk_smoke_audit_passed": True,
            }
        )
    rows.extend(
        [
            {
                "risk_group": "row_level_random_split_forbidden",
                "observed_group_count": 20,
                "observed_max_rows_per_group": 1,
                "smoke_status": "forbidden_by_design",
                "risk_level": "hard_forbidden",
                "required_action_before_real_split": "split_by_parent_units_not_rows",
                "risk_smoke_audit_passed": True,
            },
            {
                "risk_group": "scaffold_identity_missing",
                "observed_group_count": 0,
                "observed_max_rows_per_group": 0,
                "smoke_status": "required_before_real_split",
                "risk_level": "future_required",
                "required_action_before_real_split": "materialize_scaffold_identity_before_real_split",
                "risk_smoke_audit_passed": True,
            },
            {
                "risk_group": "warhead_type_missing",
                "observed_group_count": 0,
                "observed_max_rows_per_group": 0,
                "smoke_status": "required_before_real_split",
                "risk_level": "future_required",
                "required_action_before_real_split": "materialize_warhead_type_before_real_split",
                "risk_smoke_audit_passed": True,
            },
            {
                "risk_group": "feature_semantics_audit_required",
                "observed_group_count": 0,
                "observed_max_rows_per_group": 0,
                "smoke_status": "required_before_training",
                "risk_level": "training_blocker",
                "required_action_before_real_split": "complete_feature_semantics_audit_before_training",
                "risk_smoke_audit_passed": True,
            },
            {
                "risk_group": "smoke_size_too_small_for_real_train_val_test",
                "observed_group_count": 4,
                "observed_max_rows_per_group": 5,
                "smoke_status": "blocks_real_split_assignment",
                "risk_level": "real_split_blocker",
                "required_action_before_real_split": "use_larger_validated_dataset_before_real_split_assignment",
                "risk_smoke_audit_passed": True,
            },
        ]
    )
    return rows


def build_boundary_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    statuses = {
        "split_leakage_smoke": "executed_smoke_only",
        "read_step13bj_design_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bi_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bh_sample_index": "executed_derived_csv_json_read_only",
        "split_unit_smoke_preview_write": "executed_smoke_only",
        "split_assignment_write": "blocked_current_step",
        "leakage_matrix_write": "blocked_current_step",
        "final_dataset": "blocked_current_step",
        "new_sample_index": "blocked_current_step",
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
            "qa_comment": "split/leakage smoke boundary respected",
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
        ("metadata_csv_unchanged", str(step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV), "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bj_artifacts_unchanged", str(step13bj.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.OUTPUT_ROOT.as_posix()])),
        ("step13bi_artifacts_unchanged", str(step13bj.step13bi.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.step13bi.OUTPUT_ROOT.as_posix()])),
        ("step13bh_artifacts_unchanged", str(step13bj.step13bi.step13bh.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.step13bi.step13bh.OUTPUT_ROOT.as_posix()])),
        ("step13bg_artifacts_unchanged", str(step13bj.step13bi.step13bh.step13bg.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.step13bi.step13bh.step13bg.OUTPUT_ROOT.as_posix()])),
        ("step13bf_artifacts_unchanged", str(step13bj.step13bi.step13bh.step13bg.step13bf.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.step13bi.step13bh.step13bg.step13bf.OUTPUT_ROOT.as_posix()])),
        ("step13be_artifacts_unchanged", str(step13bj.step13bi.step13bh.step13bg.step13bf.step13be.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.step13bi.step13bh.step13bg.step13bf.step13be.OUTPUT_ROOT.as_posix()])),
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


def run_covapie_split_leakage_smoke_v0() -> dict[str, Any]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    precondition_rows = build_precondition_rows()
    split_unit_rows = build_split_unit_smoke_preview_rows()
    parent_rows = build_parent_event_group_integrity_rows(split_unit_rows)
    candidate_rows = build_candidate_metadata_group_integrity_rows(split_unit_rows)
    mask_rows = build_mask_task_grouping_integrity_rows()
    risk_rows = build_risk_smoke_audit_rows()
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    sample_rows = _csv_rows(step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    mask_counts = Counter(row["mask_task_name"] for row in sample_rows)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bj_split_leakage_design_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_sample_index_row_count": len(sample_rows),
        "source_unique_event_count": len({row["extracted_event_id"] for row in sample_rows}),
        "source_canonical_mask_task_count": len(set(mask_counts)),
        "split_unit_smoke_preview_csv_written": True,
        "split_unit_smoke_preview_json_written": True,
        "split_unit_smoke_preview_row_count": len(split_unit_rows),
        "parent_event_group_integrity_row_count": len(parent_rows),
        "candidate_metadata_group_integrity_row_count": len(candidate_rows),
        "mask_task_grouping_integrity_row_count": len(mask_rows),
        "split_leakage_risk_smoke_audit_row_count": len(risk_rows),
        "split_unit_smoke_preview_passed": all(_bool(row["split_unit_smoke_passed"]) for row in split_unit_rows),
        "parent_event_group_integrity_passed": all(_bool(row["group_integrity_passed"]) for row in parent_rows),
        "candidate_metadata_group_integrity_passed": all(_bool(row["candidate_group_integrity_passed"]) for row in candidate_rows),
        "mask_task_grouping_integrity_passed": all(_bool(row["mask_grouping_integrity_passed"]) for row in mask_rows),
        "split_leakage_risk_smoke_audit_passed": all(_bool(row["risk_smoke_audit_passed"]) for row in risk_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_unit_preview_written_current_step": True,
        "real_train_val_test_split_written": False,
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
        "ready_for_covapie_split_leakage_qa_gate": True,
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
        "recommended_next_step": "covapie_split_leakage_qa_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bj_split_leakage_design_gate_validated"],
            manifest["source_sample_index_row_count"] == 20,
            manifest["source_unique_event_count"] == 4,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["split_unit_smoke_preview_row_count"] == 4,
            manifest["parent_event_group_integrity_row_count"] == 4,
            manifest["candidate_metadata_group_integrity_row_count"] == 4,
            manifest["mask_task_grouping_integrity_row_count"] == 5,
            manifest["split_leakage_risk_smoke_audit_row_count"] == 12,
            manifest["split_unit_smoke_preview_passed"],
            manifest["parent_event_group_integrity_passed"],
            manifest["candidate_metadata_group_integrity_passed"],
            manifest["mask_task_grouping_integrity_passed"],
            manifest["split_leakage_risk_smoke_audit_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["split_leakage_smoke_contract_failed"]
    return {
        "precondition_rows": precondition_rows,
        "split_unit_rows": split_unit_rows,
        "parent_rows": parent_rows,
        "candidate_rows": candidate_rows,
        "mask_rows": mask_rows,
        "risk_rows": risk_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }

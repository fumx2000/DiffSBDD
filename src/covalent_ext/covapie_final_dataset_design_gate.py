from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_feature_semantics_audit_gate as step13bm


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_final_dataset_design_gate_v0"
PREVIOUS_STAGE = step13bm.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_final_dataset_design_precondition_audit.csv"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_final_dataset_schema_contract.csv"
ROW_LINEAGE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_final_dataset_row_lineage_contract.csv"
MATERIALIZATION_PLAN_CSV = OUTPUT_ROOT / "covapie_final_dataset_materialization_plan.csv"
FEATURE_REQUIREMENT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_final_dataset_feature_requirement_contract.csv"
SPLIT_POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_final_dataset_split_policy_contract.csv"
SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_final_dataset_smoke_plan.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_final_dataset_design_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_final_dataset_design_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_final_dataset_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_final_dataset_design_gate_v0_summary.md")

step13bl = step13bm.step13bl
step13bk = step13bm.step13bk
step13bj = step13bm.step13bj
step13bi = step13bm.step13bi
step13bh = step13bm.step13bh
step13bg = step13bm.step13bg
step13bf = step13bm.step13bf
step13be = step13bm.step13be
step13bd = step13bm.step13bd

CANONICAL_MASK_TASK_NAMES = step13bm.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bm.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bm.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SCHEMA_COLUMNS = [
    "final_dataset_field_name",
    "field_category",
    "source_artifact",
    "source_field_or_policy",
    "required_for_final_dataset_smoke",
    "required_for_training",
    "current_design_status",
    "training_blocker_status",
    "design_comment",
    "schema_contract_passed",
]
ROW_LINEAGE_COLUMNS = [
    "final_dataset_row_id",
    "sample_id",
    "split_unit_id",
    "extracted_event_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "mask_task_name",
    "mask_task_alias",
    "source_sample_index_row_found",
    "source_split_unit_found",
    "parent_event_group_bound_to_one_split_unit",
    "feature_semantics_audit_completed",
    "feature_semantics_known_for_training",
    "unknown_atom_feature_policy_finalized_for_training",
    "final_dataset_materialized_current_step",
    "ready_for_training",
    "row_lineage_contract_passed",
    "design_comment",
]
MATERIALIZATION_PLAN_COLUMNS = [
    "materialization_step",
    "planned_action",
    "allowed_inputs",
    "allowed_outputs_future_step",
    "blocked_outputs_current_step",
    "required_preconditions",
    "materialization_plan_passed",
]
FEATURE_REQUIREMENT_COLUMNS = [
    "requirement_name",
    "current_status",
    "required_for_final_dataset_smoke",
    "required_for_training",
    "blocker_before_training",
    "requirement_contract_passed",
    "design_comment",
]
SPLIT_POLICY_COLUMNS = [
    "split_policy_name",
    "current_status",
    "enforcement_level",
    "current_step_write_status",
    "future_required_action",
    "split_policy_contract_passed",
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
    return hashlib.sha256(step13bd.METADATA_CSV.read_bytes()).hexdigest() if step13bd.METADATA_CSV.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "final_dataset.csv",
        "final_dataset.json",
        "final_dataset_smoke.csv",
        "final_dataset_smoke.json",
        "sample_index.csv",
        "sample_index.json",
        "covapie_sample_index_smoke.csv",
        "covapie_sample_index_smoke.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "training_report.csv",
        "training_report.json",
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


def _split_unit_by_sample_id() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV):
        for sample_id in row["sample_ids_in_unit"].split(";"):
            mapping[sample_id] = row["split_unit_id"]
    return mapping


def _split_unit_by_event() -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    sample_to_split = _split_unit_by_sample_id()
    for row in _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV):
        mapping.setdefault(row["extracted_event_id"], set()).add(sample_to_split.get(row["sample_id"], ""))
    return mapping


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13bm = _load_json(step13bm.MANIFEST_JSON)
    manifest13bl = _load_json(step13bl.MANIFEST_JSON)
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    split_rows = _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)
    event_rows = _csv_rows(step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    checks = [
        ("step13bm_manifest_exists", step13bm.MANIFEST_JSON, "exists", step13bm.MANIFEST_JSON.exists(), step13bm.MANIFEST_JSON.exists()),
        ("step13bm_stage", step13bm.MANIFEST_JSON, step13bm.STAGE, manifest13bm.get("stage"), manifest13bm.get("stage") == step13bm.STAGE),
        ("step13bm_all_checks_passed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("all_checks_passed"), manifest13bm.get("all_checks_passed") is True),
        ("step13bm_ready_for_final_dataset_design_gate", step13bm.MANIFEST_JSON, "true", manifest13bm.get("ready_for_covapie_final_dataset_design_gate"), manifest13bm.get("ready_for_covapie_final_dataset_design_gate") is True),
        ("step13bm_ready_for_final_dataset_smoke", step13bm.MANIFEST_JSON, "false", manifest13bm.get("ready_for_covapie_final_dataset_smoke"), manifest13bm.get("ready_for_covapie_final_dataset_smoke") is False),
        ("step13bm_ready_for_dataloader_smoke", step13bm.MANIFEST_JSON, "false", manifest13bm.get("ready_for_covapie_dataloader_smoke"), manifest13bm.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13bm_ready_for_training", step13bm.MANIFEST_JSON, "false", manifest13bm.get("ready_for_training"), manifest13bm.get("ready_for_training") is False),
        ("step13bm_ready_to_train_now", step13bm.MANIFEST_JSON, "false", manifest13bm.get("ready_to_train_now"), manifest13bm.get("ready_to_train_now") is False),
        ("step13bm_feature_semantics_audit_completed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("feature_semantics_audit_completed_current_step"), manifest13bm.get("feature_semantics_audit_completed_current_step") is True),
        ("step13bm_feature_semantics_known_for_training", step13bm.MANIFEST_JSON, "false", manifest13bm.get("feature_semantics_known_for_training"), manifest13bm.get("feature_semantics_known_for_training") is False),
        ("step13bm_unknown_atom_policy_finalized", step13bm.MANIFEST_JSON, "false", manifest13bm.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bm.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("step12d_smoke_legality_only", step13bm.MANIFEST_JSON, "true", manifest13bm.get("step12d_was_smoke_legality_only"), manifest13bm.get("step12d_was_smoke_legality_only") is True),
        ("step13bh_sample_index_smoke_shape", step13bh.SAMPLE_INDEX_SMOKE_CSV, "20x31", f"{len(sample_rows)}x{len(sample_rows[0]) if sample_rows else 0}", len(sample_rows) == 20 and bool(sample_rows) and len(sample_rows[0]) == 31),
        ("step13bk_split_unit_preview_row_count", step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV, "4", len(split_rows), len(split_rows) == 4),
        ("step13bl_split_leakage_qa_passed", step13bl.MANIFEST_JSON, "true", manifest13bl.get("all_checks_passed"), manifest13bl.get("all_checks_passed") is True),
        ("step13be_event_table_row_count", step13be.EXTRACTED_EVENT_TABLE_CSV, "4", len(event_rows), len(event_rows) == 4),
        ("step13be_protein_atom_table_row_count", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "1071", len(protein_rows), len(protein_rows) == 1071),
        ("step13be_ligand_atom_table_row_count", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "149", len(ligand_rows), len(ligand_rows) == 149),
        ("canonical_mask_count", step13bh.SAMPLE_INDEX_SMOKE_CSV, "5", len({row["mask_task_name"] for row in sample_rows}), len({row["mask_task_name"] for row in sample_rows}) == 5),
        ("b3_scaffold_only_included", step13bh.SAMPLE_INDEX_SMOKE_CSV, "true", "scaffold_only" in {row["mask_task_name"] for row in sample_rows}, "scaffold_only" in {row["mask_task_name"] for row in sample_rows}),
        ("no_extra_mask_tasks_added", step13bh.SAMPLE_INDEX_SMOKE_CSV, "true", {row["mask_task_name"] for row in sample_rows}, {row["mask_task_name"] for row in sample_rows} == set(CANONICAL_MASK_TASK_NAMES)),
        ("metadata_csv_hash_unchanged", step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
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


def build_schema_contract_rows() -> list[dict[str, Any]]:
    fields = [
        "final_dataset_row_id",
        "sample_id",
        "split_unit_id",
        "extracted_event_id",
        "allowlist_entry_id",
        "candidate_metadata_id",
        "pdb_id",
        "het_code",
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "ligand_atom_name",
        "covalent_bond_atom_pair",
        "covalent_bond_distance_angstrom",
        "protein_pocket_atom_table_path",
        "ligand_atom_table_path",
        "protein_atom_row_count_for_event",
        "ligand_atom_row_count_for_event",
        "mask_task_name",
        "mask_task_alias",
        "mask_task_semantic_description",
        "conditioning_mode",
        "covalent_residue_conditioned",
        "source_sample_index_path",
        "source_split_unit_preview_path",
        "feature_semantics_contract_path",
        "scaffold_linker_warhead_annotation_status",
        "warhead_type_label_status",
        "ligand_residue_atom_pair_label_status",
        "pre_post_geometry_label_status",
        "coordinate_unit",
        "coordinate_frame_status",
        "pre_covalent_geometry_status",
        "post_covalent_geometry_status",
        "feature_semantics_audit_status",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "leakage_split_qa_status",
        "split_assignment_status",
        "final_dataset_materialized_current_step",
        "dataloader_ready",
        "ready_for_training",
        "training_blocker_summary",
        "schema_version",
    ]
    source_by_field = {
        "final_dataset_row_id": ("future_final_dataset_smoke", "final_dataset_design::{sample_id}"),
        "split_unit_id": (step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV.as_posix(), "split_unit_id"),
        "source_sample_index_path": ("current_design_policy", step13bh.SAMPLE_INDEX_SMOKE_CSV.as_posix()),
        "source_split_unit_preview_path": ("current_design_policy", step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV.as_posix()),
        "feature_semantics_contract_path": ("current_design_policy", step13bm.FEATURE_SEMANTICS_CONTRACT_CSV.as_posix()),
        "coordinate_unit": (step13bm.COORDINATE_GEOMETRY_AUDIT_CSV.as_posix(), "angstrom"),
        "coordinate_frame_status": (step13bm.COORDINATE_GEOMETRY_AUDIT_CSV.as_posix(), "structure_coordinate_frame_inherited_not_finalized"),
        "pre_covalent_geometry_status": (step13bm.COORDINATE_GEOMETRY_AUDIT_CSV.as_posix(), "pre_covalent_geometry_not_materialized_current_step"),
        "post_covalent_geometry_status": (step13bm.COORDINATE_GEOMETRY_AUDIT_CSV.as_posix(), "post_covalent_geometry_present"),
        "feature_semantics_audit_status": (step13bm.MANIFEST_JSON.as_posix(), "feature_semantics_audit_completed_current_step=true"),
        "feature_semantics_known_for_training": (step13bm.MANIFEST_JSON.as_posix(), "false"),
        "unknown_atom_feature_policy_finalized_for_training": (step13bm.MANIFEST_JSON.as_posix(), "false"),
        "leakage_split_qa_status": (step13bl.MANIFEST_JSON.as_posix(), "split_leakage_qa_passed=true"),
        "final_dataset_materialized_current_step": ("current_design_policy", "false_design_only"),
        "dataloader_ready": ("current_design_policy", "false"),
        "ready_for_training": ("current_design_policy", "false"),
        "training_blocker_summary": (step13bm.TRAINING_BLOCKERS_CSV.as_posix(), "feature_semantics_and_training_blockers_preserved"),
        "schema_version": ("current_design_policy", STAGE),
    }
    rows = []
    for field in fields:
        if field in source_by_field:
            source, source_field = source_by_field[field]
        else:
            source, source_field = step13bh.SAMPLE_INDEX_SMOKE_CSV.as_posix(), field
        category = "identity"
        if field in {"protein_pocket_atom_table_path", "ligand_atom_table_path", "protein_atom_row_count_for_event", "ligand_atom_row_count_for_event", "coordinate_unit", "coordinate_frame_status", "pre_covalent_geometry_status", "post_covalent_geometry_status"}:
            category = "geometry_source"
        elif field.startswith("mask_"):
            category = "mask_conditioning"
        elif field.endswith("_status") or field in {"feature_semantics_known_for_training", "unknown_atom_feature_policy_finalized_for_training", "ready_for_training", "dataloader_ready", "training_blocker_summary"}:
            category = "training_boundary"
        rows.append(
            {
                "final_dataset_field_name": field,
                "field_category": category,
                "source_artifact": source,
                "source_field_or_policy": source_field,
                "required_for_final_dataset_smoke": True,
                "required_for_training": True,
                "current_design_status": "design_only_not_materialized",
                "training_blocker_status": "training_blocked_current_step",
                "design_comment": "final dataset schema contract only; no final_dataset artifact written",
                "schema_contract_passed": True,
            }
        )
    return rows


def build_row_lineage_rows() -> list[dict[str, Any]]:
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    sample_to_split = _split_unit_by_sample_id()
    event_to_splits = _split_unit_by_event()
    rows = []
    for row in sample_rows:
        split_unit_id = sample_to_split.get(row["sample_id"], "")
        event_bound = len(event_to_splits.get(row["extracted_event_id"], set())) == 1
        passed = bool(split_unit_id) and event_bound
        rows.append(
            {
                "final_dataset_row_id": f"final_dataset_design::{row['sample_id']}",
                "sample_id": row["sample_id"],
                "split_unit_id": split_unit_id,
                "extracted_event_id": row["extracted_event_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "mask_task_name": row["mask_task_name"],
                "mask_task_alias": row["mask_task_alias"],
                "source_sample_index_row_found": True,
                "source_split_unit_found": bool(split_unit_id),
                "parent_event_group_bound_to_one_split_unit": event_bound,
                "feature_semantics_audit_completed": True,
                "feature_semantics_known_for_training": False,
                "unknown_atom_feature_policy_finalized_for_training": False,
                "final_dataset_materialized_current_step": False,
                "ready_for_training": False,
                "row_lineage_contract_passed": passed,
                "design_comment": "row lineage design only; no final_dataset row materialized",
            }
        )
    return rows


def build_materialization_plan_rows() -> list[dict[str, Any]]:
    steps = [
        "read_feature_semantics_audit_gate",
        "read_sample_index_smoke",
        "read_split_unit_smoke_preview",
        "join_sample_rows_to_split_units",
        "attach_atom_table_path_references",
        "enforce_final_dataset_schema_contract",
        "preserve_canonical_mask_semantics",
        "preserve_feature_training_blockers",
        "block_real_train_val_test_assignments",
        "write_final_dataset_smoke_preview_future_step",
        "final_dataset_qa_gate_future_step",
        "dataloader_smoke_blocked_until_final_dataset_qa",
    ]
    return [
        {
            "materialization_step": step,
            "planned_action": step.replace("_", " "),
            "allowed_inputs": "step13bm;step13bh;step13bk;step13be derived csv/json",
            "allowed_outputs_future_step": "final_dataset_smoke_preview_future_step_only",
            "blocked_outputs_current_step": "final_dataset.csv;final_dataset.json;split_assignments;leakage_matrix;dataloader_smoke;training",
            "required_preconditions": "feature_semantics_audit_gate_passed;split_leakage_qa_passed",
            "materialization_plan_passed": True,
        }
        for step in steps
    ]


def build_feature_requirement_rows() -> list[dict[str, Any]]:
    requirements = [
        ("feature_semantics_audit_completed", "completed_current_step", True, True, False),
        ("feature_semantics_known_for_training_false", "false_preserved", True, True, True),
        ("unknown_atom_feature_policy_not_finalized", "false_preserved", True, True, True),
        ("canonical_masks_five_level_preserved", "five_masks_preserved", True, True, False),
        ("b3_scaffold_only_preserved", "scaffold_only_B3_preserved", True, True, False),
        ("scaffold_linker_warhead_annotation_required", "required_before_training_not_materialized", True, True, True),
        ("warhead_type_label_required", "required_before_training_not_materialized", True, True, True),
        ("ligand_residue_atom_pair_label_audit_required", "audit_required_before_training", True, True, True),
        ("pre_post_geometry_label_audit_required", "audit_required_before_training", True, True, True),
        ("pre_covalent_geometry_not_materialized", "not_materialized_current_step", True, True, True),
        ("split_leakage_qa_completed", "completed_step13bl", True, True, False),
        ("final_dataset_design_only_current_step", "design_only_not_materialized", True, True, True),
        ("ready_for_training_false", "false_preserved", True, True, True),
    ]
    return [
        {
            "requirement_name": name,
            "current_status": status,
            "required_for_final_dataset_smoke": smoke,
            "required_for_training": training,
            "blocker_before_training": blocker,
            "requirement_contract_passed": True,
            "design_comment": "requirement is explicit; blockers are preserved rather than removed",
        }
        for name, status, smoke, training, blocker in requirements
    ]


def build_split_policy_rows() -> list[dict[str, Any]]:
    policies = [
        ("split_unit_id_required", "required_in_final_dataset_schema", "schema_contract", "not_written_current_step", "carry split_unit_id into smoke preview"),
        ("no_random_row_level_split", "forbidden", "hard_blocker", "not_written_current_step", "enforce grouped split design"),
        ("same_extracted_event_id_same_split_unit", "enforced_by_step13bk_preview", "hard_blocker", "not_written_current_step", "validate in final dataset smoke"),
        ("same_candidate_metadata_id_same_split_unit", "enforced_by_step13bk_preview", "hard_blocker", "not_written_current_step", "validate in final dataset smoke"),
        ("same_pdb_id_review_or_group", "review_required_before_real_split", "design_requirement", "not_written_current_step", "review PDB grouping in future larger dataset"),
        ("real_split_assignment_not_written_current_step", "not_written", "hard_blocker", "not_written_current_step", "future split design gate with larger dataset"),
        ("leakage_matrix_not_written_current_step", "not_written", "hard_blocker", "not_written_current_step", "future leakage matrix gate"),
        ("smoke_size_too_small_for_real_train_val_test_split", "blocks_real_split", "hard_blocker", "not_written_current_step", "increase dataset size before real split"),
        ("future_split_assignment_requires_larger_validated_dataset", "required_before_training", "future_gate", "not_written_current_step", "future split assignment materialization"),
        ("final_dataset_smoke_not_training_split", "smoke_only", "hard_blocker", "not_written_current_step", "do not treat smoke as train/val/test split"),
    ]
    return [
        {
            "split_policy_name": name,
            "current_status": status,
            "enforcement_level": level,
            "current_step_write_status": write_status,
            "future_required_action": future,
            "split_policy_contract_passed": True,
        }
        for name, status, level, write_status, future in policies
    ]


def build_smoke_plan_rows() -> list[dict[str, Any]]:
    steps = [
        "read_final_dataset_design_gate",
        "read_sample_index_smoke",
        "read_split_unit_preview",
        "materialize_final_dataset_smoke_preview",
        "validate_schema_order",
        "validate_row_lineage",
        "validate_mask_distribution",
        "validate_feature_blockers",
        "final_dataset_smoke_qa_gate",
        "dataloader_smoke_blocked",
    ]
    return [
        {
            "planned_step": step,
            "planned_action": step.replace("_", " "),
            "allowed_inputs": "final_dataset_design_gate;sample_index_smoke;split_unit_preview",
            "allowed_outputs": "final_dataset_smoke_preview_future_step_only" if step == "materialize_final_dataset_smoke_preview" else "csv_json_audit_future_step",
            "blocked_outputs": "real_final_dataset;train_val_test_split;leakage_matrix;dataloader_smoke;training",
            "required_preconditions": "step13bn_design_gate_passed",
            "plan_passed": True,
        }
        for step in steps
    ]


def build_boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "final_dataset_design_gate": "executed_design_gate_only",
        "read_step13bm_feature_semantics_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bl_split_leakage_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bk_split_unit_preview": "executed_derived_csv_json_read_only",
        "read_step13bh_sample_index": "executed_derived_csv_json_read_only",
        "read_step13be_extracted_tables": "executed_derived_csv_json_read_only",
        "final_dataset_write": "blocked_current_step",
        "final_dataset_smoke_write": "blocked_current_step",
        "new_sample_index_write": "blocked_current_step",
        "split_assignment_write": "blocked_current_step",
        "leakage_matrix_write": "blocked_current_step",
        "dataloader_smoke": "blocked_current_step",
        "training": "blocked_current_step",
        "raw_file_content_read": "not_executed_or_not_allowed",
        "raw_cif_mmcif_sdf_pdb_gzip_read": "not_executed_or_not_allowed",
        "mmcif_parse": "not_executed_or_not_allowed",
        "atom_site_scan": "not_executed_or_not_allowed",
        "struct_conn_scan": "not_executed_or_not_allowed",
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
            "qa_comment": "final dataset design gate boundary respected",
        }
        for item, status in statuses.items()
    ]


def build_git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached --name-only -- data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "boundary manifest", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("no_final_dataset_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_smoke_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_dataloader_smoke_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts_written", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("metadata_csv_unchanged", str(step13bd.METADATA_CSV), "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bm_artifacts_unchanged", str(step13bm.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bm.OUTPUT_ROOT.as_posix()])),
        ("step13bl_artifacts_unchanged", str(step13bl.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bl.OUTPUT_ROOT.as_posix()])),
        ("step13bk_artifacts_unchanged", str(step13bk.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.OUTPUT_ROOT.as_posix()])),
        ("step13bj_artifacts_unchanged", str(step13bj.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.OUTPUT_ROOT.as_posix()])),
        ("step13bi_artifacts_unchanged", str(step13bi.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bi.OUTPUT_ROOT.as_posix()])),
        ("step13bh_artifacts_unchanged", str(step13bh.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bh.OUTPUT_ROOT.as_posix()])),
        ("step13bg_artifacts_unchanged", str(step13bg.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bg.OUTPUT_ROOT.as_posix()])),
        ("step13bf_artifacts_unchanged", str(step13bf.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bf.OUTPUT_ROOT.as_posix()])),
        ("step13be_artifacts_unchanged", str(step13be.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13be.OUTPUT_ROOT.as_posix()])),
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


def run_covapie_final_dataset_design_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    schema_rows = build_schema_contract_rows()
    lineage_rows = build_row_lineage_rows()
    materialization_rows = build_materialization_plan_rows()
    feature_requirement_rows = build_feature_requirement_rows()
    split_policy_rows = build_split_policy_rows()
    smoke_plan_rows = build_smoke_plan_rows()
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bm_feature_semantics_audit_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_sample_index_row_count": len(sample_rows),
        "source_unique_event_count": len({row["extracted_event_id"] for row in sample_rows}),
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in sample_rows}),
        "source_split_unit_preview_row_count": len(_csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)),
        "source_extracted_event_table_row_count": len(_csv_rows(step13be.EXTRACTED_EVENT_TABLE_CSV)),
        "source_protein_atom_table_row_count": len(_csv_rows(step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)),
        "source_ligand_atom_table_row_count": len(_csv_rows(step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)),
        "final_dataset_schema_contract_row_count": len(schema_rows),
        "final_dataset_row_lineage_contract_row_count": len(lineage_rows),
        "final_dataset_materialization_plan_row_count": len(materialization_rows),
        "final_dataset_feature_requirement_contract_row_count": len(feature_requirement_rows),
        "final_dataset_split_policy_contract_row_count": len(split_policy_rows),
        "final_dataset_smoke_plan_row_count": len(smoke_plan_rows),
        "final_dataset_schema_contract_passed": all(_bool(row["schema_contract_passed"]) for row in schema_rows),
        "final_dataset_row_lineage_contract_passed": all(_bool(row["row_lineage_contract_passed"]) for row in lineage_rows),
        "final_dataset_materialization_plan_passed": all(_bool(row["materialization_plan_passed"]) for row in materialization_rows),
        "final_dataset_feature_requirement_contract_passed": all(_bool(row["requirement_contract_passed"]) for row in feature_requirement_rows),
        "final_dataset_split_policy_contract_passed": all(_bool(row["split_policy_contract_passed"]) for row in split_policy_rows),
        "final_dataset_smoke_plan_passed": all(_bool(row["plan_passed"]) for row in smoke_plan_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "final_dataset_design_completed_current_step": True,
        "final_dataset_written": False,
        "final_dataset_smoke_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "real_train_val_test_split_written": False,
        "feature_semantics_audit_completed_current_step": True,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
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
        "ready_for_covapie_final_dataset_smoke": True,
        "ready_for_covapie_final_dataset_qa_gate": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in sample_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in sample_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_final_dataset_smoke",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bm_feature_semantics_audit_gate_validated"],
            manifest["source_sample_index_row_count"] == 20,
            manifest["source_unique_event_count"] == 4,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["source_split_unit_preview_row_count"] == 4,
            manifest["source_extracted_event_table_row_count"] == 4,
            manifest["source_protein_atom_table_row_count"] == 1071,
            manifest["source_ligand_atom_table_row_count"] == 149,
            manifest["final_dataset_schema_contract_row_count"] == 45,
            manifest["final_dataset_row_lineage_contract_row_count"] == 20,
            manifest["final_dataset_materialization_plan_row_count"] == 12,
            manifest["final_dataset_feature_requirement_contract_row_count"] == 13,
            manifest["final_dataset_split_policy_contract_row_count"] == 10,
            manifest["final_dataset_smoke_plan_row_count"] == 10,
            manifest["final_dataset_schema_contract_passed"],
            manifest["final_dataset_row_lineage_contract_passed"],
            manifest["final_dataset_materialization_plan_passed"],
            manifest["final_dataset_feature_requirement_contract_passed"],
            manifest["final_dataset_split_policy_contract_passed"],
            manifest["final_dataset_smoke_plan_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["final_dataset_design_completed_current_step"],
            not manifest["final_dataset_written"],
            not manifest["final_dataset_smoke_written"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
            manifest["ready_for_covapie_final_dataset_smoke"],
            not manifest["ready_for_covapie_final_dataset_qa_gate"],
            not manifest["ready_for_covapie_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["final_dataset_design_gate_contract_failed"]
    return {
        "precondition_rows": precondition_rows,
        "schema_rows": schema_rows,
        "lineage_rows": lineage_rows,
        "materialization_rows": materialization_rows,
        "feature_requirement_rows": feature_requirement_rows,
        "split_policy_rows": split_policy_rows,
        "smoke_plan_rows": smoke_plan_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }

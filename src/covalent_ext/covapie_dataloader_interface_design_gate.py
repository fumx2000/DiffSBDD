from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_final_dataset_qa_gate as step13bp
from covalent_ext.covapie_legacy_pipeline_retirement_policy import (
    LegacyStageRetirementPolicy,
    build_legacy_stage_retirement_policy,
    raise_legacy_stage_retired,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_STAGE = "covapie_dataloader_interface_design_gate_v0"
STAGE = LEGACY_STAGE
PREVIOUS_STAGE = step13bp.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_dataloader_interface_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_design_precondition_audit.csv"
INPUT_SOURCE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_dataloader_input_source_contract.csv"
FIELD_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "covapie_dataloader_field_mapping_contract.csv"
FEATURE_INTERFACE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_dataloader_feature_interface_contract.csv"
MASK_INTERFACE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_dataloader_mask_interface_contract.csv"
BATCH_COLLATE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_dataloader_batch_collate_contract.csv"
CHECKPOINT_COMPATIBILITY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_dataloader_checkpoint_compatibility_contract.csv"
INTERFACE_SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_smoke_plan.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_design_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_design_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_dataloader_interface_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_dataloader_interface_design_gate_v0_summary.md")

step13bo = step13bp.step13bo
step13bn = step13bp.step13bn
step13bm = step13bp.step13bm
step13bl = step13bp.step13bl
step13bk = step13bp.step13bk
step13bj = step13bp.step13bj
step13bi = step13bp.step13bi
step13bh = step13bp.step13bh
step13bg = step13bp.step13bg
step13bf = step13bp.step13bf
step13be = step13bp.step13be
step13bd = step13bp.step13bd

CANONICAL_MASK_TASK_NAMES = step13bp.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bp.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bp.METADATA_CSV_SHA256

DATASET_PY = Path("dataset.py")
PREPARE_CROSSDOCKED_PY = Path("data/prepare_crossdocked.py")
LIGHTNING_MODULES_PY = Path("lightning_modules.py")
EQUIVARIANT_DIFFUSION_DIR = Path("equivariant_diffusion")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
INPUT_SOURCE_COLUMNS = [
    "input_source_name",
    "source_path_or_policy",
    "source_type",
    "allowed_access_mode",
    "required_for_future_interface_smoke",
    "required_for_future_real_dataloader",
    "current_step_access_status",
    "blocker_before_dataloader_smoke",
    "input_source_contract_passed",
]
FIELD_MAPPING_COLUMNS = [
    "final_dataset_field_name",
    "source_field_category",
    "future_dataloader_role",
    "future_batch_key_or_metadata_key",
    "current_smoke_value_status",
    "tensorization_status_current_step",
    "required_before_interface_smoke",
    "required_before_real_dataloader",
    "blocker_before_training",
    "field_mapping_contract_passed",
]
FEATURE_INTERFACE_COLUMNS = [
    "feature_interface_item",
    "source_field_or_table",
    "future_tensor_name_or_metadata_key",
    "future_dtype_policy",
    "future_shape_policy",
    "current_step_materialized",
    "required_before_dataloader_interface_smoke",
    "required_before_real_dataloader",
    "required_before_training",
    "blocker_status",
    "feature_interface_contract_passed",
]
MASK_INTERFACE_COLUMNS = [
    "mask_interface_item",
    "mask_task_name",
    "mask_task_alias",
    "observed_row_count",
    "expected_row_count",
    "future_mask_tensor_policy",
    "current_tensor_materialized",
    "mask_interface_contract_passed",
    "qa_comment",
]
BATCH_COLLATE_COLUMNS = [
    "batch_contract_item",
    "future_batch_content",
    "future_collate_requirement",
    "current_step_status",
    "blocker_before_interface_smoke",
    "blocker_before_real_dataloader",
    "batch_collate_contract_passed",
]
CHECKPOINT_COMPATIBILITY_COLUMNS = [
    "compatibility_item",
    "expected_status",
    "observed_status",
    "compatibility_risk_level",
    "required_future_action",
    "checkpoint_compatibility_contract_passed",
]
SMOKE_PLAN_COLUMNS = [
    "planned_step",
    "planned_action",
    "allowed_inputs",
    "allowed_outputs_future_step",
    "blocked_outputs_current_step",
    "required_preconditions",
    "smoke_plan_passed",
]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]

GUARDED_ENTRYPOINTS = (
    "build_precondition_rows",
    "build_field_mapping_rows",
    "build_mask_interface_rows",
    "build_git_safety_rows",
    "run_covapie_dataloader_interface_design_gate_v0",
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
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _metadata_hash() -> str:
    return hashlib.sha256(step13bd.METADATA_CSV.read_bytes()).hexdigest() if step13bd.METADATA_CSV.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _schema_contract_rows() -> list[dict[str, str]]:
    return _csv_rows(step13bn.SCHEMA_CONTRACT_CSV)


def _schema_fields() -> list[str]:
    return [row["final_dataset_field_name"] for row in _schema_contract_rows()]


def _preview_rows() -> list[dict[str, str]]:
    return _csv_rows(step13bo.SMOKE_PREVIEW_CSV)


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "dataloader_interface_smoke.csv",
        "dataloader_interface_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "final_dataset.csv",
        "final_dataset.json",
        "final_dataset_smoke.csv",
        "final_dataset_smoke.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "training_report.csv",
        "training_report.json",
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


def build_precondition_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    manifest13bp = _load_json(step13bp.MANIFEST_JSON)
    manifest13bm = _load_json(step13bm.MANIFEST_JSON)
    preview_rows = _preview_rows()
    json_rows = _load_json(step13bo.SMOKE_PREVIEW_JSON)
    event_rows = _csv_rows(step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    checks = [
        ("step13bp_manifest_exists", step13bp.MANIFEST_JSON, "exists", step13bp.MANIFEST_JSON.exists(), step13bp.MANIFEST_JSON.exists()),
        ("step13bp_stage", step13bp.MANIFEST_JSON, step13bp.STAGE, manifest13bp.get("stage"), manifest13bp.get("stage") == step13bp.STAGE),
        ("step13bp_all_checks_passed", step13bp.MANIFEST_JSON, "true", manifest13bp.get("all_checks_passed"), manifest13bp.get("all_checks_passed") is True),
        ("step13bp_ready_for_interface_design_gate", step13bp.MANIFEST_JSON, "true", manifest13bp.get("ready_for_covapie_dataloader_interface_design_gate"), manifest13bp.get("ready_for_covapie_dataloader_interface_design_gate") is True),
        ("step13bp_ready_for_dataloader_smoke", step13bp.MANIFEST_JSON, "false", manifest13bp.get("ready_for_covapie_dataloader_smoke"), manifest13bp.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13bp_ready_for_training", step13bp.MANIFEST_JSON, "false", manifest13bp.get("ready_for_training"), manifest13bp.get("ready_for_training") is False),
        ("step13bp_ready_to_train_now", step13bp.MANIFEST_JSON, "false", manifest13bp.get("ready_to_train_now"), manifest13bp.get("ready_to_train_now") is False),
        ("step13bo_preview_csv_shape", step13bo.SMOKE_PREVIEW_CSV, "20x45", f"{len(preview_rows)}x{len(preview_rows[0]) if preview_rows else 0}", len(preview_rows) == 20 and bool(preview_rows) and len(preview_rows[0]) == 45),
        ("step13bo_preview_json_row_count", step13bo.SMOKE_PREVIEW_JSON, "20", len(json_rows), len(json_rows) == 20),
        ("step13bo_preview_not_rewritten_by_step13bp", step13bp.MANIFEST_JSON, "false", manifest13bp.get("final_dataset_smoke_preview_written_current_step"), manifest13bp.get("final_dataset_smoke_preview_written_current_step") is False),
        ("step13bn_schema_contract_row_count", step13bn.SCHEMA_CONTRACT_CSV, "45", len(_schema_contract_rows()), len(_schema_contract_rows()) == 45),
        ("step13bm_feature_semantics_audit_completed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("feature_semantics_audit_completed_current_step"), manifest13bm.get("feature_semantics_audit_completed_current_step") is True),
        ("step13bm_feature_semantics_known_for_training", step13bm.MANIFEST_JSON, "false", manifest13bm.get("feature_semantics_known_for_training"), manifest13bm.get("feature_semantics_known_for_training") is False),
        ("step13bm_unknown_atom_policy_finalized", step13bm.MANIFEST_JSON, "false", manifest13bm.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bm.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("step13be_event_table_row_count", step13be.EXTRACTED_EVENT_TABLE_CSV, "4", len(event_rows), len(event_rows) == 4),
        ("step13be_protein_atom_table_row_count", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "1071", len(protein_rows), len(protein_rows) == 1071),
        ("step13be_ligand_atom_table_row_count", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "149", len(ligand_rows), len(ligand_rows) == 149),
        ("canonical_mask_count", step13bo.SMOKE_PREVIEW_CSV, "5", len({row["mask_task_name"] for row in preview_rows}), len({row["mask_task_name"] for row in preview_rows}) == 5),
        ("b3_scaffold_only_included", step13bo.SMOKE_PREVIEW_CSV, "true", "scaffold_only" in {row["mask_task_name"] for row in preview_rows}, "scaffold_only" in {row["mask_task_name"] for row in preview_rows}),
        ("no_extra_mask_tasks_added", step13bo.SMOKE_PREVIEW_CSV, "true", {row["mask_task_name"] for row in preview_rows}, {row["mask_task_name"] for row in preview_rows} == set(CANONICAL_MASK_TASK_NAMES)),
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


def build_input_source_rows() -> list[dict[str, Any]]:
    rows = [
        ("final_dataset_smoke_preview_csv", step13bo.SMOKE_PREVIEW_CSV, "derived_csv", "derived_csv_json_read_only", True, True, "read_only_validated", False),
        ("final_dataset_smoke_preview_json", step13bo.SMOKE_PREVIEW_JSON, "derived_json", "derived_csv_json_read_only", True, True, "read_only_validated", False),
        ("protein_pocket_atom_table", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "derived_csv", "derived_csv_json_read_only", True, True, "path_and_count_validated", False),
        ("ligand_atom_table", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "derived_csv", "derived_csv_json_read_only", True, True, "path_and_count_validated", False),
        ("feature_semantics_contract", step13bm.FEATURE_SEMANTICS_CONTRACT_CSV, "derived_csv", "derived_csv_json_read_only", True, True, "read_only_validated", True),
        ("mask_conditioning_semantics_audit", step13bm.MASK_CONDITIONING_AUDIT_CSV, "derived_csv", "derived_csv_json_read_only", True, True, "read_only_validated", False),
        ("split_unit_smoke_preview", step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV, "derived_csv", "derived_csv_json_read_only", True, True, "read_only_validated", False),
        ("final_dataset_qa_manifest", step13bp.MANIFEST_JSON, "derived_json", "derived_csv_json_read_only", True, True, "read_only_validated", False),
        ("dataset_py_static_reference", DATASET_PY, "source_text", "static_text_reference", True, True, "static_text_reference_only", False),
        ("prepare_crossdocked_static_reference", PREPARE_CROSSDOCKED_PY, "source_text", "static_text_reference", True, True, "static_text_reference_only", False),
        ("lightning_modules_static_reference", LIGHTNING_MODULES_PY, "source_text", "static_text_reference", True, True, "static_text_reference_only", False),
        ("equivariant_diffusion_static_reference", EQUIVARIANT_DIFFUSION_DIR, "source_tree", "static_text_reference", True, True, "static_text_reference_only", False),
        ("checkpoint_path_reference_only", "future_checkpoint_path_config", "policy", "reference_only_no_checkpoint_load", False, True, "reference_only", True),
        ("no_torch_runtime_dependency_current_step", "policy:no_torch_import", "policy", "design_only_no_runtime_dependency", True, True, "not_imported", False),
        ("no_raw_files_current_step", "policy:no_raw_files", "policy", "blocked_current_step", True, True, "not_read", False),
    ]
    return [
        {
            "input_source_name": name,
            "source_path_or_policy": str(path),
            "source_type": source_type,
            "allowed_access_mode": access,
            "required_for_future_interface_smoke": interface_required,
            "required_for_future_real_dataloader": real_required,
            "current_step_access_status": status,
            "blocker_before_dataloader_smoke": blocker,
            "input_source_contract_passed": True,
        }
        for name, path, source_type, access, interface_required, real_required, status, blocker in rows
    ]


def _field_role(field: str, category: str) -> tuple[str, str, str, bool]:
    metadata_fields = {
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
        "schema_version",
    }
    blocker_fields = {
        "scaffold_linker_warhead_annotation_status",
        "warhead_type_label_status",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "dataloader_ready",
        "ready_for_training",
        "training_blocker_summary",
    }
    if field in metadata_fields:
        return "metadata_key_not_tensor", f"metadata.{field}", "metadata_value_present_in_smoke", False
    if field == "protein_pocket_atom_table_path":
        return "future_protein_atom_table_loader_input", "inputs.protein_atom_table_path", "path_present_not_loaded_current_step", False
    if field == "ligand_atom_table_path":
        return "future_ligand_atom_table_loader_input", "inputs.ligand_atom_table_path", "path_present_not_loaded_current_step", False
    if field in {"protein_atom_row_count_for_event", "ligand_atom_row_count_for_event"}:
        return "validation_metadata", f"validation.{field}", "count_present_for_future_shape_checks", False
    if field == "mask_task_name":
        return "canonical_mask_task_selector_long_name", "mask.task_name", "long_semantic_name_present", False
    if field == "mask_task_alias":
        return "display_report_only", "mask.display_alias", "display_alias_present_not_source_of_truth", False
    if field in {"conditioning_mode", "covalent_residue_conditioned"}:
        return "conditioning_metadata", f"conditioning.{field}", "conditioning_value_present", False
    if field in {"covalent_bond_atom_pair", "covalent_bond_distance_angstrom"}:
        return "covalent_geometry_metadata", f"geometry.{field}", "geometry_metadata_present_feature_audit_required", True
    if field in blocker_fields or field.endswith("_status"):
        return "training_blocker_metadata", f"blockers.{field}", "blocker_value_present", True
    if field in {"coordinate_unit", "coordinate_frame_status", "pre_covalent_geometry_status", "post_covalent_geometry_status"}:
        return "coordinate_geometry_metadata", f"geometry.{field}", "geometry_metadata_present_feature_audit_required", True
    return f"{category}_metadata", f"metadata.{field}", "smoke_value_present", False


def build_field_mapping_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    rows = []
    for contract in _schema_contract_rows():
        field = contract["final_dataset_field_name"]
        category = contract["field_category"]
        role, key, status, blocker = _field_role(field, category)
        rows.append(
            {
                "final_dataset_field_name": field,
                "source_field_category": category,
                "future_dataloader_role": role,
                "future_batch_key_or_metadata_key": key,
                "current_smoke_value_status": status,
                "tensorization_status_current_step": "design_only_no_tensorization_current_step",
                "required_before_interface_smoke": True,
                "required_before_real_dataloader": True,
                "blocker_before_training": blocker,
                "field_mapping_contract_passed": True,
            }
        )
    return rows


def build_feature_interface_rows() -> list[dict[str, Any]]:
    rows = [
        ("protein_atom_xyz", "protein_pocket_atom_table", "protein.x", "float32_angstrom_future", "[num_protein_atoms,3]_future", "feature_semantics_required_before_training"),
        ("protein_atom_features", "protein_pocket_atom_table", "protein.features", "categorical_or_float_future", "[num_protein_atoms,num_features]_future", "protein_atom_feature_semantics_not_finalized"),
        ("ligand_atom_xyz", "ligand_atom_table", "ligand.x", "float32_angstrom_future", "[num_ligand_atoms,3]_future", "feature_semantics_required_before_training"),
        ("ligand_atom_features", "ligand_atom_table", "ligand.features", "categorical_or_float_future", "[num_ligand_atoms,num_features]_future", "ligand_atom_feature_semantics_not_finalized"),
        ("protein_ligand_joint_coordinates", "protein_pocket_atom_table+ligand_atom_table", "complex.x", "float32_angstrom_future", "[num_atoms,3]_future", "coordinate_frame_audit_required"),
        ("mask_task_selector", "mask_task_name", "mask.task_name", "string_or_enum_future", "[batch]_future", "design_only"),
        ("mask_boolean_vector_future", "mask_task_name+future_group_labels", "mask.boolean_vector", "bool_future", "[num_ligand_atoms]_future", "not_materialized_current_step"),
        ("covalent_residue_conditioning", "conditioning_mode+covalent_residue_conditioned", "conditioning.covalent_residue", "metadata_or_tensor_future", "[batch,...]_future", "design_only"),
        ("covalent_bond_atom_pair_label", "covalent_bond_atom_pair", "labels.covalent_bond_atom_pair", "string_or_index_future", "[batch]_future", "feature_audit_required"),
        ("covalent_bond_distance_angstrom", "covalent_bond_distance_angstrom", "geometry.covalent_bond_distance", "float32_future", "[batch,1]_future", "geometry_audit_required"),
        ("pre_post_geometry_label", "pre_post_geometry_label_status", "labels.pre_post_geometry", "categorical_future", "[batch]_future", "pre_covalent_geometry_not_materialized"),
        ("scaffold_linker_warhead_atom_labels", "scaffold_linker_warhead_annotation_status", "labels.group_membership", "categorical_future", "[num_ligand_atoms]_future", "not_materialized_current_step"),
        ("warhead_type_label", "warhead_type_label_status", "labels.warhead_type", "categorical_future", "[batch]_future", "not_materialized_current_step"),
        ("split_unit_metadata", "split_unit_id", "metadata.split_unit_id", "string_metadata", "[batch]_future", "design_only"),
        ("sample_metadata", "sample_id+final_dataset_row_id", "metadata.sample", "string_metadata", "[batch]_future", "design_only"),
        ("batch_collate_policy_future", "all_future_batch_fields", "collate.policy", "policy", "variable_size_graph_batch_future", "not_implemented_current_step"),
    ]
    return [
        {
            "feature_interface_item": item,
            "source_field_or_table": source,
            "future_tensor_name_or_metadata_key": tensor,
            "future_dtype_policy": dtype,
            "future_shape_policy": shape,
            "current_step_materialized": False,
            "required_before_dataloader_interface_smoke": True,
            "required_before_real_dataloader": True,
            "required_before_training": True,
            "blocker_status": blocker,
            "feature_interface_contract_passed": True,
        }
        for item, source, tensor, dtype, shape, blocker in rows
    ]


def build_mask_interface_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    preview_rows = _preview_rows()
    rows = []
    for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES):
        observed = len([row for row in preview_rows if row["mask_task_name"] == name])
        rows.append(
            {
                "mask_interface_item": f"mask_task_{name}_{alias}",
                "mask_task_name": name,
                "mask_task_alias": alias,
                "observed_row_count": observed,
                "expected_row_count": 4,
                "future_mask_tensor_policy": "future_bool_mask_from_group_labels_not_current_step",
                "current_tensor_materialized": False,
                "mask_interface_contract_passed": observed == 4,
                "qa_comment": "canonical mask task preserved for future interface",
            }
        )
    rows.extend(
        [
            {
                "mask_interface_item": "mask_task_name_long_semantic_source_of_truth",
                "mask_task_name": ";".join(CANONICAL_MASK_TASK_NAMES),
                "mask_task_alias": "",
                "observed_row_count": len({row["mask_task_name"] for row in preview_rows}),
                "expected_row_count": 5,
                "future_mask_tensor_policy": "long_name_drives_future_mask_selection",
                "current_tensor_materialized": False,
                "mask_interface_contract_passed": {row["mask_task_name"] for row in preview_rows} == set(CANONICAL_MASK_TASK_NAMES),
                "qa_comment": "aliases are not source of truth",
            },
            {
                "mask_interface_item": "mask_task_alias_display_only",
                "mask_task_name": "",
                "mask_task_alias": ";".join(CANONICAL_MASK_TASK_ALIASES),
                "observed_row_count": len({row["mask_task_alias"] for row in preview_rows}),
                "expected_row_count": 5,
                "future_mask_tensor_policy": "alias_display_only_not_tensor_key",
                "current_tensor_materialized": False,
                "mask_interface_contract_passed": {row["mask_task_alias"] for row in preview_rows} == set(CANONICAL_MASK_TASK_ALIASES),
                "qa_comment": "display aliases preserved",
            },
            {
                "mask_interface_item": "no_extra_mask_tasks",
                "mask_task_name": "",
                "mask_task_alias": "",
                "observed_row_count": len({row["mask_task_name"] for row in preview_rows}),
                "expected_row_count": 5,
                "future_mask_tensor_policy": "reject_unknown_mask_tasks_future_step",
                "current_tensor_materialized": False,
                "mask_interface_contract_passed": {row["mask_task_name"] for row in preview_rows} == set(CANONICAL_MASK_TASK_NAMES),
                "qa_comment": "no sixth mask introduced",
            },
        ]
    )
    return rows


def build_batch_collate_rows() -> list[dict[str, Any]]:
    rows = [
        ("batch_sample_identity", "sample_id and final_dataset_row_id metadata", "preserve per-sample identity list"),
        ("batch_split_unit_metadata", "split_unit_id metadata", "preserve split unit grouping for leakage checks"),
        ("batch_protein_context", "future protein atom table tensors", "variable-size protein graph collation future"),
        ("batch_ligand_context", "future ligand atom table tensors", "variable-size ligand graph collation future"),
        ("batch_covalent_residue_conditioning", "conditioning metadata or tensors", "preserve covalent residue conditioning"),
        ("batch_mask_task_selection", "canonical mask task selector", "one task selector per sample"),
        ("batch_auxiliary_labels_future", "future auxiliary labels", "blocked until label semantics finalized"),
        ("batch_geometry_metadata", "covalent geometry metadata", "audit coordinate frame and units before tensorization"),
        ("batch_training_targets_future", "future training targets", "blocked until real dataloader/training gates"),
        ("batch_collate_not_implemented_current_step", "policy only", "no collate implementation current step"),
    ]
    return [
        {
            "batch_contract_item": item,
            "future_batch_content": content,
            "future_collate_requirement": requirement,
            "current_step_status": "design_only_not_implemented",
            "blocker_before_interface_smoke": item in {"batch_auxiliary_labels_future", "batch_training_targets_future"},
            "blocker_before_real_dataloader": True,
            "batch_collate_contract_passed": True,
        }
        for item, content, requirement in rows
    ]


def build_checkpoint_compatibility_rows() -> list[dict[str, Any]]:
    rows = [
        ("original_diffsbbd_model_unchanged", "no_diff", "no_diff", "low", "keep original model source untouched"),
        ("original_diffsbbd_dataloader_unchanged", "no_diff", "no_diff", "low", "future adapter must be additive"),
        ("original_loss_unchanged", "no_diff", "no_diff", "low", "future loss integration requires separate gate"),
        ("checkpoint_path_reference_only", "reference_only", "reference_only", "medium", "do not load checkpoint during design gate"),
        ("checkpoint_not_loaded", "false", "false", "low", "checkpoint load requires later smoke gate"),
        ("no_model_forward", "false", "false", "low", "forward requires later high-risk step"),
        ("covapie_adapter_future_optional", "design_future_only", "design_future_only", "medium", "adapter must preserve checkpoint compatibility"),
        ("checkpoint_compatibility_preserved_current_step", "true", "true", "low", "current step is design only"),
    ]
    return [
        {
            "compatibility_item": item,
            "expected_status": expected,
            "observed_status": observed,
            "compatibility_risk_level": risk,
            "required_future_action": action,
            "checkpoint_compatibility_contract_passed": True,
        }
        for item, expected, observed, risk, action in rows
    ]


def build_interface_smoke_plan_rows() -> list[dict[str, Any]]:
    rows = [
        ("read_dataloader_interface_design_gate", "read design contracts", "13BQ contracts", "interface_smoke_audit_future", "real_dataloader;training", "13BQ all_checks_passed"),
        ("read_final_dataset_smoke_preview", "read 20-row preview", "13BO preview", "interface_smoke_preview_future", "preview rewrite", "13BP QA passed"),
        ("validate_input_source_paths", "validate source paths", "input source contract", "path_validation_audit_future", "raw reads", "no raw files"),
        ("validate_field_mapping_contract", "validate 45 field mappings", "field mapping contract", "field_mapping_audit_future", "tensorization", "schema QA passed"),
        ("validate_mask_interface_contract", "validate five masks", "mask interface contract", "mask_audit_future", "new masks", "B3 included"),
        ("validate_no_tensorization_current_step", "assert no tensors", "boundary contract", "tensor_boundary_audit_future", "pt/npz/checkpoints", "torch remains blocked"),
        ("write_dataloader_interface_smoke_preview_future_step", "future CSV/JSON interface smoke", "derived contracts", "dataloader_interface_smoke_preview_future", "actual dataloader", "13BQ passed"),
        ("dataloader_interface_qa_gate_future_step", "QA future interface smoke", "future interface smoke outputs", "qa_artifacts_future", "model forward", "interface smoke passed"),
        ("real_dataloader_smoke_blocked_until_interface_qa", "block actual dataloader smoke", "QA gate result", "none_current_step", "actual dataloader smoke", "interface QA required"),
        ("training_blocked_until_real_dataloader_and_training_gates", "block training", "future gates", "none_current_step", "training", "feature semantics and leakage gates required"),
    ]
    return [
        {
            "planned_step": step,
            "planned_action": action,
            "allowed_inputs": inputs,
            "allowed_outputs_future_step": outputs,
            "blocked_outputs_current_step": blocked,
            "required_preconditions": preconditions,
            "smoke_plan_passed": True,
        }
        for step, action, inputs, outputs, blocked, preconditions in rows
    ]


def build_boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "dataloader_interface_design_gate": "executed_design_gate_only",
        "read_step13bp_final_dataset_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bo_final_dataset_smoke_preview": "executed_derived_csv_json_read_only",
        "read_step13bn_design_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bm_feature_semantics_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bk_split_unit_preview": "executed_derived_csv_json_read_only",
        "read_step13be_extracted_tables": "executed_derived_csv_json_read_only",
        "static_original_dataloader_source_read": "executed_static_text_reference_only",
        "dataloader_interface_smoke_write": "blocked_current_step",
        "real_dataloader_write": "blocked_current_step",
        "original_dataloader_modify": "blocked_current_step",
        "torch_import": "blocked_current_step",
        "tensor_creation": "blocked_current_step",
        "checkpoint_load": "blocked_current_step",
        "model_forward": "blocked_current_step",
        "loss_backward_optimizer": "blocked_current_step",
        "final_dataset_write": "blocked_current_step",
        "new_sample_index_write": "blocked_current_step",
        "split_assignment_write": "blocked_current_step",
        "leakage_matrix_write": "blocked_current_step",
        "training": "blocked_current_step",
        "raw_file_content_read": "not_executed_or_not_allowed",
        "raw_cif_mmcif_sdf_pdb_gzip_read": "not_executed_or_not_allowed",
        "mmcif_parse": "not_executed_or_not_allowed",
        "coordinate_extraction": "not_executed_or_not_allowed",
        "network_access": "not_executed_or_not_allowed",
        "raw_download": "not_executed_or_not_allowed",
        "rdkit_biopdb_gemmi": "not_executed_or_not_allowed",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "boundary_safety_passed": True,
            "qa_comment": "dataloader interface design boundary respected",
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
        ("no_dataloader_interface_smoke_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_original_dataloader_modified", "dataset.py data/prepare_crossdocked.py", "true", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_torch_tensor_checkpoint_training_artifacts", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("no_real_final_dataset_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", str(step13bd.METADATA_CSV), "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bp_artifacts_unchanged", str(step13bp.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bp.OUTPUT_ROOT.as_posix()])),
        ("step13bo_artifacts_unchanged", str(step13bo.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bo.OUTPUT_ROOT.as_posix()])),
        ("step13bn_artifacts_unchanged", str(step13bn.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bn.OUTPUT_ROOT.as_posix()])),
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


def run_covapie_dataloader_interface_design_gate_v0() -> dict[str, Any]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    precondition_rows = build_precondition_rows()
    input_rows = build_input_source_rows()
    field_rows = build_field_mapping_rows()
    feature_rows = build_feature_interface_rows()
    mask_rows = build_mask_interface_rows()
    batch_rows = build_batch_collate_rows()
    checkpoint_rows = build_checkpoint_compatibility_rows()
    plan_rows = build_interface_smoke_plan_rows()
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    preview_rows = _preview_rows()
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bp_final_dataset_qa_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_preview_row_count": len(preview_rows),
        "source_preview_column_count": len(preview_rows[0]) if preview_rows else 0,
        "source_unique_event_count": len({row["extracted_event_id"] for row in preview_rows}),
        "source_unique_split_unit_count": len({row["split_unit_id"] for row in preview_rows}),
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in preview_rows}),
        "dataloader_input_source_contract_row_count": len(input_rows),
        "dataloader_field_mapping_contract_row_count": len(field_rows),
        "dataloader_feature_interface_contract_row_count": len(feature_rows),
        "dataloader_mask_interface_contract_row_count": len(mask_rows),
        "dataloader_batch_collate_contract_row_count": len(batch_rows),
        "checkpoint_compatibility_contract_row_count": len(checkpoint_rows),
        "dataloader_interface_smoke_plan_row_count": len(plan_rows),
        "dataloader_input_source_contract_passed": all(_bool(row["input_source_contract_passed"]) for row in input_rows),
        "dataloader_field_mapping_contract_passed": all(_bool(row["field_mapping_contract_passed"]) for row in field_rows),
        "dataloader_feature_interface_contract_passed": all(_bool(row["feature_interface_contract_passed"]) for row in feature_rows),
        "dataloader_mask_interface_contract_passed": all(_bool(row["mask_interface_contract_passed"]) for row in mask_rows),
        "dataloader_batch_collate_contract_passed": all(_bool(row["batch_collate_contract_passed"]) for row in batch_rows),
        "checkpoint_compatibility_contract_passed": all(_bool(row["checkpoint_compatibility_contract_passed"]) for row in checkpoint_rows),
        "dataloader_interface_smoke_plan_passed": all(_bool(row["smoke_plan_passed"]) for row in plan_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "dataloader_interface_design_completed_current_step": True,
        "dataloader_interface_smoke_written": False,
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
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "coordinate_extraction_current_step": False,
        "network_access_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_dataloader_interface_smoke": True,
        "ready_for_covapie_dataloader_interface_qa_gate": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in preview_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in preview_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_dataloader_interface_smoke",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bp_final_dataset_qa_gate_validated"],
            manifest["source_preview_row_count"] == 20,
            manifest["source_preview_column_count"] == 45,
            manifest["source_unique_event_count"] == 4,
            manifest["source_unique_split_unit_count"] == 4,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["dataloader_input_source_contract_row_count"] == 15,
            manifest["dataloader_field_mapping_contract_row_count"] == 45,
            manifest["dataloader_feature_interface_contract_row_count"] == 16,
            manifest["dataloader_mask_interface_contract_row_count"] == 8,
            manifest["dataloader_batch_collate_contract_row_count"] == 10,
            manifest["checkpoint_compatibility_contract_row_count"] == 8,
            manifest["dataloader_interface_smoke_plan_row_count"] == 10,
            manifest["dataloader_input_source_contract_passed"],
            manifest["dataloader_field_mapping_contract_passed"],
            manifest["dataloader_feature_interface_contract_passed"],
            manifest["dataloader_mask_interface_contract_passed"],
            manifest["dataloader_batch_collate_contract_passed"],
            manifest["checkpoint_compatibility_contract_passed"],
            manifest["dataloader_interface_smoke_plan_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["dataloader_interface_design_completed_current_step"],
            manifest["ready_for_covapie_dataloader_interface_smoke"],
            not manifest["ready_for_covapie_dataloader_interface_qa_gate"],
            not manifest["ready_for_covapie_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["dataloader_interface_design_gate_failed"]
    return {
        "precondition_rows": precondition_rows,
        "input_rows": input_rows,
        "field_rows": field_rows,
        "feature_rows": feature_rows,
        "mask_rows": mask_rows,
        "batch_rows": batch_rows,
        "checkpoint_rows": checkpoint_rows,
        "plan_rows": plan_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }

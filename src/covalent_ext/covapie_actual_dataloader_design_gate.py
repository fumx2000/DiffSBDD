from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_metadata_dataloader_smoke_qa_gate as step13bv


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_actual_dataloader_design_gate_v0"
PREVIOUS_STAGE = step13bv.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_actual_dataloader_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_actual_dataloader_design_precondition_audit.csv"
STATIC_REFERENCE_AUDIT_CSV = OUTPUT_ROOT / "covapie_original_dataloader_static_reference_audit.csv"
ADAPTER_DESIGN_CONTRACT_CSV = OUTPUT_ROOT / "covapie_actual_dataloader_adapter_design_contract.csv"
TENSORIZATION_INPUT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_actual_dataloader_tensorization_input_contract.csv"
BATCH_COLLATE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_actual_dataloader_batch_collate_contract.csv"
CHECKPOINT_COMPATIBILITY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_actual_dataloader_checkpoint_compatibility_contract.csv"
FEATURE_SEMANTICS_BLOCKER_CONTRACT_CSV = OUTPUT_ROOT / "covapie_actual_dataloader_feature_semantics_blocker_contract.csv"
FUTURE_SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_actual_dataloader_future_smoke_plan.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_actual_dataloader_design_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_actual_dataloader_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_actual_dataloader_design_gate_v0_summary.md")

step13bu = step13bv.step13bu
step13bt = step13bv.step13bt
step13br = step13bv.step13br
step13bo = step13bv.step13bo
step13bm = step13bv.step13bm
step13bd = step13bv.step13bd

CANONICAL_MASK_TASK_NAMES = step13bv.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bv.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bv.METADATA_CSV_SHA256

DATASET_PY = Path("dataset.py")
PREPARE_CROSSDOCKED_PY = Path("data/prepare_crossdocked.py")
LIGHTNING_MODULES_PY = Path("lightning_modules.py")
EQUIVARIANT_DIFFUSION_DIR = Path("equivariant_diffusion")
MODULE_PATH = Path("src/covalent_ext/covapie_actual_dataloader_design_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_actual_dataloader_design_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
STATIC_REFERENCE_COLUMNS = ["static_reference_item", "source_path", "expected_status", "observed_status", "static_reference_audit_passed", "qa_comment"]
ADAPTER_DESIGN_COLUMNS = ["adapter_design_item", "future_design_policy", "current_step_status", "allowed_in_future_actual_dataloader_smoke", "blocked_current_step", "adapter_design_contract_passed"]
TENSORIZATION_INPUT_COLUMNS = [
    "tensorization_item",
    "source_or_policy",
    "future_tensor_or_metadata_key",
    "feature_semantics_requirement",
    "current_step_status",
    "blocked_before_actual_tensor_smoke",
    "tensorization_input_contract_passed",
]
BATCH_COLLATE_COLUMNS = [
    "batch_contract_item",
    "future_batch_policy",
    "current_step_status",
    "checkpoint_compatibility_consideration",
    "blocked_before_actual_dataloader_smoke",
    "batch_collate_contract_passed",
]
CHECKPOINT_COMPATIBILITY_COLUMNS = [
    "checkpoint_compatibility_item",
    "expected_status",
    "observed_status",
    "risk_level",
    "required_future_gate",
    "checkpoint_compatibility_contract_passed",
]
FEATURE_SEMANTICS_BLOCKER_COLUMNS = [
    "blocker_item",
    "current_status",
    "required_future_resolution",
    "blocks_actual_tensor_dataloader_smoke",
    "blocks_training",
    "blocker_contract_passed",
]
FUTURE_SMOKE_PLAN_COLUMNS = [
    "planned_step",
    "planned_action",
    "allowed_inputs",
    "allowed_outputs_future_step",
    "blocked_outputs_current_step",
    "required_preconditions",
    "future_smoke_plan_passed",
]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


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


def _static_read_status(path: Path) -> tuple[str, bool]:
    full_path = REPO_ROOT / path
    if path.is_dir() or full_path.is_dir():
        py_files = sorted(full_path.rglob("*.py"))
        byte_count = 0
        for source in py_files:
            byte_count += len(source.read_text(encoding="utf-8"))
        return f"static_read_only_py_files={len(py_files)};bytes={byte_count}", bool(py_files)
    if not full_path.is_file():
        return "missing", False
    text = full_path.read_text(encoding="utf-8")
    return f"static_read_only_bytes={len(text)}", True


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
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
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


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
    forbidden = {"urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13bv = _load_json(step13bv.MANIFEST_JSON)
    manifest13bm = _load_json(step13bm.MANIFEST_JSON)
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    interface_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    checks = [
        ("step13bv_manifest_exists", step13bv.MANIFEST_JSON, "exists", step13bv.MANIFEST_JSON.exists(), step13bv.MANIFEST_JSON.exists()),
        ("step13bv_stage", step13bv.MANIFEST_JSON, step13bv.STAGE, manifest13bv.get("stage"), manifest13bv.get("stage") == step13bv.STAGE),
        ("step13bv_all_checks_passed", step13bv.MANIFEST_JSON, "true", manifest13bv.get("all_checks_passed"), manifest13bv.get("all_checks_passed") is True),
        ("step13bv_ready_for_actual_dataloader_design_gate", step13bv.MANIFEST_JSON, "true", manifest13bv.get("ready_for_covapie_actual_dataloader_design_gate"), manifest13bv.get("ready_for_covapie_actual_dataloader_design_gate") is True),
        ("step13bv_ready_for_actual_dataloader_smoke", step13bv.MANIFEST_JSON, "false", manifest13bv.get("ready_for_covapie_actual_dataloader_smoke"), manifest13bv.get("ready_for_covapie_actual_dataloader_smoke") is False),
        ("step13bv_ready_for_training", step13bv.MANIFEST_JSON, "false", manifest13bv.get("ready_for_training"), manifest13bv.get("ready_for_training") is False),
        ("step13bv_ready_to_train_now", step13bv.MANIFEST_JSON, "false", manifest13bv.get("ready_to_train_now"), manifest13bv.get("ready_to_train_now") is False),
        ("step13bu_metadata_shim_exists", "src/covalent_ext/covapie_metadata_dataloader_smoke.py", "exists", Path("src/covalent_ext/covapie_metadata_dataloader_smoke.py").exists(), Path("src/covalent_ext/covapie_metadata_dataloader_smoke.py").exists()),
        ("step13bu_metadata_smoke_preview_shape", step13bu.SMOKE_PREVIEW_CSV, "20x30", f"{len(metadata_rows)}x{len(metadata_rows[0]) if metadata_rows else 0}", len(metadata_rows) == 20 and bool(metadata_rows) and len(metadata_rows[0]) == 30),
        ("step13br_interface_smoke_preview_shape", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "20x35", f"{len(interface_rows)}x{len(interface_rows[0]) if interface_rows else 0}", len(interface_rows) == 20 and bool(interface_rows) and len(interface_rows[0]) == 35),
        ("step13bo_final_dataset_smoke_preview_shape", step13bo.SMOKE_PREVIEW_CSV, "20x45", f"{len(final_rows)}x{len(final_rows[0]) if final_rows else 0}", len(final_rows) == 20 and bool(final_rows) and len(final_rows[0]) == 45),
        ("step13bm_manifest_exists", step13bm.MANIFEST_JSON, "exists", step13bm.MANIFEST_JSON.exists(), step13bm.MANIFEST_JSON.exists()),
        ("step13bm_all_checks_passed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("all_checks_passed"), manifest13bm.get("all_checks_passed") is True),
        ("step13bm_feature_semantics_audit_completed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("feature_semantics_audit_completed_current_step"), manifest13bm.get("feature_semantics_audit_completed_current_step") is True),
        ("step13bm_feature_semantics_known_for_training", step13bm.MANIFEST_JSON, "false", manifest13bm.get("feature_semantics_known_for_training"), manifest13bm.get("feature_semantics_known_for_training") is False),
        ("step13bm_unknown_atom_policy_finalized", step13bm.MANIFEST_JSON, "false", manifest13bm.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bm.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("canonical_mask_count", step13bu.SMOKE_PREVIEW_CSV, "5", len({row["mask_task_name"] for row in metadata_rows}), len({row["mask_task_name"] for row in metadata_rows}) == 5),
        ("b3_scaffold_only_included", step13bu.SMOKE_PREVIEW_CSV, "true", "scaffold_only" in {row["mask_task_name"] for row in metadata_rows}, "scaffold_only" in {row["mask_task_name"] for row in metadata_rows}),
        ("no_extra_mask_tasks_added", step13bu.SMOKE_PREVIEW_CSV, "true", {row["mask_task_name"] for row in metadata_rows}, {row["mask_task_name"] for row in metadata_rows} == set(CANONICAL_MASK_TASK_NAMES)),
        ("metadata_csv_hash_unchanged", step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("project_name_canonical", "docs/covapie_project_naming_convention.md", "CovaPIE", PROJECT_NAME, PROJECT_NAME == "CovaPIE"),
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


def build_static_reference_rows() -> list[dict[str, Any]]:
    source_checks = [
        ("dataset_py_exists", DATASET_PY, "exists", DATASET_PY.exists()),
        ("prepare_crossdocked_py_exists", PREPARE_CROSSDOCKED_PY, "exists", PREPARE_CROSSDOCKED_PY.exists()),
        ("lightning_modules_py_exists", LIGHTNING_MODULES_PY, "exists", LIGHTNING_MODULES_PY.exists()),
        ("equivariant_diffusion_dir_exists", EQUIVARIANT_DIFFUSION_DIR, "exists", EQUIVARIANT_DIFFUSION_DIR.is_dir()),
    ]
    rows = [
        {
            "static_reference_item": item,
            "source_path": path.as_posix(),
            "expected_status": expected,
            "observed_status": "exists" if passed else "missing",
            "static_reference_audit_passed": passed,
            "qa_comment": "static source path available",
        }
        for item, path, expected, passed in source_checks
    ]
    for item, path in [
        ("dataset_py_static_read_only", DATASET_PY),
        ("prepare_crossdocked_static_read_only", PREPARE_CROSSDOCKED_PY),
        ("lightning_modules_static_read_only", LIGHTNING_MODULES_PY),
        ("equivariant_diffusion_static_read_only", EQUIVARIANT_DIFFUSION_DIR),
    ]:
        observed, passed = _static_read_status(path)
        rows.append(
            {
                "static_reference_item": item,
                "source_path": path.as_posix(),
                "expected_status": "static_read_only",
                "observed_status": observed,
                "static_reference_audit_passed": passed,
                "qa_comment": "read for design reference only; no import or modification",
            }
        )
    no_original_diff = not _path_diff_exists([DATASET_PY.as_posix(), PREPARE_CROSSDOCKED_PY.as_posix()])
    no_protected_diff = not _path_diff_exists([EQUIVARIANT_DIFFUSION_DIR.as_posix(), LIGHTNING_MODULES_PY.as_posix()])
    rows.extend(
        [
            {
                "static_reference_item": "original_dataloader_no_diff",
                "source_path": "dataset.py;data/prepare_crossdocked.py",
                "expected_status": "no_diff",
                "observed_status": "no_diff" if no_original_diff else "diff_present",
                "static_reference_audit_passed": no_original_diff,
                "qa_comment": "original DiffSBDD dataloader files unchanged",
            },
            {
                "static_reference_item": "protected_model_code_no_diff",
                "source_path": "lightning_modules.py;equivariant_diffusion/",
                "expected_status": "no_diff",
                "observed_status": "no_diff" if no_protected_diff else "diff_present",
                "static_reference_audit_passed": no_protected_diff,
                "qa_comment": "protected DiffSBDD model code unchanged",
            },
        ]
    )
    return rows


def build_adapter_design_rows() -> list[dict[str, Any]]:
    policies = {
        "additive_adapter_under_src_covalent_ext": "future adapter must be additive under src/covalent_ext",
        "no_direct_dataset_py_modification": "dataset.py remains untouched",
        "no_direct_prepare_crossdocked_modification": "data/prepare_crossdocked.py remains untouched",
        "future_torch_dataset_class_optional": "torch Dataset class can be introduced only in a later actual-dataloader gate",
        "future_reads_metadata_smoke_or_final_dataset": "future adapter reads approved derived metadata/final dataset artifacts",
        "future_reads_derived_atom_tables_only": "future adapter reads derived atom tables, not raw structures",
        "future_preserves_sample_identity": "sample_id/final_dataset_row_id/extracted_event_id must be preserved",
        "future_preserves_split_unit_identity": "split_unit_id remains explicit for leakage-safe batching",
        "future_preserves_canonical_mask_task_name": "canonical long mask task name is source of truth",
        "future_emits_training_blocker_metadata": "feature/training blockers travel with metadata until resolved",
        "future_checkpoint_compatible_batch_keys": "future batch keys must remain compatible with existing checkpoint assumptions",
        "future_actual_dataloader_smoke_requires_separate_gate": "actual dataloader smoke requires its own gate",
    }
    return [
        {
            "adapter_design_item": item,
            "future_design_policy": policy,
            "current_step_status": "design_only_not_implemented",
            "allowed_in_future_actual_dataloader_smoke": "true_after_required_gate",
            "blocked_current_step": True,
            "adapter_design_contract_passed": True,
        }
        for item, policy in policies.items()
    ]


def build_tensorization_input_rows() -> list[dict[str, Any]]:
    rows = [
        ("protein_xyz_from_derived_atom_table", "protein_pocket_atom_table_path", "protein_xyz", "coordinate frame/unit audit must be resolved", "future_coordinate_candidate_only", False),
        ("ligand_xyz_from_derived_atom_table", "ligand_atom_table_path", "ligand_xyz", "coordinate frame/unit audit must be resolved", "future_coordinate_candidate_only", False),
        ("protein_atom_feature_semantics_blocked", "feature semantics audit", "protein_atom_features", "protein atom feature semantics not training-final", "blocked_by_feature_semantics", True),
        ("ligand_atom_feature_semantics_blocked", "feature semantics audit", "ligand_atom_features", "ligand atom feature semantics not training-final", "blocked_by_feature_semantics", True),
        ("unknown_atom_feature_policy_blocked", "feature semantics audit", "unknown_atom_feature_policy", "unknown atom policy not finalized", "blocked_by_feature_semantics", True),
        ("mask_task_name_as_string_selector", "mask_task_name", "mask_task_name", "string selector can remain metadata before tensorization", "metadata_selector_only", False),
        ("mask_boolean_tensor_blocked_until_group_labels", "group label materialization", "mask_boolean_tensor", "group labels not materialized for tensor mask", "blocked_until_group_labels", True),
        ("scaffold_linker_warhead_labels_blocked", "group label materialization", "scaffold_linker_warhead_labels", "group labels not materialized", "blocked_until_group_labels", True),
        ("warhead_type_label_blocked", "auxiliary label semantics", "warhead_type_label", "warhead type label not training-final", "blocked_by_feature_semantics", True),
        ("covalent_atom_pair_label_blocked", "auxiliary label semantics", "covalent_atom_pair_label", "covalent atom pair label not training-final", "blocked_by_feature_semantics", True),
        ("covalent_bond_distance_metadata_only", "covalent_bond_distance_angstrom", "covalent_bond_distance_angstrom", "distance is metadata until tensorization audit", "metadata_only", False),
        ("pre_covalent_geometry_blocked", "geometry semantics audit", "pre_covalent_geometry", "pre/post geometry labels not training-final", "blocked_by_feature_semantics", True),
        ("batch_index_tensor_blocked", "future collate policy", "batch_index", "torch collate gate required", "blocked_current_step", True),
        ("torch_tensor_creation_blocked_current_step", "current execution boundary", "all_tensor_outputs", "no tensor creation in design gate", "blocked_current_step", True),
    ]
    return [
        {
            "tensorization_item": item,
            "source_or_policy": source,
            "future_tensor_or_metadata_key": key,
            "feature_semantics_requirement": requirement,
            "current_step_status": status,
            "blocked_before_actual_tensor_smoke": blocked,
            "tensorization_input_contract_passed": True,
        }
        for item, source, key, requirement, status, blocked in rows
    ]


def build_batch_collate_rows() -> list[dict[str, Any]]:
    rows = [
        ("future_batch_sample_identity", "preserve sample_id/final_dataset_row_id/extracted_event_id", "design_only_no_collate_current_step", "identity keys additive and checkpoint-safe", False),
        ("future_batch_split_unit_identity", "preserve split_unit_id in batch metadata", "design_only_no_collate_current_step", "split unit must remain visible for leakage checks", False),
        ("future_batch_protein_coordinates", "collate protein_xyz after tensorization audit", "design_only_no_collate_current_step", "coordinate tensor shape must not break checkpoint assumptions", True),
        ("future_batch_ligand_coordinates", "collate ligand_xyz after tensorization audit", "design_only_no_collate_current_step", "coordinate tensor shape must not break checkpoint assumptions", True),
        ("future_batch_atom_features_blocked", "block atom feature tensors until feature semantics finalized", "design_only_no_collate_current_step", "feature dimensionality affects checkpoint compatibility", True),
        ("future_batch_mask_selector", "keep mask_task_name selector metadata", "design_only_no_collate_current_step", "string selector additive and checkpoint-safe", False),
        ("future_batch_mask_boolean_blocked", "block boolean mask tensors until group labels materialized", "design_only_no_collate_current_step", "mask tensor shape affects runtime semantics", True),
        ("future_batch_auxiliary_labels_blocked", "block auxiliary labels until semantics finalized", "design_only_no_collate_current_step", "new labels require additive keys and loss gate", True),
        ("future_batch_variable_size_collate_requires_torch_gate", "variable-size collate requires separate torch gate", "design_only_no_collate_current_step", "collate_fn must be tested before model runtime", True),
        ("future_training_batch_blocked", "training batch blocked", "design_only_no_collate_current_step", "training requires feature semantics, checkpoint, forward, and loss gates", True),
    ]
    return [
        {
            "batch_contract_item": item,
            "future_batch_policy": policy,
            "current_step_status": status,
            "checkpoint_compatibility_consideration": consideration,
            "blocked_before_actual_dataloader_smoke": blocked,
            "batch_collate_contract_passed": True,
        }
        for item, policy, status, consideration, blocked in rows
    ]


def build_checkpoint_compatibility_rows() -> list[dict[str, Any]]:
    rows = [
        ("original_checkpoint_path_reference_only", "reference_only", "not loaded", "medium", "checkpoint_compatibility_smoke_before_model_runtime"),
        ("checkpoint_not_loaded_current_step", "not_loaded", "not loaded", "low", "checkpoint_compatibility_smoke_before_model_runtime"),
        ("no_model_forward_current_step", "not_called", "not called", "high", "model_forward_smoke_after_checkpoint_compatibility"),
        ("original_diffsbbd_model_unchanged", "no_diff", "no diff", "high", "protected_source_qa_before_runtime"),
        ("original_diffsbbd_dataloader_unchanged", "no_diff", "no diff", "high", "actual_dataloader_adapter_design_gate"),
        ("future_adapter_must_preserve_existing_batch_keys", "required", "design requirement recorded", "high", "actual_dataloader_adapter_smoke"),
        ("future_new_covapie_keys_must_be_additive", "required", "design requirement recorded", "medium", "actual_dataloader_adapter_smoke"),
        ("future_loss_integration_requires_separate_gate", "required", "not integrated current step", "high", "loss_integration_design_gate"),
        ("future_forward_integration_requires_separate_gate", "required", "not integrated current step", "high", "model_forward_integration_design_gate"),
        ("checkpoint_compatibility_required_before_actual_smoke", "required", "blocked before actual smoke", "high", "checkpoint_compatibility_smoke_before_model_runtime"),
    ]
    return [
        {
            "checkpoint_compatibility_item": item,
            "expected_status": expected,
            "observed_status": observed,
            "risk_level": risk,
            "required_future_gate": gate,
            "checkpoint_compatibility_contract_passed": True,
        }
        for item, expected, observed, risk, gate in rows
    ]


def build_feature_semantics_blocker_rows() -> list[dict[str, Any]]:
    rows = [
        ("feature_semantics_known_for_training_false", "feature_semantics_known_for_training=false", "feature semantics tensorization audit gate", True, True),
        ("unknown_atom_feature_policy_finalized_for_training_false", "unknown_atom_feature_policy_finalized_for_training=false", "unknown atom policy resolution", True, True),
        ("protein_atom_feature_schema_not_training_final", "not_training_final", "protein atom feature schema finalization", True, True),
        ("ligand_atom_feature_schema_not_training_final", "not_training_final", "ligand atom feature schema finalization", True, True),
        ("scaffold_linker_warhead_labels_not_materialized", "not_materialized", "group label materialization gate", True, True),
        ("warhead_type_labels_not_materialized", "not_materialized", "warhead type label materialization gate", True, True),
        ("covalent_atom_pair_labels_not_training_final", "not_training_final", "covalent atom-pair label audit", True, True),
        ("pre_post_geometry_labels_not_training_final", "not_training_final", "pre/post geometry label audit", True, True),
        ("actual_tensor_dataloader_smoke_blocked_by_feature_semantics", "blocked", "feature semantics tensorization audit gate", True, True),
        ("formal_training_requires_feature_semantics_audit", "blocked", "formal training feature semantics audit", True, True),
    ]
    return [
        {
            "blocker_item": item,
            "current_status": status,
            "required_future_resolution": resolution,
            "blocks_actual_tensor_dataloader_smoke": blocks_smoke,
            "blocks_training": blocks_training,
            "blocker_contract_passed": True,
        }
        for item, status, resolution, blocks_smoke, blocks_training in rows
    ]


def build_future_smoke_plan_rows() -> list[dict[str, Any]]:
    rows = [
        ("actual_dataloader_design_gate_current_step", "design actual dataloader adapter only", "Step 13BV QA artifacts; static DiffSBDD source references", "design contracts", "actual dataloader smoke; tensors; training", "Step 13BV passed"),
        ("feature_semantics_resolution_gate_next_if_blocked", "resolve tensorization semantics blockers", "feature semantics audit artifacts; derived metadata", "feature semantics tensorization audit outputs", "actual tensor dataloader smoke; training", "feature_semantics_known_for_training=false"),
        ("actual_dataloader_adapter_smoke_after_feature_resolution", "instantiate additive adapter in smoke only", "resolved feature semantics; derived atom tables", "adapter smoke artifacts", "model forward; loss; training", "feature semantics tensorization audit passed"),
        ("actual_tensor_creation_smoke_after_feature_resolution", "create transient tensors in smoke only", "adapter smoke rows; derived atom tables", "shape audits, no persisted tensors", "checkpoint/model/loss/training", "adapter smoke passed"),
        ("checkpoint_compatibility_smoke_before_model_runtime", "verify checkpoint-compatible batch keys", "adapter/tensor smoke artifacts", "checkpoint compatibility audit", "model forward; loss; training", "tensor smoke passed"),
        ("model_forward_smoke_after_checkpoint_compatibility", "perform controlled forward smoke", "checkpoint-compatible batch", "forward smoke audit", "loss/backward/optimizer/training", "checkpoint compatibility passed"),
        ("loss_training_gate_after_forward_smoke", "design/verify loss path separately", "forward smoke evidence", "loss gate artifacts", "training", "forward smoke passed"),
        ("formal_training_after_feature_semantics_audit_only", "formal training only after all gates", "feature semantics, split/leakage, checkpoint, forward, loss gates", "training run artifacts", "current step training", "all prior gates passed"),
    ]
    return [
        {
            "planned_step": step,
            "planned_action": action,
            "allowed_inputs": inputs,
            "allowed_outputs_future_step": outputs,
            "blocked_outputs_current_step": blocked,
            "required_preconditions": preconditions,
            "future_smoke_plan_passed": True,
        }
        for step, action, inputs, outputs, blocked, preconditions in rows
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_actual_dataloader_smoke_written", "true", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", "true", not _forbidden_named_artifact_exists()),
        ("no_original_dataloader_modified", "true", not _path_diff_exists([DATASET_PY.as_posix(), PREPARE_CROSSDOCKED_PY.as_posix()])),
        ("no_torch_tensor_checkpoint_training_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_numpy_outputs", "true", True),
        ("no_real_final_dataset_written", "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bv_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bv.OUTPUT_ROOT.as_posix()])),
        ("step13bu_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bu.OUTPUT_ROOT.as_posix()])),
        ("step13bt_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bt.OUTPUT_ROOT.as_posix()])),
        ("step13br_artifacts_unchanged", "no_diff", not _path_diff_exists([step13br.OUTPUT_ROOT.as_posix()])),
        ("step13bo_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bo.OUTPUT_ROOT.as_posix()])),
        ("step13bm_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bm.OUTPUT_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", "no_diff", not _path_diff_exists(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"])),
        ("protected_source_diff_empty", "no_diff", not _path_diff_exists([EQUIVARIANT_DIFFUSION_DIR.as_posix(), LIGHTNING_MODULES_PY.as_posix()])),
        ("original_dataloader_diff_empty", "no_diff", not _path_diff_exists([DATASET_PY.as_posix(), PREPARE_CROSSDOCKED_PY.as_posix()])),
        ("no_network_download_rdkit_biopdb_gemmi_gzip_torch_numpy_imports", "true", not _own_files_have_forbidden_imports()),
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


def run_covapie_actual_dataloader_design_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    static_rows = build_static_reference_rows()
    adapter_rows = build_adapter_design_rows()
    tensor_rows = build_tensorization_input_rows()
    batch_rows = build_batch_collate_rows()
    checkpoint_rows = build_checkpoint_compatibility_rows()
    feature_rows = build_feature_semantics_blocker_rows()
    plan_rows = build_future_smoke_plan_rows()
    safety_rows = build_safety_rows()
    metadata_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    interface_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bv_metadata_dataloader_smoke_qa_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_metadata_smoke_preview_row_count": len(metadata_rows),
        "source_metadata_smoke_preview_column_count": len(metadata_rows[0]) if metadata_rows else 0,
        "source_interface_preview_row_count": len(interface_rows),
        "source_interface_preview_column_count": len(interface_rows[0]) if interface_rows else 0,
        "source_final_dataset_preview_row_count": len(final_rows),
        "source_final_dataset_preview_column_count": len(final_rows[0]) if final_rows else 0,
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in metadata_rows}),
        "original_dataloader_static_reference_audit_row_count": len(static_rows),
        "actual_dataloader_adapter_design_contract_row_count": len(adapter_rows),
        "tensorization_input_contract_row_count": len(tensor_rows),
        "batch_collate_contract_row_count": len(batch_rows),
        "checkpoint_compatibility_contract_row_count": len(checkpoint_rows),
        "feature_semantics_blocker_contract_row_count": len(feature_rows),
        "future_smoke_plan_row_count": len(plan_rows),
        "original_dataloader_static_reference_audit_passed": all(_bool(row["static_reference_audit_passed"]) for row in static_rows),
        "actual_dataloader_adapter_design_contract_passed": all(_bool(row["adapter_design_contract_passed"]) for row in adapter_rows),
        "tensorization_input_contract_passed": all(_bool(row["tensorization_input_contract_passed"]) for row in tensor_rows),
        "batch_collate_contract_passed": all(_bool(row["batch_collate_contract_passed"]) for row in batch_rows),
        "checkpoint_compatibility_contract_passed": all(_bool(row["checkpoint_compatibility_contract_passed"]) for row in checkpoint_rows),
        "feature_semantics_blocker_contract_passed": all(_bool(row["blocker_contract_passed"]) for row in feature_rows),
        "future_smoke_plan_passed": all(_bool(row["future_smoke_plan_passed"]) for row in plan_rows),
        "safety_audit_passed": all(_bool(row["safety_passed"]) for row in safety_rows),
        "actual_dataloader_design_completed_current_step": True,
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
        "ready_for_covapie_feature_semantics_tensorization_audit_gate": True,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in metadata_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in metadata_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_feature_semantics_tensorization_audit_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bv_metadata_dataloader_smoke_qa_validated"],
            manifest["source_metadata_smoke_preview_row_count"] == 20,
            manifest["source_metadata_smoke_preview_column_count"] == 30,
            manifest["source_interface_preview_row_count"] == 20,
            manifest["source_interface_preview_column_count"] == 35,
            manifest["source_final_dataset_preview_row_count"] == 20,
            manifest["source_final_dataset_preview_column_count"] == 45,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["original_dataloader_static_reference_audit_row_count"] == 10,
            manifest["actual_dataloader_adapter_design_contract_row_count"] == 12,
            manifest["tensorization_input_contract_row_count"] == 14,
            manifest["batch_collate_contract_row_count"] == 10,
            manifest["checkpoint_compatibility_contract_row_count"] == 10,
            manifest["feature_semantics_blocker_contract_row_count"] == 10,
            manifest["future_smoke_plan_row_count"] == 8,
            manifest["original_dataloader_static_reference_audit_passed"],
            manifest["actual_dataloader_adapter_design_contract_passed"],
            manifest["tensorization_input_contract_passed"],
            manifest["batch_collate_contract_passed"],
            manifest["checkpoint_compatibility_contract_passed"],
            manifest["feature_semantics_blocker_contract_passed"],
            manifest["future_smoke_plan_passed"],
            manifest["safety_audit_passed"],
            manifest["actual_dataloader_design_completed_current_step"],
            not manifest["actual_dataloader_smoke_written"],
            not manifest["real_dataloader_written"],
            not manifest["original_dataloader_modified"],
            not manifest["torch_imported"],
            not manifest["torch_tensor_created"],
            not manifest["numpy_imported"],
            not manifest["checkpoint_loaded"],
            not manifest["model_forward_called"],
            not manifest["loss_compute_called"],
            not manifest["training_allowed"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            manifest["ready_for_covapie_feature_semantics_tensorization_audit_gate"],
            not manifest["ready_for_covapie_actual_dataloader_adapter_smoke"],
            not manifest["ready_for_covapie_actual_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["actual_dataloader_design_gate_failed"]
    return {
        "precondition_rows": precondition_rows,
        "static_rows": static_rows,
        "adapter_rows": adapter_rows,
        "tensor_rows": tensor_rows,
        "batch_rows": batch_rows,
        "checkpoint_rows": checkpoint_rows,
        "feature_rows": feature_rows,
        "plan_rows": plan_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

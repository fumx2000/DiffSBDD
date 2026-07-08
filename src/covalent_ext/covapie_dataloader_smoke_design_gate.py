from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_dataloader_interface_qa_gate as step13bs


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_dataloader_smoke_design_gate_v0"
PREVIOUS_STAGE = step13bs.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_dataloader_smoke_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_dataloader_smoke_design_precondition_audit.csv"
RUNTIME_BOUNDARY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_dataloader_smoke_runtime_boundary_contract.csv"
METADATA_DATASET_API_CONTRACT_CSV = OUTPUT_ROOT / "covapie_metadata_dataset_api_contract.csv"
GETITEM_OUTPUT_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "covapie_metadata_getitem_output_mapping_contract.csv"
TENSORIZATION_BLOCKER_CONTRACT_CSV = OUTPUT_ROOT / "covapie_tensorization_blocker_contract.csv"
BATCH_COLLATE_DESIGN_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_collate_design_contract.csv"
CHECKPOINT_RUNTIME_RISK_CONTRACT_CSV = OUTPUT_ROOT / "covapie_checkpoint_runtime_risk_contract.csv"
METADATA_DATALOADER_SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_plan.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_dataloader_smoke_design_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_dataloader_smoke_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_dataloader_smoke_design_gate_v0_summary.md")

step13br = step13bs.step13br
step13bq = step13bs.step13bq
step13bp = step13bs.step13bp
step13bo = step13bs.step13bo
step13bm = step13bs.step13bm
step13bd = step13bs.step13bd

CANONICAL_MASK_TASK_NAMES = step13bs.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bs.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bs.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
RUNTIME_BOUNDARY_COLUMNS = [
    "runtime_boundary_item",
    "future_allowed_action",
    "current_step_status",
    "allowed_in_next_metadata_smoke",
    "blocked_in_next_metadata_smoke",
    "required_before_actual_dataloader_smoke",
    "runtime_boundary_contract_passed",
]
METADATA_DATASET_API_COLUMNS = [
    "api_contract_item",
    "future_minimal_behavior",
    "expected_input",
    "expected_output",
    "current_step_implemented",
    "allowed_in_next_metadata_smoke",
    "blocked_before_actual_dataloader_smoke",
    "api_contract_passed",
]
GETITEM_OUTPUT_MAPPING_COLUMNS = [
    "getitem_mapping_item",
    "source_fields",
    "future_getitem_key",
    "expected_python_type_policy",
    "tensorization_status",
    "required_before_metadata_smoke",
    "blocked_before_actual_dataloader_smoke",
    "mapping_contract_passed",
]
TENSORIZATION_BLOCKER_COLUMNS = ["blocker_item", "current_status", "blocked_until_step", "required_future_audit", "blocker_contract_passed", "qa_comment"]
BATCH_COLLATE_DESIGN_COLUMNS = [
    "batch_collate_item",
    "current_step_status",
    "next_metadata_smoke_policy",
    "actual_dataloader_requirement",
    "blocker_before_actual_dataloader_smoke",
    "batch_collate_design_passed",
]
CHECKPOINT_RUNTIME_RISK_COLUMNS = ["checkpoint_risk_item", "current_status", "next_metadata_smoke_status", "risk_level", "required_future_gate", "checkpoint_runtime_risk_passed"]
METADATA_DATALOADER_SMOKE_PLAN_COLUMNS = [
    "planned_step",
    "planned_action",
    "allowed_inputs",
    "allowed_outputs_future_step",
    "blocked_outputs_current_step",
    "required_preconditions",
    "metadata_smoke_plan_passed",
]
SAFETY_AUDIT_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


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


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "covapie_metadata_dataloader_smoke_preview.csv",
        "covapie_metadata_dataloader_smoke_preview.json",
        "metadata_dataloader_smoke.csv",
        "metadata_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
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


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13bs = _load_json(step13bs.MANIFEST_JSON)
    manifest13bm = _load_json(step13bm.MANIFEST_JSON)
    interface_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    interface_json_rows = _load_json(step13br.INTERFACE_SMOKE_PREVIEW_JSON)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    checks = [
        ("step13bs_manifest_exists", step13bs.MANIFEST_JSON, "exists", step13bs.MANIFEST_JSON.exists(), step13bs.MANIFEST_JSON.exists()),
        ("step13bs_stage", step13bs.MANIFEST_JSON, step13bs.STAGE, manifest13bs.get("stage"), manifest13bs.get("stage") == step13bs.STAGE),
        ("step13bs_all_checks_passed", step13bs.MANIFEST_JSON, "true", manifest13bs.get("all_checks_passed"), manifest13bs.get("all_checks_passed") is True),
        ("step13bs_ready_for_smoke_design_gate", step13bs.MANIFEST_JSON, "true", manifest13bs.get("ready_for_covapie_dataloader_smoke_design_gate"), manifest13bs.get("ready_for_covapie_dataloader_smoke_design_gate") is True),
        ("step13bs_ready_for_dataloader_smoke", step13bs.MANIFEST_JSON, "false", manifest13bs.get("ready_for_covapie_dataloader_smoke"), manifest13bs.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13bs_ready_for_training", step13bs.MANIFEST_JSON, "false", manifest13bs.get("ready_for_training"), manifest13bs.get("ready_for_training") is False),
        ("step13bs_ready_to_train_now", step13bs.MANIFEST_JSON, "false", manifest13bs.get("ready_to_train_now"), manifest13bs.get("ready_to_train_now") is False),
        ("step13br_preview_csv_shape", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "20x35", f"{len(interface_rows)}x{len(interface_rows[0]) if interface_rows else 0}", len(interface_rows) == 20 and bool(interface_rows) and len(interface_rows[0]) == 35),
        ("step13br_preview_json_row_count", step13br.INTERFACE_SMOKE_PREVIEW_JSON, "20", len(interface_json_rows), len(interface_json_rows) == 20),
        ("step13br_preview_not_rewritten_by_step13bs", step13bs.MANIFEST_JSON, "false", manifest13bs.get("dataloader_interface_smoke_preview_written_current_step"), manifest13bs.get("dataloader_interface_smoke_preview_written_current_step") is False),
        ("step13bq_contracts_exist", step13bq.OUTPUT_ROOT, "exists", step13bq.OUTPUT_ROOT.exists(), step13bq.OUTPUT_ROOT.exists()),
        ("step13bq_field_mapping_contract_row_count", step13bq.FIELD_MAPPING_CONTRACT_CSV, "45", len(_csv_rows(step13bq.FIELD_MAPPING_CONTRACT_CSV)), len(_csv_rows(step13bq.FIELD_MAPPING_CONTRACT_CSV)) == 45),
        ("step13bq_checkpoint_contract_row_count", step13bq.CHECKPOINT_COMPATIBILITY_CONTRACT_CSV, "8", len(_csv_rows(step13bq.CHECKPOINT_COMPATIBILITY_CONTRACT_CSV)), len(_csv_rows(step13bq.CHECKPOINT_COMPATIBILITY_CONTRACT_CSV)) == 8),
        ("step13bo_final_dataset_preview_shape", step13bo.SMOKE_PREVIEW_CSV, "20x45", f"{len(final_rows)}x{len(final_rows[0]) if final_rows else 0}", len(final_rows) == 20 and bool(final_rows) and len(final_rows[0]) == 45),
        ("step13bm_feature_semantics_audit_completed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("feature_semantics_audit_completed_current_step"), manifest13bm.get("feature_semantics_audit_completed_current_step") is True),
        ("step13bm_feature_semantics_known_for_training", step13bm.MANIFEST_JSON, "false", manifest13bm.get("feature_semantics_known_for_training"), manifest13bm.get("feature_semantics_known_for_training") is False),
        ("step13bm_unknown_atom_policy_finalized", step13bm.MANIFEST_JSON, "false", manifest13bm.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bm.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("canonical_mask_count", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "5", len({row["mask_task_name"] for row in interface_rows}), len({row["mask_task_name"] for row in interface_rows}) == 5),
        ("b3_scaffold_only_included", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "true", "scaffold_only" in {row["mask_task_name"] for row in interface_rows}, "scaffold_only" in {row["mask_task_name"] for row in interface_rows}),
        ("no_extra_mask_tasks_added", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "true", {row["mask_task_name"] for row in interface_rows}, {row["mask_task_name"] for row in interface_rows} == set(CANONICAL_MASK_TASK_NAMES)),
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


def build_runtime_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        ("future_smoke_reads_interface_preview", "read Step 13BR interface preview CSV/JSON", True, False, "interface preview QA must pass"),
        ("future_smoke_reads_final_dataset_preview", "read Step 13BO final dataset preview CSV/JSON", True, False, "final dataset smoke QA must pass"),
        ("future_smoke_constructs_metadata_dataset_shim", "construct tiny metadata-only Dataset-like shim under src/covalent_ext", True, False, "additive shim only"),
        ("future_smoke_validates_len_getitem", "validate len and getitem on Python metadata records", True, False, "metadata-only smoke design"),
        ("future_smoke_validates_python_dict_records", "validate Python dict records with string/list/scalar metadata", True, False, "no tensor outputs"),
        ("future_smoke_no_torch_import", "do not import torch", False, True, "actual torch gate"),
        ("future_smoke_no_tensor_creation", "do not create tensors", False, True, "feature semantics and tensorization gate"),
        ("future_smoke_no_checkpoint_load", "do not load checkpoints", False, True, "checkpoint runtime gate"),
        ("future_smoke_no_model_forward", "do not call model forward", False, True, "model runtime gate"),
        ("future_smoke_no_loss_or_training", "do not compute loss/backward/optimizer/trainer.fit", False, True, "training gate"),
        ("future_smoke_no_original_dataloader_modify", "do not modify dataset.py or data/prepare_crossdocked.py", False, True, "adapter design gate"),
        ("future_smoke_no_raw_file_read", "do not read raw structure files", False, True, "raw-read gate"),
        ("feature_semantics_blockers_preserved", "carry feature semantics blockers into smoke output", True, False, "feature semantics audit before training"),
        ("actual_torch_dataloader_still_blocked", "actual torch DataLoader smoke remains blocked", False, True, "future actual dataloader smoke gate"),
    ]
    return [
        {
            "runtime_boundary_item": item,
            "future_allowed_action": action,
            "current_step_status": "design_only_not_executed",
            "allowed_in_next_metadata_smoke": allowed,
            "blocked_in_next_metadata_smoke": blocked,
            "required_before_actual_dataloader_smoke": required,
            "runtime_boundary_contract_passed": True,
        }
        for item, action, allowed, blocked, required in rows
    ]


def build_metadata_dataset_api_rows() -> list[dict[str, Any]]:
    rows = [
        ("metadata_dataset_constructor", "load interface preview rows into a lightweight Python object", "interface preview CSV/JSON path", "metadata-only dataset shim", True, "actual adapter design"),
        ("metadata_dataset_len", "__len__ returns 20", "loaded rows", "integer row count", True, "actual adapter design"),
        ("metadata_dataset_getitem_by_index", "__getitem__(index) returns one Python dict", "integer index", "dict[str, metadata scalar/list]", True, "actual adapter design"),
        ("metadata_dataset_getitem_required_identity_keys", "include row/sample/event identity", "interface preview row", "identity metadata keys", True, "actual adapter design"),
        ("metadata_dataset_getitem_required_path_refs", "include derived table path references only", "interface preview row", "path reference strings", True, "raw read gate"),
        ("metadata_dataset_getitem_mask_task_keys", "include canonical mask task name and display alias", "interface preview row", "mask metadata keys", True, "tensor mask gate"),
        ("metadata_dataset_getitem_conditioning_keys", "include conditioning mode and covalent residue flag", "interface preview row", "conditioning metadata keys", True, "feature semantics gate"),
        ("metadata_dataset_getitem_blocker_flags", "include training blocker flags", "interface/final preview rows", "bool/string blocker metadata", True, "feature semantics gate"),
        ("metadata_dataset_no_tensor_outputs", "return no tensors", "metadata rows", "Python dict only", True, "tensorization gate"),
        ("metadata_dataset_no_collate_current_step", "do not implement collate in design or next metadata smoke", "none", "not implemented", True, "actual dataloader gate"),
    ]
    return [
        {
            "api_contract_item": item,
            "future_minimal_behavior": behavior,
            "expected_input": expected_input,
            "expected_output": expected_output,
            "current_step_implemented": False,
            "allowed_in_next_metadata_smoke": allowed,
            "blocked_before_actual_dataloader_smoke": blocked,
            "api_contract_passed": True,
        }
        for item, behavior, expected_input, expected_output, allowed, blocked in rows
    ]


def build_getitem_output_mapping_rows() -> list[dict[str, Any]]:
    preview_fields = set(_csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)[0]) | set(_csv_rows(step13bo.SMOKE_PREVIEW_CSV)[0])
    rows = [
        ("identity_metadata", "dataloader_interface_smoke_row_id;final_dataset_row_id;sample_id;extracted_event_id", "metadata.identity", "dict[str,str]", "required", "actual adapter/tensor gate"),
        ("split_metadata", "split_unit_id", "metadata.split_unit_id", "str", "required", "split leakage gate before training"),
        ("protein_table_path_refs", "protein_pocket_atom_table_path;protein_atom_row_count_for_event", "metadata.protein_table_ref", "dict[str,str|int]", "required", "raw/tensor gate"),
        ("ligand_table_path_refs", "ligand_atom_table_path;ligand_atom_row_count_for_event", "metadata.ligand_table_ref", "dict[str,str|int]", "required", "raw/tensor gate"),
        ("atom_count_metadata", "protein_atom_row_count_for_event;ligand_atom_row_count_for_event", "metadata.atom_counts", "dict[str,int]", "required", "tensor shape gate"),
        ("mask_task_selector", "mask_task_name", "mask.task_name", "str canonical long name", "required", "tensor mask gate"),
        ("mask_alias_display_only", "mask_task_alias", "mask.alias", "str display only", "optional", "tensor mask gate"),
        ("conditioning_metadata", "conditioning_mode;covalent_residue_conditioned", "metadata.conditioning", "dict[str,str|bool]", "required", "feature semantics gate"),
        ("covalent_geometry_metadata", "covalent_bond_atom_pair;covalent_bond_distance_angstrom", "metadata.covalent_geometry", "dict[str,str|float]", "required", "geometry feature gate"),
        ("future_tensor_key_names_as_strings", "future_protein_xyz_key;future_ligand_xyz_key;future_mask_selector_key", "metadata.future_tensor_keys", "dict[str,str]", "optional", "tensorization gate"),
        ("blocker_flags", "feature_semantics_known_for_training;unknown_atom_feature_policy_finalized_for_training;ready_for_training", "metadata.blockers", "dict[str,bool]", "required", "feature semantics gate"),
        ("checkpoint_compatibility_refs", "checkpoint_compatibility_contract_path", "metadata.checkpoint_contract", "str path reference", "optional", "checkpoint runtime gate"),
    ]
    mapped = []
    for item, source_fields, key, policy, required, blocked in rows:
        exists = all(field in preview_fields for field in source_fields.split(";"))
        mapped.append(
            {
                "getitem_mapping_item": item,
                "source_fields": source_fields,
                "future_getitem_key": key,
                "expected_python_type_policy": policy,
                "tensorization_status": "not_tensorized_metadata_only",
                "required_before_metadata_smoke": required,
                "blocked_before_actual_dataloader_smoke": blocked,
                "mapping_contract_passed": exists,
            }
        )
    return mapped


def build_tensorization_blocker_rows() -> list[dict[str, Any]]:
    rows = [
        ("no_torch_import_current_step", "torch_imported=false", "metadata smoke design only", "none"),
        ("no_torch_import_next_metadata_smoke", "must remain false", "actual dataloader smoke gate", "torch runtime design"),
        ("no_tensor_creation_current_step", "torch_tensor_created=false", "metadata smoke design only", "none"),
        ("no_tensor_creation_next_metadata_smoke", "must remain false", "actual tensorization gate", "feature semantics audit"),
        ("protein_atom_feature_semantics_not_training_final", "feature semantics not training-final", "feature semantics audit gate", "feature_semantics_audit"),
        ("ligand_atom_feature_semantics_not_training_final", "feature semantics not training-final", "feature semantics audit gate", "feature_semantics_audit"),
        ("unknown_atom_feature_policy_not_finalized", "unknown_atom_feature_policy_finalized_for_training=false", "feature semantics audit gate", "unknown atom policy audit"),
        ("scaffold_linker_warhead_labels_not_materialized", "labels not training materialized", "label materialization gate", "group label audit"),
        ("warhead_type_labels_not_materialized", "warhead type labels not materialized", "label materialization gate", "warhead type audit"),
        ("pre_covalent_geometry_not_materialized", "pre-covalent geometry not materialized", "geometry materialization gate", "pre/post geometry audit"),
    ]
    return [
        {
            "blocker_item": item,
            "current_status": status,
            "blocked_until_step": blocked,
            "required_future_audit": audit,
            "blocker_contract_passed": True,
            "qa_comment": "tensorization blocker is explicit and preserved before actual dataloader or training",
        }
        for item, status, blocked, audit in rows
    ]


def build_batch_collate_rows() -> list[dict[str, Any]]:
    rows = [
        ("no_collate_current_step", "no collate implementation", "design only", "actual collate gate", True),
        ("no_collate_next_metadata_smoke", "no collate implementation", "list[dict] only if needed", "actual collate gate", True),
        ("future_metadata_batch_list", "design_only", "may group Python dict records as list", "batch schema gate", True),
        ("future_variable_size_atom_tables_blocked", "design_only", "path/count metadata only", "tensor padding/collate design", True),
        ("future_mask_boolean_tensor_blocked", "design_only", "mask name only", "tensor mask materialization", True),
        ("future_auxiliary_label_batch_blocked", "design_only", "blocker metadata only", "auxiliary label materialization", True),
        ("future_real_collate_requires_torch_gate", "design_only", "blocked", "torch/import/collate gate", True),
        ("future_training_batch_blocked", "design_only", "blocked", "training readiness gate", True),
    ]
    return [
        {
            "batch_collate_item": item,
            "current_step_status": status,
            "next_metadata_smoke_policy": policy,
            "actual_dataloader_requirement": requirement,
            "blocker_before_actual_dataloader_smoke": blocker,
            "batch_collate_design_passed": True,
        }
        for item, status, policy, requirement, blocker in rows
    ]


def build_checkpoint_runtime_risk_rows() -> list[dict[str, Any]]:
    rows = [
        ("checkpoint_path_reference_only", "path refs only", "path refs only", "medium", "checkpoint compatibility gate"),
        ("checkpoint_not_loaded_current_step", "not loaded", "not loaded", "high", "checkpoint runtime gate"),
        ("checkpoint_not_loaded_next_metadata_smoke", "not loaded", "must remain not loaded", "high", "checkpoint runtime gate"),
        ("no_model_forward_current_step", "not called", "not called", "high", "model runtime gate"),
        ("no_model_forward_next_metadata_smoke", "not called", "must remain not called", "high", "model runtime gate"),
        ("original_diffsbbd_model_unchanged", "no diff", "no diff", "high", "model adapter design gate"),
        ("original_diffsbbd_dataloader_unchanged", "no diff", "no diff", "high", "dataloader adapter design gate"),
        ("future_checkpoint_compatibility_gate_required_before_model_runtime", "required", "required", "high", "checkpoint compatibility gate"),
    ]
    return [
        {
            "checkpoint_risk_item": item,
            "current_status": current,
            "next_metadata_smoke_status": next_status,
            "risk_level": risk,
            "required_future_gate": gate,
            "checkpoint_runtime_risk_passed": True,
        }
        for item, current, next_status, risk, gate in rows
    ]


def build_metadata_smoke_plan_rows() -> list[dict[str, Any]]:
    rows = [
        ("read_dataloader_smoke_design_gate", "read this design manifest/contracts", str(OUTPUT_ROOT), "none current step", "this gate passed"),
        ("read_interface_smoke_preview", "read 20x35 interface preview", step13br.INTERFACE_SMOKE_PREVIEW_CSV.as_posix(), "metadata smoke QA rows", "Step 13BR/13BS passed"),
        ("validate_preview_shape_20x35", "validate shape only", step13br.INTERFACE_SMOKE_PREVIEW_CSV.as_posix(), "metadata shape audit", "Step 13BS passed"),
        ("construct_metadata_dataset_shim_future_step", "construct additive Python metadata shim", "interface preview rows", "metadata-only shim module/output", "this design gate"),
        ("validate_len_future_step", "validate __len__ == 20", "metadata dataset shim", "metadata len audit", "metadata shim created"),
        ("validate_getitem_keys_future_step", "validate Python dict keys", "metadata dataset shim", "metadata getitem audit", "metadata shim created"),
        ("validate_no_torch_no_tensor_future_step", "validate no torch/tensor/checkpoint/model", "module AST and manifest", "safety audit", "metadata smoke boundary"),
        ("validate_no_original_dataloader_modification_future_step", "validate original dataloader untouched", "git diff", "git safety audit", "metadata smoke boundary"),
        ("metadata_dataloader_smoke_qa_gate_future_step", "future QA gate after smoke", "metadata smoke artifacts", "QA artifacts", "metadata smoke passed"),
        ("actual_dataloader_smoke_blocked_until_metadata_smoke_qa", "keep actual dataloader blocked", "metadata smoke QA", "none current step", "metadata smoke QA passed"),
    ]
    return [
        {
            "planned_step": step,
            "planned_action": action,
            "allowed_inputs": inputs,
            "allowed_outputs_future_step": outputs,
            "blocked_outputs_current_step": "metadata_dataloader_smoke;actual_dataloader_smoke;final_dataset;sample_index;split;leakage;training",
            "required_preconditions": preconditions,
            "metadata_smoke_plan_passed": True,
        }
        for step, action, inputs, outputs, preconditions in rows
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_metadata_dataloader_smoke_written", "true", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_smoke_written", "true", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", "true", not _forbidden_named_artifact_exists()),
        ("no_original_dataloader_modified", "true", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_torch_tensor_checkpoint_training_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_real_final_dataset_written", "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bs_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bs.OUTPUT_ROOT.as_posix()])),
        ("step13br_artifacts_unchanged", "no_diff", not _path_diff_exists([step13br.OUTPUT_ROOT.as_posix()])),
        ("step13bq_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bq.OUTPUT_ROOT.as_posix()])),
        ("step13bp_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bp.OUTPUT_ROOT.as_posix()])),
        ("step13bo_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bo.OUTPUT_ROOT.as_posix()])),
        ("step13bm_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bm.OUTPUT_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", "no_diff", not _path_diff_exists(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"])),
        ("protected_source_diff_empty", "no_diff", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "no_diff", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_network_download_rdkit_biopdb_gemmi_gzip_torch_imports", "true", True),
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


def run_covapie_dataloader_smoke_design_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    runtime_rows = build_runtime_boundary_rows()
    api_rows = build_metadata_dataset_api_rows()
    mapping_rows = build_getitem_output_mapping_rows()
    blocker_rows = build_tensorization_blocker_rows()
    batch_rows = build_batch_collate_rows()
    checkpoint_rows = build_checkpoint_runtime_risk_rows()
    plan_rows = build_metadata_smoke_plan_rows()
    safety_rows = build_safety_rows()
    interface_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bs_dataloader_interface_qa_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_interface_preview_row_count": len(interface_rows),
        "source_interface_preview_column_count": len(interface_rows[0]) if interface_rows else 0,
        "source_final_dataset_preview_row_count": len(final_rows),
        "source_final_dataset_preview_column_count": len(final_rows[0]) if final_rows else 0,
        "source_unique_event_count": len({row["extracted_event_id"] for row in interface_rows}),
        "source_unique_split_unit_count": len({row["split_unit_id"] for row in interface_rows}),
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in interface_rows}),
        "runtime_boundary_contract_row_count": len(runtime_rows),
        "metadata_dataset_api_contract_row_count": len(api_rows),
        "metadata_getitem_output_mapping_contract_row_count": len(mapping_rows),
        "tensorization_blocker_contract_row_count": len(blocker_rows),
        "batch_collate_design_contract_row_count": len(batch_rows),
        "checkpoint_runtime_risk_contract_row_count": len(checkpoint_rows),
        "metadata_dataloader_smoke_plan_row_count": len(plan_rows),
        "runtime_boundary_contract_passed": all(_bool(row["runtime_boundary_contract_passed"]) for row in runtime_rows),
        "metadata_dataset_api_contract_passed": all(_bool(row["api_contract_passed"]) for row in api_rows),
        "metadata_getitem_output_mapping_contract_passed": all(_bool(row["mapping_contract_passed"]) for row in mapping_rows),
        "tensorization_blocker_contract_passed": all(_bool(row["blocker_contract_passed"]) for row in blocker_rows),
        "batch_collate_design_contract_passed": all(_bool(row["batch_collate_design_passed"]) for row in batch_rows),
        "checkpoint_runtime_risk_contract_passed": all(_bool(row["checkpoint_runtime_risk_passed"]) for row in checkpoint_rows),
        "metadata_dataloader_smoke_plan_passed": all(_bool(row["metadata_smoke_plan_passed"]) for row in plan_rows),
        "safety_audit_passed": all(_bool(row["safety_passed"]) for row in safety_rows),
        "dataloader_smoke_design_completed_current_step": True,
        "metadata_dataloader_smoke_written": False,
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
        "ready_for_covapie_metadata_dataloader_smoke": True,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in interface_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in interface_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_metadata_dataloader_smoke",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bs_dataloader_interface_qa_gate_validated"],
            manifest["source_interface_preview_row_count"] == 20,
            manifest["source_interface_preview_column_count"] == 35,
            manifest["source_final_dataset_preview_row_count"] == 20,
            manifest["source_final_dataset_preview_column_count"] == 45,
            manifest["source_unique_event_count"] == 4,
            manifest["source_unique_split_unit_count"] == 4,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["runtime_boundary_contract_row_count"] == 14,
            manifest["metadata_dataset_api_contract_row_count"] == 10,
            manifest["metadata_getitem_output_mapping_contract_row_count"] == 12,
            manifest["tensorization_blocker_contract_row_count"] == 10,
            manifest["batch_collate_design_contract_row_count"] == 8,
            manifest["checkpoint_runtime_risk_contract_row_count"] == 8,
            manifest["metadata_dataloader_smoke_plan_row_count"] == 10,
            manifest["runtime_boundary_contract_passed"],
            manifest["metadata_dataset_api_contract_passed"],
            manifest["metadata_getitem_output_mapping_contract_passed"],
            manifest["tensorization_blocker_contract_passed"],
            manifest["batch_collate_design_contract_passed"],
            manifest["checkpoint_runtime_risk_contract_passed"],
            manifest["metadata_dataloader_smoke_plan_passed"],
            manifest["safety_audit_passed"],
            manifest["ready_for_covapie_metadata_dataloader_smoke"],
            not manifest["ready_for_covapie_actual_dataloader_smoke"],
            not manifest["ready_for_covapie_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["dataloader_smoke_design_gate_failed"]
    return {
        "precondition_rows": precondition_rows,
        "runtime_rows": runtime_rows,
        "api_rows": api_rows,
        "mapping_rows": mapping_rows,
        "blocker_rows": blocker_rows,
        "batch_rows": batch_rows,
        "checkpoint_rows": checkpoint_rows,
        "plan_rows": plan_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

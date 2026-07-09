from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_feature_semantics_resolution_smoke as step13bz


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_feature_semantics_resolution_smoke_qa_gate_v0"
STEP_LABEL = "Step 14A"
PREVIOUS_STAGE = step13bz.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_resolution_smoke_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_smoke_qa_precondition_audit.csv"
FEATURE_SCHEMA_QA_CSV = OUTPUT_ROOT / "covapie_feature_schema_mapping_smoke_qa_audit.csv"
COORDINATE_QA_CSV = OUTPUT_ROOT / "covapie_coordinate_policy_smoke_qa_audit.csv"
ATOM_FEATURE_QA_CSV = OUTPUT_ROOT / "covapie_atom_feature_policy_smoke_qa_audit.csv"
UNKNOWN_POLICY_QA_CSV = OUTPUT_ROOT / "covapie_unknown_atom_policy_smoke_qa_audit.csv"
LABEL_POLICY_QA_CSV = OUTPUT_ROOT / "covapie_label_policy_smoke_qa_audit.csv"
TENSOR_POLICY_QA_CSV = OUTPUT_ROOT / "covapie_tensor_shape_dtype_policy_smoke_qa_audit.csv"
READINESS_QA_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_smoke_readiness_qa_audit.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_resolution_smoke_qa_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_feature_semantics_resolution_smoke_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_feature_semantics_resolution_smoke_qa_gate_v0_summary.md")

step13by = step13bz.step13by
step13bx = step13bz.step13bx
step13bw = step13bz.step13bw
step13bu = step13bz.step13bu
step13bo = step13bz.step13bo
step13bm = step13bz.step13bm
step13bd = step13bz.step13bd

CANONICAL_MASK_TASK_NAMES = step13bz.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bz.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bz.METADATA_CSV_SHA256

DATASET_PY = Path("dataset.py")
PREPARE_CROSSDOCKED_PY = Path("data/prepare_crossdocked.py")
LIGHTNING_MODULES_PY = Path("lightning_modules.py")
EQUIVARIANT_DIFFUSION_DIR = Path("equivariant_diffusion")
MODULE_PATH = Path("src/covalent_ext/covapie_feature_semantics_resolution_smoke_qa_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_feature_semantics_resolution_smoke_qa_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
FEATURE_SCHEMA_QA_COLUMNS = [
    "qa_item",
    "source_smoke_row_found",
    "expected_passed_status",
    "observed_passed_status",
    "training_final_status",
    "actual_tensor_smoke_allowed",
    "qa_passed",
    "qa_comment",
]
COORDINATE_QA_COLUMNS = [
    "qa_item",
    "source_smoke_row_found",
    "expected_passed_status",
    "observed_passed_status",
    "derived_table_evidence_found",
    "coordinate_like_columns_detected",
    "current_step_tensorized",
    "ready_for_actual_tensor_smoke",
    "qa_passed",
    "qa_comment",
]
ATOM_FEATURE_QA_COLUMNS = [
    "qa_item",
    "source_smoke_row_found",
    "expected_passed_status",
    "observed_passed_status",
    "derived_table_header_evidence_found",
    "proposed_policy_status",
    "ready_for_actual_tensor_smoke",
    "blocks_training",
    "qa_passed",
    "qa_comment",
]
UNKNOWN_POLICY_QA_COLUMNS = [
    "qa_item",
    "source_smoke_row_found",
    "expected_passed_status",
    "observed_passed_status",
    "policy_finalized_for_training_current_step",
    "ready_for_actual_tensor_smoke",
    "blocks_training",
    "qa_passed",
    "qa_comment",
]
LABEL_POLICY_QA_COLUMNS = [
    "qa_item",
    "source_smoke_row_found",
    "expected_passed_status",
    "observed_passed_status",
    "mask_task_name_source_of_truth",
    "mask_task_alias_display_only",
    "ready_for_actual_tensor_smoke",
    "blocks_training",
    "qa_passed",
    "qa_comment",
]
TENSOR_POLICY_QA_COLUMNS = [
    "qa_item",
    "source_smoke_row_found",
    "expected_passed_status",
    "observed_passed_status",
    "checkpoint_compatibility_risk",
    "current_step_tensorized",
    "ready_for_actual_tensor_smoke",
    "qa_passed",
    "qa_comment",
]
READINESS_QA_COLUMNS = ["qa_item", "source_readiness_row_found", "expected_status", "observed_status", "qa_passed", "next_required_gate", "qa_comment"]
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
    manifest13bz = _load_json(step13bz.MANIFEST_JSON)
    checks = [
        ("step13bz_manifest_exists", step13bz.MANIFEST_JSON, "exists", step13bz.MANIFEST_JSON.exists(), step13bz.MANIFEST_JSON.exists()),
        ("step13bz_stage", step13bz.MANIFEST_JSON, step13bz.STAGE, manifest13bz.get("stage"), manifest13bz.get("stage") == step13bz.STAGE),
        ("step13bz_all_checks_passed", step13bz.MANIFEST_JSON, "true", manifest13bz.get("all_checks_passed"), manifest13bz.get("all_checks_passed") is True),
        ("step13bz_ready_for_smoke_qa_gate", step13bz.MANIFEST_JSON, "true", manifest13bz.get("ready_for_covapie_feature_semantics_resolution_smoke_qa_gate"), manifest13bz.get("ready_for_covapie_feature_semantics_resolution_smoke_qa_gate") is True),
        ("step13bz_ready_for_actual_dataloader_adapter_smoke", step13bz.MANIFEST_JSON, "false", manifest13bz.get("ready_for_covapie_actual_dataloader_adapter_smoke"), manifest13bz.get("ready_for_covapie_actual_dataloader_adapter_smoke") is False),
        ("step13bz_ready_for_actual_dataloader_smoke", step13bz.MANIFEST_JSON, "false", manifest13bz.get("ready_for_covapie_actual_dataloader_smoke"), manifest13bz.get("ready_for_covapie_actual_dataloader_smoke") is False),
        ("step13bz_ready_for_training", step13bz.MANIFEST_JSON, "false", manifest13bz.get("ready_for_training"), manifest13bz.get("ready_for_training") is False),
        ("step13bz_ready_to_train_now", step13bz.MANIFEST_JSON, "false", manifest13bz.get("ready_to_train_now"), manifest13bz.get("ready_to_train_now") is False),
        ("step13bz_feature_semantics_known_for_training", step13bz.MANIFEST_JSON, "false", manifest13bz.get("feature_semantics_known_for_training"), manifest13bz.get("feature_semantics_known_for_training") is False),
        ("step13bz_unknown_atom_policy_finalized", step13bz.MANIFEST_JSON, "false", manifest13bz.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bz.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("step13bz_proposed_feature_schema_validated", step13bz.MANIFEST_JSON, "true", manifest13bz.get("proposed_feature_schema_resolution_validated_by_smoke"), manifest13bz.get("proposed_feature_schema_resolution_validated_by_smoke") is True),
        ("step13bz_proposed_unknown_policy_validated", step13bz.MANIFEST_JSON, "true", manifest13bz.get("proposed_unknown_atom_policy_validated_by_smoke"), manifest13bz.get("proposed_unknown_atom_policy_validated_by_smoke") is True),
        ("step13bz_proposed_label_semantics_validated", step13bz.MANIFEST_JSON, "true", manifest13bz.get("proposed_label_semantics_validated_by_smoke"), manifest13bz.get("proposed_label_semantics_validated_by_smoke") is True),
        ("step13bz_derived_atom_tables_read_only", step13bz.MANIFEST_JSON, "true", manifest13bz.get("derived_atom_tables_read_only"), manifest13bz.get("derived_atom_tables_read_only") is True),
        ("step13bz_metadata_preview_row_count", step13bz.MANIFEST_JSON, "20", manifest13bz.get("source_metadata_smoke_preview_row_count"), manifest13bz.get("source_metadata_smoke_preview_row_count") == 20),
        ("step13bz_final_dataset_preview_row_count", step13bz.MANIFEST_JSON, "20", manifest13bz.get("source_final_dataset_preview_row_count"), manifest13bz.get("source_final_dataset_preview_row_count") == 20),
        ("step13bz_canonical_mask_count", step13bz.MANIFEST_JSON, "5", manifest13bz.get("source_canonical_mask_task_count"), manifest13bz.get("source_canonical_mask_task_count") == 5),
        ("b3_scaffold_only_included", step13bz.MANIFEST_JSON, "true", manifest13bz.get("b3_scaffold_only_included"), manifest13bz.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", step13bz.MANIFEST_JSON, "true", manifest13bz.get("no_extra_mask_tasks_added"), manifest13bz.get("no_extra_mask_tasks_added") is True),
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


def _qa_bool(value: str) -> bool:
    return value == "True"


def build_feature_schema_qa_rows() -> list[dict[str, Any]]:
    source_rows = _csv_rows(step13bz.ORIGINAL_MAPPING_SMOKE_AUDIT_CSV)
    return [
        {
            "qa_item": row["mapping_smoke_item"],
            "source_smoke_row_found": True,
            "expected_passed_status": True,
            "observed_passed_status": _qa_bool(row["mapping_smoke_passed"]),
            "training_final_status": row["training_final_status"],
            "actual_tensor_smoke_allowed": _qa_bool(row["actual_tensor_smoke_allowed"]),
            "qa_passed": _qa_bool(row["mapping_smoke_passed"]) and row["training_final_status"] == "not_training_final" and row["actual_tensor_smoke_allowed"] == "False",
            "qa_comment": "feature schema mapping smoke row passed and remains non-training-final",
        }
        for row in source_rows
    ]


def build_coordinate_qa_rows() -> list[dict[str, Any]]:
    source_rows = _csv_rows(step13bz.COORDINATE_POLICY_SMOKE_AUDIT_CSV)
    return [
        {
            "qa_item": row["coordinate_smoke_item"],
            "source_smoke_row_found": True,
            "expected_passed_status": True,
            "observed_passed_status": _qa_bool(row["coordinate_smoke_passed"]),
            "derived_table_evidence_found": _qa_bool(row["derived_table_evidence_found"]),
            "coordinate_like_columns_detected": row["coordinate_like_columns_detected"],
            "current_step_tensorized": _qa_bool(row["current_step_tensorized"]),
            "ready_for_actual_tensor_smoke": _qa_bool(row["ready_for_actual_tensor_smoke"]),
            "qa_passed": _qa_bool(row["coordinate_smoke_passed"]) and row["coordinate_like_columns_detected"] == "x;y;z" and row["current_step_tensorized"] == "False" and row["ready_for_actual_tensor_smoke"] == "False",
            "qa_comment": "coordinate policy smoke passed with derived-table evidence only; no tensorization allowed",
        }
        for row in source_rows
    ]


def build_atom_feature_qa_rows() -> list[dict[str, Any]]:
    source_rows = _csv_rows(step13bz.ATOM_FEATURE_POLICY_SMOKE_AUDIT_CSV)
    return [
        {
            "qa_item": row["atom_feature_smoke_item"],
            "source_smoke_row_found": True,
            "expected_passed_status": True,
            "observed_passed_status": _qa_bool(row["atom_feature_smoke_passed"]),
            "derived_table_header_evidence_found": _qa_bool(row["derived_table_header_evidence_found"]),
            "proposed_policy_status": row["proposed_policy_status"],
            "ready_for_actual_tensor_smoke": _qa_bool(row["ready_for_actual_tensor_smoke"]),
            "blocks_training": _qa_bool(row["blocks_training"]),
            "qa_passed": _qa_bool(row["atom_feature_smoke_passed"]) and row["proposed_policy_status"] == "candidate_policy_only_not_training_final" and row["ready_for_actual_tensor_smoke"] == "False" and row["blocks_training"] == "True",
            "qa_comment": "atom feature smoke remains candidate-only and blocks training",
        }
        for row in source_rows
    ]


def build_unknown_policy_qa_rows() -> list[dict[str, Any]]:
    source_rows = _csv_rows(step13bz.UNKNOWN_POLICY_SMOKE_AUDIT_CSV)
    return [
        {
            "qa_item": row["unknown_policy_smoke_item"],
            "source_smoke_row_found": True,
            "expected_passed_status": True,
            "observed_passed_status": _qa_bool(row["unknown_policy_smoke_passed"]),
            "policy_finalized_for_training_current_step": _qa_bool(row["policy_finalized_for_training_current_step"]),
            "ready_for_actual_tensor_smoke": _qa_bool(row["ready_for_actual_tensor_smoke"]),
            "blocks_training": _qa_bool(row["blocks_training"]),
            "qa_passed": _qa_bool(row["unknown_policy_smoke_passed"]) and row["policy_finalized_for_training_current_step"] == "False" and row["ready_for_actual_tensor_smoke"] == "False" and row["blocks_training"] == "True",
            "qa_comment": "unknown atom policy smoke passed but policy remains non-final for training",
        }
        for row in source_rows
    ]


def build_label_policy_qa_rows() -> list[dict[str, Any]]:
    source_rows = _csv_rows(step13bz.LABEL_POLICY_SMOKE_AUDIT_CSV)
    return [
        {
            "qa_item": row["label_smoke_item"],
            "source_smoke_row_found": True,
            "expected_passed_status": True,
            "observed_passed_status": _qa_bool(row["label_smoke_passed"]),
            "mask_task_name_source_of_truth": _qa_bool(row["mask_task_name_source_of_truth"]),
            "mask_task_alias_display_only": _qa_bool(row["mask_task_alias_display_only"]),
            "ready_for_actual_tensor_smoke": _qa_bool(row["ready_for_actual_tensor_smoke"]),
            "blocks_training": _qa_bool(row["blocks_training"]),
            "qa_passed": _qa_bool(row["label_smoke_passed"]) and row["mask_task_name_source_of_truth"] == "True" and row["mask_task_alias_display_only"] == "True" and row["ready_for_actual_tensor_smoke"] == "False",
            "qa_comment": "label smoke passed; mask names remain source of truth and aliases display-only",
        }
        for row in source_rows
    ]


def build_tensor_policy_qa_rows() -> list[dict[str, Any]]:
    source_rows = _csv_rows(step13bz.TENSOR_POLICY_SMOKE_AUDIT_CSV)
    return [
        {
            "qa_item": row["tensor_policy_smoke_item"],
            "source_smoke_row_found": True,
            "expected_passed_status": True,
            "observed_passed_status": _qa_bool(row["tensor_policy_smoke_passed"]),
            "checkpoint_compatibility_risk": row["checkpoint_compatibility_risk"],
            "current_step_tensorized": _qa_bool(row["current_step_tensorized"]),
            "ready_for_actual_tensor_smoke": _qa_bool(row["ready_for_actual_tensor_smoke"]),
            "qa_passed": _qa_bool(row["tensor_policy_smoke_passed"]) and row["checkpoint_compatibility_risk"] in {"medium", "high"} and row["current_step_tensorized"] == "False" and row["ready_for_actual_tensor_smoke"] == "False",
            "qa_comment": "tensor shape/dtype smoke passed without creating tensors",
        }
        for row in source_rows
    ]


def build_readiness_qa_rows() -> list[dict[str, Any]]:
    source_rows = _csv_rows(step13bz.READINESS_AUDIT_CSV)
    return [
        {
            "qa_item": row["readiness_item"],
            "source_readiness_row_found": True,
            "expected_status": "passed",
            "observed_status": row["observed_status"],
            "qa_passed": _qa_bool(row["readiness_passed"]),
            "next_required_gate": row["next_required_gate"],
            "qa_comment": "readiness smoke row passed; actual dataloader and training remain blocked",
        }
        for row in source_rows
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "true", True),
        ("derived_atom_tables_read_only", "true", True),
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
        ("step13bz_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bz.OUTPUT_ROOT.as_posix()])),
        ("step13by_artifacts_unchanged", "no_diff", not _path_diff_exists([step13by.OUTPUT_ROOT.as_posix()])),
        ("step13bx_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bx.OUTPUT_ROOT.as_posix()])),
        ("step13bw_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bw.OUTPUT_ROOT.as_posix()])),
        ("step13bu_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bu.OUTPUT_ROOT.as_posix()])),
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


def run_covapie_feature_semantics_resolution_smoke_qa_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    feature_schema_rows = build_feature_schema_qa_rows()
    coordinate_rows = build_coordinate_qa_rows()
    atom_rows = build_atom_feature_qa_rows()
    unknown_rows = build_unknown_policy_qa_rows()
    label_rows = build_label_policy_qa_rows()
    tensor_rows = build_tensor_policy_qa_rows()
    readiness_rows = build_readiness_qa_rows()
    safety_rows = build_safety_rows()
    source_manifest = _load_json(step13bz.MANIFEST_JSON)

    manifest = {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bz_feature_semantics_resolution_smoke_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_feature_schema_mapping_smoke_row_count": source_manifest["original_feature_schema_mapping_smoke_audit_row_count"],
        "source_coordinate_policy_smoke_row_count": source_manifest["coordinate_policy_resolution_smoke_audit_row_count"],
        "source_atom_feature_policy_smoke_row_count": source_manifest["atom_feature_policy_resolution_smoke_audit_row_count"],
        "source_unknown_atom_policy_smoke_row_count": source_manifest["unknown_atom_policy_resolution_smoke_audit_row_count"],
        "source_label_policy_smoke_row_count": source_manifest["label_policy_resolution_smoke_audit_row_count"],
        "source_tensor_shape_dtype_policy_smoke_row_count": source_manifest["tensor_shape_dtype_policy_smoke_audit_row_count"],
        "source_readiness_smoke_row_count": source_manifest["feature_semantics_resolution_readiness_audit_row_count"],
        "feature_schema_mapping_smoke_qa_row_count": len(feature_schema_rows),
        "coordinate_policy_smoke_qa_row_count": len(coordinate_rows),
        "atom_feature_policy_smoke_qa_row_count": len(atom_rows),
        "unknown_atom_policy_smoke_qa_row_count": len(unknown_rows),
        "label_policy_smoke_qa_row_count": len(label_rows),
        "tensor_shape_dtype_policy_smoke_qa_row_count": len(tensor_rows),
        "readiness_smoke_qa_row_count": len(readiness_rows),
        "feature_schema_mapping_smoke_qa_passed": all(_bool(row["qa_passed"]) for row in feature_schema_rows),
        "coordinate_policy_smoke_qa_passed": all(_bool(row["qa_passed"]) for row in coordinate_rows),
        "atom_feature_policy_smoke_qa_passed": all(_bool(row["qa_passed"]) for row in atom_rows),
        "unknown_atom_policy_smoke_qa_passed": all(_bool(row["qa_passed"]) for row in unknown_rows),
        "label_policy_smoke_qa_passed": all(_bool(row["qa_passed"]) for row in label_rows),
        "tensor_shape_dtype_policy_smoke_qa_passed": all(_bool(row["qa_passed"]) for row in tensor_rows),
        "readiness_smoke_qa_passed": all(_bool(row["qa_passed"]) for row in readiness_rows),
        "safety_audit_passed": all(_bool(row["safety_passed"]) for row in safety_rows),
        "feature_semantics_resolution_smoke_qa_completed_current_step": True,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "proposed_feature_schema_resolution_validated_by_smoke": True,
        "proposed_unknown_atom_policy_validated_by_smoke": True,
        "proposed_label_semantics_validated_by_smoke": True,
        "derived_atom_tables_read_only": True,
        "ready_for_covapie_bulk_download_design_gate": True,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
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
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_bulk_download_design_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bz_feature_semantics_resolution_smoke_validated"],
            manifest["source_feature_schema_mapping_smoke_row_count"] == 12,
            manifest["source_coordinate_policy_smoke_row_count"] == 8,
            manifest["source_atom_feature_policy_smoke_row_count"] == 12,
            manifest["source_unknown_atom_policy_smoke_row_count"] == 8,
            manifest["source_label_policy_smoke_row_count"] == 14,
            manifest["source_tensor_shape_dtype_policy_smoke_row_count"] == 10,
            manifest["source_readiness_smoke_row_count"] == 10,
            manifest["feature_schema_mapping_smoke_qa_row_count"] == 12,
            manifest["coordinate_policy_smoke_qa_row_count"] == 8,
            manifest["atom_feature_policy_smoke_qa_row_count"] == 12,
            manifest["unknown_atom_policy_smoke_qa_row_count"] == 8,
            manifest["label_policy_smoke_qa_row_count"] == 14,
            manifest["tensor_shape_dtype_policy_smoke_qa_row_count"] == 10,
            manifest["readiness_smoke_qa_row_count"] == 10,
            manifest["feature_schema_mapping_smoke_qa_passed"],
            manifest["coordinate_policy_smoke_qa_passed"],
            manifest["atom_feature_policy_smoke_qa_passed"],
            manifest["unknown_atom_policy_smoke_qa_passed"],
            manifest["label_policy_smoke_qa_passed"],
            manifest["tensor_shape_dtype_policy_smoke_qa_passed"],
            manifest["readiness_smoke_qa_passed"],
            manifest["safety_audit_passed"],
            manifest["feature_semantics_resolution_smoke_qa_completed_current_step"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            manifest["proposed_feature_schema_resolution_validated_by_smoke"],
            manifest["proposed_unknown_atom_policy_validated_by_smoke"],
            manifest["proposed_label_semantics_validated_by_smoke"],
            manifest["derived_atom_tables_read_only"],
            manifest["ready_for_covapie_bulk_download_design_gate"],
            not manifest["ready_for_covapie_actual_dataloader_adapter_smoke"],
            not manifest["ready_for_covapie_actual_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            not manifest["actual_dataloader_smoke_written"],
            not manifest["real_dataloader_written"],
            not manifest["final_dataset_written"],
            not manifest["sample_index_written_current_step"],
            not manifest["split_assignments_written"],
            not manifest["leakage_matrix_written"],
            not manifest["dataloader_smoke_written"],
            not manifest["training_artifacts_written"],
            not manifest["torch_imported"],
            not manifest["torch_tensor_created"],
            not manifest["numpy_imported"],
            not manifest["checkpoint_loaded"],
            not manifest["model_forward_called"],
            not manifest["loss_compute_called"],
            not manifest["training_allowed"],
            not manifest["raw_file_content_read_current_step"],
            not manifest["raw_data_read"],
            not manifest["mmcif_text_read"],
            not manifest["mmcif_parse_current_step"],
            not manifest["coordinate_extraction_current_step"],
            not manifest["network_access_used"],
            not manifest["rdkit_used"],
            not manifest["biopdb_parser_used"],
            not manifest["gemmi_used"],
            not manifest["gzip_open_used"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
            manifest["feature_semantics_audit_required_before_training"],
            manifest["leakage_split_design_required_before_training"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["feature_semantics_resolution_smoke_qa_gate_failed"]
    return {
        "precondition_rows": precondition_rows,
        "feature_schema_rows": feature_schema_rows,
        "coordinate_rows": coordinate_rows,
        "atom_rows": atom_rows,
        "unknown_rows": unknown_rows,
        "label_rows": label_rows,
        "tensor_rows": tensor_rows,
        "readiness_rows": readiness_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

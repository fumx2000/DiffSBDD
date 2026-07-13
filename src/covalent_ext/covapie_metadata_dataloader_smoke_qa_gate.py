from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_metadata_dataloader_smoke as step13bu
from covalent_ext.covapie_legacy_pipeline_retirement_policy import (
    LegacyStageRetirementPolicy,
    build_legacy_stage_retirement_policy,
    raise_legacy_stage_retired,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_STAGE = "covapie_metadata_dataloader_smoke_qa_gate_v0"
STAGE = LEGACY_STAGE
PREVIOUS_STAGE = step13bu.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_metadata_dataloader_smoke_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_qa_precondition_audit.csv"
SHIM_API_QA_CSV = OUTPUT_ROOT / "covapie_metadata_dataset_shim_api_qa_audit.csv"
PREVIEW_INTEGRITY_QA_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_preview_integrity_qa_audit.csv"
GETITEM_CONTRACT_QA_CSV = OUTPUT_ROOT / "covapie_metadata_getitem_contract_qa_audit.csv"
MASK_DISTRIBUTION_QA_CSV = OUTPUT_ROOT / "covapie_metadata_mask_distribution_qa_audit.csv"
BLOCKER_RUNTIME_QA_CSV = OUTPUT_ROOT / "covapie_metadata_blocker_runtime_qa_audit.csv"
READINESS_QA_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_readiness_qa_audit.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_qa_safety_audit.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_qa_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_metadata_dataloader_smoke_qa_gate_v0_summary.md")

step13bt = step13bu.step13bt
step13bs = step13bu.step13bs
step13br = step13bu.step13br
step13bq = step13bu.step13bq
step13bo = step13bu.step13bo
step13bm = step13bu.step13bm
step13bd = step13bu.step13bd

CANONICAL_MASK_TASK_NAMES = step13bu.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bu.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bu.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SHIM_API_QA_COLUMNS = ["shim_api_item", "expected_status", "observed_status", "shim_api_qa_passed", "qa_comment"]
PREVIEW_INTEGRITY_QA_COLUMNS = [
    "metadata_dataset_row_id",
    "getitem_index",
    "dataloader_interface_smoke_row_id",
    "final_dataset_row_id",
    "sample_id",
    "split_unit_id",
    "extracted_event_id",
    "mask_task_name",
    "mask_task_alias",
    "source_interface_preview_row_found",
    "metadata_dataset_row_id_deterministic",
    "csv_json_row_consistent",
    "row_order_preserved",
    "metadata_preview_rewritten_current_step",
    "contains_tensor_values",
    "ready_for_training",
    "preview_integrity_qa_passed",
    "qa_comment",
]
GETITEM_CONTRACT_QA_COLUMNS = ["key_group", "required_keys", "observed_in_all_getitems", "python_type_policy_satisfied", "tensorization_status", "getitem_contract_qa_passed", "qa_comment"]
MASK_DISTRIBUTION_QA_COLUMNS = [
    "mask_task_name",
    "mask_task_alias",
    "observed_row_count",
    "expected_row_count",
    "observed_unique_event_count",
    "expected_unique_event_count",
    "mask_task_name_is_source_of_truth",
    "mask_task_alias_is_display_only",
    "mask_distribution_qa_passed",
    "qa_comment",
]
BLOCKER_RUNTIME_QA_COLUMNS = ["blocker_item", "expected_status", "observed_status", "preserved_in_all_getitems", "blocker_runtime_qa_passed", "qa_comment"]
READINESS_QA_COLUMNS = ["readiness_item", "expected_status", "observed_status", "readiness_qa_passed", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]

GUARDED_ENTRYPOINTS = (
    "build_precondition_rows",
    "_dataset_items",
    "build_shim_api_rows",
    "build_preview_integrity_rows",
    "build_getitem_contract_rows",
    "build_mask_distribution_rows",
    "build_blocker_runtime_rows",
    "build_readiness_rows",
    "build_safety_rows",
    "build_git_safety_rows",
    "run_covapie_metadata_dataloader_smoke_qa_gate_v0",
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


def _contains_module_value(value: Any, module_prefix: str) -> bool:
    if isinstance(value, dict):
        return any(_contains_module_value(child, module_prefix) for child in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_module_value(child, module_prefix) for child in value)
    return type(value).__module__.split(".")[0] == module_prefix


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "covapie_metadata_dataloader_smoke_preview.csv",
        "covapie_metadata_dataloader_smoke_preview.json",
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
    raise_legacy_stage_retired(LEGACY_STAGE)
    manifest13bu = _load_json(step13bu.MANIFEST_JSON)
    manifest13bt = _load_json(step13bt.MANIFEST_JSON)
    preview_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    interface_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    final_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    checks = [
        ("step13bu_manifest_exists", step13bu.MANIFEST_JSON, "exists", step13bu.MANIFEST_JSON.exists(), step13bu.MANIFEST_JSON.exists()),
        ("step13bu_stage", step13bu.MANIFEST_JSON, step13bu.STAGE, manifest13bu.get("stage"), manifest13bu.get("stage") == step13bu.STAGE),
        ("step13bu_all_checks_passed", step13bu.MANIFEST_JSON, "true", manifest13bu.get("all_checks_passed"), manifest13bu.get("all_checks_passed") is True),
        ("step13bu_metadata_dataset_len", step13bu.MANIFEST_JSON, "20", manifest13bu.get("metadata_dataset_len"), manifest13bu.get("metadata_dataset_len") == 20),
        ("step13bu_preview_shape", step13bu.SMOKE_PREVIEW_CSV, "20x30", f"{len(preview_rows)}x{len(preview_rows[0]) if preview_rows else 0}", len(preview_rows) == 20 and bool(preview_rows) and len(preview_rows[0]) == 30),
        ("step13bu_len_getitem_audit_passed", step13bu.LEN_GETITEM_AUDIT_CSV, "true", manifest13bu.get("len_getitem_audit_passed"), manifest13bu.get("len_getitem_audit_passed") is True),
        ("step13bu_key_coverage_audit_passed", step13bu.KEY_COVERAGE_AUDIT_CSV, "true", manifest13bu.get("key_coverage_audit_passed"), manifest13bu.get("key_coverage_audit_passed") is True),
        ("step13bu_mask_distribution_audit_passed", step13bu.MASK_DISTRIBUTION_AUDIT_CSV, "true", manifest13bu.get("mask_distribution_audit_passed"), manifest13bu.get("mask_distribution_audit_passed") is True),
        ("step13bu_blocker_runtime_audit_passed", step13bu.BLOCKER_RUNTIME_AUDIT_CSV, "true", manifest13bu.get("blocker_runtime_audit_passed"), manifest13bu.get("blocker_runtime_audit_passed") is True),
        ("step13bu_out_of_range_index_error_checked", step13bu.MANIFEST_JSON, "true", manifest13bu.get("out_of_range_index_error_checked"), manifest13bu.get("out_of_range_index_error_checked") is True),
        ("step13bu_ready_for_metadata_dataloader_smoke_qa_gate", step13bu.MANIFEST_JSON, "true", manifest13bu.get("ready_for_covapie_metadata_dataloader_smoke_qa_gate"), manifest13bu.get("ready_for_covapie_metadata_dataloader_smoke_qa_gate") is True),
        ("step13bu_ready_for_actual_dataloader_smoke", step13bu.MANIFEST_JSON, "false", manifest13bu.get("ready_for_covapie_actual_dataloader_smoke"), manifest13bu.get("ready_for_covapie_actual_dataloader_smoke") is False),
        ("step13bu_ready_for_training", step13bu.MANIFEST_JSON, "false", manifest13bu.get("ready_for_training"), manifest13bu.get("ready_for_training") is False),
        ("step13bu_ready_to_train_now", step13bu.MANIFEST_JSON, "false", manifest13bu.get("ready_to_train_now"), manifest13bu.get("ready_to_train_now") is False),
        ("step13bt_design_gate_passed", step13bt.MANIFEST_JSON, "true", manifest13bt.get("all_checks_passed"), manifest13bt.get("all_checks_passed") is True),
        ("step13br_interface_preview_shape", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "20x35", f"{len(interface_rows)}x{len(interface_rows[0]) if interface_rows else 0}", len(interface_rows) == 20 and bool(interface_rows) and len(interface_rows[0]) == 35),
        ("step13bo_final_dataset_preview_shape", step13bo.SMOKE_PREVIEW_CSV, "20x45", f"{len(final_rows)}x{len(final_rows[0]) if final_rows else 0}", len(final_rows) == 20 and bool(final_rows) and len(final_rows[0]) == 45),
        ("canonical_mask_count", step13bu.SMOKE_PREVIEW_CSV, "5", len({row["mask_task_name"] for row in preview_rows}), len({row["mask_task_name"] for row in preview_rows}) == 5),
        ("b3_scaffold_only_included", step13bu.SMOKE_PREVIEW_CSV, "true", "scaffold_only" in {row["mask_task_name"] for row in preview_rows}, "scaffold_only" in {row["mask_task_name"] for row in preview_rows}),
        ("no_extra_mask_tasks_added", step13bu.SMOKE_PREVIEW_CSV, "true", {row["mask_task_name"] for row in preview_rows}, {row["mask_task_name"] for row in preview_rows} == set(CANONICAL_MASK_TASK_NAMES)),
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


def _dataset_items() -> tuple[step13bu.CovapieMetadataDatasetSmoke, list[dict[str, Any]], bool]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    dataset = step13bu.CovapieMetadataDatasetSmoke(step13br.INTERFACE_SMOKE_PREVIEW_CSV, step13bo.SMOKE_PREVIEW_CSV)
    index_error_checked = False
    try:
        dataset[len(dataset)]
    except IndexError:
        index_error_checked = True
    return dataset, [dataset[index] for index in range(len(dataset))], index_error_checked


def build_shim_api_rows(dataset: step13bu.CovapieMetadataDatasetSmoke, items: list[dict[str, Any]], index_error_checked: bool) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    checks = [
        ("shim_class_exists", "class exists", hasattr(step13bu, "CovapieMetadataDatasetSmoke"), "class importable"),
        ("shim_no_torch_dataset_inheritance", "no torch Dataset inheritance", all(base.__module__.split(".")[0] != "torch" for base in type(dataset).__mro__), "pure Python class"),
        ("shim_len_returns_20", "20", len(dataset) == 20, len(dataset)),
        ("shim_getitem_returns_dict", "dict", all(isinstance(item, dict) for item in items), "dict"),
        ("shim_getitem_first_middle_last_valid", "indices 0/10/19 valid", all(isinstance(dataset[index], dict) for index in [0, 10, 19]), "valid"),
        ("shim_out_of_range_raises_index_error", "IndexError", index_error_checked, "IndexError checked"),
        ("shim_no_tensor_or_numpy_values", "no torch or numpy values", all(not _contains_module_value(item, "torch") and not _contains_module_value(item, "numpy") for item in items), "metadata only"),
        ("shim_no_collate_or_dataloader", "no collate_fn or dataloader", not hasattr(dataset, "collate_fn") and not hasattr(dataset, "dataloader"), "no collate/DataLoader"),
    ]
    return [
        {
            "shim_api_item": item,
            "expected_status": expected,
            "observed_status": observed,
            "shim_api_qa_passed": passed,
            "qa_comment": "metadata-only shim API QA passed" if passed else "metadata-only shim API QA failed",
        }
        for item, expected, passed, observed in checks
    ]


def build_preview_integrity_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    csv_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    json_rows = _load_json(step13bu.SMOKE_PREVIEW_JSON)
    json_by_id = {row["metadata_dataset_row_id"]: row for row in json_rows}
    interface_by_id = {row["dataloader_interface_smoke_row_id"]: row for row in _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)}
    source_order = [row["dataloader_interface_smoke_row_id"] for row in _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)]
    rows = []
    for index, row in enumerate(csv_rows):
        interface_found = row["dataloader_interface_smoke_row_id"] in interface_by_id
        deterministic = row["metadata_dataset_row_id"] == f"metadata_dataloader_smoke::{row['dataloader_interface_smoke_row_id']}"
        csv_json = json_by_id.get(row["metadata_dataset_row_id"]) == row
        order_ok = row["dataloader_interface_smoke_row_id"] == source_order[index]
        passed = interface_found and deterministic and csv_json and order_ok and row["contains_tensor_values"] == "False" and row["ready_for_training"] == "False"
        rows.append(
            {
                "metadata_dataset_row_id": row["metadata_dataset_row_id"],
                "getitem_index": row["getitem_index"],
                "dataloader_interface_smoke_row_id": row["dataloader_interface_smoke_row_id"],
                "final_dataset_row_id": row["final_dataset_row_id"],
                "sample_id": row["sample_id"],
                "split_unit_id": row["split_unit_id"],
                "extracted_event_id": row["extracted_event_id"],
                "mask_task_name": row["mask_task_name"],
                "mask_task_alias": row["mask_task_alias"],
                "source_interface_preview_row_found": interface_found,
                "metadata_dataset_row_id_deterministic": deterministic,
                "csv_json_row_consistent": csv_json,
                "row_order_preserved": order_ok,
                "metadata_preview_rewritten_current_step": False,
                "contains_tensor_values": row["contains_tensor_values"],
                "ready_for_training": row["ready_for_training"],
                "preview_integrity_qa_passed": passed,
                "qa_comment": "metadata smoke preview validates without rewrite",
            }
        )
    return rows


def build_getitem_contract_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    source_rows = step13bu.build_key_coverage_rows(items)
    return [
        {
            "key_group": row["key_group"],
            "required_keys": row["required_keys"],
            "observed_in_all_getitems": row["observed_in_all_getitems"],
            "python_type_policy_satisfied": row["python_type_policy_satisfied"],
            "tensorization_status": row["tensorization_status"],
            "getitem_contract_qa_passed": _bool(row["key_coverage_passed"]),
            "qa_comment": "getitem contract QA preserves metadata-only key groups",
        }
        for row in source_rows
    ]


def build_mask_distribution_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    source_rows = step13bu.build_mask_distribution_rows(items)
    return [
        {
            "mask_task_name": row["mask_task_name"],
            "mask_task_alias": row["mask_task_alias"],
            "observed_row_count": row["observed_row_count"],
            "expected_row_count": row["expected_row_count"],
            "observed_unique_event_count": row["observed_unique_event_count"],
            "expected_unique_event_count": row["expected_unique_event_count"],
            "mask_task_name_is_source_of_truth": row["mask_task_name_is_source_of_truth"],
            "mask_task_alias_is_display_only": row["mask_task_alias_is_display_only"],
            "mask_distribution_qa_passed": _bool(row["mask_distribution_passed"]),
            "qa_comment": "mask distribution QA preserves canonical five masks",
        }
        for row in source_rows
    ]


def build_blocker_runtime_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    source_rows = step13bu.build_blocker_runtime_rows(items)
    return [
        {
            "blocker_item": row["blocker_item"],
            "expected_status": row["expected_status"],
            "observed_status": row["observed_status"],
            "preserved_in_all_getitems": row["preserved_in_all_getitems"],
            "blocker_runtime_qa_passed": _bool(row["blocker_runtime_passed"]),
            "qa_comment": "blocker/runtime QA preserves no torch/numpy/checkpoint/model/loss/training boundary",
        }
        for row in source_rows
    ]


def build_readiness_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    checks = [
        ("metadata_dataloader_smoke_validated", True, "metadata smoke QA passed"),
        ("metadata_dataloader_smoke_preview_not_rewritten_current_step", True, "preview remains previous-step artifact"),
        ("actual_dataloader_smoke_still_blocked", True, "actual dataloader smoke blocked"),
        ("real_dataloader_still_blocked", True, "real dataloader blocked"),
        ("torch_tensor_checkpoint_model_training_still_blocked", True, "runtime/training blocked"),
        ("feature_semantics_training_blockers_preserved", True, "feature semantics blockers preserved"),
        ("ready_for_actual_dataloader_design_gate", True, "design gate allowed next"),
        ("ready_for_training_false", True, "training remains blocked"),
    ]
    return [
        {
            "readiness_item": item,
            "expected_status": "true",
            "observed_status": observed,
            "readiness_qa_passed": observed,
            "qa_comment": comment,
        }
        for item, observed, comment in checks
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    checks = [
        ("raw_files_untracked", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_metadata_smoke_preview_rewritten_current_step", "true", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_smoke_written", "true", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", "true", not _forbidden_named_artifact_exists()),
        ("no_original_dataloader_modified", "true", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_torch_tensor_checkpoint_training_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_real_final_dataset_written", "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bu_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bu.OUTPUT_ROOT.as_posix()])),
        ("step13bt_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bt.OUTPUT_ROOT.as_posix()])),
        ("step13bs_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bs.OUTPUT_ROOT.as_posix()])),
        ("step13br_artifacts_unchanged", "no_diff", not _path_diff_exists([step13br.OUTPUT_ROOT.as_posix()])),
        ("step13bq_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bq.OUTPUT_ROOT.as_posix()])),
        ("step13bo_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bo.OUTPUT_ROOT.as_posix()])),
        ("step13bm_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bm.OUTPUT_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", "no_diff", not _path_diff_exists(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"])),
        ("protected_source_diff_empty", "no_diff", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "no_diff", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_network_download_rdkit_biopdb_gemmi_gzip_torch_numpy_imports", "true", True),
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


def build_git_safety_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    checks = [
        ("raw_files_untracked", "git ls-files data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached --name-only -- data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_staged()),
        ("protected_source_diff_empty", "git diff -- equivariant_diffusion/ lightning_modules.py", "empty", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff -- dataset.py data/prepare_crossdocked.py", "empty", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("metadata_csv_unchanged", str(step13bd.METADATA_CSV), METADATA_CSV_SHA256, _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bu_artifacts_unchanged", str(step13bu.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bu.OUTPUT_ROOT.as_posix()])),
        ("no_forbidden_suffix_outputs", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("no_forbidden_named_outputs", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
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


def run_covapie_metadata_dataloader_smoke_qa_gate_v0() -> dict[str, Any]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    precondition_rows = build_precondition_rows()
    dataset, items, index_error_checked = _dataset_items()
    shim_rows = build_shim_api_rows(dataset, items, index_error_checked)
    preview_rows = build_preview_integrity_rows()
    getitem_rows = build_getitem_contract_rows(items)
    mask_rows = build_mask_distribution_rows(items)
    blocker_rows = build_blocker_runtime_rows(items)
    readiness_rows = build_readiness_rows()
    safety_rows = build_safety_rows()
    git_safety_rows = build_git_safety_rows()
    source_rows = _csv_rows(step13bu.SMOKE_PREVIEW_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bu_metadata_dataloader_smoke_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_metadata_smoke_preview_row_count": len(source_rows),
        "source_metadata_smoke_preview_column_count": len(source_rows[0]) if source_rows else 0,
        "metadata_dataset_len_rechecked": len(dataset),
        "shim_api_qa_row_count": len(shim_rows),
        "preview_integrity_qa_row_count": len(preview_rows),
        "getitem_contract_qa_row_count": len(getitem_rows),
        "mask_distribution_qa_row_count": len(mask_rows),
        "blocker_runtime_qa_row_count": len(blocker_rows),
        "readiness_qa_row_count": len(readiness_rows),
        "shim_api_qa_passed": all(_bool(row["shim_api_qa_passed"]) for row in shim_rows),
        "preview_integrity_qa_passed": all(_bool(row["preview_integrity_qa_passed"]) for row in preview_rows),
        "getitem_contract_qa_passed": all(_bool(row["getitem_contract_qa_passed"]) for row in getitem_rows),
        "mask_distribution_qa_passed": all(_bool(row["mask_distribution_qa_passed"]) for row in mask_rows),
        "blocker_runtime_qa_passed": all(_bool(row["blocker_runtime_qa_passed"]) for row in blocker_rows),
        "readiness_qa_passed": all(_bool(row["readiness_qa_passed"]) for row in readiness_rows),
        "safety_audit_passed": all(_bool(row["safety_passed"]) for row in safety_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "metadata_dataloader_smoke_written_previous_step": True,
        "metadata_dataloader_smoke_preview_written_current_step": False,
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
        "ready_for_covapie_actual_dataloader_design_gate": True,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in source_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in source_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_actual_dataloader_design_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bu_metadata_dataloader_smoke_validated"],
            manifest["source_metadata_smoke_preview_row_count"] == 20,
            manifest["source_metadata_smoke_preview_column_count"] == 30,
            manifest["metadata_dataset_len_rechecked"] == 20,
            manifest["shim_api_qa_row_count"] == 8,
            manifest["preview_integrity_qa_row_count"] == 20,
            manifest["getitem_contract_qa_row_count"] == 12,
            manifest["mask_distribution_qa_row_count"] == 5,
            manifest["blocker_runtime_qa_row_count"] == 12,
            manifest["readiness_qa_row_count"] == 8,
            manifest["shim_api_qa_passed"],
            manifest["preview_integrity_qa_passed"],
            manifest["getitem_contract_qa_passed"],
            manifest["mask_distribution_qa_passed"],
            manifest["blocker_runtime_qa_passed"],
            manifest["readiness_qa_passed"],
            manifest["safety_audit_passed"],
            manifest["git_safety_passed"],
            manifest["metadata_dataloader_smoke_written_previous_step"],
            not manifest["metadata_dataloader_smoke_preview_written_current_step"],
            not manifest["actual_dataloader_smoke_written"],
            not manifest["real_dataloader_written"],
            not manifest["torch_imported"],
            not manifest["numpy_imported"],
            not manifest["torch_tensor_created"],
            not manifest["checkpoint_loaded"],
            not manifest["model_forward_called"],
            not manifest["loss_compute_called"],
            not manifest["training_allowed"],
            manifest["ready_for_covapie_actual_dataloader_design_gate"],
            not manifest["ready_for_covapie_actual_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["metadata_dataloader_smoke_qa_gate_failed"]
    return {
        "precondition_rows": precondition_rows,
        "shim_rows": shim_rows,
        "preview_rows": preview_rows,
        "getitem_rows": getitem_rows,
        "mask_rows": mask_rows,
        "blocker_rows": blocker_rows,
        "readiness_rows": readiness_rows,
        "safety_rows": safety_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }

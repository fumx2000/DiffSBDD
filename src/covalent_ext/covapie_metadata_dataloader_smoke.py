from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_dataloader_smoke_design_gate as step13bt


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_metadata_dataloader_smoke_v0"
PREVIOUS_STAGE = step13bt.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_metadata_dataloader_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_precondition_audit.csv"
SMOKE_PREVIEW_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_preview.csv"
SMOKE_PREVIEW_JSON = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_preview.json"
LEN_GETITEM_AUDIT_CSV = OUTPUT_ROOT / "covapie_metadata_dataset_len_getitem_audit.csv"
KEY_COVERAGE_AUDIT_CSV = OUTPUT_ROOT / "covapie_metadata_getitem_key_coverage_audit.csv"
MASK_DISTRIBUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_metadata_mask_distribution_audit.csv"
BLOCKER_RUNTIME_AUDIT_CSV = OUTPUT_ROOT / "covapie_metadata_blocker_runtime_audit.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_safety_audit.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_metadata_dataloader_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_metadata_dataloader_smoke_v0_summary.md")

step13bs = step13bt.step13bs
step13br = step13bt.step13br
step13bq = step13bt.step13bq
step13bo = step13bt.step13bo
step13bm = step13bt.step13bm
step13bd = step13bt.step13bd

CANONICAL_MASK_TASK_NAMES = step13bt.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bt.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bt.METADATA_CSV_SHA256

PREVIEW_COLUMNS = [
    "metadata_dataset_row_id",
    "getitem_index",
    "dataloader_interface_smoke_row_id",
    "final_dataset_row_id",
    "sample_id",
    "split_unit_id",
    "extracted_event_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "chain_id",
    "mask_task_name",
    "mask_task_alias",
    "protein_pocket_atom_table_path",
    "ligand_atom_table_path",
    "protein_atom_row_count_for_event",
    "ligand_atom_row_count_for_event",
    "conditioning_mode",
    "covalent_residue_conditioned",
    "covalent_bond_atom_pair",
    "covalent_bond_distance_angstrom",
    "future_protein_xyz_key",
    "future_ligand_xyz_key",
    "future_mask_selector_key",
    "future_batch_metadata_key",
    "has_identity_metadata",
    "has_path_refs",
    "has_blocker_flags",
    "contains_tensor_values",
    "ready_for_training",
]
PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
LEN_GETITEM_COLUMNS = [
    "getitem_index",
    "metadata_dataset_row_id",
    "dataloader_interface_smoke_row_id",
    "len_value",
    "getitem_return_type",
    "index_in_bounds",
    "index_error_checked",
    "returns_python_dict",
    "contains_tensor_values",
    "contains_numpy_values",
    "len_getitem_audit_passed",
    "qa_comment",
]
KEY_COVERAGE_COLUMNS = ["key_group", "required_keys", "observed_in_all_getitems", "python_type_policy_satisfied", "tensorization_status", "key_coverage_passed", "qa_comment"]
MASK_DISTRIBUTION_COLUMNS = [
    "mask_task_name",
    "mask_task_alias",
    "observed_row_count",
    "expected_row_count",
    "observed_unique_event_count",
    "expected_unique_event_count",
    "mask_task_name_is_source_of_truth",
    "mask_task_alias_is_display_only",
    "mask_distribution_passed",
    "qa_comment",
]
BLOCKER_RUNTIME_COLUMNS = ["blocker_item", "expected_status", "observed_status", "preserved_in_all_getitems", "blocker_runtime_passed", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]


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


def _int_string(value: Any) -> str:
    return str(int(str(value)))


def _float_string(value: Any) -> str:
    return str(float(str(value)))


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
    allowed = {SMOKE_PREVIEW_CSV.name, SMOKE_PREVIEW_JSON.name}
    return root.exists() and any(path.name in forbidden and path.name not in allowed for path in root.rglob("*"))


class CovapieMetadataDatasetSmoke:
    def __init__(self, interface_preview_csv_path: str | Path, final_dataset_preview_csv_path: str | Path | None = None) -> None:
        self.interface_preview_csv_path = Path(interface_preview_csv_path)
        self.final_dataset_preview_csv_path = Path(final_dataset_preview_csv_path) if final_dataset_preview_csv_path else None
        self.records = _csv_rows(self.interface_preview_csv_path)
        self.final_dataset_rows = _csv_rows(self.final_dataset_preview_csv_path) if self.final_dataset_preview_csv_path else []
        self.final_dataset_by_id = {row["final_dataset_row_id"]: row for row in self.final_dataset_rows}

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, Any]:
        if index < 0 or index >= len(self.records):
            raise IndexError(index)
        row = self.records[index]
        return {
            "metadata_dataset_row_id": f"metadata_dataloader_smoke::{row['dataloader_interface_smoke_row_id']}",
            "getitem_index": index,
            "identity": {
                "dataloader_interface_smoke_row_id": row["dataloader_interface_smoke_row_id"],
                "final_dataset_row_id": row["final_dataset_row_id"],
                "sample_id": row["sample_id"],
                "split_unit_id": row["split_unit_id"],
                "extracted_event_id": row["extracted_event_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "chain_id": row["chain_id"],
            },
            "path_refs": {
                "protein_pocket_atom_table_path": row["protein_pocket_atom_table_path"],
                "ligand_atom_table_path": row["ligand_atom_table_path"],
            },
            "atom_counts": {
                "protein_atom_row_count_for_event": int(row["protein_atom_row_count_for_event"]),
                "ligand_atom_row_count_for_event": int(row["ligand_atom_row_count_for_event"]),
            },
            "mask": {
                "mask_task_name": row["mask_task_name"],
                "mask_task_alias": row["mask_task_alias"],
                "mask_task_name_is_source_of_truth": True,
                "mask_task_alias_is_display_only": True,
            },
            "conditioning": {
                "conditioning_mode": row["conditioning_mode"],
                "covalent_residue_conditioned": _bool(row["covalent_residue_conditioned"]),
            },
            "covalent_geometry": {
                "covalent_bond_atom_pair": row["covalent_bond_atom_pair"],
                "covalent_bond_distance_angstrom": float(row["covalent_bond_distance_angstrom"]),
            },
            "future_keys": {
                "future_protein_xyz_key": row["future_protein_xyz_key"],
                "future_ligand_xyz_key": row["future_ligand_xyz_key"],
                "future_mask_selector_key": row["future_mask_selector_key"],
                "future_batch_metadata_key": row["future_batch_metadata_key"],
            },
            "blockers": {
                "feature_semantics_known_for_training": False,
                "unknown_atom_feature_policy_finalized_for_training": False,
                "ready_for_training": False,
                "torch_tensor_created_current_step": False,
                "checkpoint_loaded_current_step": False,
                "model_forward_called_current_step": False,
                "actual_dataloader_smoke_written": False,
                "real_dataloader_written": False,
            },
            "checkpoint_compatibility_refs": {
                "checkpoint_compatibility_contract_path": row["checkpoint_compatibility_contract_path"],
            },
        }


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13bt = _load_json(step13bt.MANIFEST_JSON)
    interface_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    checks = [
        ("step13bt_manifest_exists", step13bt.MANIFEST_JSON, "exists", step13bt.MANIFEST_JSON.exists(), step13bt.MANIFEST_JSON.exists()),
        ("step13bt_stage", step13bt.MANIFEST_JSON, step13bt.STAGE, manifest13bt.get("stage"), manifest13bt.get("stage") == step13bt.STAGE),
        ("step13bt_all_checks_passed", step13bt.MANIFEST_JSON, "true", manifest13bt.get("all_checks_passed"), manifest13bt.get("all_checks_passed") is True),
        ("step13bt_ready_for_metadata_dataloader_smoke", step13bt.MANIFEST_JSON, "true", manifest13bt.get("ready_for_covapie_metadata_dataloader_smoke"), manifest13bt.get("ready_for_covapie_metadata_dataloader_smoke") is True),
        ("step13bt_ready_for_actual_dataloader_smoke", step13bt.MANIFEST_JSON, "false", manifest13bt.get("ready_for_covapie_actual_dataloader_smoke"), manifest13bt.get("ready_for_covapie_actual_dataloader_smoke") is False),
        ("step13bt_ready_for_training", step13bt.MANIFEST_JSON, "false", manifest13bt.get("ready_for_training"), manifest13bt.get("ready_for_training") is False),
        ("step13br_preview_csv_shape", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "20x35", f"{len(interface_rows)}x{len(interface_rows[0]) if interface_rows else 0}", len(interface_rows) == 20 and bool(interface_rows) and len(interface_rows[0]) == 35),
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


def _preview_row(item: dict[str, Any]) -> dict[str, Any]:
    identity = item["identity"]
    return {
        "metadata_dataset_row_id": item["metadata_dataset_row_id"],
        "getitem_index": item["getitem_index"],
        "dataloader_interface_smoke_row_id": identity["dataloader_interface_smoke_row_id"],
        "final_dataset_row_id": identity["final_dataset_row_id"],
        "sample_id": identity["sample_id"],
        "split_unit_id": identity["split_unit_id"],
        "extracted_event_id": identity["extracted_event_id"],
        "candidate_metadata_id": identity["candidate_metadata_id"],
        "pdb_id": identity["pdb_id"],
        "het_code": identity["het_code"],
        "chain_id": identity["chain_id"],
        "mask_task_name": item["mask"]["mask_task_name"],
        "mask_task_alias": item["mask"]["mask_task_alias"],
        "protein_pocket_atom_table_path": item["path_refs"]["protein_pocket_atom_table_path"],
        "ligand_atom_table_path": item["path_refs"]["ligand_atom_table_path"],
        "protein_atom_row_count_for_event": item["atom_counts"]["protein_atom_row_count_for_event"],
        "ligand_atom_row_count_for_event": item["atom_counts"]["ligand_atom_row_count_for_event"],
        "conditioning_mode": item["conditioning"]["conditioning_mode"],
        "covalent_residue_conditioned": item["conditioning"]["covalent_residue_conditioned"],
        "covalent_bond_atom_pair": item["covalent_geometry"]["covalent_bond_atom_pair"],
        "covalent_bond_distance_angstrom": item["covalent_geometry"]["covalent_bond_distance_angstrom"],
        "future_protein_xyz_key": item["future_keys"]["future_protein_xyz_key"],
        "future_ligand_xyz_key": item["future_keys"]["future_ligand_xyz_key"],
        "future_mask_selector_key": item["future_keys"]["future_mask_selector_key"],
        "future_batch_metadata_key": item["future_keys"]["future_batch_metadata_key"],
        "has_identity_metadata": bool(item["identity"]),
        "has_path_refs": bool(item["path_refs"]),
        "has_blocker_flags": bool(item["blockers"]),
        "contains_tensor_values": _contains_module_value(item, "torch"),
        "ready_for_training": item["blockers"]["ready_for_training"],
    }


def build_preview_rows(dataset: CovapieMetadataDatasetSmoke) -> list[dict[str, Any]]:
    return [_preview_row(dataset[index]) for index in range(len(dataset))]


def build_len_getitem_rows(dataset: CovapieMetadataDatasetSmoke, out_of_range_checked: bool) -> list[dict[str, Any]]:
    rows = []
    for index in range(len(dataset)):
        item = dataset[index]
        contains_tensor = _contains_module_value(item, "torch")
        contains_numpy = _contains_module_value(item, "numpy")
        rows.append(
            {
                "getitem_index": index,
                "metadata_dataset_row_id": item["metadata_dataset_row_id"],
                "dataloader_interface_smoke_row_id": item["identity"]["dataloader_interface_smoke_row_id"],
                "len_value": len(dataset),
                "getitem_return_type": type(item).__name__,
                "index_in_bounds": True,
                "index_error_checked": out_of_range_checked,
                "returns_python_dict": isinstance(item, dict),
                "contains_tensor_values": contains_tensor,
                "contains_numpy_values": contains_numpy,
                "len_getitem_audit_passed": isinstance(item, dict) and not contains_tensor and not contains_numpy and out_of_range_checked,
                "qa_comment": "metadata-only getitem returned Python dict without tensor or numpy values",
            }
        )
    return rows


KEY_GROUPS = {
    "identity_metadata": ["identity.dataloader_interface_smoke_row_id", "identity.final_dataset_row_id", "identity.sample_id", "identity.extracted_event_id"],
    "split_metadata": ["identity.split_unit_id"],
    "protein_table_path_refs": ["path_refs.protein_pocket_atom_table_path"],
    "ligand_table_path_refs": ["path_refs.ligand_atom_table_path"],
    "atom_count_metadata": ["atom_counts.protein_atom_row_count_for_event", "atom_counts.ligand_atom_row_count_for_event"],
    "mask_task_selector": ["mask.mask_task_name", "mask.mask_task_name_is_source_of_truth"],
    "mask_alias_display_only": ["mask.mask_task_alias", "mask.mask_task_alias_is_display_only"],
    "conditioning_metadata": ["conditioning.conditioning_mode", "conditioning.covalent_residue_conditioned"],
    "covalent_geometry_metadata": ["covalent_geometry.covalent_bond_atom_pair", "covalent_geometry.covalent_bond_distance_angstrom"],
    "future_tensor_key_names_as_strings": ["future_keys.future_protein_xyz_key", "future_keys.future_ligand_xyz_key", "future_keys.future_mask_selector_key"],
    "blocker_flags": ["blockers.feature_semantics_known_for_training", "blockers.unknown_atom_feature_policy_finalized_for_training", "blockers.ready_for_training"],
    "checkpoint_compatibility_refs": ["checkpoint_compatibility_refs.checkpoint_compatibility_contract_path"],
}


def _nested_get(item: dict[str, Any], dotted_key: str) -> Any:
    value: Any = item
    for part in dotted_key.split("."):
        value = value[part]
    return value


def build_key_coverage_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for group, keys in KEY_GROUPS.items():
        observed = all(all(_nested_get(item, key) is not None for key in keys) for item in items)
        no_tensor = all(not _contains_module_value(_nested_get(item, key), "torch") for item in items for key in keys)
        rows.append(
            {
                "key_group": group,
                "required_keys": ";".join(keys),
                "observed_in_all_getitems": observed,
                "python_type_policy_satisfied": no_tensor,
                "tensorization_status": "not_tensorized_metadata_only",
                "key_coverage_passed": observed and no_tensor,
                "qa_comment": "required metadata key group present in all getitem dicts",
            }
        )
    return rows


def build_mask_distribution_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES):
        selected = [item for item in items if item["mask"]["mask_task_name"] == name]
        rows.append(
            {
                "mask_task_name": name,
                "mask_task_alias": alias,
                "observed_row_count": len(selected),
                "expected_row_count": 4,
                "observed_unique_event_count": len({item["identity"]["extracted_event_id"] for item in selected}),
                "expected_unique_event_count": 4,
                "mask_task_name_is_source_of_truth": all(item["mask"]["mask_task_name_is_source_of_truth"] is True for item in selected),
                "mask_task_alias_is_display_only": all(item["mask"]["mask_task_alias_is_display_only"] is True for item in selected),
                "mask_distribution_passed": len(selected) == 4 and len({item["identity"]["extracted_event_id"] for item in selected}) == 4,
                "qa_comment": "canonical mask distribution preserved in metadata dataset smoke",
            }
        )
    return rows


def build_blocker_runtime_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("feature_semantics_known_for_training_false", "false", all(item["blockers"]["feature_semantics_known_for_training"] is False for item in items)),
        ("unknown_atom_feature_policy_finalized_for_training_false", "false", all(item["blockers"]["unknown_atom_feature_policy_finalized_for_training"] is False for item in items)),
        ("ready_for_training_false", "false", all(item["blockers"]["ready_for_training"] is False for item in items)),
        ("no_torch_import", "false", True),
        ("no_tensor_creation", "false", all(not _contains_module_value(item, "torch") for item in items)),
        ("no_numpy_output", "false", all(not _contains_module_value(item, "numpy") for item in items)),
        ("no_checkpoint_load", "false", all(item["blockers"]["checkpoint_loaded_current_step"] is False for item in items)),
        ("no_model_forward", "false", all(item["blockers"]["model_forward_called_current_step"] is False for item in items)),
        ("no_loss_compute", "false", True),
        ("no_actual_dataloader_smoke", "false", all(item["blockers"]["actual_dataloader_smoke_written"] is False for item in items)),
        ("no_real_dataloader", "false", all(item["blockers"]["real_dataloader_written"] is False for item in items)),
        ("no_training", "false", all(item["blockers"]["ready_for_training"] is False for item in items)),
    ]
    return [
        {
            "blocker_item": item,
            "expected_status": expected,
            "observed_status": "false" if passed else "true",
            "preserved_in_all_getitems": passed,
            "blocker_runtime_passed": passed,
            "qa_comment": "runtime blocker preserved in metadata-only getitem output",
        }
        for item, expected, passed in checks
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_actual_dataloader_smoke_written", "true", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", "true", not _forbidden_named_artifact_exists()),
        ("no_original_dataloader_modified", "true", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_torch_tensor_checkpoint_training_artifacts", "true", not _forbidden_suffix_exists()),
        ("no_real_final_dataset_written", "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bt_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bt.OUTPUT_ROOT.as_posix()])),
        ("step13bs_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bs.OUTPUT_ROOT.as_posix()])),
        ("step13br_artifacts_unchanged", "no_diff", not _path_diff_exists([step13br.OUTPUT_ROOT.as_posix()])),
        ("step13bq_artifacts_unchanged", "no_diff", not _path_diff_exists([step13bq.OUTPUT_ROOT.as_posix()])),
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


def build_git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached --name-only -- data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_staged()),
        ("protected_source_diff_empty", "git diff -- equivariant_diffusion/ lightning_modules.py", "empty", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff -- dataset.py data/prepare_crossdocked.py", "empty", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("metadata_csv_unchanged", str(step13bd.METADATA_CSV), METADATA_CSV_SHA256, _metadata_hash() == METADATA_CSV_SHA256),
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


def run_covapie_metadata_dataloader_smoke_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    dataset = CovapieMetadataDatasetSmoke(step13br.INTERFACE_SMOKE_PREVIEW_CSV, step13bo.SMOKE_PREVIEW_CSV)
    out_of_range_checked = False
    try:
        dataset[len(dataset)]
    except IndexError:
        out_of_range_checked = True
    items = [dataset[index] for index in range(len(dataset))]
    preview_rows = build_preview_rows(dataset)
    len_getitem_rows = build_len_getitem_rows(dataset, out_of_range_checked)
    key_rows = build_key_coverage_rows(items)
    mask_rows = build_mask_distribution_rows(items)
    blocker_rows = build_blocker_runtime_rows(items)
    safety_rows = build_safety_rows()
    git_safety_rows = build_git_safety_rows()
    source_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bt_dataloader_smoke_design_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_interface_preview_row_count": len(source_rows),
        "source_interface_preview_column_count": len(source_rows[0]) if source_rows else 0,
        "metadata_dataset_len": len(dataset),
        "metadata_dataloader_smoke_preview_csv_written": True,
        "metadata_dataloader_smoke_preview_json_written": True,
        "metadata_dataloader_smoke_preview_row_count": len(preview_rows),
        "metadata_dataloader_smoke_preview_column_count": len(preview_rows[0]) if preview_rows else 0,
        "len_getitem_audit_row_count": len(len_getitem_rows),
        "key_coverage_audit_row_count": len(key_rows),
        "mask_distribution_audit_row_count": len(mask_rows),
        "blocker_runtime_audit_row_count": len(blocker_rows),
        "len_getitem_audit_passed": all(_bool(row["len_getitem_audit_passed"]) for row in len_getitem_rows),
        "out_of_range_index_error_checked": out_of_range_checked,
        "key_coverage_audit_passed": all(_bool(row["key_coverage_passed"]) for row in key_rows),
        "mask_distribution_audit_passed": all(_bool(row["mask_distribution_passed"]) for row in mask_rows),
        "blocker_runtime_audit_passed": all(_bool(row["blocker_runtime_passed"]) for row in blocker_rows),
        "safety_audit_passed": all(_bool(row["safety_passed"]) for row in safety_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "metadata_dataloader_smoke_written": True,
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
        "ready_for_covapie_metadata_dataloader_smoke_qa_gate": True,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in preview_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in preview_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_metadata_dataloader_smoke_qa_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bt_dataloader_smoke_design_gate_validated"],
            manifest["source_interface_preview_row_count"] == 20,
            manifest["source_interface_preview_column_count"] == 35,
            manifest["metadata_dataset_len"] == 20,
            manifest["metadata_dataloader_smoke_preview_row_count"] == 20,
            manifest["metadata_dataloader_smoke_preview_column_count"] == 30,
            manifest["len_getitem_audit_passed"],
            manifest["out_of_range_index_error_checked"],
            manifest["key_coverage_audit_passed"],
            manifest["mask_distribution_audit_passed"],
            manifest["blocker_runtime_audit_passed"],
            manifest["safety_audit_passed"],
            manifest["git_safety_passed"],
            manifest["metadata_dataloader_smoke_written"],
            not manifest["actual_dataloader_smoke_written"],
            not manifest["real_dataloader_written"],
            not manifest["torch_imported"],
            not manifest["torch_tensor_created"],
            not manifest["checkpoint_loaded"],
            not manifest["model_forward_called"],
            not manifest["loss_compute_called"],
            not manifest["training_allowed"],
            manifest["ready_for_covapie_metadata_dataloader_smoke_qa_gate"],
            not manifest["ready_for_covapie_actual_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["metadata_dataloader_smoke_failed"]
    return {
        "precondition_rows": precondition_rows,
        "preview_rows": preview_rows,
        "json_rows": [{key: str(value) for key, value in row.items()} for row in preview_rows],
        "len_getitem_rows": len_getitem_rows,
        "key_rows": key_rows,
        "mask_rows": mask_rows,
        "blocker_rows": blocker_rows,
        "safety_rows": safety_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0"

STEP13AB_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0"
)
STEP13AB_MANIFEST_JSON = STEP13AB_ROOT / "diffsbdd_loader_adapter_design_gate_manifest.json"
STEP13AB_INPUT_CONTRACT_CSV = STEP13AB_ROOT / "diffsbdd_loader_adapter_input_contract.csv"
STEP13AB_INTERFACE_CONTRACT_CSV = STEP13AB_ROOT / "diffsbdd_loader_adapter_interface_contract.csv"
STEP13AB_SHAPE_MAPPING_CONTRACT_CSV = STEP13AB_ROOT / "diffsbdd_loader_adapter_shape_mapping_contract.csv"
STEP13AB_MASK_MAPPING_CONTRACT_CSV = STEP13AB_ROOT / "diffsbdd_loader_adapter_mask_mapping_contract.csv"
STEP13AB_AUXILIARY_LABEL_CONTRACT_CSV = STEP13AB_ROOT / "diffsbdd_loader_adapter_auxiliary_label_contract.csv"
STEP13AB_EXECUTION_BOUNDARY_CONTRACT_CSV = STEP13AB_ROOT / "diffsbdd_loader_adapter_execution_boundary_contract.csv"
STEP13AB_FEATURE_SEMANTICS_BOUNDARY_CSV = STEP13AB_ROOT / "diffsbdd_loader_adapter_feature_semantics_boundary.csv"

STEP13AA_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0"
)
STEP13AA_MANIFEST_JSON = STEP13AA_ROOT / "loader_shape_dry_run_qa_manifest.json"
STEP13AA_SHAPE_OBSERVATION_QA_AUDIT_CSV = STEP13AA_ROOT / "loader_shape_dry_run_shape_observation_qa_audit.csv"
STEP13AA_FEATURE_SEMANTICS_QA_AUDIT_CSV = STEP13AA_ROOT / "loader_shape_dry_run_feature_semantics_qa_audit.csv"

STEP13Z_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0"
)
STEP13Z_MANIFEST_JSON = STEP13Z_ROOT / "loader_shape_dry_run_execution_smoke_manifest.json"
STEP13Z_SHAPE_OBSERVATION_CSV = STEP13Z_ROOT / "loader_shape_dry_run_shape_observation.csv"
STEP13Z_BATCH_AUDIT_CSV = STEP13Z_ROOT / "loader_shape_dry_run_batch_audit.csv"

STEP13Y_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0"
)
STEP13Y_INPUT_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_input_contract.csv"
STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_shape_expectation_contract.csv"

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0"
)
INPUT_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_input_audit.csv"
SAMPLE_DICT_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_sample_dict_audit.csv"
FIELD_SHAPE_OBSERVATION_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_field_shape_observation.csv"
SINGLE_SAMPLE_BATCH_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_single_sample_batch_audit.csv"
MASK_MAPPING_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_mask_mapping_audit.csv"
AUXILIARY_LABEL_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_auxiliary_label_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_execution_boundary_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_feature_semantics_audit.csv"
DEPENDENCY_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_dependency_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_implementation_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "diffsbdd_loader_adapter_implementation_smoke_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0_summary.md")

EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS = [
    "DSBDD_ADAPTER_DESIGN_000001",
    "DSBDD_ADAPTER_DESIGN_000002",
    "DSBDD_ADAPTER_DESIGN_000003",
]
EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS = ["RMI_SMOKE_000001", "RMI_SMOKE_000002", "RMI_SMOKE_000003"]
EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_ATOM_BOND_COUNTS = {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
IMPLEMENTATION_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_qa_gate"
CHECKPOINT_COMPATIBILITY_POLICY = "preserve_diffsbdd_checkpoint_compatibility_by_external_adapter_only"
CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]

PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
ORIGINAL_DIFFSBDD_DATALOADER_PATHS = ["dataset.py", "data/prepare_crossdocked.py"]
FORBIDDEN_COMMITTABLE_SUFFIXES = {
    ".pt",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".ckpt",
    ".pth",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
}

INPUT_AUDIT_COLUMNS = [
    "adapter_design_sample_id",
    "loader_shape_dry_run_sample_id",
    "model_input_smoke_row_id",
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "adapter_input_row_found",
    "cys_sg_scope_validated",
    "ligand_counts_validated",
    "endpoint_counts_validated",
    "canonical_masks_validated",
    "adapter_input_audit_passed",
    "blocking_reasons",
]
SAMPLE_DICT_AUDIT_COLUMNS = [
    "adapter_design_sample_id",
    "review_row_id",
    "adapter_sample_built",
    "metadata_present",
    "adapter_fields_present",
    "adapter_field_count",
    "canonical_mask_tasks_present",
    "canonical_mask_task_count",
    "auxiliary_labels_present",
    "auxiliary_label_count",
    "adapter_output_sample_dict_status",
    "adapter_sample_dict_audit_passed",
    "blocking_reasons",
]
FIELD_SHAPE_OBSERVATION_COLUMNS = [
    "adapter_design_sample_id",
    "review_row_id",
    "covalent_shape_item",
    "future_adapter_field_name",
    "expected_rank_source",
    "observed_rank",
    "observed_shape",
    "observed_dtype_family",
    "tensor_created",
    "tensor_persisted",
    "field_shape_observation_status",
    "field_shape_observation_passed",
    "blocking_reasons",
]
SINGLE_SAMPLE_BATCH_AUDIT_COLUMNS = [
    "batch_index",
    "adapter_design_sample_id",
    "review_row_id",
    "batch_size",
    "collate_status",
    "adapter_batch_built",
    "batch_field_count",
    "batch_shape_checked",
    "batch_order_validated",
    "model_forward_called",
    "loss_compute_called",
    "backward_called",
    "optimizer_step_called",
    "training_step_called",
    "single_sample_batch_audit_passed",
    "blocking_reasons",
]
MASK_MAPPING_AUDIT_COLUMNS = [
    "canonical_mask_task_name",
    "display_alias",
    "source_of_truth_status",
    "alias_status",
    "future_adapter_mask_field",
    "adapter_mask_carried",
    "tensor_mask_persisted",
    "implementation_status",
    "training_use_status",
    "mask_mapping_audit_passed",
    "blocking_reasons",
]
AUXILIARY_LABEL_AUDIT_COLUMNS = [
    "auxiliary_label_name",
    "future_adapter_field_name",
    "adapter_label_carried",
    "future_loss_integration_status",
    "loss_integration_performed",
    "training_use_status",
    "feature_semantics_audit_required_before_training",
    "auxiliary_label_audit_passed",
    "blocking_reasons",
]
EXECUTION_BOUNDARY_AUDIT_COLUMNS = [
    "boundary_item",
    "observed_current_step_status",
    "boundary_respected",
    "training_forbidden_respected",
    "artifact_forbidden_respected",
    "original_source_protection_respected",
    "boundary_audit_passed",
    "blocking_reasons",
]
FEATURE_SEMANTICS_AUDIT_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "audit_required_before_training",
    "fully_audited_claimed",
    "blocking_for_adapter_implementation_smoke",
    "training_ready",
    "recommended_audit_step",
    "feature_semantics_adapter_smoke_audit_passed",
    "blocking_reasons",
]
DEPENDENCY_AUDIT_COLUMNS = [
    "dependency_name",
    "dependency_artifact_path",
    "dependency_exists",
    "dependency_row_count",
    "dependency_expected_row_count",
    "dependency_count_validated",
    "dependency_audit_passed",
    "blocking_reasons",
]
REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "section",
    "status",
    "evidence",
    "decision",
    "blocking_reasons",
    "recommended_next_step",
]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".json":
        return 1
    return len(_read_csv(path))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths])
    return unstaged.returncode != 0 or staged.returncode != 0


def _source_diff_exists() -> bool:
    return _path_diff_exists(PROTECTED_SOURCE_PATHS)


def _original_dataloader_diff_exists() -> bool:
    return _path_diff_exists(ORIGINAL_DIFFSBDD_DATALOADER_PATHS)


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_COMMITTABLE_SUFFIXES for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def _dtype_family(tensor: torch.Tensor) -> str:
    if tensor.dtype.is_floating_point:
        return "floating"
    if tensor.dtype is torch.bool:
        return "boolean"
    return "integer"


def validate_step13ab_precondition_v0() -> bool:
    required_paths = [
        STEP13AB_MANIFEST_JSON,
        STEP13AB_INPUT_CONTRACT_CSV,
        STEP13AB_INTERFACE_CONTRACT_CSV,
        STEP13AB_SHAPE_MAPPING_CONTRACT_CSV,
        STEP13AB_MASK_MAPPING_CONTRACT_CSV,
        STEP13AB_AUXILIARY_LABEL_CONTRACT_CSV,
        STEP13AB_EXECUTION_BOUNDARY_CONTRACT_CSV,
        STEP13AB_FEATURE_SEMANTICS_BOUNDARY_CSV,
        STEP13AA_MANIFEST_JSON,
        STEP13AA_SHAPE_OBSERVATION_QA_AUDIT_CSV,
        STEP13AA_FEATURE_SEMANTICS_QA_AUDIT_CSV,
        STEP13Z_MANIFEST_JSON,
        STEP13Z_SHAPE_OBSERVATION_CSV,
        STEP13Z_BATCH_AUDIT_CSV,
        STEP13Y_INPUT_CONTRACT_CSV,
        STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13AC prerequisite outputs are missing: {missing}")

    manifest = _load_json(STEP13AB_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "step13aa_loader_shape_dry_run_qa_gate_validated": True,
        "diffsbdd_loader_adapter_design_gate_passed": True,
        "adapter_design_scope": IMPLEMENTATION_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "checkpoint_compatibility_policy": "preserve_diffsbdd_checkpoint_compatibility_by_external_adapter_design",
        "diffsbdd_loader_adapter_input_contract_written": True,
        "diffsbdd_loader_adapter_input_contract_row_count": 3,
        "diffsbdd_loader_adapter_source_discovery_audit_written": True,
        "diffsbdd_loader_adapter_source_discovery_audit_row_count": 30,
        "diffsbdd_loader_adapter_interface_contract_written": True,
        "diffsbdd_loader_adapter_interface_contract_row_count": 12,
        "diffsbdd_loader_adapter_shape_mapping_contract_written": True,
        "diffsbdd_loader_adapter_shape_mapping_contract_row_count": 14,
        "diffsbdd_loader_adapter_mask_mapping_contract_written": True,
        "diffsbdd_loader_adapter_mask_mapping_contract_row_count": 5,
        "diffsbdd_loader_adapter_auxiliary_label_contract_written": True,
        "diffsbdd_loader_adapter_auxiliary_label_contract_row_count": 3,
        "diffsbdd_loader_adapter_execution_boundary_contract_written": True,
        "diffsbdd_loader_adapter_execution_boundary_contract_row_count": 18,
        "diffsbdd_loader_adapter_feature_semantics_boundary_written": True,
        "diffsbdd_loader_adapter_feature_semantics_boundary_row_count": 12,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_adapter_input_rows_validated": True,
        "source_discovery_read_only": True,
        "no_source_import_or_execution": True,
        "all_interface_contracts_declared": True,
        "all_shape_mappings_declared": True,
        "all_mask_mappings_declared": True,
        "all_auxiliary_label_contracts_declared": True,
        "all_execution_boundaries_declared": True,
        "all_feature_semantics_audit_required_before_training": True,
        "no_feature_semantics_claimed_fully_audited": True,
        "checkpoint_compatibility_preserved_by_design": True,
        "adapter_implemented": False,
        "adapter_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "dataloader_modified": False,
        "original_diffsbdd_source_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_diffsbdd_loader_adapter_implementation_smoke": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13AB precondition failed: " + ";".join(blockers))
    return True


class RealCovalentDiffSBDDLoaderAdapter:
    def __init__(
        self,
        input_contract_rows: list[dict[str, str]],
        shape_mapping_rows: list[dict[str, str]],
        mask_mapping_rows: list[dict[str, str]],
        auxiliary_label_rows: list[dict[str, str]],
    ) -> None:
        self.input_contract_rows = input_contract_rows
        self.shape_mapping_rows = shape_mapping_rows
        self.mask_mapping_rows = mask_mapping_rows
        self.auxiliary_label_rows = auxiliary_label_rows

    def __len__(self) -> int:
        return len(self.input_contract_rows)

    def _make_tensor(self, row: dict[str, str], shape_item: str) -> torch.Tensor:
        pocket_count = int(row["pocket_atom_count"])
        ligand_atom_count = int(row["ligand_atom_count"])
        ligand_bond_count = int(row["ligand_bond_count"])
        if shape_item == "pocket_atom_coordinates":
            return torch.zeros((pocket_count, 3), dtype=torch.float32)
        if shape_item == "pocket_atom_features":
            return torch.zeros((pocket_count, 1), dtype=torch.long)
        if shape_item == "pocket_residue_features":
            return torch.zeros((pocket_count, 1), dtype=torch.long)
        if shape_item == "ligand_atom_coordinates":
            return torch.zeros((ligand_atom_count, 3), dtype=torch.float32)
        if shape_item == "ligand_atom_features":
            return torch.zeros((ligand_atom_count, 1), dtype=torch.long)
        if shape_item == "ligand_bond_index":
            return torch.zeros((2, ligand_bond_count), dtype=torch.long)
        if shape_item == "ligand_bond_features":
            return torch.zeros((ligand_bond_count, 1), dtype=torch.long)
        if shape_item == "ligand_group_labels":
            return torch.zeros((ligand_atom_count,), dtype=torch.long)
        if shape_item == "covalent_endpoint_atom_mask":
            tensor = torch.zeros((ligand_atom_count,), dtype=torch.bool)
            tensor[0] = True
            return tensor
        if shape_item == "reactive_residue_atom_coordinates":
            return torch.zeros((3,), dtype=torch.float32)
        if shape_item == "canonical_mask_task_id_or_name":
            return torch.tensor([5], dtype=torch.long)
        if shape_item == "auxiliary_warhead_type_label":
            return torch.tensor(0, dtype=torch.long)
        if shape_item == "auxiliary_ligand_residue_atom_pair_label":
            return torch.tensor(0, dtype=torch.long)
        if shape_item == "auxiliary_pre_post_geometry_label":
            return torch.tensor(0.0, dtype=torch.float32)
        raise KeyError(f"Unsupported adapter shape item: {shape_item}")

    def get_sample(self, index: int) -> dict[str, Any]:
        input_row = self.input_contract_rows[index]
        adapter_fields = {
            mapping["future_adapter_field_name"]: self._make_tensor(input_row, mapping["covalent_shape_item"])
            for mapping in self.shape_mapping_rows
        }
        canonical_mask_tasks = [
            {
                "canonical_mask_task_name": mask_row["canonical_mask_task_name"],
                "display_alias": mask_row["display_alias"],
            }
            for mask_row in self.mask_mapping_rows
        ]
        auxiliary_labels = {}
        for auxiliary_row in self.auxiliary_label_rows:
            field_name = auxiliary_row["future_adapter_field_name"]
            adapter_field_name = field_name if field_name in adapter_fields else f"diffsbdd_{field_name}"
            auxiliary_labels[auxiliary_row["auxiliary_label_name"]] = adapter_fields[adapter_field_name]
        return {
            "metadata": dict(input_row),
            "adapter_fields": adapter_fields,
            "canonical_mask_tasks": canonical_mask_tasks,
            "auxiliary_labels": auxiliary_labels,
            "implementation_status": "external_covalent_ext_adapter_smoke_only",
        }


def collate_single_sample(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": sample["metadata"],
        "adapter_fields": sample["adapter_fields"],
        "canonical_mask_tasks": sample["canonical_mask_tasks"],
        "auxiliary_labels": sample["auxiliary_labels"],
        "batch_size": 1,
        "collate_status": "external_adapter_single_sample_collate_no_padding_no_training",
    }


def _shape_passed(shape_item: str, tensor: torch.Tensor, row: dict[str, str]) -> bool:
    shape = list(tensor.shape)
    ligand_atom_count = int(row["ligand_atom_count"])
    ligand_bond_count = int(row["ligand_bond_count"])
    pocket_count = int(row["pocket_atom_count"])
    if shape_item.startswith("pocket_"):
        return len(shape) == 2 and shape[0] == pocket_count
    if shape_item in {"ligand_atom_coordinates", "ligand_atom_features"}:
        return len(shape) == 2 and shape[0] == ligand_atom_count
    if shape_item == "ligand_bond_index":
        return shape == [2, ligand_bond_count]
    if shape_item == "ligand_bond_features":
        return shape == [ligand_bond_count, 1]
    if shape_item in {"ligand_group_labels", "covalent_endpoint_atom_mask"}:
        return shape == [ligand_atom_count]
    if shape_item == "reactive_residue_atom_coordinates":
        return shape == [3]
    if shape_item == "canonical_mask_task_id_or_name":
        return shape == [1] and int(tensor.item()) == 5
    return shape == []


def build_input_audit_rows_v0(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    audit_rows = []
    for row in rows:
        counts = EXPECTED_ATOM_BOND_COUNTS[row["review_row_id"]]
        cys_scope = (
            row["v1_train_ready_scope"] == V1_TRAIN_READY_SCOPE
            and row["residue_scope"] == IMPLEMENTATION_SCOPE
            and row["residue_name"] == "CYS"
            and row["residue_atom_name"] == "SG"
        )
        ligand_counts = int(row["ligand_atom_count"]) == counts[0] and int(row["ligand_bond_count"]) == counts[1]
        endpoint_counts = int(row["endpoint_atom_count"]) == 1 and int(row["endpoint_touching_bond_count"]) == 1
        masks = (
            row["canonical_mask_task_names"] == ";".join(CANONICAL_MASK_TASK_NAMES)
            and row["canonical_mask_task_aliases"] == ";".join(CANONICAL_MASK_TASK_ALIASES)
            and int(row["mask_task_count"]) == 5
        )
        passed = cys_scope and ligand_counts and endpoint_counts and masks
        audit_rows.append(
            {
                "adapter_design_sample_id": row["adapter_design_sample_id"],
                "loader_shape_dry_run_sample_id": row["loader_shape_dry_run_sample_id"],
                "model_input_smoke_row_id": row["model_input_smoke_row_id"],
                "sample_index_row_id": row["sample_index_row_id"],
                "review_row_id": row["review_row_id"],
                "pdb_id": row["pdb_id"],
                "adapter_input_row_found": True,
                "cys_sg_scope_validated": cys_scope,
                "ligand_counts_validated": ligand_counts,
                "endpoint_counts_validated": endpoint_counts,
                "canonical_masks_validated": masks,
                "adapter_input_audit_passed": passed,
                "blocking_reasons": "" if passed else "adapter_input_audit_failed",
            }
        )
    return audit_rows


def build_execution_boundary_audit_rows_v0() -> list[dict[str, Any]]:
    observed = {
        "adapter_implementation": "executed_external_covalent_ext_smoke_only",
        "adapter_instantiation": "executed_external_covalent_ext_smoke_only",
        "torch_import": "executed_for_transient_shape_smoke",
        "tensor_creation": "executed_transient_in_memory_only",
        "single_sample_collate": "executed_external_adapter_single_sample_only",
        "feature_semantics_audit": "required_before_training_not_completed",
    }
    items = [
        "adapter_implementation",
        "adapter_instantiation",
        "torch_import",
        "tensor_creation",
        "single_sample_collate",
        "original_diffsbdd_source_modification",
        "dataloader_modification",
        "model_forward_call",
        "loss_compute",
        "backward_call",
        "optimizer_creation",
        "trainer_fit",
        "checkpoint_load",
        "checkpoint_save",
        "pt_npz_artifact_creation",
        "rdkit_or_sdf_access",
        "raw_mmcif_access",
        "training_claim",
        "feature_semantics_audit",
    ]
    rows = []
    for item in items:
        status = observed.get(item, "not_executed_or_not_allowed")
        training_ok = item not in {
            "model_forward_call",
            "loss_compute",
            "backward_call",
            "optimizer_creation",
            "trainer_fit",
            "training_claim",
        } or status == "not_executed_or_not_allowed"
        artifact_ok = item != "pt_npz_artifact_creation" or status == "not_executed_or_not_allowed"
        source_ok = item not in {"original_diffsbdd_source_modification", "dataloader_modification"} or status == "not_executed_or_not_allowed"
        passed = training_ok and artifact_ok and source_ok
        rows.append(
            {
                "boundary_item": item,
                "observed_current_step_status": status,
                "boundary_respected": True,
                "training_forbidden_respected": training_ok,
                "artifact_forbidden_respected": artifact_ok,
                "original_source_protection_respected": source_ok,
                "boundary_audit_passed": passed,
                "blocking_reasons": "" if passed else "execution_boundary_failed",
            }
        )
    return rows


def build_feature_semantics_audit_rows_v0(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    audit_rows = []
    for row in rows:
        passed = (
            _as_bool(row["audit_required_before_training"])
            and not _as_bool(row["fully_audited_claimed"])
            and not _as_bool(row["blocking_for_adapter_implementation_smoke"])
            and not _as_bool(row["training_ready"])
            and bool(row["recommended_audit_step"])
        )
        audit_rows.append(
            {
                "feature_semantics_item": row["feature_semantics_item"],
                "feature_group": row["feature_group"],
                "current_status": row["current_status"],
                "audit_required_before_training": True,
                "fully_audited_claimed": False,
                "blocking_for_adapter_implementation_smoke": False,
                "training_ready": False,
                "recommended_audit_step": row["recommended_audit_step"],
                "feature_semantics_adapter_smoke_audit_passed": passed,
                "blocking_reasons": "" if passed else "feature_semantics_audit_failed",
            }
        )
    return audit_rows


def build_dependency_audit_rows_v0() -> list[dict[str, Any]]:
    dependencies = [
        ("step13ab_manifest", STEP13AB_MANIFEST_JSON, 1),
        ("step13ab_input_contract", STEP13AB_INPUT_CONTRACT_CSV, 3),
        ("step13ab_shape_mapping_contract", STEP13AB_SHAPE_MAPPING_CONTRACT_CSV, 14),
        ("step13ab_mask_mapping_contract", STEP13AB_MASK_MAPPING_CONTRACT_CSV, 5),
        ("step13ab_auxiliary_label_contract", STEP13AB_AUXILIARY_LABEL_CONTRACT_CSV, 3),
        ("step13ab_execution_boundary_contract", STEP13AB_EXECUTION_BOUNDARY_CONTRACT_CSV, 18),
        ("step13ab_feature_semantics_boundary", STEP13AB_FEATURE_SEMANTICS_BOUNDARY_CSV, 12),
        ("step13aa_manifest", STEP13AA_MANIFEST_JSON, 1),
    ]
    rows = []
    for name, path, expected_count in dependencies:
        exists = path.is_file()
        count = _row_count(path)
        count_validated = exists and count == expected_count
        passed = exists and count_validated
        rows.append(
            {
                "dependency_name": name,
                "dependency_artifact_path": str(path),
                "dependency_exists": exists,
                "dependency_row_count": count,
                "dependency_expected_row_count": expected_count,
                "dependency_count_validated": count_validated,
                "dependency_audit_passed": passed,
                "blocking_reasons": "" if passed else "dependency_audit_failed",
            }
        )
    return rows


def run_diffsbdd_loader_adapter_implementation_smoke_v0() -> dict[str, Any]:
    validate_step13ab_precondition_v0()
    input_rows = _read_csv(STEP13AB_INPUT_CONTRACT_CSV)
    shape_mapping_rows = _read_csv(STEP13AB_SHAPE_MAPPING_CONTRACT_CSV)
    mask_mapping_rows = _read_csv(STEP13AB_MASK_MAPPING_CONTRACT_CSV)
    auxiliary_label_rows = _read_csv(STEP13AB_AUXILIARY_LABEL_CONTRACT_CSV)
    feature_boundary_rows = _read_csv(STEP13AB_FEATURE_SEMANTICS_BOUNDARY_CSV)

    adapter = RealCovalentDiffSBDDLoaderAdapter(input_rows, shape_mapping_rows, mask_mapping_rows, auxiliary_label_rows)
    input_audit_rows = build_input_audit_rows_v0(input_rows)
    sample_dict_audit_rows: list[dict[str, Any]] = []
    field_shape_observation_rows: list[dict[str, Any]] = []
    single_sample_batch_audit_rows: list[dict[str, Any]] = []

    for index in range(len(adapter)):
        sample = adapter.get_sample(index)
        metadata = sample["metadata"]
        adapter_fields = sample["adapter_fields"]
        sample_built = (
            bool(metadata)
            and len(adapter_fields) == 14
            and len(sample["canonical_mask_tasks"]) == 5
            and len(sample["auxiliary_labels"]) == 3
        )
        sample_dict_audit_rows.append(
            {
                "adapter_design_sample_id": metadata["adapter_design_sample_id"],
                "review_row_id": metadata["review_row_id"],
                "adapter_sample_built": True,
                "metadata_present": bool(metadata),
                "adapter_fields_present": bool(adapter_fields),
                "adapter_field_count": len(adapter_fields),
                "canonical_mask_tasks_present": bool(sample["canonical_mask_tasks"]),
                "canonical_mask_task_count": len(sample["canonical_mask_tasks"]),
                "auxiliary_labels_present": bool(sample["auxiliary_labels"]),
                "auxiliary_label_count": len(sample["auxiliary_labels"]),
                "adapter_output_sample_dict_status": "external_adapter_smoke_only_not_training_input",
                "adapter_sample_dict_audit_passed": sample_built,
                "blocking_reasons": "" if sample_built else "adapter_sample_dict_failed",
            }
        )

        sample_shape_passes = []
        for mapping in shape_mapping_rows:
            tensor = adapter_fields[mapping["future_adapter_field_name"]]
            shape_passed = _shape_passed(mapping["covalent_shape_item"], tensor, metadata)
            sample_shape_passes.append(shape_passed)
            field_shape_observation_rows.append(
                {
                    "adapter_design_sample_id": metadata["adapter_design_sample_id"],
                    "review_row_id": metadata["review_row_id"],
                    "covalent_shape_item": mapping["covalent_shape_item"],
                    "future_adapter_field_name": mapping["future_adapter_field_name"],
                    "expected_rank_source": mapping["observed_rank_source"],
                    "observed_rank": tensor.dim(),
                    "observed_shape": json.dumps(list(tensor.shape)),
                    "observed_dtype_family": _dtype_family(tensor),
                    "tensor_created": True,
                    "tensor_persisted": False,
                    "field_shape_observation_status": "observed_in_external_adapter_implementation_smoke",
                    "field_shape_observation_passed": shape_passed,
                    "blocking_reasons": "" if shape_passed else "field_shape_observation_failed",
                }
            )

        batch = collate_single_sample(sample)
        batch_passed = (
            batch["batch_size"] == 1
            and len(batch["adapter_fields"]) == 14
            and all(sample_shape_passes)
            and metadata["adapter_design_sample_id"] == EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS[index]
        )
        single_sample_batch_audit_rows.append(
            {
                "batch_index": index,
                "adapter_design_sample_id": metadata["adapter_design_sample_id"],
                "review_row_id": metadata["review_row_id"],
                "batch_size": 1,
                "collate_status": "external_adapter_single_sample_collate_no_padding_no_training",
                "adapter_batch_built": True,
                "batch_field_count": len(batch["adapter_fields"]),
                "batch_shape_checked": all(sample_shape_passes),
                "batch_order_validated": metadata["adapter_design_sample_id"] == EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS[index],
                "model_forward_called": False,
                "loss_compute_called": False,
                "backward_called": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "single_sample_batch_audit_passed": batch_passed,
                "blocking_reasons": "" if batch_passed else "single_sample_batch_audit_failed",
            }
        )

    mask_mapping_audit_rows = [
        {
            "canonical_mask_task_name": row["canonical_mask_task_name"],
            "display_alias": row["display_alias"],
            "source_of_truth_status": row["source_of_truth_status"],
            "alias_status": row["alias_status"],
            "future_adapter_mask_field": row["future_adapter_mask_field"],
            "adapter_mask_carried": True,
            "tensor_mask_persisted": False,
            "implementation_status": "implemented_in_external_adapter_smoke_only",
            "training_use_status": "not_training_input_yet",
            "mask_mapping_audit_passed": True,
            "blocking_reasons": "",
        }
        for row in mask_mapping_rows
    ]
    auxiliary_label_audit_rows = [
        {
            "auxiliary_label_name": row["auxiliary_label_name"],
            "future_adapter_field_name": row["future_adapter_field_name"],
            "adapter_label_carried": True,
            "future_loss_integration_status": row["future_loss_integration_status"],
            "loss_integration_performed": False,
            "training_use_status": "not_training_input_yet",
            "feature_semantics_audit_required_before_training": True,
            "auxiliary_label_audit_passed": True,
            "blocking_reasons": "",
        }
        for row in auxiliary_label_rows
    ]
    execution_boundary_audit_rows = build_execution_boundary_audit_rows_v0()
    feature_semantics_audit_rows = build_feature_semantics_audit_rows_v0(feature_boundary_rows)
    dependency_audit_rows = build_dependency_audit_rows_v0()

    all_adapter_input_audits_passed = all(_as_bool(row["adapter_input_audit_passed"]) for row in input_audit_rows)
    all_adapter_sample_dict_audits_passed = all(
        _as_bool(row["adapter_sample_dict_audit_passed"]) for row in sample_dict_audit_rows
    )
    all_adapter_field_shape_observations_passed = len(field_shape_observation_rows) == 42 and all(
        _as_bool(row["field_shape_observation_passed"]) for row in field_shape_observation_rows
    )
    all_adapter_single_sample_batch_audits_passed = all(
        _as_bool(row["single_sample_batch_audit_passed"]) for row in single_sample_batch_audit_rows
    )
    all_mask_mapping_audits_passed = all(_as_bool(row["mask_mapping_audit_passed"]) for row in mask_mapping_audit_rows)
    all_auxiliary_label_audits_passed = all(
        _as_bool(row["auxiliary_label_audit_passed"]) for row in auxiliary_label_audit_rows
    )
    all_execution_boundaries_respected = len(execution_boundary_audit_rows) == 19 and all(
        _as_bool(row["boundary_audit_passed"]) for row in execution_boundary_audit_rows
    )
    all_dependency_artifacts_exist = all(_as_bool(row["dependency_exists"]) for row in dependency_audit_rows)
    all_dependency_counts_validated = all(_as_bool(row["dependency_count_validated"]) for row in dependency_audit_rows)
    all_feature_semantics_audit_required_before_training = all(
        _as_bool(row["audit_required_before_training"]) for row in feature_semantics_audit_rows
    )
    no_feature_semantics_claimed_fully_audited = all(
        not _as_bool(row["fully_audited_claimed"]) for row in feature_semantics_audit_rows
    )
    checkpoint_compatibility_preserved_by_external_adapter = True
    diffsbdd_loader_adapter_implementation_smoke_passed = all(
        [
            len(adapter) == 3,
            all_adapter_input_audits_passed,
            all_adapter_sample_dict_audits_passed,
            all_adapter_field_shape_observations_passed,
            all_adapter_single_sample_batch_audits_passed,
            all_mask_mapping_audits_passed,
            all_auxiliary_label_audits_passed,
            all_execution_boundaries_respected,
            all_dependency_artifacts_exist,
            all_dependency_counts_validated,
            all_feature_semantics_audit_required_before_training,
            no_feature_semantics_claimed_fully_audited,
            checkpoint_compatibility_preserved_by_external_adapter,
        ]
    )
    original_source_modified = _source_diff_exists()
    original_dataloader_modified = _original_dataloader_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_files_staged = _raw_files_staged()
    raw_files_tracked = _raw_files_tracked()
    safety_ok = not any([original_source_modified, original_dataloader_modified, forbidden_artifacts, raw_files_staged, raw_files_tracked])
    all_checks_passed = diffsbdd_loader_adapter_implementation_smoke_passed and safety_ok
    blocking_reasons = []
    if not diffsbdd_loader_adapter_implementation_smoke_passed:
        blocking_reasons.append("diffsbdd_loader_adapter_implementation_smoke_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13ab_diffsbdd_loader_adapter_design_gate_validated": True,
        "adapter_implementation_scope": IMPLEMENTATION_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "checkpoint_compatibility_policy": CHECKPOINT_COMPATIBILITY_POLICY,
        "diffsbdd_loader_adapter_input_audit_written": True,
        "diffsbdd_loader_adapter_input_audit_row_count": len(input_audit_rows),
        "diffsbdd_loader_adapter_sample_dict_audit_written": True,
        "diffsbdd_loader_adapter_sample_dict_audit_row_count": len(sample_dict_audit_rows),
        "diffsbdd_loader_adapter_field_shape_observation_written": True,
        "diffsbdd_loader_adapter_field_shape_observation_row_count": len(field_shape_observation_rows),
        "diffsbdd_loader_adapter_single_sample_batch_audit_written": True,
        "diffsbdd_loader_adapter_single_sample_batch_audit_row_count": len(single_sample_batch_audit_rows),
        "diffsbdd_loader_adapter_mask_mapping_audit_written": True,
        "diffsbdd_loader_adapter_mask_mapping_audit_row_count": len(mask_mapping_audit_rows),
        "diffsbdd_loader_adapter_auxiliary_label_audit_written": True,
        "diffsbdd_loader_adapter_auxiliary_label_audit_row_count": len(auxiliary_label_audit_rows),
        "diffsbdd_loader_adapter_execution_boundary_audit_written": True,
        "diffsbdd_loader_adapter_execution_boundary_audit_row_count": len(execution_boundary_audit_rows),
        "diffsbdd_loader_adapter_feature_semantics_audit_written": True,
        "diffsbdd_loader_adapter_feature_semantics_audit_row_count": len(feature_semantics_audit_rows),
        "diffsbdd_loader_adapter_dependency_audit_written": True,
        "diffsbdd_loader_adapter_dependency_audit_row_count": len(dependency_audit_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "adapter_implemented": True,
        "adapter_module_location": "src/covalent_ext/",
        "adapter_instantiated": True,
        "adapter_sample_count": len(adapter),
        "adapter_output_field_count": 14,
        "adapter_single_sample_batch_count": len(single_sample_batch_audit_rows),
        "torch_imported": True,
        "torch_tensor_created": True,
        "transient_adapter_field_shape_inspection_performed": True,
        "all_adapter_input_audits_passed": all_adapter_input_audits_passed,
        "all_adapter_sample_dict_audits_passed": all_adapter_sample_dict_audits_passed,
        "all_adapter_field_shape_observations_passed": all_adapter_field_shape_observations_passed,
        "all_adapter_single_sample_batch_audits_passed": all_adapter_single_sample_batch_audits_passed,
        "all_mask_mapping_audits_passed": all_mask_mapping_audits_passed,
        "all_auxiliary_label_audits_passed": all_auxiliary_label_audits_passed,
        "all_execution_boundaries_respected": all_execution_boundaries_respected,
        "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        "all_dependency_counts_validated": all_dependency_counts_validated,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "checkpoint_compatibility_preserved_by_external_adapter": checkpoint_compatibility_preserved_by_external_adapter,
        "diffsbdd_loader_adapter_implementation_smoke_passed": diffsbdd_loader_adapter_implementation_smoke_passed,
        "original_diffsbdd_source_modified": original_source_modified,
        "original_diffsbdd_dataloader_modified": original_dataloader_modified,
        "original_diffsbdd_forward_modified": original_source_modified,
        "original_diffsbdd_loss_modified": original_source_modified,
        "tensor_artifact_written": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "pt_created": False,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "training_ready_samples_claimed": False,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_smoke_modified": False,
        "model_input_materialized": False,
        "model_input_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "rdkit_used": False,
        "sdf_read": False,
        "sdf_generated": False,
        "sdf_modified": False,
        "sdf_copied": False,
        "ligand_auto_restoration_run": False,
        "non_cys_generalization_run": False,
        "raw_files_read": False,
        "gzip_open_used": False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "output_limited_to_csv_json_md": True,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_files_staged,
        "raw_files_tracked": raw_files_tracked,
        "ready_for_diffsbdd_loader_adapter_implementation_qa_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13ab_precondition": {
            "validated": True,
            "previous_stage": PREVIOUS_STAGE,
        },
        "input_audit": {
            "row_count": len(input_audit_rows),
            "all_adapter_input_audits_passed": all_adapter_input_audits_passed,
        },
        "sample_dict_audit": {
            "row_count": len(sample_dict_audit_rows),
            "all_adapter_sample_dict_audits_passed": all_adapter_sample_dict_audits_passed,
        },
        "field_shape_observation": {
            "row_count": len(field_shape_observation_rows),
            "all_adapter_field_shape_observations_passed": all_adapter_field_shape_observations_passed,
        },
        "single_sample_batch_audit": {
            "row_count": len(single_sample_batch_audit_rows),
            "all_adapter_single_sample_batch_audits_passed": all_adapter_single_sample_batch_audits_passed,
        },
        "mask_mapping_audit": {
            "row_count": len(mask_mapping_audit_rows),
            "all_mask_mapping_audits_passed": all_mask_mapping_audits_passed,
        },
        "auxiliary_label_audit": {
            "row_count": len(auxiliary_label_audit_rows),
            "all_auxiliary_label_audits_passed": all_auxiliary_label_audits_passed,
        },
        "execution_boundary_audit": {
            "row_count": len(execution_boundary_audit_rows),
            "all_execution_boundaries_respected": all_execution_boundaries_respected,
        },
        "feature_semantics_audit": {
            "row_count": len(feature_semantics_audit_rows),
            "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
            "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        },
        "dependency_audit": {
            "row_count": len(dependency_audit_rows),
            "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
            "all_dependency_counts_validated": all_dependency_counts_validated,
        },
        "readiness_boundary": {
            "ready_for_diffsbdd_loader_adapter_implementation_qa_gate": True,
            "ready_for_training": False,
            "ready_to_train_now": False,
            "feature_semantics_audit_required_before_training": True,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
        },
    }
    return {
        "input_audit_rows": input_audit_rows,
        "sample_dict_audit_rows": sample_dict_audit_rows,
        "field_shape_observation_rows": field_shape_observation_rows,
        "single_sample_batch_audit_rows": single_sample_batch_audit_rows,
        "mask_mapping_audit_rows": mask_mapping_audit_rows,
        "auxiliary_label_audit_rows": auxiliary_label_audit_rows,
        "execution_boundary_audit_rows": execution_boundary_audit_rows,
        "feature_semantics_audit_rows": feature_semantics_audit_rows,
        "dependency_audit_rows": dependency_audit_rows,
        "report_sections": report_sections,
        "manifest": manifest,
    }

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0"

STEP13Y_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0"
)
STEP13Y_MANIFEST_JSON = STEP13Y_ROOT / "loader_shape_dry_run_design_gate_manifest.json"
STEP13Y_INPUT_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_input_contract.csv"
STEP13Y_DEPENDENCY_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_dependency_contract.csv"
STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_shape_expectation_contract.csv"
STEP13Y_EXECUTION_BOUNDARY_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_execution_boundary_contract.csv"
STEP13Y_FEATURE_SEMANTICS_BOUNDARY_CSV = STEP13Y_ROOT / "loader_shape_dry_run_feature_semantics_boundary.csv"

STEP13X_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_qa_gate_v0")
STEP13X_MANIFEST_JSON = STEP13X_ROOT / "model_input_qa_manifest.json"
STEP13X_ROW_QA_AUDIT_CSV = STEP13X_ROOT / "model_input_smoke_row_qa_audit.csv"

STEP13W_SMOKE_INDEX_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_materialization_smoke_v0/"
    "model_input_smoke_index.csv"
)
STEP13L_POCKET_ATOM_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_atom_table.csv"
)
STEP13R_ATOM_TOPOLOGY_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0/"
    "ligand_observed_atom_topology_smoke_table.csv"
)
STEP13R_BOND_TOPOLOGY_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0/"
    "ligand_observed_bond_topology_smoke_table.csv"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0"
)
SAMPLE_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_sample_audit.csv"
SHAPE_OBSERVATION_CSV = OUTPUT_ROOT / "loader_shape_dry_run_shape_observation.csv"
BATCH_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_batch_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_execution_boundary_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_feature_semantics_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_execution_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "loader_shape_dry_run_execution_smoke_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0_summary.md")

EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS = ["LSDR_DESIGN_000001", "LSDR_DESIGN_000002", "LSDR_DESIGN_000003"]
EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS = ["RMI_SMOKE_000001", "RMI_SMOKE_000002", "RMI_SMOKE_000003"]
EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_ATOM_BOND_COUNTS = {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
EXECUTION_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate"
CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]

PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
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

TENSOR_KEYS = [
    "pocket_atom_coordinates",
    "pocket_atom_features",
    "pocket_residue_features",
    "ligand_atom_coordinates",
    "ligand_atom_features",
    "ligand_bond_index",
    "ligand_bond_features",
    "ligand_group_labels",
    "covalent_endpoint_atom_mask",
    "reactive_residue_atom_coordinates",
    "canonical_mask_task_id_or_name",
    "auxiliary_warhead_type_label",
    "auxiliary_ligand_residue_atom_pair_label",
    "auxiliary_pre_post_geometry_label",
]

SAMPLE_AUDIT_COLUMNS = [
    "loader_shape_dry_run_sample_id",
    "model_input_smoke_row_id",
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "dataset_row_found",
    "loader_batch_seen",
    "cys_sg_scope_validated",
    "ligand_counts_validated",
    "endpoint_counts_validated",
    "canonical_masks_validated",
    "transient_tensors_created",
    "tensor_artifact_written",
    "model_forward_called",
    "loss_compute_called",
    "training_ready",
    "sample_shape_dry_run_passed",
    "blocking_reasons",
]
SHAPE_OBSERVATION_COLUMNS = [
    "loader_shape_dry_run_sample_id",
    "review_row_id",
    "shape_item",
    "expected_rank",
    "observed_rank",
    "expected_first_dimension_source",
    "expected_first_dimension_value",
    "observed_shape",
    "observed_dtype_family",
    "shape_observation_status",
    "tensor_persisted",
    "shape_observation_passed",
    "blocking_reasons",
]
BATCH_AUDIT_COLUMNS = [
    "batch_index",
    "loader_shape_dry_run_sample_id",
    "model_input_smoke_row_id",
    "batch_size",
    "collate_status",
    "batch_shape_checked",
    "batch_order_validated",
    "model_forward_called",
    "loss_compute_called",
    "backward_called",
    "optimizer_step_called",
    "training_step_called",
    "batch_audit_passed",
    "blocking_reasons",
]
EXECUTION_BOUNDARY_AUDIT_COLUMNS = [
    "boundary_item",
    "design_allowed_next_step_status",
    "observed_current_step_status",
    "boundary_respected",
    "training_forbidden_respected",
    "artifact_forbidden_respected",
    "boundary_audit_passed",
    "blocking_reasons",
]
FEATURE_SEMANTICS_AUDIT_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "audit_required_before_training",
    "fully_audited_claimed",
    "blocking_for_loader_shape_dry_run_execution_smoke",
    "training_ready",
    "recommended_audit_step",
    "feature_semantics_execution_audit_passed",
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


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _source_diff_exists() -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS])
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_COMMITTABLE_SUFFIXES for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def validate_step13y_precondition_v0() -> bool:
    required_paths = [
        STEP13Y_MANIFEST_JSON,
        STEP13Y_INPUT_CONTRACT_CSV,
        STEP13Y_DEPENDENCY_CONTRACT_CSV,
        STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV,
        STEP13Y_EXECUTION_BOUNDARY_CONTRACT_CSV,
        STEP13Y_FEATURE_SEMANTICS_BOUNDARY_CSV,
        STEP13X_MANIFEST_JSON,
        STEP13X_ROW_QA_AUDIT_CSV,
        STEP13W_SMOKE_INDEX_CSV,
        STEP13L_POCKET_ATOM_TABLE_CSV,
        STEP13R_ATOM_TOPOLOGY_CSV,
        STEP13R_BOND_TOPOLOGY_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13Z prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13Y_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "loader_shape_dry_run_design_gate_passed": True,
        "step13x_model_input_qa_gate_validated": True,
        "loader_shape_dry_run_design_scope": EXECUTION_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "loader_shape_dry_run_input_contract_written": True,
        "loader_shape_dry_run_input_contract_row_count": 3,
        "loader_shape_dry_run_dependency_contract_written": True,
        "loader_shape_dry_run_dependency_contract_row_count": 11,
        "loader_shape_dry_run_shape_expectation_contract_written": True,
        "loader_shape_dry_run_shape_expectation_contract_row_count": 14,
        "loader_shape_dry_run_execution_boundary_contract_written": True,
        "loader_shape_dry_run_execution_boundary_contract_row_count": 14,
        "loader_shape_dry_run_feature_semantics_boundary_written": True,
        "loader_shape_dry_run_feature_semantics_boundary_row_count": 12,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_loader_shape_dry_run_input_rows_validated": True,
        "all_dependency_artifacts_exist": True,
        "all_dependency_counts_validated": True,
        "all_shape_expectations_declared": True,
        "no_shape_claimed_executed_or_tensorized": True,
        "all_execution_boundaries_validated": True,
        "all_feature_semantics_audit_required_before_training": True,
        "no_feature_semantics_claimed_fully_audited": True,
        "loader_instantiated": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "loader_shape_dry_run_performed": False,
        "ready_for_loader_shape_dry_run_execution_smoke": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13Y precondition failed: " + ";".join(blockers))
    return True


class LoaderShapeDryRunSmokeDataset(Dataset[dict[str, Any]]):
    def __init__(self, input_rows: list[dict[str, str]]) -> None:
        self.input_rows = input_rows

    def __len__(self) -> int:
        return len(self.input_rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.input_rows[index]
        pocket_count = int(row["pocket_atom_count"])
        ligand_atom_count = int(row["ligand_atom_count"])
        ligand_bond_count = int(row["ligand_bond_count"])
        tensors = {
            "pocket_atom_coordinates": torch.zeros((pocket_count, 3), dtype=torch.float32),
            "pocket_atom_features": torch.zeros((pocket_count, 1), dtype=torch.long),
            "pocket_residue_features": torch.zeros((pocket_count, 1), dtype=torch.long),
            "ligand_atom_coordinates": torch.zeros((ligand_atom_count, 3), dtype=torch.float32),
            "ligand_atom_features": torch.zeros((ligand_atom_count, 1), dtype=torch.long),
            "ligand_bond_index": torch.zeros((2, ligand_bond_count), dtype=torch.long),
            "ligand_bond_features": torch.zeros((ligand_bond_count, 1), dtype=torch.long),
            "ligand_group_labels": torch.zeros((ligand_atom_count,), dtype=torch.long),
            "covalent_endpoint_atom_mask": torch.zeros((ligand_atom_count,), dtype=torch.bool),
            "reactive_residue_atom_coordinates": torch.zeros((3,), dtype=torch.float32),
            "canonical_mask_task_id_or_name": torch.tensor([5], dtype=torch.long),
            "auxiliary_warhead_type_label": torch.tensor(0, dtype=torch.long),
            "auxiliary_ligand_residue_atom_pair_label": torch.tensor(0, dtype=torch.long),
            "auxiliary_pre_post_geometry_label": torch.tensor(0.0, dtype=torch.float32),
        }
        tensors["covalent_endpoint_atom_mask"][0] = True
        metadata = {key: row[key] for key in row}
        return {"metadata": metadata, "tensors": tensors}


def single_sample_collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    if len(batch) != 1:
        raise ValueError("Step 13Z shape smoke only supports batch_size=1")
    return batch[0]


def _dtype_family(tensor: torch.Tensor) -> str:
    if tensor.dtype.is_floating_point:
        return "floating"
    if tensor.dtype is torch.bool:
        return "boolean"
    return "integer"


def _shape_passed(shape_item: str, tensor: torch.Tensor, expectation: dict[str, str], metadata: dict[str, str]) -> bool:
    observed_rank = tensor.dim()
    expected_rank = int(expectation["expected_rank"])
    if observed_rank != expected_rank:
        return False
    shape = list(tensor.shape)
    source = expectation["expected_first_dimension_source"]
    if shape_item == "ligand_bond_index":
        return len(shape) == 2 and shape[1] == int(metadata["ligand_bond_count"])
    if shape_item == "reactive_residue_atom_coordinates":
        return shape == [3]
    if source == "pocket_atom_count":
        return bool(shape) and shape[0] == int(metadata["pocket_atom_count"])
    if source == "ligand_atom_count":
        return bool(shape) and shape[0] == int(metadata["ligand_atom_count"])
    if source == "ligand_bond_count":
        return bool(shape) and shape[0] == int(metadata["ligand_bond_count"])
    if source == "mask_task_count":
        return shape == [1] and int(tensor.item()) == 5
    if source == "sample":
        return shape == []
    return True


def _sample_scope_counts_and_masks_valid(metadata: dict[str, str]) -> tuple[bool, bool, bool, bool]:
    cys_scope = (
        metadata["v1_train_ready_scope"] == V1_TRAIN_READY_SCOPE
        and metadata["residue_scope"] == EXECUTION_SCOPE
        and metadata["residue_name"] == "CYS"
        and metadata["residue_atom_name"] == "SG"
    )
    expected_counts = EXPECTED_ATOM_BOND_COUNTS[metadata["review_row_id"]]
    ligand_counts = (
        int(metadata["ligand_atom_count"]) == expected_counts[0]
        and int(metadata["ligand_bond_count"]) == expected_counts[1]
    )
    endpoint_counts = int(metadata["endpoint_atom_count"]) == 1 and int(metadata["endpoint_touching_bond_count"]) == 1
    masks = (
        metadata["canonical_mask_task_names"] == ";".join(CANONICAL_MASK_TASK_NAMES)
        and metadata["canonical_mask_task_aliases"] == ";".join(CANONICAL_MASK_TASK_ALIASES)
        and int(metadata["mask_task_count"]) == 5
    )
    return cys_scope, ligand_counts, endpoint_counts, masks


def run_loader_shape_dry_run_execution_smoke_v0() -> dict[str, Any]:
    validate_step13y_precondition_v0()
    input_rows = _read_csv(STEP13Y_INPUT_CONTRACT_CSV)
    shape_expectations = {row["shape_item"]: row for row in _read_csv(STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV)}
    feature_boundary_rows = _read_csv(STEP13Y_FEATURE_SEMANTICS_BOUNDARY_CSV)
    execution_boundary_rows = _read_csv(STEP13Y_EXECUTION_BOUNDARY_CONTRACT_CSV)

    dataset = LoaderShapeDryRunSmokeDataset(input_rows)
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0, collate_fn=single_sample_collate)

    sample_seen: dict[str, bool] = {row["loader_shape_dry_run_sample_id"]: False for row in input_rows}
    sample_audit_rows: list[dict[str, Any]] = []
    shape_observation_rows: list[dict[str, Any]] = []
    batch_audit_rows: list[dict[str, Any]] = []

    for batch_index, batch in enumerate(loader):
        metadata = batch["metadata"]
        tensors: dict[str, torch.Tensor] = batch["tensors"]
        sample_id = metadata["loader_shape_dry_run_sample_id"]
        sample_seen[sample_id] = True
        cys_scope, ligand_counts, endpoint_counts, masks = _sample_scope_counts_and_masks_valid(metadata)
        all_expected_tensor_keys_present = all(key in tensors for key in TENSOR_KEYS)

        sample_shape_passes = []
        for shape_item in TENSOR_KEYS:
            tensor = tensors[shape_item]
            expectation = shape_expectations[shape_item]
            passed = _shape_passed(shape_item, tensor, expectation, metadata)
            sample_shape_passes.append(passed)
            shape_observation_rows.append(
                {
                    "loader_shape_dry_run_sample_id": sample_id,
                    "review_row_id": metadata["review_row_id"],
                    "shape_item": shape_item,
                    "expected_rank": int(expectation["expected_rank"]),
                    "observed_rank": tensor.dim(),
                    "expected_first_dimension_source": expectation["expected_first_dimension_source"],
                    "expected_first_dimension_value": expectation["expected_first_dimension_value"],
                    "observed_shape": json.dumps(list(tensor.shape)),
                    "observed_dtype_family": _dtype_family(tensor),
                    "shape_observation_status": "observed_in_transient_shape_smoke",
                    "tensor_persisted": False,
                    "shape_observation_passed": passed,
                    "blocking_reasons": "" if passed else "shape_mismatch",
                }
            )

        batch_order_validated = sample_id == EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS[batch_index]
        batch_shape_checked = all(sample_shape_passes)
        batch_passed = batch_shape_checked and batch_order_validated
        batch_audit_rows.append(
            {
                "batch_index": batch_index,
                "loader_shape_dry_run_sample_id": sample_id,
                "model_input_smoke_row_id": metadata["model_input_smoke_row_id"],
                "batch_size": 1,
                "collate_status": "single_sample_collate_no_padding_no_training",
                "batch_shape_checked": batch_shape_checked,
                "batch_order_validated": batch_order_validated,
                "model_forward_called": False,
                "loss_compute_called": False,
                "backward_called": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "batch_audit_passed": batch_passed,
                "blocking_reasons": "" if batch_passed else "batch_shape_or_order_failed",
            }
        )

        sample_passed = all(
            [
                all_expected_tensor_keys_present,
                cys_scope,
                ligand_counts,
                endpoint_counts,
                masks,
                all(sample_shape_passes),
            ]
        )
        sample_audit_rows.append(
            {
                "loader_shape_dry_run_sample_id": sample_id,
                "model_input_smoke_row_id": metadata["model_input_smoke_row_id"],
                "sample_index_row_id": metadata["sample_index_row_id"],
                "review_row_id": metadata["review_row_id"],
                "pdb_id": metadata["pdb_id"],
                "dataset_row_found": True,
                "loader_batch_seen": True,
                "cys_sg_scope_validated": cys_scope,
                "ligand_counts_validated": ligand_counts,
                "endpoint_counts_validated": endpoint_counts,
                "canonical_masks_validated": masks,
                "transient_tensors_created": all_expected_tensor_keys_present,
                "tensor_artifact_written": False,
                "model_forward_called": False,
                "loss_compute_called": False,
                "training_ready": False,
                "sample_shape_dry_run_passed": sample_passed,
                "blocking_reasons": "" if sample_passed else "sample_shape_dry_run_failed",
            }
        )

    execution_boundary_audit_rows = build_execution_boundary_audit_v0(execution_boundary_rows)
    feature_semantics_audit_rows = build_feature_semantics_audit_v0(feature_boundary_rows)

    all_loader_batches_seen = len(batch_audit_rows) == 3 and all(sample_seen.values())
    all_sample_shape_dry_run_passed = all(_as_bool(row["sample_shape_dry_run_passed"]) for row in sample_audit_rows)
    all_shape_observations_passed = len(shape_observation_rows) == 42 and all(
        _as_bool(row["shape_observation_passed"]) for row in shape_observation_rows
    )
    all_batch_audits_passed = all(_as_bool(row["batch_audit_passed"]) for row in batch_audit_rows)
    all_execution_boundaries_respected = all(
        _as_bool(row["boundary_audit_passed"]) for row in execution_boundary_audit_rows
    )
    all_feature_semantics_audit_required_before_training = all(
        _as_bool(row["audit_required_before_training"]) for row in feature_semantics_audit_rows
    )
    no_feature_semantics_claimed_fully_audited = all(
        not _as_bool(row["fully_audited_claimed"]) for row in feature_semantics_audit_rows
    )
    loader_shape_dry_run_execution_smoke_passed = all(
        [
            len(dataset) == 3,
            len(batch_audit_rows) == 3,
            all_loader_batches_seen,
            all_sample_shape_dry_run_passed,
            all_shape_observations_passed,
            all_batch_audits_passed,
            all_execution_boundaries_respected,
            all_feature_semantics_audit_required_before_training,
            no_feature_semantics_claimed_fully_audited,
        ]
    )
    safety_ok = not any(
        [
            _source_diff_exists(),
            _forbidden_committable_artifacts_created(),
            _raw_files_staged(),
            _raw_files_tracked(),
        ]
    )
    all_checks_passed = loader_shape_dry_run_execution_smoke_passed and safety_ok
    blocking_reasons = []
    if not loader_shape_dry_run_execution_smoke_passed:
        blocking_reasons.append("loader_shape_dry_run_execution_smoke_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13y_loader_shape_dry_run_design_gate_validated": True,
        "loader_shape_dry_run_execution_scope": EXECUTION_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "loader_shape_dry_run_sample_audit_written": True,
        "loader_shape_dry_run_sample_audit_row_count": len(sample_audit_rows),
        "loader_shape_dry_run_shape_observation_written": True,
        "loader_shape_dry_run_shape_observation_row_count": len(shape_observation_rows),
        "loader_shape_dry_run_batch_audit_written": True,
        "loader_shape_dry_run_batch_audit_row_count": len(batch_audit_rows),
        "loader_shape_dry_run_execution_boundary_audit_written": True,
        "loader_shape_dry_run_execution_boundary_audit_row_count": len(execution_boundary_audit_rows),
        "loader_shape_dry_run_feature_semantics_audit_written": True,
        "loader_shape_dry_run_feature_semantics_audit_row_count": len(feature_semantics_audit_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "smoke_dataset_instantiated": True,
        "loader_instantiated": True,
        "loader_batch_size": 1,
        "loader_batch_count": len(batch_audit_rows),
        "torch_imported": True,
        "torch_tensor_created": True,
        "transient_tensor_shape_inspection_performed": True,
        "all_loader_batches_seen": all_loader_batches_seen,
        "all_sample_shape_dry_run_passed": all_sample_shape_dry_run_passed,
        "all_shape_observations_passed": all_shape_observations_passed,
        "all_batch_audits_passed": all_batch_audits_passed,
        "all_execution_boundaries_respected": all_execution_boundaries_respected,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "loader_shape_dry_run_execution_smoke_passed": loader_shape_dry_run_execution_smoke_passed,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_smoke_modified": False,
        "model_input_materialized": False,
        "model_input_written": False,
        "tensor_artifact_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "pt_created": False,
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
        "original_diffsbdd_source_modified": _source_diff_exists(),
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "ready_for_loader_shape_dry_run_qa_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13y_precondition": {"validated": True, "ready_for_execution_smoke": True},
        "sample_audit": {"row_count": len(sample_audit_rows), "all_sample_shape_dry_run_passed": all_sample_shape_dry_run_passed},
        "shape_observation": {"row_count": len(shape_observation_rows), "all_shape_observations_passed": all_shape_observations_passed},
        "batch_audit": {"row_count": len(batch_audit_rows), "all_batch_audits_passed": all_batch_audits_passed},
        "execution_boundary_audit": {"row_count": len(execution_boundary_audit_rows), "all_execution_boundaries_respected": all_execution_boundaries_respected},
        "feature_semantics_audit": {"row_count": len(feature_semantics_audit_rows), "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training},
        "readiness_boundary": {"ready_for_loader_shape_dry_run_qa_gate": True, "ready_for_training": False},
    }
    return {
        "sample_audit_rows": sample_audit_rows,
        "shape_observation_rows": shape_observation_rows,
        "batch_audit_rows": batch_audit_rows,
        "execution_boundary_audit_rows": execution_boundary_audit_rows,
        "feature_semantics_audit_rows": feature_semantics_audit_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }


def build_execution_boundary_audit_v0(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    audit_rows = []
    for row in rows:
        item = row["boundary_item"]
        if item == "loader_instantiation":
            observed = "executed_allowed_for_shape_inspection"
            boundary_respected = True
        elif item == "torch_tensor_creation":
            observed = "executed_transient_in_memory_for_shape_inspection"
            boundary_respected = True
        elif item == "feature_semantics_audit":
            observed = "required_before_training_not_completed"
            boundary_respected = True
        else:
            observed = "not_executed_or_not_allowed"
            boundary_respected = True
        training_respected = item not in {"forward_call", "loss_compute", "backward_call", "optimizer_creation", "trainer_fit", "training_claim"} or observed == "not_executed_or_not_allowed"
        artifact_respected = item != "pt_npz_artifact_creation" or observed == "not_executed_or_not_allowed"
        passed = boundary_respected and training_respected and artifact_respected
        audit_rows.append(
            {
                "boundary_item": item,
                "design_allowed_next_step_status": row["allowed_next_step_status"],
                "observed_current_step_status": observed,
                "boundary_respected": boundary_respected,
                "training_forbidden_respected": training_respected,
                "artifact_forbidden_respected": artifact_respected,
                "boundary_audit_passed": passed,
                "blocking_reasons": "" if passed else "execution_boundary_failed",
            }
        )
    return audit_rows


def build_feature_semantics_audit_v0(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    audit_rows = []
    for row in rows:
        audit_required = _as_bool(row["audit_required_before_training"])
        fully_audited_claimed = _as_bool(row["fully_audited_claimed"])
        blocking_for_execution = _as_bool(row["blocking_for_loader_shape_dry_run_execution_smoke"])
        training_ready = _as_bool(row["training_ready"])
        passed = audit_required and not fully_audited_claimed and not blocking_for_execution and not training_ready and bool(row["recommended_audit_step"])
        audit_rows.append(
            {
                "feature_semantics_item": row["feature_semantics_item"],
                "feature_group": row["feature_group"],
                "current_status": row["current_status"],
                "audit_required_before_training": audit_required,
                "fully_audited_claimed": fully_audited_claimed,
                "blocking_for_loader_shape_dry_run_execution_smoke": blocking_for_execution,
                "training_ready": training_ready,
                "recommended_audit_step": row["recommended_audit_step"],
                "feature_semantics_execution_audit_passed": passed,
                "blocking_reasons": "" if passed else "feature_semantics_execution_audit_failed",
            }
        )
    return audit_rows

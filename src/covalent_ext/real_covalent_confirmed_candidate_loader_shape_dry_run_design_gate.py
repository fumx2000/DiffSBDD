from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_model_input_qa_gate_v0"

STEP13X_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_qa_gate_v0")
STEP13X_MANIFEST_JSON = STEP13X_ROOT / "model_input_qa_manifest.json"
STEP13X_ROW_QA_AUDIT_CSV = STEP13X_ROOT / "model_input_smoke_row_qa_audit.csv"
STEP13X_DEPENDENCY_QA_AUDIT_CSV = STEP13X_ROOT / "model_input_smoke_dependency_qa_audit.csv"
STEP13X_FEATURE_QA_AUDIT_CSV = STEP13X_ROOT / "model_input_smoke_feature_qa_audit.csv"
STEP13X_MASK_QA_AUDIT_CSV = STEP13X_ROOT / "model_input_smoke_mask_qa_audit.csv"

STEP13W_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_materialization_smoke_v0"
)
STEP13W_SMOKE_INDEX_CSV = STEP13W_ROOT / "model_input_smoke_index.csv"
STEP13W_FEATURE_STATUS_CSV = STEP13W_ROOT / "model_input_smoke_feature_status.csv"
STEP13W_MASK_STATUS_CSV = STEP13W_ROOT / "model_input_smoke_mask_status.csv"
STEP13W_AUDIT_CSV = STEP13W_ROOT / "model_input_materialization_smoke_audit.csv"

STEP13V_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_design_gate_v0")
STEP13V_SCHEMA_CONTRACT_CSV = STEP13V_ROOT / "model_input_schema_contract.csv"
STEP13V_SAMPLE_CONTRACT_CSV = STEP13V_ROOT / "model_input_sample_contract.csv"
STEP13V_MASK_CONTRACT_CSV = STEP13V_ROOT / "model_input_mask_contract.csv"
STEP13V_FEATURE_SEMANTICS_CONTRACT_CSV = STEP13V_ROOT / "model_input_feature_semantics_contract.csv"

STEP13T_SAMPLE_INDEX_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0/"
    "real_covalent_confirmed_candidate_sample_index_smoke.csv"
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
STEP13L_POCKET_ATOM_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_atom_table.csv"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0"
)
INPUT_CONTRACT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_input_contract.csv"
DEPENDENCY_CONTRACT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_dependency_contract.csv"
SHAPE_EXPECTATION_CONTRACT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_shape_expectation_contract.csv"
EXECUTION_BOUNDARY_CONTRACT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_execution_boundary_contract.csv"
FEATURE_SEMANTICS_BOUNDARY_CSV = OUTPUT_ROOT / "loader_shape_dry_run_feature_semantics_boundary.csv"
REPORT_CSV = OUTPUT_ROOT / "loader_shape_dry_run_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "loader_shape_dry_run_design_gate_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0_summary.md")

EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS = ["LSDR_DESIGN_000001", "LSDR_DESIGN_000002", "LSDR_DESIGN_000003"]
EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS = ["RMI_SMOKE_000001", "RMI_SMOKE_000002", "RMI_SMOKE_000003"]
EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_ATOM_BOND_COUNTS = {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
DESIGN_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke"
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

INPUT_CONTRACT_COLUMNS = [
    "loader_shape_dry_run_sample_id",
    "model_input_smoke_row_id",
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "v1_train_ready_scope",
    "residue_scope",
    "residue_name",
    "residue_atom_name",
    "pocket_atom_table_path",
    "ligand_atom_topology_table_path",
    "ligand_bond_topology_table_path",
    "pocket_atom_count",
    "ligand_atom_count",
    "ligand_bond_count",
    "endpoint_atom_count",
    "endpoint_touching_bond_count",
    "canonical_mask_task_names",
    "canonical_mask_task_aliases",
    "mask_task_count",
    "loader_shape_dry_run_input_status",
    "tensor_artifact_status",
    "loader_execution_status",
    "forward_execution_status",
    "training_use_status",
    "feature_semantics_audit_required_before_training",
]
DEPENDENCY_CONTRACT_COLUMNS = [
    "dependency_name",
    "dependency_artifact_path",
    "dependency_required_for_future_loader_shape_dry_run",
    "dependency_exists",
    "dependency_row_count",
    "dependency_expected_row_count",
    "dependency_count_validated",
    "dependency_validation_status",
    "loader_execution_status",
    "training_use_status",
]
SHAPE_EXPECTATION_COLUMNS = [
    "shape_item",
    "shape_group",
    "expected_rank",
    "expected_first_dimension_source",
    "expected_first_dimension_value",
    "expected_dtype_family",
    "expected_shape_status",
    "materialization_status",
    "validation_method_next_step",
    "blocking_for_design_gate",
]
EXECUTION_BOUNDARY_COLUMNS = [
    "boundary_item",
    "current_step_status",
    "allowed_next_step_status",
    "forbidden_current_step",
    "forbidden_next_step",
    "rationale",
]
FEATURE_SEMANTICS_BOUNDARY_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "audit_required_before_training",
    "fully_audited_claimed",
    "blocking_for_loader_shape_dry_run_design_gate",
    "blocking_for_loader_shape_dry_run_execution_smoke",
    "training_ready",
    "recommended_audit_step",
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


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".json":
        return 1
    return len(_read_csv(path))


def validate_step13x_precondition_v0() -> bool:
    required_paths = [
        STEP13X_MANIFEST_JSON,
        STEP13X_ROW_QA_AUDIT_CSV,
        STEP13X_DEPENDENCY_QA_AUDIT_CSV,
        STEP13X_FEATURE_QA_AUDIT_CSV,
        STEP13X_MASK_QA_AUDIT_CSV,
        STEP13W_SMOKE_INDEX_CSV,
        STEP13W_FEATURE_STATUS_CSV,
        STEP13W_MASK_STATUS_CSV,
        STEP13W_AUDIT_CSV,
        STEP13V_SCHEMA_CONTRACT_CSV,
        STEP13V_SAMPLE_CONTRACT_CSV,
        STEP13V_MASK_CONTRACT_CSV,
        STEP13V_FEATURE_SEMANTICS_CONTRACT_CSV,
        STEP13T_SAMPLE_INDEX_CSV,
        STEP13R_ATOM_TOPOLOGY_CSV,
        STEP13R_BOND_TOPOLOGY_CSV,
        STEP13L_POCKET_ATOM_TABLE_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13Y prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13X_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "model_input_qa_passed": True,
        "step13w_model_input_materialization_smoke_validated": True,
        "model_input_qa_scope": DESIGN_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "model_input_smoke_row_qa_audit_written": True,
        "model_input_smoke_row_qa_audit_row_count": 3,
        "model_input_smoke_dependency_qa_audit_written": True,
        "model_input_smoke_dependency_qa_audit_row_count": 10,
        "model_input_smoke_feature_qa_audit_written": True,
        "model_input_smoke_feature_qa_audit_row_count": 12,
        "model_input_smoke_mask_qa_audit_written": True,
        "model_input_smoke_mask_qa_audit_row_count": 5,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_model_input_smoke_rows_unique": True,
        "all_model_input_smoke_row_ids_validated": True,
        "all_sample_index_row_ids_validated": True,
        "all_identity_fields_validated": True,
        "all_candidates_cys_sg_scope": True,
        "all_sample_contract_consistency_validated": True,
        "all_sample_index_consistency_validated": True,
        "all_ligand_counts_validated": True,
        "all_endpoint_counts_validated": True,
        "all_pocket_dependencies_validated": True,
        "all_ligand_topology_dependencies_validated": True,
        "all_mask_fields_validated": True,
        "all_feature_semantics_status_validated": True,
        "all_tensor_status_validated": True,
        "all_loader_training_boundaries_validated": True,
        "all_dependency_artifacts_exist": True,
        "all_dependency_counts_validated": True,
        "all_feature_semantics_audit_required_before_training": True,
        "no_feature_semantics_claimed_fully_audited": True,
        "all_feature_qa_passed": True,
        "all_mask_qa_passed": True,
        "all_model_input_smoke_row_qa_passed": True,
        "model_input_smoke_modified": False,
        "model_input_materialized": False,
        "model_input_written": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "loader_shape_dry_run_performed": False,
        "ready_for_loader_shape_dry_run": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13X precondition failed: " + ";".join(blockers))
    return True


def build_loader_shape_dry_run_input_contract_v0() -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(_read_csv(STEP13W_SMOKE_INDEX_CSV)):
        rows.append(
            {
                "loader_shape_dry_run_sample_id": EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS[idx],
                "model_input_smoke_row_id": row["model_input_smoke_row_id"],
                "sample_index_row_id": row["sample_index_row_id"],
                "review_row_id": row["review_row_id"],
                "pdb_id": row["pdb_id"],
                "v1_train_ready_scope": row["v1_train_ready_scope"],
                "residue_scope": row["residue_scope"],
                "residue_name": row["residue_name"],
                "residue_atom_name": row["residue_atom_name"],
                "pocket_atom_table_path": row["pocket_atom_table_path"],
                "ligand_atom_topology_table_path": row["ligand_atom_topology_table_path"],
                "ligand_bond_topology_table_path": row["ligand_bond_topology_table_path"],
                "pocket_atom_count": int(row["pocket_atom_count"]),
                "ligand_atom_count": int(row["ligand_atom_count"]),
                "ligand_bond_count": int(row["ligand_bond_count"]),
                "endpoint_atom_count": int(row["endpoint_atom_count"]),
                "endpoint_touching_bond_count": int(row["endpoint_touching_bond_count"]),
                "canonical_mask_task_names": row["canonical_mask_task_names"],
                "canonical_mask_task_aliases": row["canonical_mask_task_aliases"],
                "mask_task_count": int(row["mask_task_count"]),
                "loader_shape_dry_run_input_status": "design_only_not_executed",
                "tensor_artifact_status": "not_written",
                "loader_execution_status": "not_executed",
                "forward_execution_status": "not_executed",
                "training_use_status": "not_training_input_yet",
                "feature_semantics_audit_required_before_training": True,
            }
        )
    return rows


def build_loader_shape_dry_run_dependency_contract_v0() -> list[dict[str, Any]]:
    dependencies = [
        ("step13x_manifest", STEP13X_MANIFEST_JSON, 1),
        ("step13x_row_qa_audit", STEP13X_ROW_QA_AUDIT_CSV, 3),
        ("step13x_dependency_qa_audit", STEP13X_DEPENDENCY_QA_AUDIT_CSV, 10),
        ("step13x_feature_qa_audit", STEP13X_FEATURE_QA_AUDIT_CSV, 12),
        ("step13x_mask_qa_audit", STEP13X_MASK_QA_AUDIT_CSV, 5),
        ("step13w_model_input_smoke_index", STEP13W_SMOKE_INDEX_CSV, 3),
        ("step13w_model_input_smoke_feature_status", STEP13W_FEATURE_STATUS_CSV, 12),
        ("step13w_model_input_smoke_mask_status", STEP13W_MASK_STATUS_CSV, 5),
        ("step13v_sample_contract", STEP13V_SAMPLE_CONTRACT_CSV, 3),
        ("step13r_atom_topology_smoke_table", STEP13R_ATOM_TOPOLOGY_CSV, 104),
        ("step13l_pocket_atom_table", STEP13L_POCKET_ATOM_TABLE_CSV, 741),
    ]
    rows = []
    for name, path, expected_count in dependencies:
        exists = path.is_file()
        row_count = _row_count(path)
        count_validated = exists and row_count == expected_count
        rows.append(
            {
                "dependency_name": name,
                "dependency_artifact_path": str(path),
                "dependency_required_for_future_loader_shape_dry_run": True,
                "dependency_exists": exists,
                "dependency_row_count": row_count,
                "dependency_expected_row_count": expected_count,
                "dependency_count_validated": count_validated,
                "dependency_validation_status": "exists_and_count_validated"
                if count_validated
                else "missing_or_count_mismatch",
                "loader_execution_status": "not_executed",
                "training_use_status": "not_training_input_yet",
            }
        )
    return rows


def build_loader_shape_dry_run_shape_expectation_contract_v0() -> list[dict[str, Any]]:
    specs = [
        ("pocket_atom_coordinates", "protein_pocket", 2, "pocket_atom_count", "per_sample_variable", "floating"),
        ("pocket_atom_features", "protein_pocket", 2, "pocket_atom_count", "per_sample_variable", "numeric_or_categorical"),
        ("pocket_residue_features", "protein_pocket", 2, "pocket_atom_count", "per_sample_variable", "numeric_or_categorical"),
        ("ligand_atom_coordinates", "ligand", 2, "ligand_atom_count", "per_sample_variable", "floating"),
        ("ligand_atom_features", "ligand", 2, "ligand_atom_count", "per_sample_variable", "numeric_or_categorical"),
        ("ligand_bond_index", "ligand", 2, "ligand_bond_count", "per_sample_variable", "integer_index"),
        ("ligand_bond_features", "ligand", 2, "ligand_bond_count", "per_sample_variable", "numeric_or_categorical"),
        ("ligand_group_labels", "group_labels", 1, "ligand_atom_count", "per_sample_variable", "boolean_or_integer"),
        ("covalent_endpoint_atom_mask", "covalent_labels", 1, "ligand_atom_count", "per_sample_variable", "boolean"),
        ("reactive_residue_atom_coordinates", "covalent_labels", 1, "single_reactive_atom", "1", "floating"),
        ("canonical_mask_task_id_or_name", "mask_tasks", 1, "mask_task_count", "5", "string_or_integer"),
        ("auxiliary_warhead_type_label", "auxiliary_labels", 0, "sample", "1", "string_or_integer"),
        ("auxiliary_ligand_residue_atom_pair_label", "auxiliary_labels", 0, "sample", "1", "string_or_integer"),
        ("auxiliary_pre_post_geometry_label", "auxiliary_labels", 0, "sample", "1", "floating_or_categorical"),
    ]
    return [
        {
            "shape_item": item,
            "shape_group": group,
            "expected_rank": rank,
            "expected_first_dimension_source": first_dim_source,
            "expected_first_dimension_value": first_dim_value,
            "expected_dtype_family": dtype,
            "expected_shape_status": "declared_for_future_dry_run",
            "materialization_status": "design_only_not_tensorized",
            "validation_method_next_step": "loader_shape_dry_run_execution_smoke",
            "blocking_for_design_gate": False,
        }
        for item, group, rank, first_dim_source, first_dim_value, dtype in specs
    ]


def build_loader_shape_dry_run_execution_boundary_contract_v0() -> list[dict[str, Any]]:
    boundaries = [
        ("loader_instantiation", "allowed_only_for_shape_dry_run_execution_smoke", False, "Next step may instantiate only for shape inspection."),
        ("torch_tensor_creation", "allowed_only_for_shape_dry_run_execution_smoke", False, "Next step may create transient tensors only if required for shape inspection."),
        ("dataloader_modification", "forbidden_in_next_step", True, "Design and execution smoke must not edit dataloader code."),
        ("forward_call", "forbidden_in_next_step", True, "Shape dry run must not call model forward."),
        ("loss_compute", "forbidden_in_next_step", True, "Shape dry run must not compute loss."),
        ("backward_call", "forbidden_in_next_step", True, "Shape dry run must not run backward."),
        ("optimizer_creation", "forbidden_in_next_step", True, "Shape dry run must not create optimizers."),
        ("trainer_fit", "forbidden_in_next_step", True, "Shape dry run must not train."),
        ("checkpoint_save", "forbidden_in_next_step", True, "Shape dry run must not save checkpoints."),
        ("pt_npz_artifact_creation", "forbidden_in_next_step", True, "Shape dry run must not create persistent PT or NPZ artifacts."),
        ("rdkit_or_sdf_access", "forbidden_in_next_step", True, "Loader shape smoke must use existing CSV/JSON dependencies only."),
        ("raw_mmcif_access", "forbidden_in_next_step", True, "Raw structure parsing is outside this path."),
        ("training_claim", "forbidden_in_next_step", True, "No training readiness claim is allowed."),
        ("feature_semantics_audit", "remains_required_before_training", False, "Feature semantics audit remains required before formal training."),
    ]
    rows = []
    for item, allowed_next, forbidden_next, rationale in boundaries:
        rows.append(
            {
                "boundary_item": item,
                "current_step_status": "not_executed_or_not_allowed"
                if item != "feature_semantics_audit"
                else "required_before_training_not_completed",
                "allowed_next_step_status": allowed_next,
                "forbidden_current_step": item != "feature_semantics_audit",
                "forbidden_next_step": forbidden_next,
                "rationale": rationale,
            }
        )
    return rows


def build_loader_shape_dry_run_feature_semantics_boundary_v0() -> list[dict[str, Any]]:
    rows = []
    for row in _read_csv(STEP13W_FEATURE_STATUS_CSV):
        rows.append(
            {
                "feature_semantics_item": row["feature_semantics_item"],
                "feature_group": row["feature_group"],
                "current_status": row["current_status"],
                "audit_required_before_training": True,
                "fully_audited_claimed": False,
                "blocking_for_loader_shape_dry_run_design_gate": False,
                "blocking_for_loader_shape_dry_run_execution_smoke": False,
                "training_ready": False,
                "recommended_audit_step": row["recommended_audit_step"],
            }
        )
    return rows


def _input_rows_validated(rows: list[dict[str, Any]]) -> bool:
    expected_names = ";".join(CANONICAL_MASK_TASK_NAMES)
    expected_aliases = ";".join(CANONICAL_MASK_TASK_ALIASES)
    for idx, row in enumerate(rows):
        counts = EXPECTED_ATOM_BOND_COUNTS[row["review_row_id"]]
        if not (
            row["loader_shape_dry_run_sample_id"] == EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS[idx]
            and row["model_input_smoke_row_id"] == EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS[idx]
            and row["sample_index_row_id"] == EXPECTED_SAMPLE_INDEX_ROW_IDS[idx]
            and row["review_row_id"] == EXPECTED_REVIEW_ROW_IDS[idx]
            and row["pdb_id"] == EXPECTED_PDB_IDS[idx]
            and row["v1_train_ready_scope"] == V1_TRAIN_READY_SCOPE
            and row["residue_scope"] == DESIGN_SCOPE
            and row["residue_name"] == "CYS"
            and row["residue_atom_name"] == "SG"
            and row["ligand_atom_count"] == counts[0]
            and row["ligand_bond_count"] == counts[1]
            and row["endpoint_atom_count"] == 1
            and row["endpoint_touching_bond_count"] == 1
            and row["canonical_mask_task_names"] == expected_names
            and row["canonical_mask_task_aliases"] == expected_aliases
            and row["mask_task_count"] == 5
            and row["loader_shape_dry_run_input_status"] == "design_only_not_executed"
            and row["tensor_artifact_status"] == "not_written"
            and row["loader_execution_status"] == "not_executed"
            and row["forward_execution_status"] == "not_executed"
            and row["training_use_status"] == "not_training_input_yet"
            and _as_bool(row["feature_semantics_audit_required_before_training"])
        ):
            return False
    return len(rows) == 3


def build_real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0() -> dict[str, Any]:
    validate_step13x_precondition_v0()
    input_rows = build_loader_shape_dry_run_input_contract_v0()
    dependency_rows = build_loader_shape_dry_run_dependency_contract_v0()
    shape_rows = build_loader_shape_dry_run_shape_expectation_contract_v0()
    execution_rows = build_loader_shape_dry_run_execution_boundary_contract_v0()
    feature_rows = build_loader_shape_dry_run_feature_semantics_boundary_v0()

    all_loader_shape_dry_run_input_rows_validated = _input_rows_validated(input_rows)
    all_dependency_artifacts_exist = all(_as_bool(row["dependency_exists"]) for row in dependency_rows)
    all_dependency_counts_validated = all(_as_bool(row["dependency_count_validated"]) for row in dependency_rows)
    all_shape_expectations_declared = (
        len(shape_rows) >= 14
        and all(row["expected_shape_status"] == "declared_for_future_dry_run" for row in shape_rows)
        and all(row["validation_method_next_step"] == "loader_shape_dry_run_execution_smoke" for row in shape_rows)
    )
    no_shape_claimed_executed_or_tensorized = all(
        row["materialization_status"] == "design_only_not_tensorized" and not _as_bool(row["blocking_for_design_gate"])
        for row in shape_rows
    )
    all_execution_boundaries_validated = (
        len(execution_rows) >= 14
        and all(_as_bool(row["forbidden_current_step"]) for row in execution_rows if row["boundary_item"] != "feature_semantics_audit")
        and all(
            _as_bool(row["forbidden_next_step"])
            for row in execution_rows
            if row["boundary_item"]
            in {
                "dataloader_modification",
                "forward_call",
                "loss_compute",
                "backward_call",
                "optimizer_creation",
                "trainer_fit",
                "checkpoint_save",
                "pt_npz_artifact_creation",
                "training_claim",
            }
        )
    )
    all_feature_semantics_audit_required_before_training = all(
        _as_bool(row["audit_required_before_training"]) for row in feature_rows
    )
    no_feature_semantics_claimed_fully_audited = all(
        not _as_bool(row["fully_audited_claimed"]) for row in feature_rows
    )
    loader_shape_dry_run_design_gate_passed = all(
        [
            all_loader_shape_dry_run_input_rows_validated,
            all_dependency_artifacts_exist,
            all_dependency_counts_validated,
            all_shape_expectations_declared,
            no_shape_claimed_executed_or_tensorized,
            all_execution_boundaries_validated,
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
    all_checks_passed = loader_shape_dry_run_design_gate_passed and safety_ok
    blocking_reasons = []
    if not loader_shape_dry_run_design_gate_passed:
        blocking_reasons.append("loader_shape_dry_run_design_gate_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13x_model_input_qa_gate_validated": True,
        "loader_shape_dry_run_design_scope": DESIGN_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "loader_shape_dry_run_input_contract_written": True,
        "loader_shape_dry_run_input_contract_row_count": len(input_rows),
        "loader_shape_dry_run_dependency_contract_written": True,
        "loader_shape_dry_run_dependency_contract_row_count": len(dependency_rows),
        "loader_shape_dry_run_shape_expectation_contract_written": True,
        "loader_shape_dry_run_shape_expectation_contract_row_count": len(shape_rows),
        "loader_shape_dry_run_execution_boundary_contract_written": True,
        "loader_shape_dry_run_execution_boundary_contract_row_count": len(execution_rows),
        "loader_shape_dry_run_feature_semantics_boundary_written": True,
        "loader_shape_dry_run_feature_semantics_boundary_row_count": len(feature_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_loader_shape_dry_run_input_rows_validated": all_loader_shape_dry_run_input_rows_validated,
        "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        "all_dependency_counts_validated": all_dependency_counts_validated,
        "all_shape_expectations_declared": all_shape_expectations_declared,
        "no_shape_claimed_executed_or_tensorized": no_shape_claimed_executed_or_tensorized,
        "all_execution_boundaries_validated": all_execution_boundaries_validated,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "loader_shape_dry_run_design_gate_passed": loader_shape_dry_run_design_gate_passed,
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
        "loader_instantiated": False,
        "torch_tensor_created": False,
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
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "loader_shape_dry_run_performed": False,
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": _source_diff_exists(),
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "ready_for_loader_shape_dry_run_execution_smoke": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13x_precondition": {"validated": True, "model_input_qa_passed": True},
        "input_contract": {"row_count": len(input_rows), "all_loader_shape_dry_run_input_rows_validated": all_loader_shape_dry_run_input_rows_validated},
        "dependency_contract": {"row_count": len(dependency_rows), "all_dependency_counts_validated": all_dependency_counts_validated},
        "shape_expectation_contract": {"row_count": len(shape_rows), "all_shape_expectations_declared": all_shape_expectations_declared},
        "execution_boundary_contract": {"row_count": len(execution_rows), "all_execution_boundaries_validated": all_execution_boundaries_validated},
        "feature_semantics_boundary": {"row_count": len(feature_rows), "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training},
        "readiness_boundary": {"ready_for_loader_shape_dry_run_execution_smoke": True, "ready_for_training": False},
    }
    return {
        "input_rows": input_rows,
        "dependency_rows": dependency_rows,
        "shape_rows": shape_rows,
        "execution_rows": execution_rows,
        "feature_rows": feature_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

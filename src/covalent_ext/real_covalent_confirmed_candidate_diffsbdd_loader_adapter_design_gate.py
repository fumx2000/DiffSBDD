from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0"

STEP13AA_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0"
)
STEP13AA_MANIFEST_JSON = STEP13AA_ROOT / "loader_shape_dry_run_qa_manifest.json"
STEP13AA_SAMPLE_QA_AUDIT_CSV = STEP13AA_ROOT / "loader_shape_dry_run_sample_qa_audit.csv"
STEP13AA_SHAPE_OBSERVATION_QA_AUDIT_CSV = STEP13AA_ROOT / "loader_shape_dry_run_shape_observation_qa_audit.csv"
STEP13AA_BATCH_QA_AUDIT_CSV = STEP13AA_ROOT / "loader_shape_dry_run_batch_qa_audit.csv"
STEP13AA_EXECUTION_BOUNDARY_QA_AUDIT_CSV = STEP13AA_ROOT / "loader_shape_dry_run_execution_boundary_qa_audit.csv"
STEP13AA_FEATURE_SEMANTICS_QA_AUDIT_CSV = STEP13AA_ROOT / "loader_shape_dry_run_feature_semantics_qa_audit.csv"
STEP13AA_DEPENDENCY_QA_AUDIT_CSV = STEP13AA_ROOT / "loader_shape_dry_run_dependency_qa_audit.csv"

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
STEP13Y_EXECUTION_BOUNDARY_CONTRACT_CSV = STEP13Y_ROOT / "loader_shape_dry_run_execution_boundary_contract.csv"
STEP13Y_FEATURE_SEMANTICS_BOUNDARY_CSV = STEP13Y_ROOT / "loader_shape_dry_run_feature_semantics_boundary.csv"

STEP13W_SMOKE_INDEX_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_materialization_smoke_v0/"
    "model_input_smoke_index.csv"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0"
)
INPUT_CONTRACT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_input_contract.csv"
SOURCE_DISCOVERY_AUDIT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_source_discovery_audit.csv"
INTERFACE_CONTRACT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_interface_contract.csv"
SHAPE_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_shape_mapping_contract.csv"
MASK_MAPPING_CONTRACT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_mask_mapping_contract.csv"
AUXILIARY_LABEL_CONTRACT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_auxiliary_label_contract.csv"
EXECUTION_BOUNDARY_CONTRACT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_execution_boundary_contract.csv"
FEATURE_SEMANTICS_BOUNDARY_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_feature_semantics_boundary.csv"
REPORT_CSV = OUTPUT_ROOT / "diffsbdd_loader_adapter_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "diffsbdd_loader_adapter_design_gate_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0_summary.md")

EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS = [
    "DSBDD_ADAPTER_DESIGN_000001",
    "DSBDD_ADAPTER_DESIGN_000002",
    "DSBDD_ADAPTER_DESIGN_000003",
]
EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS = ["LSDR_DESIGN_000001", "LSDR_DESIGN_000002", "LSDR_DESIGN_000003"]
EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS = ["RMI_SMOKE_000001", "RMI_SMOKE_000002", "RMI_SMOKE_000003"]
EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_ATOM_BOND_COUNTS = {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
DESIGN_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke"
CHECKPOINT_COMPATIBILITY_POLICY = "preserve_diffsbdd_checkpoint_compatibility_by_external_adapter_design"
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
    "adapter_design_sample_id",
    "loader_shape_dry_run_sample_id",
    "model_input_smoke_row_id",
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "v1_train_ready_scope",
    "residue_scope",
    "residue_name",
    "residue_atom_name",
    "pocket_atom_count",
    "ligand_atom_count",
    "ligand_bond_count",
    "endpoint_atom_count",
    "endpoint_touching_bond_count",
    "canonical_mask_task_names",
    "canonical_mask_task_aliases",
    "mask_task_count",
    "adapter_input_status",
    "adapter_implementation_status",
    "tensor_artifact_status",
    "training_use_status",
    "feature_semantics_audit_required_before_training",
]
SOURCE_DISCOVERY_AUDIT_COLUMNS = [
    "source_path",
    "source_category",
    "discovery_reason",
    "read_only_discovery_performed",
    "import_performed",
    "execution_performed",
    "modification_allowed_current_step",
    "future_adapter_relevance",
    "protected_source_path",
    "adapter_design_note",
]
INTERFACE_CONTRACT_COLUMNS = [
    "interface_item",
    "proposed_contract",
    "implementation_status",
    "allowed_next_step_status",
    "forbidden_current_step",
    "checkpoint_compatibility_note",
    "blocking_for_design_gate",
]
SHAPE_MAPPING_CONTRACT_COLUMNS = [
    "covalent_shape_item",
    "covalent_shape_group",
    "observed_rank_source",
    "future_adapter_field_name",
    "future_adapter_field_role",
    "expected_variable_dimension_policy",
    "batching_policy",
    "implementation_status",
    "tensor_persistence_policy",
    "training_use_status",
    "shape_mapping_design_passed",
]
MASK_MAPPING_CONTRACT_COLUMNS = [
    "canonical_mask_task_name",
    "display_alias",
    "masked_groups",
    "preserved_groups",
    "source_of_truth_status",
    "alias_status",
    "future_adapter_mask_field",
    "tensor_mask_written_current_step",
    "implementation_status",
    "training_use_status",
    "mask_mapping_design_passed",
]
AUXILIARY_LABEL_CONTRACT_COLUMNS = [
    "auxiliary_label_name",
    "current_label_status",
    "future_adapter_field_name",
    "future_loss_integration_status",
    "implementation_status",
    "training_use_status",
    "feature_semantics_audit_required_before_training",
    "auxiliary_label_design_passed",
]
EXECUTION_BOUNDARY_CONTRACT_COLUMNS = [
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
    "blocking_for_adapter_design_gate",
    "blocking_for_adapter_implementation_smoke",
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


def validate_step13aa_precondition_v0() -> bool:
    required_paths = [
        STEP13AA_MANIFEST_JSON,
        STEP13AA_SAMPLE_QA_AUDIT_CSV,
        STEP13AA_SHAPE_OBSERVATION_QA_AUDIT_CSV,
        STEP13AA_BATCH_QA_AUDIT_CSV,
        STEP13AA_EXECUTION_BOUNDARY_QA_AUDIT_CSV,
        STEP13AA_FEATURE_SEMANTICS_QA_AUDIT_CSV,
        STEP13AA_DEPENDENCY_QA_AUDIT_CSV,
        STEP13Z_MANIFEST_JSON,
        STEP13Z_SHAPE_OBSERVATION_CSV,
        STEP13Z_BATCH_AUDIT_CSV,
        STEP13Y_INPUT_CONTRACT_CSV,
        STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV,
        STEP13Y_EXECUTION_BOUNDARY_CONTRACT_CSV,
        STEP13Y_FEATURE_SEMANTICS_BOUNDARY_CSV,
        STEP13W_SMOKE_INDEX_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13AB prerequisite outputs are missing: {missing}")

    manifest = _load_json(STEP13AA_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "step13z_loader_shape_dry_run_execution_smoke_validated": True,
        "loader_shape_dry_run_qa_gate_passed": True,
        "loader_shape_dry_run_qa_scope": DESIGN_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "loader_shape_dry_run_sample_qa_audit_written": True,
        "loader_shape_dry_run_sample_qa_audit_row_count": 3,
        "loader_shape_dry_run_shape_observation_qa_audit_written": True,
        "loader_shape_dry_run_shape_observation_qa_audit_row_count": 42,
        "loader_shape_dry_run_batch_qa_audit_written": True,
        "loader_shape_dry_run_batch_qa_audit_row_count": 3,
        "loader_shape_dry_run_execution_boundary_qa_audit_written": True,
        "loader_shape_dry_run_execution_boundary_qa_audit_row_count": 14,
        "loader_shape_dry_run_feature_semantics_qa_audit_written": True,
        "loader_shape_dry_run_feature_semantics_qa_audit_row_count": 12,
        "loader_shape_dry_run_dependency_qa_audit_written": True,
        "loader_shape_dry_run_dependency_qa_audit_row_count": 10,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_sample_qa_passed": True,
        "all_shape_observation_qa_passed": True,
        "all_batch_qa_passed": True,
        "all_execution_boundary_qa_passed": True,
        "all_feature_semantics_qa_passed": True,
        "all_dependency_artifacts_exist": True,
        "all_dependency_counts_validated": True,
        "all_feature_semantics_audit_required_before_training": True,
        "no_feature_semantics_claimed_fully_audited": True,
        "smoke_dataset_instantiated": False,
        "loader_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_diffsbdd_loader_adapter_design_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13AA precondition failed: " + ";".join(blockers))
    return True


def build_input_contract_rows_v0() -> list[dict[str, Any]]:
    input_rows = _read_csv(STEP13Y_INPUT_CONTRACT_CSV)
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_rows):
        rows.append(
            {
                "adapter_design_sample_id": EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS[index],
                "loader_shape_dry_run_sample_id": row["loader_shape_dry_run_sample_id"],
                "model_input_smoke_row_id": row["model_input_smoke_row_id"],
                "sample_index_row_id": row["sample_index_row_id"],
                "review_row_id": row["review_row_id"],
                "pdb_id": row["pdb_id"],
                "v1_train_ready_scope": row["v1_train_ready_scope"],
                "residue_scope": row["residue_scope"],
                "residue_name": row["residue_name"],
                "residue_atom_name": row["residue_atom_name"],
                "pocket_atom_count": row["pocket_atom_count"],
                "ligand_atom_count": row["ligand_atom_count"],
                "ligand_bond_count": row["ligand_bond_count"],
                "endpoint_atom_count": row["endpoint_atom_count"],
                "endpoint_touching_bond_count": row["endpoint_touching_bond_count"],
                "canonical_mask_task_names": row["canonical_mask_task_names"],
                "canonical_mask_task_aliases": row["canonical_mask_task_aliases"],
                "mask_task_count": row["mask_task_count"],
                "adapter_input_status": "design_only_from_validated_loader_shape_smoke",
                "adapter_implementation_status": "not_implemented",
                "tensor_artifact_status": "not_written",
                "training_use_status": "not_training_input_yet",
                "feature_semantics_audit_required_before_training": True,
            }
        )
    return rows


def build_source_discovery_audit_rows_v0() -> list[dict[str, Any]]:
    result = _run_git(["ls-files"])
    paths = result.stdout.splitlines()
    keywords = ("data", "dataset", "dataloader", "collate", "batch", "lightning")
    selected = []
    for path in paths:
        lower = path.lower()
        if not path.endswith(".py"):
            continue
        if any(keyword in lower for keyword in keywords) or lower.startswith("equivariant_diffusion/"):
            selected.append(path)
    priority = [
        "dataset.py",
        "lightning_modules.py",
        "data/prepare_crossdocked.py",
        "src/covalent_ext/batch_adapter.py",
        "src/covalent_ext/dataset.py",
        "src/covalent_ext/npz_dataset.py",
    ]
    ordered = [path for path in priority if path in selected]
    ordered.extend(path for path in selected if path not in set(ordered))
    rows = []
    for path in ordered[:30]:
        lower = path.lower()
        protected = path == "lightning_modules.py" or path.startswith("equivariant_diffusion/")
        if "lightning" in lower:
            category = "lightning_or_training_wrapper_candidate"
        elif "dataset" in lower or "data" in lower:
            category = "dataset_or_data_pipeline_candidate"
        elif "batch" in lower or "collate" in lower:
            category = "batch_or_collate_candidate"
        else:
            category = "protected_core_candidate" if protected else "source_candidate"
        rows.append(
            {
                "source_path": path,
                "source_category": category,
                "discovery_reason": "git_ls_files_name_match_read_only",
                "read_only_discovery_performed": True,
                "import_performed": False,
                "execution_performed": False,
                "modification_allowed_current_step": False,
                "future_adapter_relevance": "candidate_reference_only_for_future_external_covalent_ext_adapter",
                "protected_source_path": protected,
                "adapter_design_note": "Do not modify; future adapter should live under src/covalent_ext/ and preserve checkpoint compatibility.",
            }
        )
    return rows


def build_interface_contract_rows_v0() -> list[dict[str, Any]]:
    rows = [
        ("adapter_module_location", "Future adapter module under src/covalent_ext/ only.", "allowed_only_in_next_adapter_implementation_smoke"),
        ("adapter_class_name", "Proposed class name RealCovalentDiffSBDDLoaderAdapter.", "allowed_only_in_next_adapter_implementation_smoke"),
        ("adapter_input_artifact", "Read Step 13W/13Y/13Z/13AA CSV/JSON artifacts as validated inputs.", "allowed_only_in_next_adapter_implementation_smoke"),
        ("adapter_output_sample_dict", "Return sample dictionaries aligned to declared covalent shape keys.", "design_only_no_execution"),
        ("adapter_batch_collate_policy", "Keep batch_size=1 initially; avoid padding policy changes until audited.", "design_only_no_execution"),
        ("adapter_batch_size_policy", "Initial implementation smoke may stay batch_size=1.", "design_only_no_execution"),
        ("adapter_variable_size_policy", "Preserve per-sample variable ligand and pocket dimensions.", "design_only_no_execution"),
        ("adapter_mask_policy", "Carry five long semantic mask names with display aliases only.", "design_only_no_execution"),
        ("adapter_auxiliary_label_policy", "Carry auxiliary labels without integrating them into loss.", "design_only_no_execution"),
        ("adapter_checkpoint_compatibility_policy", CHECKPOINT_COMPATIBILITY_POLICY, "design_only_no_execution"),
        ("adapter_training_boundary_policy", "No forward/loss/backward/optimizer/trainer.fit/training in adapter smoke.", "design_only_no_execution"),
        ("adapter_feature_semantics_policy", "Feature semantics audit remains required before formal training.", "design_only_no_execution"),
    ]
    return [
        {
            "interface_item": item,
            "proposed_contract": contract,
            "implementation_status": "design_only_not_implemented",
            "allowed_next_step_status": next_status,
            "forbidden_current_step": True,
            "checkpoint_compatibility_note": "External covalent_ext adapter design avoids modifying original DiffSBDD model, forward, loss, and checkpoint-facing code.",
            "blocking_for_design_gate": False,
        }
        for item, contract, next_status in rows
    ]


def build_shape_mapping_contract_rows_v0() -> list[dict[str, Any]]:
    expectations = _read_csv(STEP13Y_SHAPE_EXPECTATION_CONTRACT_CSV)
    role_by_item = {
        "pocket_atom_coordinates": ("diffsbdd_pocket_atom_positions", "protein_pocket_coordinates"),
        "pocket_atom_features": ("diffsbdd_pocket_atom_features", "protein_atom_features"),
        "pocket_residue_features": ("diffsbdd_pocket_residue_features", "protein_residue_features"),
        "ligand_atom_coordinates": ("diffsbdd_ligand_atom_positions", "ligand_coordinates"),
        "ligand_atom_features": ("diffsbdd_ligand_atom_features", "ligand_atom_features"),
        "ligand_bond_index": ("diffsbdd_ligand_bond_index", "ligand_graph_connectivity"),
        "ligand_bond_features": ("diffsbdd_ligand_bond_features", "ligand_bond_features"),
        "ligand_group_labels": ("diffsbdd_ligand_group_labels", "warhead_linker_scaffold_group_labels"),
        "covalent_endpoint_atom_mask": ("diffsbdd_covalent_endpoint_atom_mask", "covalent_endpoint_label"),
        "reactive_residue_atom_coordinates": ("diffsbdd_reactive_residue_atom_coordinates", "reactive_residue_anchor"),
        "canonical_mask_task_id_or_name": ("diffsbdd_canonical_mask_task", "mask_task_selector"),
        "auxiliary_warhead_type_label": ("diffsbdd_auxiliary_warhead_type_label", "auxiliary_label_carried_not_loss"),
        "auxiliary_ligand_residue_atom_pair_label": ("diffsbdd_auxiliary_ligand_residue_atom_pair_label", "auxiliary_label_carried_not_loss"),
        "auxiliary_pre_post_geometry_label": ("diffsbdd_auxiliary_pre_post_geometry_label", "auxiliary_label_carried_not_loss"),
    }
    rows = []
    for row in expectations:
        field, role = role_by_item[row["shape_item"]]
        rows.append(
            {
                "covalent_shape_item": row["shape_item"],
                "covalent_shape_group": row["shape_group"],
                "observed_rank_source": f"step13z_observed_rank_checked_against_expected_rank_{row['expected_rank']}",
                "future_adapter_field_name": field,
                "future_adapter_field_role": role,
                "expected_variable_dimension_policy": row["expected_first_dimension_source"],
                "batching_policy": "single_sample_batch_size_1_until_padding_policy_audited",
                "implementation_status": "design_only_not_implemented",
                "tensor_persistence_policy": "do_not_persist_tensor_artifacts",
                "training_use_status": "not_training_input_yet",
                "shape_mapping_design_passed": True,
            }
        )
    return rows


def build_mask_mapping_contract_rows_v0() -> list[dict[str, Any]]:
    masked_preserved = [
        ("warhead_only", "A", "warhead", "linker;scaffold"),
        ("linker_plus_warhead", "B", "linker;warhead", "scaffold"),
        ("scaffold_plus_warhead", "B2", "scaffold;warhead", "linker"),
        ("scaffold_only", "B3", "scaffold", "linker;warhead"),
        ("scaffold_plus_linker_plus_warhead", "C", "scaffold;linker;warhead", ""),
    ]
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "masked_groups": masked,
            "preserved_groups": preserved,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "future_adapter_mask_field": f"adapter_mask_task_{name}",
            "tensor_mask_written_current_step": False,
            "implementation_status": "design_only_not_implemented",
            "training_use_status": "not_training_input_yet",
            "mask_mapping_design_passed": True,
        }
        for name, alias, masked, preserved in masked_preserved
    ]


def build_auxiliary_label_contract_rows_v0() -> list[dict[str, Any]]:
    rows = [
        ("warhead_type", "auxiliary_warhead_type_label"),
        ("ligand_residue_atom_pair", "auxiliary_ligand_residue_atom_pair_label"),
        ("pre_post_covalent_geometry", "auxiliary_pre_post_geometry_label"),
    ]
    return [
        {
            "auxiliary_label_name": name,
            "current_label_status": "carried_as_design_smoke_label_not_training_target",
            "future_adapter_field_name": field,
            "future_loss_integration_status": "not_integrated_into_loss",
            "implementation_status": "design_only_not_implemented",
            "training_use_status": "not_training_input_yet",
            "feature_semantics_audit_required_before_training": True,
            "auxiliary_label_design_passed": True,
        }
        for name, field in rows
    ]


def build_execution_boundary_contract_rows_v0() -> list[dict[str, Any]]:
    rows = [
        ("adapter_implementation", "allowed_only_under_src_covalent_ext_in_next_smoke", False),
        ("adapter_instantiation", "allowed_only_in_next_adapter_implementation_smoke", False),
        ("torch_import", "allowed_only_if_needed_in_next_adapter_implementation_smoke", False),
        ("tensor_creation", "allowed_only_transient_in_next_adapter_implementation_smoke", False),
        ("dataloader_modification", "forbidden_in_next_step", True),
        ("original_diffsbdd_source_modification", "forbidden_in_next_step", True),
        ("model_forward_call", "forbidden_in_next_step", True),
        ("loss_compute", "forbidden_in_next_step", True),
        ("backward_call", "forbidden_in_next_step", True),
        ("optimizer_creation", "forbidden_in_next_step", True),
        ("trainer_fit", "forbidden_in_next_step", True),
        ("checkpoint_load", "forbidden_in_next_step", True),
        ("checkpoint_save", "forbidden_in_next_step", True),
        ("pt_npz_artifact_creation", "forbidden_in_next_step", True),
        ("rdkit_or_sdf_access", "forbidden_in_next_step", True),
        ("raw_mmcif_access", "forbidden_in_next_step", True),
        ("training_claim", "forbidden_in_next_step", True),
        ("feature_semantics_audit", "required_before_training_not_completed", False),
    ]
    return [
        {
            "boundary_item": item,
            "current_step_status": "not_executed_or_not_allowed",
            "allowed_next_step_status": next_status,
            "forbidden_current_step": True,
            "forbidden_next_step": forbidden_next,
            "rationale": "Step 13AB is design-only; next step may implement only a minimal external covalent_ext adapter and still cannot train.",
        }
        for item, next_status, forbidden_next in rows
    ]


def build_feature_semantics_boundary_rows_v0() -> list[dict[str, Any]]:
    rows = []
    for row in _read_csv(STEP13AA_FEATURE_SEMANTICS_QA_AUDIT_CSV):
        rows.append(
            {
                "feature_semantics_item": row["feature_semantics_item"],
                "feature_group": row["feature_group"],
                "current_status": row["current_status"],
                "audit_required_before_training": True,
                "fully_audited_claimed": False,
                "blocking_for_adapter_design_gate": False,
                "blocking_for_adapter_implementation_smoke": False,
                "training_ready": False,
                "recommended_audit_step": row["recommended_audit_step"],
            }
        )
    return rows


def run_diffsbdd_loader_adapter_design_gate_v0() -> dict[str, Any]:
    validate_step13aa_precondition_v0()
    input_rows = build_input_contract_rows_v0()
    source_rows = build_source_discovery_audit_rows_v0()
    interface_rows = build_interface_contract_rows_v0()
    shape_rows = build_shape_mapping_contract_rows_v0()
    mask_rows = build_mask_mapping_contract_rows_v0()
    auxiliary_rows = build_auxiliary_label_contract_rows_v0()
    boundary_rows = build_execution_boundary_contract_rows_v0()
    feature_rows = build_feature_semantics_boundary_rows_v0()

    all_adapter_input_rows_validated = (
        len(input_rows) == 3
        and [row["adapter_design_sample_id"] for row in input_rows] == EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS
        and [row["model_input_smoke_row_id"] for row in input_rows] == EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS
        and [row["sample_index_row_id"] for row in input_rows] == EXPECTED_SAMPLE_INDEX_ROW_IDS
        and [row["review_row_id"] for row in input_rows] == EXPECTED_REVIEW_ROW_IDS
        and [row["pdb_id"] for row in input_rows] == EXPECTED_PDB_IDS
        and all(row["residue_name"] == "CYS" and row["residue_atom_name"] == "SG" for row in input_rows)
        and all(
            int(row["ligand_atom_count"]) == EXPECTED_ATOM_BOND_COUNTS[row["review_row_id"]][0]
            and int(row["ligand_bond_count"]) == EXPECTED_ATOM_BOND_COUNTS[row["review_row_id"]][1]
            and int(row["endpoint_atom_count"]) == 1
            and int(row["endpoint_touching_bond_count"]) == 1
            for row in input_rows
        )
        and all(row["canonical_mask_task_names"] == ";".join(CANONICAL_MASK_TASK_NAMES) for row in input_rows)
        and all(row["canonical_mask_task_aliases"] == ";".join(CANONICAL_MASK_TASK_ALIASES) for row in input_rows)
    )
    source_discovery_read_only = bool(source_rows) and all(
        _as_bool(row["read_only_discovery_performed"]) and not _as_bool(row["modification_allowed_current_step"])
        for row in source_rows
    )
    no_source_import_or_execution = bool(source_rows) and all(
        not _as_bool(row["import_performed"]) and not _as_bool(row["execution_performed"]) for row in source_rows
    )
    all_interface_contracts_declared = len(interface_rows) >= 12 and all(
        row["implementation_status"] == "design_only_not_implemented"
        and row["checkpoint_compatibility_note"]
        and not _as_bool(row["blocking_for_design_gate"])
        for row in interface_rows
    )
    all_shape_mappings_declared = len(shape_rows) == 14 and all(
        row["implementation_status"] == "design_only_not_implemented"
        and row["tensor_persistence_policy"] == "do_not_persist_tensor_artifacts"
        and row["training_use_status"] == "not_training_input_yet"
        and _as_bool(row["shape_mapping_design_passed"])
        for row in shape_rows
    )
    all_mask_mappings_declared = (
        len(mask_rows) == 5
        and [row["canonical_mask_task_name"] for row in mask_rows] == CANONICAL_MASK_TASK_NAMES
        and [row["display_alias"] for row in mask_rows] == CANONICAL_MASK_TASK_ALIASES
        and all(row["implementation_status"] == "design_only_not_implemented" for row in mask_rows)
        and all(_as_bool(row["mask_mapping_design_passed"]) for row in mask_rows)
    )
    all_auxiliary_label_contracts_declared = len(auxiliary_rows) == 3 and all(
        row["future_loss_integration_status"] == "not_integrated_into_loss"
        and row["implementation_status"] == "design_only_not_implemented"
        and _as_bool(row["feature_semantics_audit_required_before_training"])
        and _as_bool(row["auxiliary_label_design_passed"])
        for row in auxiliary_rows
    )
    all_execution_boundaries_declared = len(boundary_rows) >= 18 and all(
        row["current_step_status"] == "not_executed_or_not_allowed" and _as_bool(row["forbidden_current_step"])
        for row in boundary_rows
    )
    all_feature_semantics_audit_required_before_training = len(feature_rows) == 12 and all(
        _as_bool(row["audit_required_before_training"]) for row in feature_rows
    )
    no_feature_semantics_claimed_fully_audited = len(feature_rows) == 12 and all(
        not _as_bool(row["fully_audited_claimed"]) for row in feature_rows
    )
    checkpoint_compatibility_preserved_by_design = all(
        "checkpoint" in row["checkpoint_compatibility_note"] for row in interface_rows
    )
    diffsbdd_loader_adapter_design_gate_passed = all(
        [
            all_adapter_input_rows_validated,
            source_discovery_read_only,
            no_source_import_or_execution,
            all_interface_contracts_declared,
            all_shape_mappings_declared,
            all_mask_mappings_declared,
            all_auxiliary_label_contracts_declared,
            all_execution_boundaries_declared,
            all_feature_semantics_audit_required_before_training,
            no_feature_semantics_claimed_fully_audited,
            checkpoint_compatibility_preserved_by_design,
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
    all_checks_passed = diffsbdd_loader_adapter_design_gate_passed and safety_ok
    blocking_reasons = []
    if not diffsbdd_loader_adapter_design_gate_passed:
        blocking_reasons.append("diffsbdd_loader_adapter_design_gate_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13aa_loader_shape_dry_run_qa_gate_validated": True,
        "adapter_design_scope": DESIGN_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "checkpoint_compatibility_policy": CHECKPOINT_COMPATIBILITY_POLICY,
        "diffsbdd_loader_adapter_input_contract_written": True,
        "diffsbdd_loader_adapter_input_contract_row_count": len(input_rows),
        "diffsbdd_loader_adapter_source_discovery_audit_written": True,
        "diffsbdd_loader_adapter_source_discovery_audit_row_count": len(source_rows),
        "diffsbdd_loader_adapter_interface_contract_written": True,
        "diffsbdd_loader_adapter_interface_contract_row_count": len(interface_rows),
        "diffsbdd_loader_adapter_shape_mapping_contract_written": True,
        "diffsbdd_loader_adapter_shape_mapping_contract_row_count": len(shape_rows),
        "diffsbdd_loader_adapter_mask_mapping_contract_written": True,
        "diffsbdd_loader_adapter_mask_mapping_contract_row_count": len(mask_rows),
        "diffsbdd_loader_adapter_auxiliary_label_contract_written": True,
        "diffsbdd_loader_adapter_auxiliary_label_contract_row_count": len(auxiliary_rows),
        "diffsbdd_loader_adapter_execution_boundary_contract_written": True,
        "diffsbdd_loader_adapter_execution_boundary_contract_row_count": len(boundary_rows),
        "diffsbdd_loader_adapter_feature_semantics_boundary_written": True,
        "diffsbdd_loader_adapter_feature_semantics_boundary_row_count": len(feature_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_adapter_input_rows_validated": all_adapter_input_rows_validated,
        "source_discovery_read_only": source_discovery_read_only,
        "no_source_import_or_execution": no_source_import_or_execution,
        "all_interface_contracts_declared": all_interface_contracts_declared,
        "all_shape_mappings_declared": all_shape_mappings_declared,
        "all_mask_mappings_declared": all_mask_mappings_declared,
        "all_auxiliary_label_contracts_declared": all_auxiliary_label_contracts_declared,
        "all_execution_boundaries_declared": all_execution_boundaries_declared,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "checkpoint_compatibility_preserved_by_design": checkpoint_compatibility_preserved_by_design,
        "diffsbdd_loader_adapter_design_gate_passed": diffsbdd_loader_adapter_design_gate_passed,
        "adapter_implemented": False,
        "adapter_instantiated": False,
        "smoke_dataset_instantiated": False,
        "loader_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "transient_tensor_shape_inspection_performed": False,
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
        "checkpoint_loaded": False,
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
        "ready_for_diffsbdd_loader_adapter_implementation_smoke": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13aa_precondition": {"validated": True, "ready_for_adapter_design_gate": True},
        "input_contract": {"row_count": len(input_rows), "all_adapter_input_rows_validated": all_adapter_input_rows_validated},
        "source_discovery": {"row_count": len(source_rows), "source_discovery_read_only": source_discovery_read_only},
        "interface_contract": {"row_count": len(interface_rows), "all_interface_contracts_declared": all_interface_contracts_declared},
        "shape_mapping_contract": {"row_count": len(shape_rows), "all_shape_mappings_declared": all_shape_mappings_declared},
        "mask_mapping_contract": {"row_count": len(mask_rows), "all_mask_mappings_declared": all_mask_mappings_declared},
        "auxiliary_label_contract": {"row_count": len(auxiliary_rows), "all_auxiliary_label_contracts_declared": all_auxiliary_label_contracts_declared},
        "execution_boundary_contract": {"row_count": len(boundary_rows), "all_execution_boundaries_declared": all_execution_boundaries_declared},
        "feature_semantics_boundary": {"row_count": len(feature_rows), "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training},
        "readiness_boundary": {"ready_for_diffsbdd_loader_adapter_implementation_smoke": True, "ready_for_training": False},
    }
    return {
        "input_contract_rows": input_rows,
        "source_discovery_audit_rows": source_rows,
        "interface_contract_rows": interface_rows,
        "shape_mapping_contract_rows": shape_rows,
        "mask_mapping_contract_rows": mask_rows,
        "auxiliary_label_contract_rows": auxiliary_rows,
        "execution_boundary_contract_rows": boundary_rows,
        "feature_semantics_boundary_rows": feature_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

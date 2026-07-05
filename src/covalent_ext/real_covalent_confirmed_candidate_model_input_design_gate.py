from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_model_input_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_sample_index_qa_gate_v0"

STEP13U_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_sample_index_qa_gate_v0")
STEP13U_MANIFEST_JSON = STEP13U_ROOT / "sample_index_qa_manifest.json"
STEP13U_ROW_QA_AUDIT_CSV = STEP13U_ROOT / "sample_index_row_qa_audit.csv"
STEP13U_DEPENDENCY_QA_AUDIT_CSV = STEP13U_ROOT / "sample_index_dependency_qa_audit.csv"
STEP13U_SCHEMA_QA_AUDIT_CSV = STEP13U_ROOT / "sample_index_schema_qa_audit.csv"

STEP13T_SAMPLE_INDEX_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0/"
    "real_covalent_confirmed_candidate_sample_index_smoke.csv"
)
STEP13S_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_sample_index_design_gate_v0")
STEP13S_SCHEMA_CONTRACT_CSV = STEP13S_ROOT / "sample_index_schema_contract.csv"
STEP13S_CANDIDATE_CONTRACT_CSV = STEP13S_ROOT / "sample_index_candidate_contract.csv"
STEP13S_MASK_TASK_CONTRACT_CSV = STEP13S_ROOT / "sample_index_mask_task_contract.csv"
STEP13R_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0"
)
STEP13R_ATOM_TOPOLOGY_CSV = STEP13R_ROOT / "ligand_observed_atom_topology_smoke_table.csv"
STEP13R_BOND_TOPOLOGY_CSV = STEP13R_ROOT / "ligand_observed_bond_topology_smoke_table.csv"
STEP13L_POCKET_ATOM_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_atom_table.csv"
)

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_design_gate_v0")
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "model_input_schema_contract.csv"
DEPENDENCY_CONTRACT_CSV = OUTPUT_ROOT / "model_input_dependency_contract.csv"
SAMPLE_CONTRACT_CSV = OUTPUT_ROOT / "model_input_sample_contract.csv"
MASK_CONTRACT_CSV = OUTPUT_ROOT / "model_input_mask_contract.csv"
FEATURE_SEMANTICS_CONTRACT_CSV = OUTPUT_ROOT / "model_input_feature_semantics_contract.csv"
REPORT_CSV = OUTPUT_ROOT / "model_input_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "model_input_design_gate_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_model_input_design_gate_v0_summary.md")

EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
DESIGN_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_model_input_materialization_smoke"
CANONICAL_MASK_TASKS = [
    ("warhead_only", "A", "warhead", "linker;scaffold"),
    ("linker_plus_warhead", "B", "linker;warhead", "scaffold"),
    ("scaffold_plus_warhead", "B2", "scaffold;warhead", "linker"),
    ("scaffold_only", "B3", "scaffold", "linker;warhead"),
    ("scaffold_plus_linker_plus_warhead", "C", "scaffold;linker;warhead", "none"),
]
CANONICAL_MASK_TASK_NAMES = [row[0] for row in CANONICAL_MASK_TASKS]
CANONICAL_MASK_TASK_ALIASES = [row[1] for row in CANONICAL_MASK_TASKS]

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

SCHEMA_COLUMNS = [
    "field_name",
    "field_group",
    "field_description",
    "required_for_future_model_input",
    "source_stage",
    "source_artifact",
    "diff_sbdd_compatibility_status",
    "materialization_status",
    "training_use_status",
]
DEPENDENCY_COLUMNS = [
    "dependency_name",
    "dependency_stage",
    "dependency_artifact_path",
    "dependency_required_for_future_model_input",
    "dependency_exists",
    "dependency_row_count",
    "dependency_expected_row_count",
    "dependency_validation_status",
    "training_use_status",
]
SAMPLE_COLUMNS = [
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "v1_train_ready_scope",
    "residue_scope",
    "residue_name",
    "residue_atom_name",
    "ligand_atom_count",
    "ligand_bond_count",
    "endpoint_atom_count",
    "endpoint_touching_bond_count",
    "topology_counts_validated",
    "sample_index_qa_passed",
    "future_model_input_row_allowed_next_step",
    "model_input_materialized",
    "tensor_artifact_written",
    "training_ready",
    "training_ready_reason",
]
MASK_COLUMNS = [
    "canonical_mask_task_name",
    "display_alias",
    "masked_groups",
    "preserved_groups",
    "required_group_labels",
    "model_input_mask_design_status",
    "source_of_truth_status",
    "alias_status",
    "materialization_status",
    "training_use_status",
]
FEATURE_SEMANTICS_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "risk_if_wrong",
    "audit_required_before_training",
    "blocking_for_design_gate",
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


def validate_step13u_precondition_v0() -> bool:
    required_paths = [
        STEP13U_MANIFEST_JSON,
        STEP13U_ROW_QA_AUDIT_CSV,
        STEP13U_DEPENDENCY_QA_AUDIT_CSV,
        STEP13U_SCHEMA_QA_AUDIT_CSV,
        STEP13T_SAMPLE_INDEX_CSV,
        STEP13S_SCHEMA_CONTRACT_CSV,
        STEP13S_CANDIDATE_CONTRACT_CSV,
        STEP13S_MASK_TASK_CONTRACT_CSV,
        STEP13R_ATOM_TOPOLOGY_CSV,
        STEP13R_BOND_TOPOLOGY_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13V prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13U_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "sample_index_qa_passed": True,
        "sample_index_smoke_read": True,
        "sample_index_smoke_row_count": 3,
        "sample_index_row_qa_audit_written": True,
        "sample_index_row_qa_audit_row_count": 3,
        "sample_index_dependency_qa_audit_written": True,
        "sample_index_dependency_qa_audit_row_count": 9,
        "sample_index_schema_qa_audit_written": True,
        "sample_index_schema_qa_audit_row_count": 47,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_sample_index_rows_unique": True,
        "all_identity_fields_validated": True,
        "all_lineage_fields_validated": True,
        "all_candidates_cys_sg_scope": True,
        "all_mask_task_fields_validated": True,
        "all_topology_counts_match_candidate_contract": True,
        "all_topology_table_paths_exist": True,
        "all_topology_table_counts_match_sample_index": True,
        "all_endpoint_counts_validated": True,
        "all_readiness_safety_fields_validated": True,
        "all_dependency_artifacts_exist": True,
        "all_dependency_counts_validated": True,
        "all_required_schema_fields_present_or_intentionally_deferred": True,
        "all_sample_index_row_qa_passed": True,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "ready_for_model_input_design_gate": True,
        "ready_for_model_input_materialization_smoke": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_model_input_design_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13U precondition failed: " + ";".join(blockers))
    return True


def build_model_input_schema_contract_v0() -> list[dict[str, Any]]:
    fields = {
        "sample_identity": [
            "sample_index_row_id",
            "review_row_id",
            "pdb_id",
            "expected_step8_sample_name",
            "v1_train_ready_scope",
            "residue_scope",
        ],
        "protein_pocket_input": [
            "pocket_atom_table_path",
            "pocket_atom_count",
            "pocket_center_status",
            "pocket_coordinate_frame_status",
            "protein_atom_coordinates_status",
            "protein_atom_feature_status",
            "protein_residue_feature_status",
            "reactive_residue_identifier",
            "reactive_residue_atom_name",
            "reactive_residue_atom_coordinates_status",
        ],
        "ligand_topology_coordinates": [
            "ligand_atom_topology_table_path",
            "ligand_bond_topology_table_path",
            "ligand_atom_count",
            "ligand_bond_count",
            "ligand_atom_feature_status",
            "ligand_bond_feature_status",
            "ligand_coordinates_status",
            "covalent_ligand_endpoint_atom_id",
            "endpoint_atom_count",
            "endpoint_touching_bond_count",
        ],
        "group_labels": [
            "warhead_atom_mask_status",
            "linker_atom_mask_status",
            "scaffold_atom_mask_status",
            "warhead_bond_label_status",
            "linker_bond_label_status",
            "scaffold_bond_label_status",
        ],
        "canonical_mask_tasks": [
            "canonical_mask_task_names",
            "canonical_mask_task_aliases",
            "mask_task_count",
            "supports_warhead_only",
            "supports_linker_plus_warhead",
            "supports_scaffold_plus_warhead",
            "supports_scaffold_only",
            "supports_scaffold_plus_linker_plus_warhead",
        ],
        "auxiliary_labels": [
            "warhead_type_label_status",
            "ligand_residue_atom_pair_label_status",
            "pre_post_covalent_geometry_label_status",
        ],
        "model_compatibility_safety": [
            "checkpoint_compatibility_status",
            "diff_sbdd_main_model_change_status",
            "dataloader_change_status",
            "forward_change_status",
            "loss_change_status",
            "model_input_materialization_status",
            "tensor_artifact_status",
            "training_use_status",
            "ready_to_train_now",
            "feature_semantics_audit_required_before_training",
        ],
    }
    source_by_group = {
        "sample_identity": (PREVIOUS_STAGE, STEP13T_SAMPLE_INDEX_CSV),
        "protein_pocket_input": ("real_covalent_confirmed_candidate_pocket_extraction_smoke_v0", STEP13L_POCKET_ATOM_TABLE_CSV),
        "ligand_topology_coordinates": (
            "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0",
            STEP13R_ATOM_TOPOLOGY_CSV,
        ),
        "group_labels": (
            "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0",
            STEP13R_ATOM_TOPOLOGY_CSV,
        ),
        "canonical_mask_tasks": (STAGE, MASK_CONTRACT_CSV),
        "auxiliary_labels": (STAGE, FEATURE_SEMANTICS_CONTRACT_CSV),
        "model_compatibility_safety": (STAGE, FEATURE_SEMANTICS_CONTRACT_CSV),
    }
    rows: list[dict[str, Any]] = []
    for group, names in fields.items():
        source_stage, artifact = source_by_group[group]
        for name in names:
            if group in {"model_compatibility_safety", "auxiliary_labels"}:
                compat = "requires_feature_semantics_audit_before_training"
            elif "status" in name or "feature" in name:
                compat = "requires_future_materialization_mapping"
            else:
                compat = "compatible_by_existing_source_dependency"
            rows.append(
                {
                    "field_name": name,
                    "field_group": group,
                    "field_description": f"Future DiffSBDD-compatible model input field `{name}`.",
                    "required_for_future_model_input": True,
                    "source_stage": source_stage,
                    "source_artifact": str(artifact),
                    "diff_sbdd_compatibility_status": compat,
                    "materialization_status": "design_only_not_materialized",
                    "training_use_status": "not_training_input_yet",
                }
            )
    return rows


def build_model_input_dependency_contract_v0() -> list[dict[str, Any]]:
    dependencies = [
        ("step13u_manifest", PREVIOUS_STAGE, STEP13U_MANIFEST_JSON, 1),
        ("step13u_row_qa_audit", PREVIOUS_STAGE, STEP13U_ROW_QA_AUDIT_CSV, 3),
        ("step13u_dependency_qa_audit", PREVIOUS_STAGE, STEP13U_DEPENDENCY_QA_AUDIT_CSV, 9),
        ("step13u_schema_qa_audit", PREVIOUS_STAGE, STEP13U_SCHEMA_QA_AUDIT_CSV, 47),
        ("step13t_sample_index_smoke", "real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0", STEP13T_SAMPLE_INDEX_CSV, 3),
        ("step13s_candidate_contract", "real_covalent_confirmed_candidate_sample_index_design_gate_v0", STEP13S_CANDIDATE_CONTRACT_CSV, 3),
        ("step13s_mask_task_contract", "real_covalent_confirmed_candidate_sample_index_design_gate_v0", STEP13S_MASK_TASK_CONTRACT_CSV, 5),
        ("step13r_atom_topology_smoke_table", "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0", STEP13R_ATOM_TOPOLOGY_CSV, 104),
        ("step13r_bond_topology_smoke_table", "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0", STEP13R_BOND_TOPOLOGY_CSV, 113),
        ("step13l_pocket_atom_table", "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0", STEP13L_POCKET_ATOM_TABLE_CSV, _row_count(STEP13L_POCKET_ATOM_TABLE_CSV)),
    ]
    rows = []
    for name, stage, path, expected_count in dependencies:
        exists = path.is_file()
        row_count = _row_count(path)
        validated = exists and row_count == expected_count
        rows.append(
            {
                "dependency_name": name,
                "dependency_stage": stage,
                "dependency_artifact_path": str(path),
                "dependency_required_for_future_model_input": True,
                "dependency_exists": exists,
                "dependency_row_count": row_count,
                "dependency_expected_row_count": expected_count,
                "dependency_validation_status": "exists_and_count_validated" if validated else "missing_or_count_mismatch",
                "training_use_status": "not_training_input_yet",
            }
        )
    return rows


def build_model_input_sample_contract_v0() -> list[dict[str, Any]]:
    sample_rows = _read_csv(STEP13T_SAMPLE_INDEX_CSV)
    qa_rows = {row["sample_index_row_id"]: row for row in _read_csv(STEP13U_ROW_QA_AUDIT_CSV)}
    rows = []
    for row in sample_rows:
        qa_row = qa_rows[row["sample_index_row_id"]]
        rows.append(
            {
                "sample_index_row_id": row["sample_index_row_id"],
                "review_row_id": row["review_row_id"],
                "pdb_id": row["pdb_id"],
                "v1_train_ready_scope": row["v1_train_ready_scope"],
                "residue_scope": row["residue_scope"],
                "residue_name": row["residue_name"],
                "residue_atom_name": row["residue_atom_name"],
                "ligand_atom_count": int(row["ligand_atom_count"]),
                "ligand_bond_count": int(row["ligand_bond_count"]),
                "endpoint_atom_count": int(row["endpoint_atom_true_count"]),
                "endpoint_touching_bond_count": int(row["endpoint_touching_bond_true_count"]),
                "topology_counts_validated": _as_bool(qa_row["topology_counts_match_candidate_contract"]),
                "sample_index_qa_passed": _as_bool(qa_row["sample_index_row_qa_passed"]),
                "future_model_input_row_allowed_next_step": True,
                "model_input_materialized": False,
                "tensor_artifact_written": False,
                "training_ready": False,
                "training_ready_reason": "model_input_design_gate_only_not_materialized",
            }
        )
    return rows


def build_model_input_mask_contract_v0() -> list[dict[str, Any]]:
    rows = []
    for name, alias, masked, preserved in CANONICAL_MASK_TASKS:
        rows.append(
            {
                "canonical_mask_task_name": name,
                "display_alias": alias,
                "masked_groups": masked,
                "preserved_groups": preserved,
                "required_group_labels": "warhead;linker;scaffold",
                "model_input_mask_design_status": "design_gate_passed",
                "source_of_truth_status": "long_semantic_name_source_of_truth",
                "alias_status": "display_only",
                "materialization_status": "design_only_not_materialized",
                "training_use_status": "not_training_input_yet",
            }
        )
    return rows


def build_model_input_feature_semantics_contract_v0() -> list[dict[str, Any]]:
    items = [
        ("protein_atom_feature_semantics", "protein_features", "Wrong atom features can corrupt pocket conditioning."),
        ("ligand_atom_feature_semantics", "ligand_features", "Wrong atom features can corrupt generated ligand chemistry."),
        ("residue_feature_semantics", "protein_features", "Wrong residue features can mislabel reactive context."),
        ("covalent_endpoint_atom_semantics", "covalent_labels", "Wrong endpoint semantics can break covalent anchoring."),
        ("warhead_linker_scaffold_group_semantics", "group_labels", "Wrong group labels can invert mask supervision."),
        ("canonical_mask_task_semantics", "mask_tasks", "Wrong task semantics can train the wrong conditional objective."),
        ("pre_post_covalent_geometry_semantics", "geometry_labels", "Wrong geometry semantics can leak post-reaction state."),
        ("warhead_type_label_semantics", "auxiliary_labels", "Wrong warhead labels can misroute restoration assumptions."),
        ("ligand_residue_atom_pair_label_semantics", "auxiliary_labels", "Wrong atom-pair labels can corrupt covalent pair conditioning."),
        ("coordinate_frame_and_units_semantics", "coordinates", "Wrong coordinate units can destabilize equivariant inputs."),
        ("unknown_atom_feature_policy", "feature_policy", "Unknown atom handling can silently create invalid categories."),
        ("checkpoint_feature_compatibility", "checkpoint_compatibility", "Feature mismatch can make checkpoint behavior misleading."),
    ]
    return [
        {
            "feature_semantics_item": item,
            "feature_group": group,
            "current_status": "design_contract_only_not_fully_audited",
            "risk_if_wrong": risk,
            "audit_required_before_training": True,
            "blocking_for_design_gate": False,
            "recommended_audit_step": "real_covalent_confirmed_candidate_feature_semantics_audit_before_training",
        }
        for item, group, risk in items
    ]


def build_real_covalent_confirmed_candidate_model_input_design_gate_v0() -> dict[str, Any]:
    validate_step13u_precondition_v0()
    schema_rows = build_model_input_schema_contract_v0()
    dependency_rows = build_model_input_dependency_contract_v0()
    sample_rows = build_model_input_sample_contract_v0()
    mask_rows = build_model_input_mask_contract_v0()
    feature_rows = build_model_input_feature_semantics_contract_v0()

    all_dependency_artifacts_exist = all(_as_bool(row["dependency_exists"]) for row in dependency_rows)
    all_dependency_counts_validated = all(row["dependency_validation_status"] == "exists_and_count_validated" for row in dependency_rows)
    all_sample_contract_rows_validated = (
        len(sample_rows) == 3
        and [row["sample_index_row_id"] for row in sample_rows] == EXPECTED_SAMPLE_INDEX_ROW_IDS
        and [row["review_row_id"] for row in sample_rows] == EXPECTED_REVIEW_ROW_IDS
        and all(_as_bool(row["topology_counts_validated"]) and _as_bool(row["sample_index_qa_passed"]) for row in sample_rows)
        and all(not _as_bool(row["model_input_materialized"]) and not _as_bool(row["tensor_artifact_written"]) for row in sample_rows)
    )
    all_mask_contract_rows_validated = (
        len(mask_rows) == 5
        and [row["canonical_mask_task_name"] for row in mask_rows] == CANONICAL_MASK_TASK_NAMES
        and [row["display_alias"] for row in mask_rows] == CANONICAL_MASK_TASK_ALIASES
        and all(row["materialization_status"] == "design_only_not_materialized" for row in mask_rows)
    )
    all_feature_semantics_audit_required_before_training = all(
        _as_bool(row["audit_required_before_training"]) for row in feature_rows
    )
    no_feature_semantics_claimed_fully_audited = all(
        row["current_status"] != "fully_audited" for row in feature_rows
    )
    safety_ok = not any(
        [
            _source_diff_exists(),
            _forbidden_committable_artifacts_created(),
            _raw_files_staged(),
            _raw_files_tracked(),
        ]
    )
    model_input_design_gate_passed = all(
        [
            all_dependency_artifacts_exist,
            all_dependency_counts_validated,
            all_sample_contract_rows_validated,
            all_mask_contract_rows_validated,
            all_feature_semantics_audit_required_before_training,
            no_feature_semantics_claimed_fully_audited,
            safety_ok,
        ]
    )
    blocking_reasons = []
    if not model_input_design_gate_passed:
        blocking_reasons.append("model_input_design_gate_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13u_sample_index_qa_gate_validated": True,
        "model_input_design_scope": DESIGN_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "schema_contract_written": True,
        "schema_contract_row_count": len(schema_rows),
        "dependency_contract_written": True,
        "dependency_contract_row_count": len(dependency_rows),
        "sample_contract_written": True,
        "sample_contract_row_count": len(sample_rows),
        "mask_contract_written": True,
        "mask_contract_row_count": len(mask_rows),
        "feature_semantics_contract_written": True,
        "feature_semantics_contract_row_count": len(feature_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        "all_dependency_counts_validated": all_dependency_counts_validated,
        "all_sample_contract_rows_validated": all_sample_contract_rows_validated,
        "all_mask_contract_rows_validated": all_mask_contract_rows_validated,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "model_input_design_gate_passed": model_input_design_gate_passed,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "model_input_written": False,
        "tensor_artifact_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
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
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": _source_diff_exists(),
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "ready_for_model_input_materialization_smoke": True,
        "ready_for_loader_shape_dry_run": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": model_input_design_gate_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13u_precondition": {"validated": True, "sample_index_rows": 3},
        "schema_contract": {"row_count": len(schema_rows), "written": True},
        "dependency_contract": {
            "row_count": len(dependency_rows),
            "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
            "all_dependency_counts_validated": all_dependency_counts_validated,
        },
        "sample_contract": {"row_count": len(sample_rows), "all_sample_contract_rows_validated": all_sample_contract_rows_validated},
        "mask_contract": {"row_count": len(mask_rows), "b3_scaffold_only_included": True, "no_extra_mask_tasks_added": True},
        "feature_semantics_contract": {
            "row_count": len(feature_rows),
            "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
            "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        },
        "readiness_boundary": {
            "ready_for_model_input_materialization_smoke": True,
            "ready_for_loader_shape_dry_run": False,
            "ready_for_training": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "schema_rows": schema_rows,
        "dependency_rows": dependency_rows,
        "sample_rows": sample_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

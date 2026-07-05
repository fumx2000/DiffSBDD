from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_model_input_materialization_smoke_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_model_input_design_gate_v0"

STEP13V_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_design_gate_v0")
STEP13V_MANIFEST_JSON = STEP13V_ROOT / "model_input_design_gate_manifest.json"
STEP13V_SCHEMA_CONTRACT_CSV = STEP13V_ROOT / "model_input_schema_contract.csv"
STEP13V_DEPENDENCY_CONTRACT_CSV = STEP13V_ROOT / "model_input_dependency_contract.csv"
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
    "data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_materialization_smoke_v0"
)
MODEL_INPUT_SMOKE_INDEX_CSV = OUTPUT_ROOT / "model_input_smoke_index.csv"
FEATURE_STATUS_CSV = OUTPUT_ROOT / "model_input_smoke_feature_status.csv"
MASK_STATUS_CSV = OUTPUT_ROOT / "model_input_smoke_mask_status.csv"
AUDIT_CSV = OUTPUT_ROOT / "model_input_materialization_smoke_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "model_input_materialization_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "model_input_materialization_smoke_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_model_input_materialization_smoke_v0_summary.md")

EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS = ["RMI_SMOKE_000001", "RMI_SMOKE_000002", "RMI_SMOKE_000003"]
EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
SMOKE_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_model_input_qa_gate"
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

INDEX_COLUMNS = [
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
    "supports_warhead_only",
    "supports_linker_plus_warhead",
    "supports_scaffold_plus_warhead",
    "supports_scaffold_only",
    "supports_scaffold_plus_linker_plus_warhead",
    "protein_coordinates_source_status",
    "ligand_coordinates_source_status",
    "feature_semantics_status",
    "model_input_smoke_materialization_status",
    "tensor_artifact_status",
    "training_use_status",
    "ready_for_loader_shape_dry_run",
    "ready_to_train_now",
    "feature_semantics_audit_required_before_training",
]
FEATURE_STATUS_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "audit_required_before_training",
    "blocking_for_smoke_materialization",
    "fully_audited_claimed",
    "training_ready",
    "recommended_audit_step",
]
MASK_STATUS_COLUMNS = [
    "canonical_mask_task_name",
    "display_alias",
    "masked_groups",
    "preserved_groups",
    "source_of_truth_status",
    "alias_status",
    "model_input_smoke_mask_status",
    "tensor_mask_written",
    "training_use_status",
]
AUDIT_COLUMNS = [
    "model_input_smoke_row_id",
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "sample_contract_row_found",
    "sample_index_row_found",
    "pocket_dependency_path_exists",
    "ligand_topology_paths_exist",
    "ligand_counts_match_sample_contract",
    "endpoint_counts_validated",
    "mask_contract_validated",
    "feature_semantics_audit_required",
    "model_input_smoke_row_written",
    "tensor_artifact_written",
    "loader_shape_dry_run_performed",
    "training_ready",
    "materialization_smoke_passed",
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


def validate_step13v_precondition_v0() -> bool:
    required_paths = [
        STEP13V_MANIFEST_JSON,
        STEP13V_SCHEMA_CONTRACT_CSV,
        STEP13V_DEPENDENCY_CONTRACT_CSV,
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
        raise FileNotFoundError(f"Step 13W prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13V_MANIFEST_JSON)
    expected = {
        "stage": "real_covalent_confirmed_candidate_model_input_design_gate_v0",
        "all_checks_passed": True,
        "model_input_design_gate_passed": True,
        "schema_contract_written": True,
        "schema_contract_row_count": 53,
        "dependency_contract_written": True,
        "dependency_contract_row_count": 10,
        "sample_contract_written": True,
        "sample_contract_row_count": 3,
        "mask_contract_written": True,
        "mask_contract_row_count": 5,
        "feature_semantics_contract_written": True,
        "feature_semantics_contract_row_count": 12,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_dependency_artifacts_exist": True,
        "all_dependency_counts_validated": True,
        "all_sample_contract_rows_validated": True,
        "all_mask_contract_rows_validated": True,
        "all_feature_semantics_audit_required_before_training": True,
        "no_feature_semantics_claimed_fully_audited": True,
        "model_input_materialized": False,
        "model_input_written": False,
        "tensor_artifact_written": False,
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "ready_for_model_input_materialization_smoke": True,
        "ready_for_loader_shape_dry_run": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_model_input_materialization_smoke",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13V precondition failed: " + ";".join(blockers))
    return True


def _count_by_review(rows: list[dict[str, str]]) -> dict[str, int]:
    return {review_row_id: sum(row.get("review_row_id") == review_row_id for row in rows) for review_row_id in EXPECTED_REVIEW_ROW_IDS}


def build_model_input_smoke_index_v0() -> list[dict[str, Any]]:
    sample_contract = _read_csv(STEP13V_SAMPLE_CONTRACT_CSV)
    sample_index = {row["sample_index_row_id"]: row for row in _read_csv(STEP13T_SAMPLE_INDEX_CSV)}
    pocket_counts = _count_by_review(_read_csv(STEP13L_POCKET_ATOM_TABLE_CSV))
    joined_names = ";".join(CANONICAL_MASK_TASK_NAMES)
    joined_aliases = ";".join(CANONICAL_MASK_TASK_ALIASES)
    rows = []
    for idx, contract in enumerate(sample_contract):
        sample_index_row = sample_index[contract["sample_index_row_id"]]
        rows.append(
            {
                "model_input_smoke_row_id": EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS[idx],
                "sample_index_row_id": contract["sample_index_row_id"],
                "review_row_id": contract["review_row_id"],
                "pdb_id": contract["pdb_id"],
                "v1_train_ready_scope": contract["v1_train_ready_scope"],
                "residue_scope": contract["residue_scope"],
                "residue_name": contract["residue_name"],
                "residue_atom_name": contract["residue_atom_name"],
                "pocket_atom_table_path": str(STEP13L_POCKET_ATOM_TABLE_CSV),
                "ligand_atom_topology_table_path": sample_index_row["ligand_atom_topology_table_path"],
                "ligand_bond_topology_table_path": sample_index_row["ligand_bond_topology_table_path"],
                "pocket_atom_count": pocket_counts[contract["review_row_id"]],
                "ligand_atom_count": int(contract["ligand_atom_count"]),
                "ligand_bond_count": int(contract["ligand_bond_count"]),
                "endpoint_atom_count": int(contract["endpoint_atom_count"]),
                "endpoint_touching_bond_count": int(contract["endpoint_touching_bond_count"]),
                "canonical_mask_task_names": joined_names,
                "canonical_mask_task_aliases": joined_aliases,
                "mask_task_count": 5,
                "supports_warhead_only": True,
                "supports_linker_plus_warhead": True,
                "supports_scaffold_plus_warhead": True,
                "supports_scaffold_only": True,
                "supports_scaffold_plus_linker_plus_warhead": True,
                "protein_coordinates_source_status": "source_dependency_declared_not_tensorized",
                "ligand_coordinates_source_status": "source_dependency_declared_not_tensorized",
                "feature_semantics_status": "audit_required_before_training",
                "model_input_smoke_materialization_status": "csv_json_smoke_only",
                "tensor_artifact_status": "not_written",
                "training_use_status": "not_training_input_yet",
                "ready_for_loader_shape_dry_run": False,
                "ready_to_train_now": False,
                "feature_semantics_audit_required_before_training": True,
            }
        )
    return rows


def build_feature_status_v0() -> list[dict[str, Any]]:
    rows = []
    for row in _read_csv(STEP13V_FEATURE_SEMANTICS_CONTRACT_CSV):
        rows.append(
            {
                "feature_semantics_item": row["feature_semantics_item"],
                "feature_group": row["feature_group"],
                "current_status": row["current_status"],
                "audit_required_before_training": True,
                "blocking_for_smoke_materialization": False,
                "fully_audited_claimed": False,
                "training_ready": False,
                "recommended_audit_step": row["recommended_audit_step"],
            }
        )
    return rows


def build_mask_status_v0() -> list[dict[str, Any]]:
    rows = []
    for row in _read_csv(STEP13V_MASK_CONTRACT_CSV):
        rows.append(
            {
                "canonical_mask_task_name": row["canonical_mask_task_name"],
                "display_alias": row["display_alias"],
                "masked_groups": row["masked_groups"],
                "preserved_groups": row["preserved_groups"],
                "source_of_truth_status": row["source_of_truth_status"],
                "alias_status": row["alias_status"],
                "model_input_smoke_mask_status": "csv_json_smoke_only",
                "tensor_mask_written": False,
                "training_use_status": "not_training_input_yet",
            }
        )
    return rows


def build_materialization_audit_v0(index_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sample_contract = {row["sample_index_row_id"]: row for row in _read_csv(STEP13V_SAMPLE_CONTRACT_CSV)}
    sample_index = {row["sample_index_row_id"]: row for row in _read_csv(STEP13T_SAMPLE_INDEX_CSV)}
    mask_valid = [row["canonical_mask_task_name"] for row in _read_csv(STEP13V_MASK_CONTRACT_CSV)] == CANONICAL_MASK_TASK_NAMES
    feature_required = all(_as_bool(row["audit_required_before_training"]) for row in _read_csv(STEP13V_FEATURE_SEMANTICS_CONTRACT_CSV))
    rows = []
    for row in index_rows:
        sample_contract_row = sample_contract.get(row["sample_index_row_id"])
        sample_index_row = sample_index.get(row["sample_index_row_id"])
        sample_contract_found = sample_contract_row is not None
        sample_index_found = sample_index_row is not None
        pocket_path_exists = Path(row["pocket_atom_table_path"]).is_file()
        ligand_paths_exist = Path(row["ligand_atom_topology_table_path"]).is_file() and Path(row["ligand_bond_topology_table_path"]).is_file()
        counts_match = sample_contract_found and (
            int(sample_contract_row["ligand_atom_count"]) == row["ligand_atom_count"]
            and int(sample_contract_row["ligand_bond_count"]) == row["ligand_bond_count"]
        )
        endpoint_valid = row["endpoint_atom_count"] == 1 and row["endpoint_touching_bond_count"] == 1
        smoke_row_written = row["model_input_smoke_materialization_status"] == "csv_json_smoke_only"
        tensor_written = False
        loader_shape_dry_run = False
        training_ready = False
        checks = {
            "sample_contract_row_found": sample_contract_found,
            "sample_index_row_found": sample_index_found,
            "pocket_dependency_path_exists": pocket_path_exists,
            "ligand_topology_paths_exist": ligand_paths_exist,
            "ligand_counts_match_sample_contract": counts_match,
            "endpoint_counts_validated": endpoint_valid,
            "mask_contract_validated": mask_valid,
            "feature_semantics_audit_required": feature_required,
            "model_input_smoke_row_written": smoke_row_written,
        }
        blockers = [name for name, passed in checks.items() if not passed]
        rows.append(
            {
                "model_input_smoke_row_id": row["model_input_smoke_row_id"],
                "sample_index_row_id": row["sample_index_row_id"],
                "review_row_id": row["review_row_id"],
                "pdb_id": row["pdb_id"],
                **checks,
                "tensor_artifact_written": tensor_written,
                "loader_shape_dry_run_performed": loader_shape_dry_run,
                "training_ready": training_ready,
                "materialization_smoke_passed": not blockers,
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def build_real_covalent_confirmed_candidate_model_input_materialization_smoke_v0() -> dict[str, Any]:
    validate_step13v_precondition_v0()
    index_rows = build_model_input_smoke_index_v0()
    feature_rows = build_feature_status_v0()
    mask_rows = build_mask_status_v0()
    audit_rows = build_materialization_audit_v0(index_rows)

    all_model_input_smoke_rows_written = len(index_rows) == 3
    all_sample_contract_rows_found = all(_as_bool(row["sample_contract_row_found"]) for row in audit_rows)
    all_sample_index_rows_found = all(_as_bool(row["sample_index_row_found"]) for row in audit_rows)
    all_ligand_topology_paths_exist = all(_as_bool(row["ligand_topology_paths_exist"]) for row in audit_rows)
    all_pocket_dependency_paths_exist = all(_as_bool(row["pocket_dependency_path_exists"]) for row in audit_rows)
    all_ligand_counts_match_sample_contract = all(_as_bool(row["ligand_counts_match_sample_contract"]) for row in audit_rows)
    all_endpoint_counts_validated = all(_as_bool(row["endpoint_counts_validated"]) for row in audit_rows)
    all_mask_contracts_validated = all(_as_bool(row["mask_contract_validated"]) for row in audit_rows)
    all_feature_semantics_audit_required_before_training = all(
        _as_bool(row["audit_required_before_training"]) for row in feature_rows
    )
    no_feature_semantics_claimed_fully_audited = all(not _as_bool(row["fully_audited_claimed"]) for row in feature_rows)
    model_input_materialization_smoke_passed = all(
        _as_bool(row["materialization_smoke_passed"]) for row in audit_rows
    )
    safety_ok = not any(
        [
            _source_diff_exists(),
            _forbidden_committable_artifacts_created(),
            _raw_files_staged(),
            _raw_files_tracked(),
        ]
    )
    all_checks_passed = all(
        [
            all_model_input_smoke_rows_written,
            all_sample_contract_rows_found,
            all_sample_index_rows_found,
            all_ligand_topology_paths_exist,
            all_pocket_dependency_paths_exist,
            all_ligand_counts_match_sample_contract,
            all_endpoint_counts_validated,
            all_mask_contracts_validated,
            all_feature_semantics_audit_required_before_training,
            no_feature_semantics_claimed_fully_audited,
            model_input_materialization_smoke_passed,
            safety_ok,
        ]
    )
    blocking_reasons = []
    if not all_checks_passed:
        blocking_reasons.append("model_input_materialization_smoke_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13v_model_input_design_gate_validated": True,
        "model_input_smoke_scope": SMOKE_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "model_input_smoke_index_written": True,
        "model_input_smoke_index_row_count": len(index_rows),
        "model_input_smoke_feature_status_written": True,
        "model_input_smoke_feature_status_row_count": len(feature_rows),
        "model_input_smoke_mask_status_written": True,
        "model_input_smoke_mask_status_row_count": len(mask_rows),
        "model_input_materialization_smoke_audit_written": True,
        "model_input_materialization_smoke_audit_row_count": len(audit_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_model_input_smoke_rows_written": all_model_input_smoke_rows_written,
        "all_sample_contract_rows_found": all_sample_contract_rows_found,
        "all_sample_index_rows_found": all_sample_index_rows_found,
        "all_ligand_topology_paths_exist": all_ligand_topology_paths_exist,
        "all_pocket_dependency_paths_exist": all_pocket_dependency_paths_exist,
        "all_ligand_counts_match_sample_contract": all_ligand_counts_match_sample_contract,
        "all_endpoint_counts_validated": all_endpoint_counts_validated,
        "all_mask_contracts_validated": all_mask_contracts_validated,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "model_input_materialization_smoke_passed": model_input_materialization_smoke_passed,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_smoke_written": True,
        "model_input_smoke_materialized": True,
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
        "ready_for_model_input_qa_gate": True,
        "ready_for_loader_shape_dry_run": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13v_precondition": {"validated": True, "sample_contract_rows": 3},
        "model_input_smoke_index": {"row_count": len(index_rows), "all_model_input_smoke_rows_written": all_model_input_smoke_rows_written},
        "feature_status": {"row_count": len(feature_rows), "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training},
        "mask_status": {"row_count": len(mask_rows), "b3_scaffold_only_included": True},
        "materialization_audit": {"row_count": len(audit_rows), "model_input_materialization_smoke_passed": model_input_materialization_smoke_passed},
        "readiness_boundary": {"ready_for_model_input_qa_gate": True, "ready_for_loader_shape_dry_run": False, "ready_for_training": False},
    }
    return {
        "index_rows": index_rows,
        "feature_rows": feature_rows,
        "mask_rows": mask_rows,
        "audit_rows": audit_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_model_input_qa_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_model_input_materialization_smoke_v0"

STEP13W_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_materialization_smoke_v0"
)
STEP13W_MANIFEST_JSON = STEP13W_ROOT / "model_input_materialization_smoke_manifest.json"
STEP13W_SMOKE_INDEX_CSV = STEP13W_ROOT / "model_input_smoke_index.csv"
STEP13W_FEATURE_STATUS_CSV = STEP13W_ROOT / "model_input_smoke_feature_status.csv"
STEP13W_MASK_STATUS_CSV = STEP13W_ROOT / "model_input_smoke_mask_status.csv"
STEP13W_AUDIT_CSV = STEP13W_ROOT / "model_input_materialization_smoke_audit.csv"

STEP13V_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_design_gate_v0")
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

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_model_input_qa_gate_v0")
ROW_QA_AUDIT_CSV = OUTPUT_ROOT / "model_input_smoke_row_qa_audit.csv"
DEPENDENCY_QA_AUDIT_CSV = OUTPUT_ROOT / "model_input_smoke_dependency_qa_audit.csv"
FEATURE_QA_AUDIT_CSV = OUTPUT_ROOT / "model_input_smoke_feature_qa_audit.csv"
MASK_QA_AUDIT_CSV = OUTPUT_ROOT / "model_input_smoke_mask_qa_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "model_input_qa_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "model_input_qa_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_model_input_qa_gate_v0_summary.md")

EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS = ["RMI_SMOKE_000001", "RMI_SMOKE_000002", "RMI_SMOKE_000003"]
EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_ATOM_BOND_COUNTS = {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
QA_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate"
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

ROW_QA_COLUMNS = [
    "model_input_smoke_row_id",
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "row_identity_validated",
    "cys_sg_scope_validated",
    "sample_contract_consistency_validated",
    "sample_index_consistency_validated",
    "ligand_counts_validated",
    "endpoint_counts_validated",
    "pocket_dependency_validated",
    "ligand_topology_dependency_validated",
    "mask_fields_validated",
    "feature_semantics_status_validated",
    "tensor_status_validated",
    "loader_training_boundary_validated",
    "model_input_smoke_row_qa_passed",
    "blocking_reasons",
]
DEPENDENCY_QA_COLUMNS = [
    "dependency_name",
    "dependency_artifact_path",
    "dependency_exists",
    "dependency_row_count",
    "dependency_expected_row_count",
    "dependency_count_validated",
    "dependency_qa_passed",
    "blocking_reasons",
]
FEATURE_QA_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "audit_required_before_training",
    "fully_audited_claimed",
    "training_ready",
    "blocking_for_smoke_materialization",
    "recommended_audit_step",
    "feature_qa_passed",
    "blocking_reasons",
]
MASK_QA_COLUMNS = [
    "canonical_mask_task_name",
    "display_alias",
    "masked_groups",
    "preserved_groups",
    "source_of_truth_status",
    "alias_status",
    "tensor_mask_written",
    "training_use_status",
    "mask_qa_passed",
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


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".json":
        return 1
    return len(_read_csv(path))


def validate_step13w_precondition_v0() -> bool:
    required_paths = [
        STEP13W_MANIFEST_JSON,
        STEP13W_SMOKE_INDEX_CSV,
        STEP13W_FEATURE_STATUS_CSV,
        STEP13W_MASK_STATUS_CSV,
        STEP13W_AUDIT_CSV,
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
        raise FileNotFoundError(f"Step 13X prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13W_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "step13v_model_input_design_gate_validated": True,
        "model_input_smoke_scope": QA_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "model_input_smoke_index_written": True,
        "model_input_smoke_index_row_count": 3,
        "model_input_smoke_feature_status_written": True,
        "model_input_smoke_feature_status_row_count": 12,
        "model_input_smoke_mask_status_written": True,
        "model_input_smoke_mask_status_row_count": 5,
        "model_input_materialization_smoke_audit_written": True,
        "model_input_materialization_smoke_audit_row_count": 3,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_model_input_smoke_rows_written": True,
        "all_sample_contract_rows_found": True,
        "all_sample_index_rows_found": True,
        "all_ligand_topology_paths_exist": True,
        "all_pocket_dependency_paths_exist": True,
        "all_ligand_counts_match_sample_contract": True,
        "all_endpoint_counts_validated": True,
        "all_mask_contracts_validated": True,
        "all_feature_semantics_audit_required_before_training": True,
        "no_feature_semantics_claimed_fully_audited": True,
        "model_input_materialization_smoke_passed": True,
        "model_input_smoke_written": True,
        "model_input_smoke_materialized": True,
        "model_input_materialized": False,
        "model_input_written": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "dataloader_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "loader_shape_dry_run_performed": False,
        "ready_for_model_input_qa_gate": True,
        "ready_for_loader_shape_dry_run": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_model_input_qa_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13W precondition failed: " + ";".join(blockers))
    return True


def _count_by_review(rows: list[dict[str, str]]) -> dict[str, int]:
    return {review_row_id: sum(row.get("review_row_id") == review_row_id for row in rows) for review_row_id in EXPECTED_REVIEW_ROW_IDS}


def build_model_input_smoke_row_qa_audit_v0() -> list[dict[str, Any]]:
    smoke_rows = _read_csv(STEP13W_SMOKE_INDEX_CSV)
    sample_contract = {row["sample_index_row_id"]: row for row in _read_csv(STEP13V_SAMPLE_CONTRACT_CSV)}
    sample_index = {row["sample_index_row_id"]: row for row in _read_csv(STEP13T_SAMPLE_INDEX_CSV)}
    atom_counts = _count_by_review(_read_csv(STEP13R_ATOM_TOPOLOGY_CSV))
    bond_counts = _count_by_review(_read_csv(STEP13R_BOND_TOPOLOGY_CSV))
    expected_names = ";".join(CANONICAL_MASK_TASK_NAMES)
    expected_aliases = ";".join(CANONICAL_MASK_TASK_ALIASES)
    rows: list[dict[str, Any]] = []
    seen_model_input_ids = [row["model_input_smoke_row_id"] for row in smoke_rows]
    for idx, row in enumerate(smoke_rows):
        review_row_id = row["review_row_id"]
        contract = sample_contract.get(row["sample_index_row_id"], {})
        sample = sample_index.get(row["sample_index_row_id"], {})
        expected_counts = EXPECTED_ATOM_BOND_COUNTS[review_row_id]
        row_identity_validated = (
            row["model_input_smoke_row_id"] == EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS[idx]
            and seen_model_input_ids.count(row["model_input_smoke_row_id"]) == 1
            and row["sample_index_row_id"] == EXPECTED_SAMPLE_INDEX_ROW_IDS[idx]
            and review_row_id == EXPECTED_REVIEW_ROW_IDS[idx]
            and row["pdb_id"] == EXPECTED_PDB_IDS[idx]
        )
        cys_sg_scope_validated = (
            row["v1_train_ready_scope"] == V1_TRAIN_READY_SCOPE
            and row["residue_scope"] == QA_SCOPE
            and row["residue_name"] == "CYS"
            and row["residue_atom_name"] == "SG"
        )
        sample_contract_consistency_validated = (
            bool(contract)
            and contract["review_row_id"] == review_row_id
            and contract["pdb_id"] == row["pdb_id"]
            and int(contract["ligand_atom_count"]) == int(row["ligand_atom_count"])
            and int(contract["ligand_bond_count"]) == int(row["ligand_bond_count"])
        )
        sample_index_consistency_validated = (
            bool(sample)
            and sample["review_row_id"] == review_row_id
            and sample["pdb_id"] == row["pdb_id"]
            and int(sample["ligand_atom_count"]) == int(row["ligand_atom_count"])
            and int(sample["ligand_bond_count"]) == int(row["ligand_bond_count"])
        )
        ligand_counts_validated = (
            int(row["ligand_atom_count"]) == expected_counts[0]
            and int(row["ligand_bond_count"]) == expected_counts[1]
            and atom_counts[review_row_id] == expected_counts[0]
            and bond_counts[review_row_id] == expected_counts[1]
        )
        endpoint_counts_validated = int(row["endpoint_atom_count"]) == 1 and int(row["endpoint_touching_bond_count"]) == 1
        pocket_dependency_validated = Path(row["pocket_atom_table_path"]).is_file()
        ligand_topology_dependency_validated = (
            Path(row["ligand_atom_topology_table_path"]).is_file()
            and Path(row["ligand_bond_topology_table_path"]).is_file()
        )
        mask_fields_validated = (
            row["canonical_mask_task_names"] == expected_names
            and row["canonical_mask_task_aliases"] == expected_aliases
            and int(row["mask_task_count"]) == 5
            and all(_as_bool(row[f"supports_{name}"]) for name in CANONICAL_MASK_TASK_NAMES)
        )
        feature_semantics_status_validated = (
            row["feature_semantics_status"] == "audit_required_before_training"
            and _as_bool(row["feature_semantics_audit_required_before_training"])
        )
        tensor_status_validated = row["tensor_artifact_status"] == "not_written"
        loader_training_boundary_validated = (
            not _as_bool(row["ready_for_loader_shape_dry_run"])
            and not _as_bool(row["ready_to_train_now"])
            and row["training_use_status"] == "not_training_input_yet"
        )
        checks = {
            "row_identity_validated": row_identity_validated,
            "cys_sg_scope_validated": cys_sg_scope_validated,
            "sample_contract_consistency_validated": sample_contract_consistency_validated,
            "sample_index_consistency_validated": sample_index_consistency_validated,
            "ligand_counts_validated": ligand_counts_validated,
            "endpoint_counts_validated": endpoint_counts_validated,
            "pocket_dependency_validated": pocket_dependency_validated,
            "ligand_topology_dependency_validated": ligand_topology_dependency_validated,
            "mask_fields_validated": mask_fields_validated,
            "feature_semantics_status_validated": feature_semantics_status_validated,
            "tensor_status_validated": tensor_status_validated,
            "loader_training_boundary_validated": loader_training_boundary_validated,
        }
        blockers = [name for name, passed in checks.items() if not passed]
        rows.append(
            {
                "model_input_smoke_row_id": row["model_input_smoke_row_id"],
                "sample_index_row_id": row["sample_index_row_id"],
                "review_row_id": review_row_id,
                "pdb_id": row["pdb_id"],
                **checks,
                "model_input_smoke_row_qa_passed": not blockers,
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def build_model_input_smoke_dependency_qa_audit_v0() -> list[dict[str, Any]]:
    dependencies = [
        ("step13w_manifest", STEP13W_MANIFEST_JSON, 1),
        ("step13w_model_input_smoke_index", STEP13W_SMOKE_INDEX_CSV, 3),
        ("step13w_model_input_smoke_feature_status", STEP13W_FEATURE_STATUS_CSV, 12),
        ("step13w_model_input_smoke_mask_status", STEP13W_MASK_STATUS_CSV, 5),
        ("step13w_model_input_materialization_smoke_audit", STEP13W_AUDIT_CSV, 3),
        ("step13v_sample_contract", STEP13V_SAMPLE_CONTRACT_CSV, 3),
        ("step13v_mask_contract", STEP13V_MASK_CONTRACT_CSV, 5),
        ("step13v_feature_semantics_contract", STEP13V_FEATURE_SEMANTICS_CONTRACT_CSV, 12),
        ("step13t_sample_index_smoke", STEP13T_SAMPLE_INDEX_CSV, 3),
        ("step13l_pocket_atom_table", STEP13L_POCKET_ATOM_TABLE_CSV, 741),
    ]
    rows: list[dict[str, Any]] = []
    for name, path, expected_count in dependencies:
        exists = path.is_file()
        row_count = _row_count(path)
        count_validated = exists and row_count == expected_count
        blockers = []
        if not exists:
            blockers.append("dependency_missing")
        if exists and not count_validated:
            blockers.append("dependency_count_mismatch")
        rows.append(
            {
                "dependency_name": name,
                "dependency_artifact_path": str(path),
                "dependency_exists": exists,
                "dependency_row_count": row_count,
                "dependency_expected_row_count": expected_count,
                "dependency_count_validated": count_validated,
                "dependency_qa_passed": exists and count_validated,
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def build_model_input_smoke_feature_qa_audit_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _read_csv(STEP13W_FEATURE_STATUS_CSV):
        audit_required = _as_bool(row["audit_required_before_training"])
        fully_audited_claimed = _as_bool(row["fully_audited_claimed"])
        training_ready = _as_bool(row["training_ready"])
        blocking_for_smoke = _as_bool(row["blocking_for_smoke_materialization"])
        recommended_step_present = bool(row["recommended_audit_step"])
        passed = audit_required and not fully_audited_claimed and not training_ready and not blocking_for_smoke and recommended_step_present
        blockers = []
        if not passed:
            blockers.append("feature_semantics_qa_failed")
        rows.append(
            {
                "feature_semantics_item": row["feature_semantics_item"],
                "feature_group": row["feature_group"],
                "current_status": row["current_status"],
                "audit_required_before_training": audit_required,
                "fully_audited_claimed": fully_audited_claimed,
                "training_ready": training_ready,
                "blocking_for_smoke_materialization": blocking_for_smoke,
                "recommended_audit_step": row["recommended_audit_step"],
                "feature_qa_passed": passed,
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def build_model_input_smoke_mask_qa_audit_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(_read_csv(STEP13W_MASK_STATUS_CSV)):
        passed = (
            row["canonical_mask_task_name"] == CANONICAL_MASK_TASK_NAMES[idx]
            and row["display_alias"] == CANONICAL_MASK_TASK_ALIASES[idx]
            and row["source_of_truth_status"] == "long_semantic_name_source_of_truth"
            and row["alias_status"] == "display_only"
            and not _as_bool(row["tensor_mask_written"])
            and row["training_use_status"] == "not_training_input_yet"
        )
        rows.append(
            {
                "canonical_mask_task_name": row["canonical_mask_task_name"],
                "display_alias": row["display_alias"],
                "masked_groups": row["masked_groups"],
                "preserved_groups": row["preserved_groups"],
                "source_of_truth_status": row["source_of_truth_status"],
                "alias_status": row["alias_status"],
                "tensor_mask_written": _as_bool(row["tensor_mask_written"]),
                "training_use_status": row["training_use_status"],
                "mask_qa_passed": passed,
                "blocking_reasons": "" if passed else "mask_qa_failed",
            }
        )
    return rows


def build_real_covalent_confirmed_candidate_model_input_qa_gate_v0() -> dict[str, Any]:
    validate_step13w_precondition_v0()
    row_qa_rows = build_model_input_smoke_row_qa_audit_v0()
    dependency_qa_rows = build_model_input_smoke_dependency_qa_audit_v0()
    feature_qa_rows = build_model_input_smoke_feature_qa_audit_v0()
    mask_qa_rows = build_model_input_smoke_mask_qa_audit_v0()

    all_model_input_smoke_rows_unique = len({row["model_input_smoke_row_id"] for row in row_qa_rows}) == 3
    all_model_input_smoke_row_ids_validated = [row["model_input_smoke_row_id"] for row in row_qa_rows] == EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS
    all_sample_index_row_ids_validated = [row["sample_index_row_id"] for row in row_qa_rows] == EXPECTED_SAMPLE_INDEX_ROW_IDS
    all_identity_fields_validated = all(_as_bool(row["row_identity_validated"]) for row in row_qa_rows)
    all_candidates_cys_sg_scope = all(_as_bool(row["cys_sg_scope_validated"]) for row in row_qa_rows)
    all_sample_contract_consistency_validated = all(
        _as_bool(row["sample_contract_consistency_validated"]) for row in row_qa_rows
    )
    all_sample_index_consistency_validated = all(
        _as_bool(row["sample_index_consistency_validated"]) for row in row_qa_rows
    )
    all_ligand_counts_validated = all(_as_bool(row["ligand_counts_validated"]) for row in row_qa_rows)
    all_endpoint_counts_validated = all(_as_bool(row["endpoint_counts_validated"]) for row in row_qa_rows)
    all_pocket_dependencies_validated = all(_as_bool(row["pocket_dependency_validated"]) for row in row_qa_rows)
    all_ligand_topology_dependencies_validated = all(
        _as_bool(row["ligand_topology_dependency_validated"]) for row in row_qa_rows
    )
    all_mask_fields_validated = all(_as_bool(row["mask_fields_validated"]) for row in row_qa_rows)
    all_feature_semantics_status_validated = all(
        _as_bool(row["feature_semantics_status_validated"]) for row in row_qa_rows
    )
    all_tensor_status_validated = all(_as_bool(row["tensor_status_validated"]) for row in row_qa_rows)
    all_loader_training_boundaries_validated = all(
        _as_bool(row["loader_training_boundary_validated"]) for row in row_qa_rows
    )
    all_dependency_artifacts_exist = all(_as_bool(row["dependency_exists"]) for row in dependency_qa_rows)
    all_dependency_counts_validated = all(_as_bool(row["dependency_count_validated"]) for row in dependency_qa_rows)
    all_feature_semantics_audit_required_before_training = all(
        _as_bool(row["audit_required_before_training"]) for row in feature_qa_rows
    )
    no_feature_semantics_claimed_fully_audited = all(
        not _as_bool(row["fully_audited_claimed"]) for row in feature_qa_rows
    )
    all_feature_qa_passed = all(_as_bool(row["feature_qa_passed"]) for row in feature_qa_rows)
    all_mask_qa_passed = all(_as_bool(row["mask_qa_passed"]) for row in mask_qa_rows)
    all_model_input_smoke_row_qa_passed = all(
        _as_bool(row["model_input_smoke_row_qa_passed"]) for row in row_qa_rows
    )
    model_input_qa_passed = all(
        [
            all_model_input_smoke_rows_unique,
            all_model_input_smoke_row_ids_validated,
            all_sample_index_row_ids_validated,
            all_identity_fields_validated,
            all_candidates_cys_sg_scope,
            all_sample_contract_consistency_validated,
            all_sample_index_consistency_validated,
            all_ligand_counts_validated,
            all_endpoint_counts_validated,
            all_pocket_dependencies_validated,
            all_ligand_topology_dependencies_validated,
            all_mask_fields_validated,
            all_feature_semantics_status_validated,
            all_tensor_status_validated,
            all_loader_training_boundaries_validated,
            all_dependency_artifacts_exist,
            all_dependency_counts_validated,
            all_feature_semantics_audit_required_before_training,
            no_feature_semantics_claimed_fully_audited,
            all_feature_qa_passed,
            all_mask_qa_passed,
            all_model_input_smoke_row_qa_passed,
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
    all_checks_passed = model_input_qa_passed and safety_ok
    blocking_reasons = []
    if not model_input_qa_passed:
        blocking_reasons.append("model_input_qa_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13w_model_input_materialization_smoke_validated": True,
        "model_input_qa_scope": QA_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "model_input_smoke_row_qa_audit_written": True,
        "model_input_smoke_row_qa_audit_row_count": len(row_qa_rows),
        "model_input_smoke_dependency_qa_audit_written": True,
        "model_input_smoke_dependency_qa_audit_row_count": len(dependency_qa_rows),
        "model_input_smoke_feature_qa_audit_written": True,
        "model_input_smoke_feature_qa_audit_row_count": len(feature_qa_rows),
        "model_input_smoke_mask_qa_audit_written": True,
        "model_input_smoke_mask_qa_audit_row_count": len(mask_qa_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_model_input_smoke_rows_unique": all_model_input_smoke_rows_unique,
        "all_model_input_smoke_row_ids_validated": all_model_input_smoke_row_ids_validated,
        "all_sample_index_row_ids_validated": all_sample_index_row_ids_validated,
        "all_identity_fields_validated": all_identity_fields_validated,
        "all_candidates_cys_sg_scope": all_candidates_cys_sg_scope,
        "all_sample_contract_consistency_validated": all_sample_contract_consistency_validated,
        "all_sample_index_consistency_validated": all_sample_index_consistency_validated,
        "all_ligand_counts_validated": all_ligand_counts_validated,
        "all_endpoint_counts_validated": all_endpoint_counts_validated,
        "all_pocket_dependencies_validated": all_pocket_dependencies_validated,
        "all_ligand_topology_dependencies_validated": all_ligand_topology_dependencies_validated,
        "all_mask_fields_validated": all_mask_fields_validated,
        "all_feature_semantics_status_validated": all_feature_semantics_status_validated,
        "all_tensor_status_validated": all_tensor_status_validated,
        "all_loader_training_boundaries_validated": all_loader_training_boundaries_validated,
        "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        "all_dependency_counts_validated": all_dependency_counts_validated,
        "all_feature_semantics_audit_required_before_training": all_feature_semantics_audit_required_before_training,
        "no_feature_semantics_claimed_fully_audited": no_feature_semantics_claimed_fully_audited,
        "all_feature_qa_passed": all_feature_qa_passed,
        "all_mask_qa_passed": all_mask_qa_passed,
        "all_model_input_smoke_row_qa_passed": all_model_input_smoke_row_qa_passed,
        "model_input_qa_passed": model_input_qa_passed,
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
        "ready_for_loader_shape_dry_run": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13w_precondition": {"validated": True, "model_input_smoke_index_rows": 3},
        "row_qa": {"row_count": len(row_qa_rows), "all_model_input_smoke_row_qa_passed": all_model_input_smoke_row_qa_passed},
        "dependency_qa": {"row_count": len(dependency_qa_rows), "all_dependency_counts_validated": all_dependency_counts_validated},
        "feature_qa": {"row_count": len(feature_qa_rows), "all_feature_qa_passed": all_feature_qa_passed},
        "mask_qa": {"row_count": len(mask_qa_rows), "all_mask_qa_passed": all_mask_qa_passed},
        "readiness_boundary": {"ready_for_loader_shape_dry_run": True, "ready_for_training": False},
    }
    return {
        "row_qa_rows": row_qa_rows,
        "dependency_qa_rows": dependency_qa_rows,
        "feature_qa_rows": feature_qa_rows,
        "mask_qa_rows": mask_qa_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

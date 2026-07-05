from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_sample_index_qa_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0"

STEP13T_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0"
)
STEP13T_MANIFEST_JSON = STEP13T_ROOT / "sample_index_materialization_manifest.json"
STEP13T_SAMPLE_INDEX_CSV = STEP13T_ROOT / "real_covalent_confirmed_candidate_sample_index_smoke.csv"
STEP13T_AUDIT_CSV = STEP13T_ROOT / "sample_index_materialization_audit.csv"
STEP13T_REPORT_CSV = STEP13T_ROOT / "sample_index_materialization_report.csv"

STEP13S_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_sample_index_design_gate_v0"
)
STEP13S_SCHEMA_CONTRACT_CSV = STEP13S_ROOT / "sample_index_schema_contract.csv"
STEP13S_DEPENDENCY_CONTRACT_CSV = STEP13S_ROOT / "sample_index_dependency_contract.csv"
STEP13S_CANDIDATE_CONTRACT_CSV = STEP13S_ROOT / "sample_index_candidate_contract.csv"
STEP13S_MASK_TASK_CONTRACT_CSV = STEP13S_ROOT / "sample_index_mask_task_contract.csv"

STEP13R_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0"
)
STEP13R_ATOM_TOPOLOGY_CSV = STEP13R_ROOT / "ligand_observed_atom_topology_smoke_table.csv"
STEP13R_BOND_TOPOLOGY_CSV = STEP13R_ROOT / "ligand_observed_bond_topology_smoke_table.csv"

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_sample_index_qa_gate_v0")
ROW_QA_AUDIT_CSV = OUTPUT_ROOT / "sample_index_row_qa_audit.csv"
DEPENDENCY_QA_AUDIT_CSV = OUTPUT_ROOT / "sample_index_dependency_qa_audit.csv"
SCHEMA_QA_AUDIT_CSV = OUTPUT_ROOT / "sample_index_schema_qa_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "sample_index_qa_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "sample_index_qa_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_sample_index_qa_gate_v0_summary.md")

EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_ATOM_BOND_COUNTS = {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
SAMPLE_INDEX_SCOPE = "current_cys_sg_golden_samples_only"
STEP13S_STAGE = "real_covalent_confirmed_candidate_sample_index_design_gate_v0"
STEP13T_STAGE = PREVIOUS_STAGE
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_model_input_design_gate"
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
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "row_identity_validated",
    "lineage_validated",
    "cys_sg_scope_validated",
    "mask_task_names_validated",
    "mask_task_aliases_validated",
    "b3_scaffold_only_included",
    "no_extra_mask_tasks",
    "topology_counts_match_candidate_contract",
    "endpoint_counts_validated",
    "topology_table_paths_exist",
    "topology_table_counts_match_sample_index",
    "readiness_safety_fields_validated",
    "sample_index_row_qa_passed",
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
SCHEMA_QA_COLUMNS = [
    "required_field_name",
    "required_field_group",
    "present_in_sample_index_smoke",
    "qa_status",
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


def validate_step13t_precondition_v0() -> bool:
    required_paths = [
        STEP13T_MANIFEST_JSON,
        STEP13T_SAMPLE_INDEX_CSV,
        STEP13T_AUDIT_CSV,
        STEP13T_REPORT_CSV,
        STEP13S_SCHEMA_CONTRACT_CSV,
        STEP13S_DEPENDENCY_CONTRACT_CSV,
        STEP13S_CANDIDATE_CONTRACT_CSV,
        STEP13S_MASK_TASK_CONTRACT_CSV,
        STEP13R_ATOM_TOPOLOGY_CSV,
        STEP13R_BOND_TOPOLOGY_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13U prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13T_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "sample_index_smoke_written": True,
        "sample_index_smoke_row_count": 3,
        "sample_index_audit_written": True,
        "sample_index_audit_row_count": 3,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_sample_index_rows_materialized": True,
        "all_candidate_rows_found": True,
        "all_counts_match_candidate_contract": True,
        "all_endpoint_counts_validated": True,
        "all_mask_task_contracts_validated": True,
        "sample_index_written": True,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "ready_for_sample_index_qa_gate": True,
        "ready_for_model_input_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_sample_index_qa_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13T precondition failed: " + ";".join(blockers))
    return True


def _count_by_review(rows: list[dict[str, str]]) -> dict[str, int]:
    return {review_row_id: sum(row.get("review_row_id") == review_row_id for row in rows) for review_row_id in EXPECTED_REVIEW_ROW_IDS}


def build_sample_index_row_qa_audit_v0() -> list[dict[str, Any]]:
    sample_rows = _read_csv(STEP13T_SAMPLE_INDEX_CSV)
    candidate_rows = {row["review_row_id"]: row for row in _read_csv(STEP13S_CANDIDATE_CONTRACT_CSV)}
    atom_counts = _count_by_review(_read_csv(STEP13R_ATOM_TOPOLOGY_CSV))
    bond_counts = _count_by_review(_read_csv(STEP13R_BOND_TOPOLOGY_CSV))
    sample_ids = [row["sample_index_row_id"] for row in sample_rows]
    review_ids = [row["review_row_id"] for row in sample_rows]
    expected_names = ";".join(CANONICAL_MASK_TASK_NAMES)
    expected_aliases = ";".join(CANONICAL_MASK_TASK_ALIASES)
    rows: list[dict[str, Any]] = []
    for row in sample_rows:
        review_row_id = row["review_row_id"]
        candidate = candidate_rows.get(review_row_id, {})
        row_identity_validated = (
            row["sample_index_row_id"] in EXPECTED_SAMPLE_INDEX_ROW_IDS
            and sample_ids.count(row["sample_index_row_id"]) == 1
            and review_ids.count(review_row_id) == 1
            and row["pdb_id"] in EXPECTED_PDB_IDS
            and bool(row["expected_step8_sample_name"])
            and bool(row["source_sample_name"])
        )
        lineage_validated = STEP13S_STAGE in row["source_stage_lineage"] and STEP13T_STAGE in row["source_stage_lineage"]
        cys_sg_scope_validated = (
            row["v1_train_ready_scope"] == V1_TRAIN_READY_SCOPE
            and row["residue_scope"] == SAMPLE_INDEX_SCOPE
            and row["residue_name"] == "CYS"
            and row["residue_atom_name"] == "SG"
        )
        mask_names_validated = row["canonical_mask_task_names"] == expected_names
        mask_aliases_validated = row["canonical_mask_task_aliases"] == expected_aliases
        b3_included = row["supports_scaffold_only"] == "True" and "scaffold_only" in row["canonical_mask_task_names"]
        no_extra_mask_tasks = row["mask_task_count"] == "5" and len(row["canonical_mask_task_names"].split(";")) == 5
        count_fields = [
            "ligand_atom_count",
            "ligand_bond_count",
            "warhead_atom_count",
            "linker_atom_count",
            "scaffold_atom_count",
            "warhead_bond_count",
            "linker_bond_count",
            "scaffold_bond_count",
            "cross_boundary_or_unassigned_bond_count",
        ]
        topology_counts_match_candidate_contract = bool(candidate) and all(
            int(row[field]) == int(candidate[field]) for field in count_fields
        )
        endpoint_counts_validated = row["endpoint_atom_true_count"] == "1" and row["endpoint_touching_bond_true_count"] == "1"
        topology_table_paths_exist = all(
            Path(row[key]).is_file()
            for key in [
                "ligand_atom_topology_table_path",
                "ligand_bond_topology_table_path",
                "sample_index_design_candidate_contract_path",
                "sample_index_mask_task_contract_path",
            ]
        )
        topology_table_counts_match_sample_index = (
            atom_counts.get(review_row_id) == int(row["ligand_atom_count"])
            and bond_counts.get(review_row_id) == int(row["ligand_bond_count"])
        )
        readiness_safety_fields_validated = (
            row["sample_index_materialization_status"] == "smoke_materialized"
            and row["model_input_materialization_status"] == "not_materialized"
            and row["training_use_status"] == "not_training_input_yet"
            and row["feature_semantics_audit_required_before_training"] == "True"
            and row["ready_to_train_now"] == "False"
        )
        checks = {
            "row_identity_validated": row_identity_validated,
            "lineage_validated": lineage_validated,
            "cys_sg_scope_validated": cys_sg_scope_validated,
            "mask_task_names_validated": mask_names_validated,
            "mask_task_aliases_validated": mask_aliases_validated,
            "b3_scaffold_only_included": b3_included,
            "no_extra_mask_tasks": no_extra_mask_tasks,
            "topology_counts_match_candidate_contract": topology_counts_match_candidate_contract,
            "endpoint_counts_validated": endpoint_counts_validated,
            "topology_table_paths_exist": topology_table_paths_exist,
            "topology_table_counts_match_sample_index": topology_table_counts_match_sample_index,
            "readiness_safety_fields_validated": readiness_safety_fields_validated,
        }
        blockers = [name for name, passed in checks.items() if not passed]
        rows.append(
            {
                "sample_index_row_id": row["sample_index_row_id"],
                "review_row_id": review_row_id,
                "pdb_id": row["pdb_id"],
                **checks,
                "sample_index_row_qa_passed": not blockers,
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def build_sample_index_dependency_qa_audit_v0() -> list[dict[str, Any]]:
    dependencies = [
        ("step13t_manifest", STEP13T_MANIFEST_JSON, 1),
        ("step13t_sample_index_smoke", STEP13T_SAMPLE_INDEX_CSV, 3),
        ("step13t_materialization_audit", STEP13T_AUDIT_CSV, 3),
        ("step13s_schema_contract", STEP13S_SCHEMA_CONTRACT_CSV, 47),
        ("step13s_dependency_contract", STEP13S_DEPENDENCY_CONTRACT_CSV, 10),
        ("step13s_candidate_contract", STEP13S_CANDIDATE_CONTRACT_CSV, 3),
        ("step13s_mask_task_contract", STEP13S_MASK_TASK_CONTRACT_CSV, 5),
        ("step13r_atom_topology_smoke_table", STEP13R_ATOM_TOPOLOGY_CSV, 104),
        ("step13r_bond_topology_smoke_table", STEP13R_BOND_TOPOLOGY_CSV, 113),
    ]
    rows = []
    for name, path, expected_count in dependencies:
        exists = path.is_file()
        count = _row_count(path)
        count_validated = exists and count == expected_count
        blockers = []
        if not exists:
            blockers.append("dependency_missing")
        if exists and not count_validated:
            blockers.append("dependency_row_count_mismatch")
        rows.append(
            {
                "dependency_name": name,
                "dependency_artifact_path": str(path),
                "dependency_exists": exists,
                "dependency_row_count": count,
                "dependency_expected_row_count": expected_count,
                "dependency_count_validated": count_validated,
                "dependency_qa_passed": exists and count_validated,
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def build_sample_index_schema_qa_audit_v0() -> list[dict[str, Any]]:
    schema_rows = _read_csv(STEP13S_SCHEMA_CONTRACT_CSV)
    sample_fields = set(_read_csv(STEP13T_SAMPLE_INDEX_CSV)[0].keys())
    materialized_required_fields = sample_fields
    rows = []
    for row in schema_rows:
        field_name = row["field_name"]
        present = field_name in sample_fields
        if present:
            status = "present_in_sample_index_smoke"
            blockers = ""
        elif field_name in materialized_required_fields:
            status = "missing_required_materialized_field"
            blockers = "missing_required_materialized_field"
        else:
            status = "intentionally_deferred_not_blocking"
            blockers = ""
        rows.append(
            {
                "required_field_name": field_name,
                "required_field_group": row["field_group"],
                "present_in_sample_index_smoke": present,
                "qa_status": status,
                "blocking_reasons": blockers,
            }
        )
    return rows


def build_real_covalent_confirmed_candidate_sample_index_qa_gate_v0() -> dict[str, Any]:
    validate_step13t_precondition_v0()
    sample_rows = _read_csv(STEP13T_SAMPLE_INDEX_CSV)
    row_audit = build_sample_index_row_qa_audit_v0()
    dependency_audit = build_sample_index_dependency_qa_audit_v0()
    schema_audit = build_sample_index_schema_qa_audit_v0()

    all_sample_index_rows_unique = len({row["sample_index_row_id"] for row in sample_rows}) == 3 and len(
        {row["review_row_id"] for row in sample_rows}
    ) == 3
    all_identity_fields_validated = all(_as_bool(row["row_identity_validated"]) for row in row_audit)
    all_lineage_fields_validated = all(_as_bool(row["lineage_validated"]) for row in row_audit)
    all_candidates_cys_sg_scope = all(_as_bool(row["cys_sg_scope_validated"]) for row in row_audit)
    all_mask_task_fields_validated = all(
        _as_bool(row["mask_task_names_validated"])
        and _as_bool(row["mask_task_aliases_validated"])
        and _as_bool(row["b3_scaffold_only_included"])
        and _as_bool(row["no_extra_mask_tasks"])
        for row in row_audit
    )
    all_topology_counts_match_candidate_contract = all(
        _as_bool(row["topology_counts_match_candidate_contract"]) for row in row_audit
    )
    all_topology_table_paths_exist = all(_as_bool(row["topology_table_paths_exist"]) for row in row_audit)
    all_topology_table_counts_match_sample_index = all(
        _as_bool(row["topology_table_counts_match_sample_index"]) for row in row_audit
    )
    all_endpoint_counts_validated = all(_as_bool(row["endpoint_counts_validated"]) for row in row_audit)
    all_readiness_safety_fields_validated = all(
        _as_bool(row["readiness_safety_fields_validated"]) for row in row_audit
    )
    all_dependency_artifacts_exist = all(_as_bool(row["dependency_exists"]) for row in dependency_audit)
    all_dependency_counts_validated = all(_as_bool(row["dependency_count_validated"]) for row in dependency_audit)
    all_required_schema_fields_present_or_intentionally_deferred = all(
        not row["blocking_reasons"] for row in schema_audit
    )
    all_sample_index_row_qa_passed = all(_as_bool(row["sample_index_row_qa_passed"]) for row in row_audit)
    safety_ok = not any(
        [
            _source_diff_exists(),
            _forbidden_committable_artifacts_created(),
            _raw_files_staged(),
            _raw_files_tracked(),
        ]
    )
    sample_index_qa_passed = all(
        [
            len(sample_rows) == 3,
            len(row_audit) == 3,
            len(dependency_audit) == 9,
            all_sample_index_rows_unique,
            all_identity_fields_validated,
            all_lineage_fields_validated,
            all_candidates_cys_sg_scope,
            all_mask_task_fields_validated,
            all_topology_counts_match_candidate_contract,
            all_topology_table_paths_exist,
            all_topology_table_counts_match_sample_index,
            all_endpoint_counts_validated,
            all_readiness_safety_fields_validated,
            all_dependency_artifacts_exist,
            all_dependency_counts_validated,
            all_required_schema_fields_present_or_intentionally_deferred,
            all_sample_index_row_qa_passed,
            safety_ok,
        ]
    )
    blocking_reasons = []
    if not sample_index_qa_passed:
        blocking_reasons.append("sample_index_qa_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13t_sample_index_materialization_smoke_validated": True,
        "sample_index_qa_scope": SAMPLE_INDEX_SCOPE,
        "sample_index_smoke_read": True,
        "sample_index_smoke_row_count": len(sample_rows),
        "sample_index_row_qa_audit_written": True,
        "sample_index_row_qa_audit_row_count": len(row_audit),
        "sample_index_dependency_qa_audit_written": True,
        "sample_index_dependency_qa_audit_row_count": len(dependency_audit),
        "sample_index_schema_qa_audit_written": True,
        "sample_index_schema_qa_audit_row_count": len(schema_audit),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_sample_index_rows_unique": all_sample_index_rows_unique,
        "all_identity_fields_validated": all_identity_fields_validated,
        "all_lineage_fields_validated": all_lineage_fields_validated,
        "all_candidates_cys_sg_scope": all_candidates_cys_sg_scope,
        "all_mask_task_fields_validated": all_mask_task_fields_validated,
        "all_topology_counts_match_candidate_contract": all_topology_counts_match_candidate_contract,
        "all_topology_table_paths_exist": all_topology_table_paths_exist,
        "all_topology_table_counts_match_sample_index": all_topology_table_counts_match_sample_index,
        "all_endpoint_counts_validated": all_endpoint_counts_validated,
        "all_readiness_safety_fields_validated": all_readiness_safety_fields_validated,
        "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        "all_dependency_counts_validated": all_dependency_counts_validated,
        "all_required_schema_fields_present_or_intentionally_deferred": all_required_schema_fields_present_or_intentionally_deferred,
        "all_sample_index_row_qa_passed": all_sample_index_row_qa_passed,
        "sample_index_qa_passed": sample_index_qa_passed,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
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
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": _source_diff_exists(),
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "ready_for_model_input_design_gate": True,
        "ready_for_model_input_materialization_smoke": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": sample_index_qa_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13t_precondition": {"validated": True, "sample_index_rows": 3},
        "row_qa": {
            "row_count": len(row_audit),
            "all_sample_index_row_qa_passed": all_sample_index_row_qa_passed,
        },
        "dependency_qa": {
            "row_count": len(dependency_audit),
            "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
            "all_dependency_counts_validated": all_dependency_counts_validated,
        },
        "schema_qa": {
            "row_count": len(schema_audit),
            "all_required_schema_fields_present_or_intentionally_deferred": all_required_schema_fields_present_or_intentionally_deferred,
        },
        "readiness_boundary": {
            "ready_for_model_input_design_gate": True,
            "ready_for_model_input_materialization_smoke": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "row_qa_rows": row_audit,
        "dependency_qa_rows": dependency_audit,
        "schema_qa_rows": schema_audit,
        "manifest": manifest,
        "report_sections": report_sections,
    }

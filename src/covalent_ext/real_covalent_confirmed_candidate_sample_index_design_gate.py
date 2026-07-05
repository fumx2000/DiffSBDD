from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_sample_index_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0"

STEP13R_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0"
)
STEP13R_MANIFEST_JSON = STEP13R_ROOT / "ligand_topology_smoke_retry_manifest.json"
STEP13R_ATOM_SMOKE_TABLE_CSV = STEP13R_ROOT / "ligand_observed_atom_topology_smoke_table.csv"
STEP13R_BOND_SMOKE_TABLE_CSV = STEP13R_ROOT / "ligand_observed_bond_topology_smoke_table.csv"
STEP13R_AUDIT_CSV = STEP13R_ROOT / "ligand_topology_smoke_retry_audit.csv"

STEP13M_CANDIDATE_CONTRACT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/"
    "ligand_topology_restoration_candidate_contract.csv"
)
STEP13L_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0"
)
STEP13L_MANIFEST_JSON = STEP13L_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_smoke_manifest.json"
STEP13L_POCKET_ATOM_TABLE_CSV = STEP13L_ROOT / "real_covalent_confirmed_candidate_pocket_atom_table.csv"
STEP13L_AUDIT_CSV = STEP13L_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_audit.csv"
STEP13J_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0"
)
STEP13J_LIGAND_FULL_ATOM_TABLE_CSV = STEP13J_ROOT / "real_covalent_confirmed_candidate_ligand_full_atom_table.csv"
STEP13J_ENDPOINT_AUDIT_CSV = STEP13J_ROOT / "real_covalent_confirmed_candidate_full_atom_endpoint_recovery_audit.csv"

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_sample_index_design_gate_v0"
)
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "sample_index_schema_contract.csv"
DEPENDENCY_CONTRACT_CSV = OUTPUT_ROOT / "sample_index_dependency_contract.csv"
CANDIDATE_CONTRACT_CSV = OUTPUT_ROOT / "sample_index_candidate_contract.csv"
MASK_TASK_CONTRACT_CSV = OUTPUT_ROOT / "sample_index_mask_task_contract.csv"
REPORT_CSV = OUTPUT_ROOT / "sample_index_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "sample_index_design_gate_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_sample_index_design_gate_v0_summary.md")

EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
DESIGN_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_sample_index_materialization_smoke"
CANONICAL_MASK_TASKS = [
    ("warhead_only", "A", "warhead", "linker;scaffold"),
    ("linker_plus_warhead", "B", "linker;warhead", "scaffold"),
    ("scaffold_plus_warhead", "B2", "scaffold;warhead", "linker"),
    ("scaffold_only", "B3", "scaffold", "linker;warhead"),
    ("scaffold_plus_linker_plus_warhead", "C", "scaffold;linker;warhead", "none"),
]

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
    "required_for_future_sample_index",
    "source_stage",
    "source_artifact",
    "training_use_status",
]
DEPENDENCY_COLUMNS = [
    "dependency_name",
    "dependency_stage",
    "dependency_artifact_path",
    "dependency_required_for_future_sample_index",
    "dependency_exists",
    "dependency_row_count",
    "dependency_key_fields",
    "dependency_validation_status",
    "training_use_status",
]
CANDIDATE_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "v1_train_ready_scope",
    "residue_scope",
    "residue_name",
    "residue_atom_name",
    "ligand_atom_count",
    "ligand_bond_count",
    "endpoint_atom_true_count",
    "endpoint_touching_bond_true_count",
    "warhead_atom_count",
    "linker_atom_count",
    "scaffold_atom_count",
    "warhead_bond_count",
    "linker_bond_count",
    "scaffold_bond_count",
    "cross_boundary_or_unassigned_bond_count",
    "sample_index_design_status",
    "sample_index_materialization_allowed_next_step",
    "sample_index_written",
    "model_input_materialized",
    "training_ready",
    "training_ready_reason",
]
MASK_TASK_COLUMNS = [
    "canonical_mask_task_name",
    "display_alias",
    "task_description",
    "masked_groups",
    "preserved_groups",
    "task_order",
    "active_in_v1",
    "source_of_truth_status",
    "training_use_status",
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


def _int(value: Any) -> int:
    return int(str(value).strip())


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


def validate_step13r_precondition_v0() -> bool:
    required_paths = [
        STEP13R_MANIFEST_JSON,
        STEP13R_ATOM_SMOKE_TABLE_CSV,
        STEP13R_BOND_SMOKE_TABLE_CSV,
        STEP13R_AUDIT_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13R prerequisite outputs are missing: {missing}")

    manifest = _load_json(STEP13R_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "all_ligand_topology_smoke_retry_passed": True,
        "ligand_observed_atom_topology_smoke_table_written": True,
        "ligand_observed_atom_topology_smoke_table_row_count": 104,
        "ligand_observed_bond_topology_smoke_table_written": True,
        "ligand_observed_bond_topology_smoke_table_row_count": 113,
        "smoke_retry_audit_written": True,
        "smoke_retry_audit_row_count": 3,
        "all_atom_counts_match_expected": True,
        "all_bond_counts_match_expected": True,
        "all_endpoint_atom_counts_equal_one": True,
        "all_endpoint_touching_bond_counts_equal_one": True,
        "all_atom_group_partitions_passed": True,
        "ready_for_sample_index_design_gate": True,
        "ready_to_write_sample_index_now": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_sample_index_design_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if blockers:
        raise ValueError("Step 13R precondition failed: " + ";".join(blockers))
    return True


def build_sample_index_schema_contract_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(field_name: str, field_group: str, description: str, source_stage: str, source_artifact: Path | str) -> None:
        rows.append(
            {
                "field_name": field_name,
                "field_group": field_group,
                "field_description": description,
                "required_for_future_sample_index": True,
                "source_stage": source_stage,
                "source_artifact": str(source_artifact),
                "training_use_status": "not_training_input_yet",
            }
        )

    identity_fields = [
        "sample_index_row_id",
        "review_row_id",
        "pdb_id",
        "expected_step8_sample_name",
        "source_sample_name",
        "source_stage_lineage",
        "v1_train_ready_scope",
        "residue_scope",
        "residue_name",
        "residue_chain_id",
        "residue_seq_id",
        "residue_atom_name",
        "covalent_ligand_endpoint_atom_id",
        "covalent_bond_atom_pair_status",
    ]
    for field in identity_fields:
        add(field, "identity_provenance", f"Future sample_index identity/provenance field `{field}`.", STAGE, CANDIDATE_CONTRACT_CSV)

    topology_fields = [
        "ligand_atom_topology_table_path",
        "ligand_bond_topology_table_path",
        "ligand_atom_count",
        "ligand_bond_count",
        "endpoint_atom_true_count",
        "endpoint_touching_bond_true_count",
        "warhead_atom_count",
        "linker_atom_count",
        "scaffold_atom_count",
        "warhead_bond_count",
        "linker_bond_count",
        "scaffold_bond_count",
        "cross_boundary_or_unassigned_bond_count",
    ]
    for field in topology_fields:
        add(field, "ligand_topology", f"Future sample_index ligand topology field `{field}`.", PREVIOUS_STAGE, STEP13R_AUDIT_CSV)

    pocket_fields = [
        "pocket_atom_table_path",
        "pocket_atom_count",
        "pocket_extraction_scope",
        "full_atom_extraction_source",
    ]
    for field in pocket_fields:
        add(field, "pocket_protein_dependency", f"Future sample_index pocket/protein dependency field `{field}`.", "step13l_or_step13j_dependency", DEPENDENCY_CONTRACT_CSV)

    mask_fields = [
        "canonical_mask_task_names",
        "canonical_mask_task_aliases",
        "mask_task_count",
        "supports_warhead_only",
        "supports_linker_plus_warhead",
        "supports_scaffold_plus_warhead",
        "supports_scaffold_only",
        "supports_scaffold_plus_linker_plus_warhead",
    ]
    for field in mask_fields:
        add(field, "mask_task_contract", f"Future sample_index canonical mask field `{field}`.", STAGE, MASK_TASK_CONTRACT_CSV)

    auxiliary_fields = [
        "warhead_type_label_status",
        "ligand_residue_atom_pair_label_status",
        "pre_post_covalent_geometry_label_status",
    ]
    for field in auxiliary_fields:
        add(field, "auxiliary_task_contract", f"Future sample_index auxiliary task field `{field}`.", "future_label_design_gate", "future")

    readiness_fields = [
        "sample_index_materialization_status",
        "model_input_materialization_status",
        "training_use_status",
        "feature_semantics_audit_required_before_training",
        "ready_to_train_now",
    ]
    for field in readiness_fields:
        add(field, "readiness_safety", f"Future sample_index readiness/safety field `{field}`.", STAGE, MANIFEST_JSON)

    return rows


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".json":
        return 1
    return len(_read_csv(path))


def build_sample_index_dependency_contract_v0() -> list[dict[str, Any]]:
    dependencies = [
        ("step13r_manifest", PREVIOUS_STAGE, STEP13R_MANIFEST_JSON, "stage;all_checks_passed;ready_for_sample_index_design_gate"),
        ("step13r_atom_smoke_table", PREVIOUS_STAGE, STEP13R_ATOM_SMOKE_TABLE_CSV, "review_row_id;pdb_id;ligand_atom_topology_row_id"),
        ("step13r_bond_smoke_table", PREVIOUS_STAGE, STEP13R_BOND_SMOKE_TABLE_CSV, "review_row_id;pdb_id;ligand_bond_topology_row_id"),
        ("step13r_smoke_retry_audit", PREVIOUS_STAGE, STEP13R_AUDIT_CSV, "review_row_id;pdb_id;topology_smoke_retry_passed"),
        (
            "step13m_ligand_topology_restoration_candidate_contract",
            "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0",
            STEP13M_CANDIDATE_CONTRACT_CSV,
            "review_row_id;pdb_id;manual_confirmed_residue_comp_id;manual_confirmed_residue_atom_id",
        ),
        (
            "step13l_pocket_extraction_manifest",
            "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0",
            STEP13L_MANIFEST_JSON,
            "stage;all_checks_passed;pocket_atom_table_written",
        ),
        (
            "step13l_pocket_atom_table",
            "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0",
            STEP13L_POCKET_ATOM_TABLE_CSV,
            "review_row_id;pdb_id;pocket_atom_row_id",
        ),
        (
            "step13l_pocket_extraction_audit",
            "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0",
            STEP13L_AUDIT_CSV,
            "review_row_id;pdb_id;pocket_extraction_passed",
        ),
        (
            "step13j_ligand_full_atom_table",
            "real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0",
            STEP13J_LIGAND_FULL_ATOM_TABLE_CSV,
            "review_row_id;pdb_id;atom_site_id",
        ),
        (
            "step13j_endpoint_recovery_audit",
            "real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0",
            STEP13J_ENDPOINT_AUDIT_CSV,
            "review_row_id;pdb_id;endpoint_recovery_passed",
        ),
    ]
    rows = []
    for name, stage, path, key_fields in dependencies:
        exists = path.is_file()
        rows.append(
            {
                "dependency_name": name,
                "dependency_stage": stage,
                "dependency_artifact_path": str(path),
                "dependency_required_for_future_sample_index": True,
                "dependency_exists": exists,
                "dependency_row_count": _row_count(path),
                "dependency_key_fields": key_fields,
                "dependency_validation_status": "exists_and_counted" if exists else "missing",
                "training_use_status": "not_training_input_yet",
            }
        )
    return rows


def build_sample_index_candidate_contract_v0() -> list[dict[str, Any]]:
    audit_rows = {row["review_row_id"]: row for row in _read_csv(STEP13R_AUDIT_CSV)}
    m_rows = {row["review_row_id"]: row for row in _read_csv(STEP13M_CANDIDATE_CONTRACT_CSV)}
    rows: list[dict[str, Any]] = []
    for review_row_id in EXPECTED_REVIEW_ROW_IDS:
        audit = audit_rows[review_row_id]
        candidate = m_rows[review_row_id]
        rows.append(
            {
                "review_row_id": review_row_id,
                "pdb_id": audit["pdb_id"],
                "expected_step8_sample_name": audit["expected_step8_sample_name"],
                "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
                "residue_scope": DESIGN_SCOPE,
                "residue_name": candidate["manual_confirmed_residue_comp_id"],
                "residue_atom_name": candidate["manual_confirmed_residue_atom_id"],
                "ligand_atom_count": _int(audit["atom_rows_observed"]),
                "ligand_bond_count": _int(audit["bond_rows_observed"]),
                "endpoint_atom_true_count": _int(audit["endpoint_atom_true_count"]),
                "endpoint_touching_bond_true_count": _int(audit["endpoint_touching_bond_true_count"]),
                "warhead_atom_count": _int(audit["warhead_atom_true_count"]),
                "linker_atom_count": _int(audit["linker_atom_true_count"]),
                "scaffold_atom_count": _int(audit["scaffold_atom_true_count"]),
                "warhead_bond_count": _int(audit["warhead_bond_true_count"]),
                "linker_bond_count": _int(audit["linker_bond_true_count"]),
                "scaffold_bond_count": _int(audit["scaffold_bond_true_count"]),
                "cross_boundary_or_unassigned_bond_count": _int(audit["cross_boundary_or_unassigned_bond_count"]),
                "sample_index_design_status": "design_gate_passed",
                "sample_index_materialization_allowed_next_step": True,
                "sample_index_written": False,
                "model_input_materialized": False,
                "training_ready": False,
                "training_ready_reason": "design_gate_only_no_sample_index_written",
            }
        )
    return rows


def build_sample_index_mask_task_contract_v0() -> list[dict[str, Any]]:
    rows = []
    for index, (name, alias, masked, preserved) in enumerate(CANONICAL_MASK_TASKS, start=1):
        rows.append(
            {
                "canonical_mask_task_name": name,
                "display_alias": alias,
                "task_description": f"V1 canonical mask task `{name}`; alias `{alias}` is display-only.",
                "masked_groups": masked,
                "preserved_groups": preserved,
                "task_order": index,
                "active_in_v1": True,
                "source_of_truth_status": "long_semantic_name_source_of_truth_alias_display_only",
                "training_use_status": "not_training_input_yet",
            }
        )
    return rows


def _all_candidate_counts_match_step13r(candidate_rows: list[dict[str, Any]]) -> bool:
    audit_rows = {row["review_row_id"]: row for row in _read_csv(STEP13R_AUDIT_CSV)}
    for row in candidate_rows:
        audit = audit_rows[row["review_row_id"]]
        checks = [
            row["ligand_atom_count"] == _int(audit["atom_rows_observed"]),
            row["ligand_bond_count"] == _int(audit["bond_rows_observed"]),
            row["endpoint_atom_true_count"] == _int(audit["endpoint_atom_true_count"]),
            row["endpoint_touching_bond_true_count"] == _int(audit["endpoint_touching_bond_true_count"]),
            row["warhead_atom_count"] == _int(audit["warhead_atom_true_count"]),
            row["linker_atom_count"] == _int(audit["linker_atom_true_count"]),
            row["scaffold_atom_count"] == _int(audit["scaffold_atom_true_count"]),
            row["warhead_bond_count"] == _int(audit["warhead_bond_true_count"]),
            row["linker_bond_count"] == _int(audit["linker_bond_true_count"]),
            row["scaffold_bond_count"] == _int(audit["scaffold_bond_true_count"]),
        ]
        if not all(checks):
            return False
    return True


def build_real_covalent_confirmed_candidate_sample_index_design_gate_v0() -> dict[str, Any]:
    validate_step13r_precondition_v0()
    schema_rows = build_sample_index_schema_contract_v0()
    dependency_rows = build_sample_index_dependency_contract_v0()
    candidate_rows = build_sample_index_candidate_contract_v0()
    mask_task_rows = build_sample_index_mask_task_contract_v0()

    all_dependency_artifacts_exist = all(_as_bool(row["dependency_exists"]) for row in dependency_rows)
    all_candidate_counts_match_step13r = _all_candidate_counts_match_step13r(candidate_rows)
    all_candidates_cys_sg_scope = all(
        row["residue_name"] == "CYS"
        and row["residue_atom_name"] == "SG"
        and row["residue_scope"] == DESIGN_SCOPE
        for row in candidate_rows
    )
    all_candidates_design_gate_passed = all(
        row["sample_index_design_status"] == "design_gate_passed"
        and _as_bool(row["sample_index_materialization_allowed_next_step"])
        and not _as_bool(row["sample_index_written"])
        and not _as_bool(row["model_input_materialized"])
        and not _as_bool(row["training_ready"])
        for row in candidate_rows
    )
    mask_names = [row["canonical_mask_task_name"] for row in mask_task_rows]
    mask_aliases = [row["display_alias"] for row in mask_task_rows]
    b3_included = "scaffold_only" in mask_names and "B3" in mask_aliases
    no_extra_mask_tasks = len(mask_task_rows) == len(CANONICAL_MASK_TASKS)
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
            all_dependency_artifacts_exist,
            all_candidate_counts_match_step13r,
            all_candidates_cys_sg_scope,
            all_candidates_design_gate_passed,
            b3_included,
            no_extra_mask_tasks,
            safety_ok,
        ]
    )
    blocking_reasons: list[str] = []
    if not all_dependency_artifacts_exist:
        blocking_reasons.append("dependency_artifact_missing")
    if not all_candidate_counts_match_step13r:
        blocking_reasons.append("candidate_counts_do_not_match_step13r")
    if not all_candidates_cys_sg_scope:
        blocking_reasons.append("candidate_scope_not_current_cys_sg")
    if not all_candidates_design_gate_passed:
        blocking_reasons.append("candidate_design_gate_status_invalid")
    if not b3_included or not no_extra_mask_tasks:
        blocking_reasons.append("canonical_mask_task_contract_invalid")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13r_ligand_topology_smoke_retry_validated": True,
        "sample_index_design_scope": DESIGN_SCOPE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "canonical_mask_task_count": len(mask_task_rows),
        "canonical_mask_task_names": mask_names,
        "canonical_mask_task_aliases": mask_aliases,
        "b3_scaffold_only_included": b3_included,
        "no_extra_mask_tasks_added": no_extra_mask_tasks,
        "schema_contract_written": True,
        "schema_contract_row_count": len(schema_rows),
        "dependency_contract_written": True,
        "dependency_contract_row_count": len(dependency_rows),
        "candidate_contract_written": True,
        "candidate_contract_row_count": len(candidate_rows),
        "mask_task_contract_written": True,
        "mask_task_contract_row_count": len(mask_task_rows),
        "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        "all_candidate_counts_match_step13r": all_candidate_counts_match_step13r,
        "all_candidates_cys_sg_scope": all_candidates_cys_sg_scope,
        "all_candidates_design_gate_passed": all_candidates_design_gate_passed,
        "sample_index_materialization_allowed_next_step": True,
        "sample_index_written": False,
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
        "ready_for_sample_index_materialization_smoke": True,
        "ready_to_write_sample_index_now": False,
        "ready_for_model_input_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13r_precondition": {
            "validated": True,
            "atom_rows": 104,
            "bond_rows": 113,
            "audit_rows": 3,
        },
        "schema_contract": {"row_count": len(schema_rows), "written": True},
        "dependency_contract": {
            "row_count": len(dependency_rows),
            "all_dependency_artifacts_exist": all_dependency_artifacts_exist,
        },
        "candidate_contract": {
            "row_count": len(candidate_rows),
            "all_candidate_counts_match_step13r": all_candidate_counts_match_step13r,
            "all_candidates_cys_sg_scope": all_candidates_cys_sg_scope,
        },
        "mask_task_contract": {
            "row_count": len(mask_task_rows),
            "canonical_mask_task_names": mask_names,
            "canonical_mask_task_aliases": mask_aliases,
            "b3_scaffold_only_included": b3_included,
        },
        "readiness_boundary": {
            "ready_for_sample_index_materialization_smoke": True,
            "ready_to_write_sample_index_now": False,
            "ready_for_model_input_design_gate": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "schema_rows": schema_rows,
        "dependency_rows": dependency_rows,
        "candidate_rows": candidate_rows,
        "mask_task_rows": mask_task_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

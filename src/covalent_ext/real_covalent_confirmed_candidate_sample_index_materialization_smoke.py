from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_sample_index_design_gate_v0"

STEP13S_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_sample_index_design_gate_v0"
)
STEP13S_MANIFEST_JSON = STEP13S_ROOT / "sample_index_design_gate_manifest.json"
STEP13S_SCHEMA_CONTRACT_CSV = STEP13S_ROOT / "sample_index_schema_contract.csv"
STEP13S_DEPENDENCY_CONTRACT_CSV = STEP13S_ROOT / "sample_index_dependency_contract.csv"
STEP13S_CANDIDATE_CONTRACT_CSV = STEP13S_ROOT / "sample_index_candidate_contract.csv"
STEP13S_MASK_TASK_CONTRACT_CSV = STEP13S_ROOT / "sample_index_mask_task_contract.csv"

STEP13R_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0"
)
STEP13R_ATOM_SMOKE_TABLE_CSV = STEP13R_ROOT / "ligand_observed_atom_topology_smoke_table.csv"
STEP13R_BOND_SMOKE_TABLE_CSV = STEP13R_ROOT / "ligand_observed_bond_topology_smoke_table.csv"

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0"
)
SAMPLE_INDEX_SMOKE_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_sample_index_smoke.csv"
AUDIT_CSV = OUTPUT_ROOT / "sample_index_materialization_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "sample_index_materialization_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "sample_index_materialization_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0_summary.md")

EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_SAMPLE_INDEX_ROW_IDS = ["RSIDX_000001", "RSIDX_000002", "RSIDX_000003"]
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
SAMPLE_INDEX_SCOPE = "current_cys_sg_golden_samples_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_sample_index_qa_gate"
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

SAMPLE_INDEX_COLUMNS = [
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "source_sample_name",
    "source_stage_lineage",
    "v1_train_ready_scope",
    "residue_scope",
    "residue_name",
    "residue_atom_name",
    "canonical_mask_task_names",
    "canonical_mask_task_aliases",
    "mask_task_count",
    "supports_warhead_only",
    "supports_linker_plus_warhead",
    "supports_scaffold_plus_warhead",
    "supports_scaffold_only",
    "supports_scaffold_plus_linker_plus_warhead",
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
    "ligand_atom_topology_table_path",
    "ligand_bond_topology_table_path",
    "sample_index_design_candidate_contract_path",
    "sample_index_mask_task_contract_path",
    "sample_index_materialization_status",
    "model_input_materialization_status",
    "training_use_status",
    "feature_semantics_audit_required_before_training",
    "ready_to_train_now",
]
AUDIT_COLUMNS = [
    "sample_index_row_id",
    "review_row_id",
    "pdb_id",
    "candidate_contract_row_found",
    "mask_task_contract_validated",
    "ligand_atom_count_matches_candidate_contract",
    "ligand_bond_count_matches_candidate_contract",
    "endpoint_counts_validated",
    "canonical_mask_count_validated",
    "b3_scaffold_only_included",
    "sample_index_row_materialized",
    "model_input_materialized",
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


def validate_step13s_precondition_v0() -> bool:
    required_paths = [
        STEP13S_MANIFEST_JSON,
        STEP13S_SCHEMA_CONTRACT_CSV,
        STEP13S_DEPENDENCY_CONTRACT_CSV,
        STEP13S_CANDIDATE_CONTRACT_CSV,
        STEP13S_MASK_TASK_CONTRACT_CSV,
        STEP13R_ATOM_SMOKE_TABLE_CSV,
        STEP13R_BOND_SMOKE_TABLE_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13T prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13S_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "schema_contract_written": True,
        "schema_contract_row_count": 47,
        "dependency_contract_written": True,
        "dependency_contract_row_count": 10,
        "candidate_contract_written": True,
        "candidate_contract_row_count": 3,
        "mask_task_contract_written": True,
        "mask_task_contract_row_count": 5,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_dependency_artifacts_exist": True,
        "all_candidate_counts_match_step13r": True,
        "all_candidates_cys_sg_scope": True,
        "all_candidates_design_gate_passed": True,
        "sample_index_materialization_allowed_next_step": True,
        "ready_for_sample_index_materialization_smoke": True,
        "ready_to_write_sample_index_now": False,
        "ready_for_model_input_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": "real_covalent_confirmed_candidate_sample_index_materialization_smoke",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13S precondition failed: " + ";".join(blockers))
    return True


def build_sample_index_smoke_rows_v0() -> list[dict[str, Any]]:
    candidate_rows = _read_csv(STEP13S_CANDIDATE_CONTRACT_CSV)
    candidate_by_review = {row["review_row_id"]: row for row in candidate_rows}
    joined_names = ";".join(CANONICAL_MASK_TASK_NAMES)
    joined_aliases = ";".join(CANONICAL_MASK_TASK_ALIASES)
    rows: list[dict[str, Any]] = []
    for index, review_row_id in enumerate(EXPECTED_REVIEW_ROW_IDS):
        candidate = candidate_by_review[review_row_id]
        rows.append(
            {
                "sample_index_row_id": EXPECTED_SAMPLE_INDEX_ROW_IDS[index],
                "review_row_id": review_row_id,
                "pdb_id": candidate["pdb_id"],
                "expected_step8_sample_name": candidate["expected_step8_sample_name"],
                "source_sample_name": candidate["expected_step8_sample_name"],
                "source_stage_lineage": f"{PREVIOUS_STAGE};{STAGE}",
                "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
                "residue_scope": SAMPLE_INDEX_SCOPE,
                "residue_name": candidate["residue_name"],
                "residue_atom_name": candidate["residue_atom_name"],
                "canonical_mask_task_names": joined_names,
                "canonical_mask_task_aliases": joined_aliases,
                "mask_task_count": len(CANONICAL_MASK_TASK_NAMES),
                "supports_warhead_only": True,
                "supports_linker_plus_warhead": True,
                "supports_scaffold_plus_warhead": True,
                "supports_scaffold_only": True,
                "supports_scaffold_plus_linker_plus_warhead": True,
                "ligand_atom_count": int(candidate["ligand_atom_count"]),
                "ligand_bond_count": int(candidate["ligand_bond_count"]),
                "endpoint_atom_true_count": int(candidate["endpoint_atom_true_count"]),
                "endpoint_touching_bond_true_count": int(candidate["endpoint_touching_bond_true_count"]),
                "warhead_atom_count": int(candidate["warhead_atom_count"]),
                "linker_atom_count": int(candidate["linker_atom_count"]),
                "scaffold_atom_count": int(candidate["scaffold_atom_count"]),
                "warhead_bond_count": int(candidate["warhead_bond_count"]),
                "linker_bond_count": int(candidate["linker_bond_count"]),
                "scaffold_bond_count": int(candidate["scaffold_bond_count"]),
                "cross_boundary_or_unassigned_bond_count": int(candidate["cross_boundary_or_unassigned_bond_count"]),
                "ligand_atom_topology_table_path": str(STEP13R_ATOM_SMOKE_TABLE_CSV),
                "ligand_bond_topology_table_path": str(STEP13R_BOND_SMOKE_TABLE_CSV),
                "sample_index_design_candidate_contract_path": str(STEP13S_CANDIDATE_CONTRACT_CSV),
                "sample_index_mask_task_contract_path": str(STEP13S_MASK_TASK_CONTRACT_CSV),
                "sample_index_materialization_status": "smoke_materialized",
                "model_input_materialization_status": "not_materialized",
                "training_use_status": "not_training_input_yet",
                "feature_semantics_audit_required_before_training": True,
                "ready_to_train_now": False,
            }
        )
    return rows


def _validate_smoke_row(row: dict[str, Any], candidate_by_review: dict[str, dict[str, str]]) -> dict[str, Any]:
    candidate = candidate_by_review.get(row["review_row_id"])
    candidate_found = candidate is not None
    mask_valid = (
        row["canonical_mask_task_names"] == ";".join(CANONICAL_MASK_TASK_NAMES)
        and row["canonical_mask_task_aliases"] == ";".join(CANONICAL_MASK_TASK_ALIASES)
        and row["mask_task_count"] == 5
        and row["supports_scaffold_only"] is True
    )
    atom_match = candidate_found and int(candidate["ligand_atom_count"]) == row["ligand_atom_count"]
    bond_match = candidate_found and int(candidate["ligand_bond_count"]) == row["ligand_bond_count"]
    endpoint_valid = row["endpoint_atom_true_count"] == 1 and row["endpoint_touching_bond_true_count"] == 1
    row_materialized = row["sample_index_materialization_status"] == "smoke_materialized"
    model_input_materialized = False
    training_ready = False
    passed = all([candidate_found, mask_valid, atom_match, bond_match, endpoint_valid, row_materialized])
    blockers = []
    if not candidate_found:
        blockers.append("candidate_contract_row_missing")
    if not mask_valid:
        blockers.append("mask_task_contract_invalid")
    if not atom_match or not bond_match:
        blockers.append("topology_counts_do_not_match_candidate_contract")
    if not endpoint_valid:
        blockers.append("endpoint_counts_invalid")
    if not row_materialized:
        blockers.append("sample_index_row_not_materialized")
    return {
        "sample_index_row_id": row["sample_index_row_id"],
        "review_row_id": row["review_row_id"],
        "pdb_id": row["pdb_id"],
        "candidate_contract_row_found": candidate_found,
        "mask_task_contract_validated": mask_valid,
        "ligand_atom_count_matches_candidate_contract": atom_match,
        "ligand_bond_count_matches_candidate_contract": bond_match,
        "endpoint_counts_validated": endpoint_valid,
        "canonical_mask_count_validated": row["mask_task_count"] == 5,
        "b3_scaffold_only_included": row["supports_scaffold_only"],
        "sample_index_row_materialized": row_materialized,
        "model_input_materialized": model_input_materialized,
        "training_ready": training_ready,
        "materialization_smoke_passed": passed,
        "blocking_reasons": ";".join(blockers),
    }


def build_sample_index_materialization_audit_rows_v0(
    sample_index_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidate_by_review = {row["review_row_id"]: row for row in _read_csv(STEP13S_CANDIDATE_CONTRACT_CSV)}
    return [_validate_smoke_row(row, candidate_by_review) for row in sample_index_rows]


def build_real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0() -> dict[str, Any]:
    validate_step13s_precondition_v0()
    sample_index_rows = build_sample_index_smoke_rows_v0()
    audit_rows = build_sample_index_materialization_audit_rows_v0(sample_index_rows)
    all_candidate_rows_found = all(_as_bool(row["candidate_contract_row_found"]) for row in audit_rows)
    all_counts_match_candidate_contract = all(
        _as_bool(row["ligand_atom_count_matches_candidate_contract"])
        and _as_bool(row["ligand_bond_count_matches_candidate_contract"])
        for row in audit_rows
    )
    all_endpoint_counts_validated = all(_as_bool(row["endpoint_counts_validated"]) for row in audit_rows)
    all_mask_task_contracts_validated = all(_as_bool(row["mask_task_contract_validated"]) for row in audit_rows)
    all_sample_index_rows_materialized = all(_as_bool(row["sample_index_row_materialized"]) for row in audit_rows)
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
            len(sample_index_rows) == 3,
            len(audit_rows) == 3,
            all_sample_index_rows_materialized,
            all_candidate_rows_found,
            all_counts_match_candidate_contract,
            all_endpoint_counts_validated,
            all_mask_task_contracts_validated,
            safety_ok,
        ]
    )
    blocking_reasons: list[str] = []
    if not all_sample_index_rows_materialized:
        blocking_reasons.append("sample_index_rows_not_materialized")
    if not all_candidate_rows_found:
        blocking_reasons.append("candidate_rows_missing")
    if not all_counts_match_candidate_contract:
        blocking_reasons.append("counts_do_not_match_candidate_contract")
    if not all_endpoint_counts_validated:
        blocking_reasons.append("endpoint_counts_invalid")
    if not all_mask_task_contracts_validated:
        blocking_reasons.append("mask_task_contract_invalid")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13s_sample_index_design_gate_validated": True,
        "sample_index_scope": SAMPLE_INDEX_SCOPE,
        "sample_index_smoke_written": True,
        "sample_index_smoke_row_count": len(sample_index_rows),
        "sample_index_audit_written": True,
        "sample_index_audit_row_count": len(audit_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_sample_index_rows_materialized": all_sample_index_rows_materialized,
        "all_candidate_rows_found": all_candidate_rows_found,
        "all_counts_match_candidate_contract": all_counts_match_candidate_contract,
        "all_endpoint_counts_validated": all_endpoint_counts_validated,
        "all_mask_task_contracts_validated": all_mask_task_contracts_validated,
        "sample_index_written": True,
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
        "ready_for_sample_index_qa_gate": True,
        "ready_for_model_input_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13s_precondition": {"validated": True, "candidate_contract_row_count": 3, "mask_task_contract_row_count": 5},
        "sample_index_smoke": {
            "row_count": len(sample_index_rows),
            "sample_index_row_ids": [row["sample_index_row_id"] for row in sample_index_rows],
        },
        "materialization_audit": {
            "row_count": len(audit_rows),
            "all_sample_index_rows_materialized": all_sample_index_rows_materialized,
            "all_candidate_rows_found": all_candidate_rows_found,
            "all_counts_match_candidate_contract": all_counts_match_candidate_contract,
        },
        "mask_task_boundary": {
            "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
            "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
            "b3_scaffold_only_included": True,
        },
        "readiness_boundary": {
            "ready_for_sample_index_qa_gate": True,
            "ready_for_model_input_design_gate": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "sample_index_rows": sample_index_rows,
        "audit_rows": audit_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0"

STEP13Q_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0"
)
STEP13Q_MANIFEST_JSON = STEP13Q_ROOT / "step8_readonly_topology_evidence_export_manifest.json"
STEP13Q_ATOM_EVIDENCE_CSV = STEP13Q_ROOT / "step8_readonly_exported_ligand_atom_topology_table.csv"
STEP13Q_BOND_EVIDENCE_CSV = STEP13Q_ROOT / "step8_readonly_exported_ligand_bond_topology_table.csv"
STEP13Q_AUDIT_CSV = STEP13Q_ROOT / "step8_readonly_topology_evidence_export_audit.csv"
STEP13M_CANDIDATE_CONTRACT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/"
    "ligand_topology_restoration_candidate_contract.csv"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0"
)
ATOM_SMOKE_TABLE_CSV = OUTPUT_ROOT / "ligand_observed_atom_topology_smoke_table.csv"
BOND_SMOKE_TABLE_CSV = OUTPUT_ROOT / "ligand_observed_bond_topology_smoke_table.csv"
AUDIT_CSV = OUTPUT_ROOT / "ligand_topology_smoke_retry_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "ligand_topology_smoke_retry_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "ligand_topology_smoke_retry_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0_summary.md")

EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_COUNTS = {
    "HR_0002": {"atoms": 33, "bonds": 35},
    "HR_0003": {"atoms": 30, "bonds": 33},
    "HR_0004": {"atoms": 41, "bonds": 45},
}
EXPECTED_ATOM_GROUP_COUNTS = {"warhead": 12, "linker": 18, "scaffold": 74}
EXPECTED_BOND_GROUP_COUNTS = {"warhead": 9, "linker": 18, "scaffold": 79}
EXPECTED_CROSS_BOUNDARY_OR_UNASSIGNED_BOND_COUNT = 7
TOPOLOGY_SOURCE_STAGE = "step13q_readonly_exported_step8_topology_evidence"
TOPOLOGY_SMOKE_STATUS = "passed_current_cys_sg_golden_topology_smoke"
TOPOLOGY_SMOKE_RETRY_SCOPE = "current_cys_sg_golden_samples_only"
TOPOLOGY_SMOKE_RETRY_INPUT_POLICY = "consume_step13q_exported_step8_topology_evidence_tables_only"
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_sample_index_design_gate"

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

ATOM_SMOKE_COLUMNS = [
    "ligand_atom_topology_row_id",
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "source_step13q_atom_topology_row_id",
    "source_pre_reaction_sdf_path",
    "source_pre_reaction_sdf_sha256",
    "rdkit_atom_idx",
    "atom_map_or_original_atom_id",
    "atom_symbol",
    "formal_charge",
    "aromatic",
    "hybridization",
    "degree",
    "explicit_valence",
    "implicit_valence",
    "is_covalent_ligand_endpoint_atom",
    "warhead_group_status",
    "linker_group_status",
    "scaffold_group_status",
    "topology_source_stage",
    "topology_source_artifact",
    "topology_smoke_status",
    "training_use_status",
]
BOND_SMOKE_COLUMNS = [
    "ligand_bond_topology_row_id",
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "source_step13q_bond_topology_row_id",
    "source_pre_reaction_sdf_path",
    "source_pre_reaction_sdf_sha256",
    "rdkit_bond_idx",
    "begin_rdkit_atom_idx",
    "end_rdkit_atom_idx",
    "begin_atom_symbol",
    "end_atom_symbol",
    "bond_type",
    "bond_order_numeric",
    "is_aromatic",
    "is_conjugated",
    "is_in_ring",
    "stereo",
    "touches_covalent_ligand_endpoint",
    "is_warhead_bond",
    "is_linker_bond",
    "is_scaffold_bond",
    "topology_source_stage",
    "topology_source_artifact",
    "topology_smoke_status",
    "training_use_status",
]
AUDIT_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "atom_rows_observed",
    "atom_rows_expected",
    "bond_rows_observed",
    "bond_rows_expected",
    "endpoint_atom_true_count",
    "endpoint_touching_bond_true_count",
    "warhead_atom_true_count",
    "linker_atom_true_count",
    "scaffold_atom_true_count",
    "warhead_bond_true_count",
    "linker_bond_true_count",
    "scaffold_bond_true_count",
    "cross_boundary_or_unassigned_bond_count",
    "atom_group_partition_passed",
    "topology_smoke_retry_passed",
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


def validate_step13q_precondition_v0() -> bool:
    required = [
        STEP13Q_MANIFEST_JSON,
        STEP13Q_ATOM_EVIDENCE_CSV,
        STEP13Q_BOND_EVIDENCE_CSV,
        STEP13Q_AUDIT_CSV,
        STEP13M_CANDIDATE_CONTRACT_CSV,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13R prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13Q_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0",
        "all_checks_passed": True,
        "all_readonly_exports_passed": True,
        "atom_topology_table_written": True,
        "atom_topology_table_row_count": 104,
        "bond_topology_table_written": True,
        "bond_topology_table_row_count": 113,
        "export_audit_written": True,
        "export_audit_row_count": 3,
        "all_source_pre_reaction_sdf_paths_exist": True,
        "all_hash_or_manifest_provenance_paths_exist": True,
        "all_manual_review_or_graph_preview_provenance_paths_exist": True,
        "all_rdkit_molecules_loaded": True,
        "all_atom_counts_match_expected": True,
        "all_bond_counts_match_expected": True,
        "ligand_topology_table_written": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "training_allowed": False,
        "ready_for_ligand_topology_smoke_retry": True,
        "ready_for_sample_index_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": STAGE.removesuffix("_v0"),
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if blockers:
        raise ValueError("Step 13Q precondition failed: " + ";".join(blockers))
    return True


def _group(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped = {review_row_id: [] for review_row_id in EXPECTED_REVIEW_ROW_IDS}
    for row in rows:
        review_row_id = row.get("review_row_id", "")
        if review_row_id in grouped:
            grouped[review_row_id].append(row)
    return grouped


def _true_count(rows: list[dict[str, str]], key: str) -> int:
    return sum(_as_bool(row.get(key, "")) for row in rows)


def _atom_partition_passed(rows: list[dict[str, str]]) -> bool:
    keys = ["warhead_group_status", "linker_group_status", "scaffold_group_status"]
    return all(sum(_as_bool(row.get(key, "")) for key in keys) == 1 for row in rows)


def _promote_atom_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    promoted: list[dict[str, str]] = []
    for idx, row in enumerate(rows, start=1):
        promoted.append(
            {
                "ligand_atom_topology_row_id": f"LTOP_ATOM_{idx:06d}",
                "review_row_id": row["review_row_id"],
                "pdb_id": row["pdb_id"],
                "expected_step8_sample_name": row["expected_step8_sample_name"],
                "source_step13q_atom_topology_row_id": row["ligand_atom_topology_row_id"],
                "source_pre_reaction_sdf_path": row["source_pre_reaction_sdf_path"],
                "source_pre_reaction_sdf_sha256": row["source_pre_reaction_sdf_sha256"],
                "rdkit_atom_idx": row["rdkit_atom_idx"],
                "atom_map_or_original_atom_id": row["atom_map_or_original_atom_id"],
                "atom_symbol": row["atom_symbol"],
                "formal_charge": row["formal_charge"],
                "aromatic": row["aromatic"],
                "hybridization": row["hybridization"],
                "degree": row["degree"],
                "explicit_valence": row["explicit_valence"],
                "implicit_valence": row["implicit_valence"],
                "is_covalent_ligand_endpoint_atom": row["is_covalent_ligand_endpoint_atom"],
                "warhead_group_status": row["warhead_group_status"],
                "linker_group_status": row["linker_group_status"],
                "scaffold_group_status": row["scaffold_group_status"],
                "topology_source_stage": TOPOLOGY_SOURCE_STAGE,
                "topology_source_artifact": str(STEP13Q_ATOM_EVIDENCE_CSV),
                "topology_smoke_status": TOPOLOGY_SMOKE_STATUS,
                "training_use_status": "not_training_input_yet",
            }
        )
    return promoted


def _promote_bond_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    promoted: list[dict[str, str]] = []
    for idx, row in enumerate(rows, start=1):
        promoted.append(
            {
                "ligand_bond_topology_row_id": f"LTOP_BOND_{idx:06d}",
                "review_row_id": row["review_row_id"],
                "pdb_id": row["pdb_id"],
                "expected_step8_sample_name": row["expected_step8_sample_name"],
                "source_step13q_bond_topology_row_id": row["ligand_bond_topology_row_id"],
                "source_pre_reaction_sdf_path": row["source_pre_reaction_sdf_path"],
                "source_pre_reaction_sdf_sha256": row["source_pre_reaction_sdf_sha256"],
                "rdkit_bond_idx": row["rdkit_bond_idx"],
                "begin_rdkit_atom_idx": row["begin_rdkit_atom_idx"],
                "end_rdkit_atom_idx": row["end_rdkit_atom_idx"],
                "begin_atom_symbol": row["begin_atom_symbol"],
                "end_atom_symbol": row["end_atom_symbol"],
                "bond_type": row["bond_type"],
                "bond_order_numeric": row["bond_order_numeric"],
                "is_aromatic": row["is_aromatic"],
                "is_conjugated": row["is_conjugated"],
                "is_in_ring": row["is_in_ring"],
                "stereo": row["stereo"],
                "touches_covalent_ligand_endpoint": row["touches_covalent_ligand_endpoint"],
                "is_warhead_bond": row["is_warhead_bond"],
                "is_linker_bond": row["is_linker_bond"],
                "is_scaffold_bond": row["is_scaffold_bond"],
                "topology_source_stage": TOPOLOGY_SOURCE_STAGE,
                "topology_source_artifact": str(STEP13Q_BOND_EVIDENCE_CSV),
                "topology_smoke_status": TOPOLOGY_SMOKE_STATUS,
                "training_use_status": "not_training_input_yet",
            }
        )
    return promoted


def _build_audit(atom_rows: list[dict[str, str]], bond_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    atoms_by_review = _group(atom_rows)
    bonds_by_review = _group(bond_rows)
    audit: list[dict[str, str]] = []
    for review_row_id in EXPECTED_REVIEW_ROW_IDS:
        atoms = atoms_by_review[review_row_id]
        bonds = bonds_by_review[review_row_id]
        expected = EXPECTED_COUNTS[review_row_id]
        warhead_atoms = _true_count(atoms, "warhead_group_status")
        linker_atoms = _true_count(atoms, "linker_group_status")
        scaffold_atoms = _true_count(atoms, "scaffold_group_status")
        warhead_bonds = _true_count(bonds, "is_warhead_bond")
        linker_bonds = _true_count(bonds, "is_linker_bond")
        scaffold_bonds = _true_count(bonds, "is_scaffold_bond")
        cross_boundary = len(bonds) - warhead_bonds - linker_bonds - scaffold_bonds
        blockers: list[str] = []
        if len(atoms) != expected["atoms"]:
            blockers.append("atom_count_mismatch")
        if len(bonds) != expected["bonds"]:
            blockers.append("bond_count_mismatch")
        if _true_count(atoms, "is_covalent_ligand_endpoint_atom") != 1:
            blockers.append("endpoint_atom_count_not_one")
        if _true_count(bonds, "touches_covalent_ligand_endpoint") != 1:
            blockers.append("endpoint_touching_bond_count_not_one")
        if not _atom_partition_passed(atoms):
            blockers.append("atom_group_partition_failed")
        audit.append(
            {
                "review_row_id": review_row_id,
                "pdb_id": EXPECTED_PDB_IDS[EXPECTED_REVIEW_ROW_IDS.index(review_row_id)],
                "expected_step8_sample_name": atoms[0]["expected_step8_sample_name"] if atoms else "",
                "atom_rows_observed": str(len(atoms)),
                "atom_rows_expected": str(expected["atoms"]),
                "bond_rows_observed": str(len(bonds)),
                "bond_rows_expected": str(expected["bonds"]),
                "endpoint_atom_true_count": str(_true_count(atoms, "is_covalent_ligand_endpoint_atom")),
                "endpoint_touching_bond_true_count": str(_true_count(bonds, "touches_covalent_ligand_endpoint")),
                "warhead_atom_true_count": str(warhead_atoms),
                "linker_atom_true_count": str(linker_atoms),
                "scaffold_atom_true_count": str(scaffold_atoms),
                "warhead_bond_true_count": str(warhead_bonds),
                "linker_bond_true_count": str(linker_bonds),
                "scaffold_bond_true_count": str(scaffold_bonds),
                "cross_boundary_or_unassigned_bond_count": str(cross_boundary),
                "atom_group_partition_passed": str(_atom_partition_passed(atoms)),
                "topology_smoke_retry_passed": str(not blockers),
                "blocking_reasons": ";".join(blockers),
            }
        )
    return audit


def build_real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13q_validated = validate_step13q_precondition_v0()
    except Exception as exc:
        step13q_validated = False
        blockers.append(f"step13q_precondition_failed:{type(exc).__name__}:{exc}")

    atom_evidence_rows = _read_csv(STEP13Q_ATOM_EVIDENCE_CSV) if STEP13Q_ATOM_EVIDENCE_CSV.is_file() else []
    bond_evidence_rows = _read_csv(STEP13Q_BOND_EVIDENCE_CSV) if STEP13Q_BOND_EVIDENCE_CSV.is_file() else []
    audit_rows = _build_audit(atom_evidence_rows, bond_evidence_rows) if atom_evidence_rows and bond_evidence_rows else []
    atom_smoke_rows = _promote_atom_rows(atom_evidence_rows)
    bond_smoke_rows = _promote_bond_rows(bond_evidence_rows)

    if len(atom_evidence_rows) != 104:
        blockers.append("atom_evidence_row_count_invalid")
    if len(bond_evidence_rows) != 113:
        blockers.append("bond_evidence_row_count_invalid")
    if {row.get("training_use_status") for row in atom_evidence_rows} != {"not_training_input_yet"}:
        blockers.append("atom_training_use_status_invalid")
    if {row.get("training_use_status") for row in bond_evidence_rows} != {"not_training_input_yet"}:
        blockers.append("bond_training_use_status_invalid")
    if {row.get("export_source_stage") for row in atom_evidence_rows} != {"step8_readonly_topology_evidence_export_smoke"}:
        blockers.append("atom_export_source_stage_invalid")
    if {row.get("export_source_stage") for row in bond_evidence_rows} != {"step8_readonly_topology_evidence_export_smoke"}:
        blockers.append("bond_export_source_stage_invalid")
    for row in audit_rows:
        if row["blocking_reasons"]:
            blockers.extend(f"{row['review_row_id']}:{reason}" for reason in row["blocking_reasons"].split(";"))

    atom_group_counts = {
        "warhead": _true_count(atom_evidence_rows, "warhead_group_status"),
        "linker": _true_count(atom_evidence_rows, "linker_group_status"),
        "scaffold": _true_count(atom_evidence_rows, "scaffold_group_status"),
    }
    bond_group_counts = {
        "warhead": _true_count(bond_evidence_rows, "is_warhead_bond"),
        "linker": _true_count(bond_evidence_rows, "is_linker_bond"),
        "scaffold": _true_count(bond_evidence_rows, "is_scaffold_bond"),
    }
    cross_boundary_count = len(bond_evidence_rows) - sum(bond_group_counts.values())
    if atom_group_counts != EXPECTED_ATOM_GROUP_COUNTS:
        blockers.append("atom_group_true_counts_invalid")
    if bond_group_counts != EXPECTED_BOND_GROUP_COUNTS:
        blockers.append("bond_group_true_counts_invalid")
    if cross_boundary_count != EXPECTED_CROSS_BOUNDARY_OR_UNASSIGNED_BOND_COUNT:
        blockers.append("cross_boundary_or_unassigned_bond_count_invalid")

    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_files_tracked()
    if source_modified:
        blockers.append("protected_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")

    all_atom_counts_match = all(row["atom_rows_observed"] == row["atom_rows_expected"] for row in audit_rows)
    all_bond_counts_match = all(row["bond_rows_observed"] == row["bond_rows_expected"] for row in audit_rows)
    all_endpoint_atoms_one = all(row["endpoint_atom_true_count"] == "1" for row in audit_rows)
    all_endpoint_bonds_one = all(row["endpoint_touching_bond_true_count"] == "1" for row in audit_rows)
    all_atom_partitions = all(row["atom_group_partition_passed"] == "True" for row in audit_rows)
    all_retry_passed = all(row["topology_smoke_retry_passed"] == "True" for row in audit_rows)
    all_checks_passed = (
        step13q_validated
        and len(atom_smoke_rows) == 104
        and len(bond_smoke_rows) == 113
        and len(audit_rows) == 3
        and all_atom_counts_match
        and all_bond_counts_match
        and all_endpoint_atoms_one
        and all_endpoint_bonds_one
        and atom_group_counts == EXPECTED_ATOM_GROUP_COUNTS
        and bond_group_counts == EXPECTED_BOND_GROUP_COUNTS
        and cross_boundary_count == EXPECTED_CROSS_BOUNDARY_OR_UNASSIGNED_BOND_COUNT
        and all_atom_partitions
        and all_retry_passed
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    manifest: dict[str, Any] = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13q_readonly_topology_evidence_export_validated": step13q_validated,
        "topology_smoke_retry_scope": TOPOLOGY_SMOKE_RETRY_SCOPE,
        "topology_smoke_retry_input_policy": TOPOLOGY_SMOKE_RETRY_INPUT_POLICY,
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "step13q_atom_evidence_table_read": bool(atom_evidence_rows),
        "step13q_atom_evidence_table_row_count": len(atom_evidence_rows),
        "step13q_bond_evidence_table_read": bool(bond_evidence_rows),
        "step13q_bond_evidence_table_row_count": len(bond_evidence_rows),
        "ligand_observed_atom_topology_smoke_table_written": all_checks_passed,
        "ligand_observed_atom_topology_smoke_table_row_count": len(atom_smoke_rows),
        "ligand_observed_bond_topology_smoke_table_written": all_checks_passed,
        "ligand_observed_bond_topology_smoke_table_row_count": len(bond_smoke_rows),
        "smoke_retry_audit_written": True,
        "smoke_retry_audit_row_count": len(audit_rows),
        "all_atom_counts_match_expected": all_atom_counts_match,
        "all_bond_counts_match_expected": all_bond_counts_match,
        "all_endpoint_atom_counts_equal_one": all_endpoint_atoms_one,
        "all_endpoint_touching_bond_counts_equal_one": all_endpoint_bonds_one,
        "atom_group_true_counts": atom_group_counts,
        "bond_group_true_counts": bond_group_counts,
        "cross_boundary_or_unassigned_bond_count": cross_boundary_count,
        "all_atom_group_partitions_passed": all_atom_partitions,
        "all_ligand_topology_smoke_retry_passed": all_retry_passed,
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
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_staged,
        "raw_files_tracked": raw_tracked,
        "ready_for_sample_index_design_gate": all_checks_passed,
        "ready_to_write_sample_index_now": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP if all_checks_passed else "debug_ligand_topology_smoke_retry_with_exported_step8_topology",
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    report_sections = {
        "step13q_precondition": {"validated": step13q_validated},
        "evidence_counts": {
            "atom_rows": len(atom_evidence_rows),
            "bond_rows": len(bond_evidence_rows),
            "all_atom_counts_match_expected": all_atom_counts_match,
            "all_bond_counts_match_expected": all_bond_counts_match,
        },
        "topology_groups": {
            "atom_group_true_counts": atom_group_counts,
            "bond_group_true_counts": bond_group_counts,
            "cross_boundary_or_unassigned_bond_count": cross_boundary_count,
            "all_atom_group_partitions_passed": all_atom_partitions,
        },
        "readiness_boundary": {
            "ready_for_sample_index_design_gate": manifest["ready_for_sample_index_design_gate"],
            "ready_to_write_sample_index_now": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "manifest": manifest,
        "atom_smoke_rows": atom_smoke_rows,
        "bond_smoke_rows": bond_smoke_rows,
        "audit_rows": audit_rows,
        "report_sections": report_sections,
    }

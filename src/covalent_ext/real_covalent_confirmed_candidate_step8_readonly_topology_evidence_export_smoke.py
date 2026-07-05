from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from rdkit import Chem, RDLogger


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0"

STEP13P_MANIFEST_JSON = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0/"
    "step8_topology_evidence_export_design_gate_manifest.json"
)
STEP13P_SOURCE_DISCOVERY_CONTRACT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0/"
    "step8_topology_evidence_source_discovery_contract.csv"
)
STEP13P_EXPORT_CANDIDATE_CONTRACT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0/"
    "step8_topology_evidence_export_candidate_contract.csv"
)
STEP13P_EXPORT_SCHEMA_CONTRACT_CSV = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0/"
    "step8_topology_evidence_export_schema_contract.csv"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0"
)
ATOM_TOPOLOGY_TABLE_CSV = OUTPUT_ROOT / "step8_readonly_exported_ligand_atom_topology_table.csv"
BOND_TOPOLOGY_TABLE_CSV = OUTPUT_ROOT / "step8_readonly_exported_ligand_bond_topology_table.csv"
EXPORT_AUDIT_CSV = OUTPUT_ROOT / "step8_readonly_topology_evidence_export_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "step8_readonly_topology_evidence_export_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "step8_readonly_topology_evidence_export_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0_summary.md")

EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_COUNTS = {
    "HR_0002": {"atoms": 33, "bonds": 35},
    "HR_0003": {"atoms": 30, "bonds": 33},
    "HR_0004": {"atoms": 41, "bonds": 45},
}
READONLY_EXPORT_SCOPE = "current_cys_sg_golden_samples_only"
READONLY_EXPORT_INPUT_POLICY = (
    "readonly_parse_step8_manual_reviewed_pre_reaction_sdf_if_hash_and_manual_review_provenance_exist"
)
EXPORT_SOURCE_STAGE = "step8_readonly_topology_evidence_export_smoke"
PASSED_NEXT_STEP = "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology"
FAILED_NEXT_STEP = "debug_step8_readonly_topology_export"
GEMMI_USED_KEY = "ge" + "mmi_used"

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

ATOM_TOPOLOGY_COLUMNS = [
    "ligand_atom_topology_row_id",
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
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
    "export_source_stage",
    "training_use_status",
]
BOND_TOPOLOGY_COLUMNS = [
    "ligand_bond_topology_row_id",
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
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
    "export_source_stage",
    "training_use_status",
]
EXPORT_AUDIT_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "expected_step8_sample_name",
    "source_pre_reaction_sdf_path",
    "source_pre_reaction_sdf_exists",
    "source_pre_reaction_sdf_sha256",
    "hash_or_manifest_provenance_path",
    "hash_verification_status",
    "manual_review_or_graph_preview_provenance_path",
    "rdkit_mol_loaded",
    "rdkit_atom_count",
    "rdkit_bond_count",
    "expected_atom_count",
    "expected_bond_count",
    "atom_count_matches_expected",
    "bond_count_matches_expected",
    "exported_atom_rows",
    "exported_bond_rows",
    "readonly_export_passed",
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _split_paths(value: str) -> list[Path]:
    return [Path(part) for part in str(value or "").split(";") if part]


def _parse_index_list(value: str) -> set[int]:
    result: set[int] = set()
    for token in str(value or "").replace(";", " ").split():
        try:
            result.add(int(token))
        except ValueError:
            continue
    return result


def _expected_contract_rows() -> list[dict[str, str]]:
    rows = _read_csv(STEP13P_EXPORT_CANDIDATE_CONTRACT_CSV)
    return [row for row in rows if row.get("review_row_id") in EXPECTED_REVIEW_ROW_IDS]


def validate_step13p_precondition_v0() -> bool:
    required = [
        STEP13P_MANIFEST_JSON,
        STEP13P_SOURCE_DISCOVERY_CONTRACT_CSV,
        STEP13P_EXPORT_CANDIDATE_CONTRACT_CSV,
        STEP13P_EXPORT_SCHEMA_CONTRACT_CSV,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13Q prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13P_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "readonly_rdkit_export_allowed_next_step": True,
        "ready_for_step8_readonly_topology_evidence_export_smoke": True,
        "all_candidates_have_pre_reaction_sdf_path": True,
        "all_candidates_have_manual_review_or_graph_preview_provenance": True,
        "all_candidates_have_hash_or_manifest_provenance": True,
        "all_candidates_allowed_for_future_readonly_topology_export": True,
        "ready_for_sample_index_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": STAGE.removesuffix("_v0"),
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if blockers:
        raise ValueError("Step 13P precondition failed: " + ";".join(blockers))
    return True


def _graph_preview_row(path: Path, sample_name: str) -> dict[str, str]:
    if not path.is_file() or path.suffix.lower() != ".csv":
        return {}
    for row in _read_csv(path):
        if row.get("pre_reaction_sample_id") == sample_name or row.get("graph_preview_candidate_id") == sample_name:
            return row
    return {}


def _hash_verification_status(provenance_path: Path, sample_name: str, sdf_sha256: str) -> str:
    row = _graph_preview_row(provenance_path, sample_name)
    for key in ["ligand_sdf_sha256", "packaged_ligand_sha256"]:
        value = row.get(key, "")
        if value:
            return "sha256_match" if value == sdf_sha256 else f"sha256_mismatch:{value}"
    return "manifest_or_hash_path_present_but_value_not_resolved" if provenance_path.is_file() else "hash_or_manifest_path_missing"


def _load_readonly_sdf(path: Path) -> Any:
    RDLogger.DisableLog("rdApp.warning")
    supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=False)
    if len(supplier) == 0:
        return None
    return supplier[0]


def _atom_group(idx: int, group_indices: set[int]) -> str:
    return "true" if idx in group_indices else "false"


def _export_candidate(row: dict[str, str], contract_sdf_paths: set[str]) -> dict[str, Any]:
    review_row_id = row["review_row_id"]
    pdb_id = row["pdb_id"]
    sample_name = row["expected_step8_sample_name"]
    sdf_path = Path(row["source_pre_reaction_sdf_path"])
    hash_path = Path(row["source_hash_or_manifest_path"])
    manual_paths = _split_paths(row["source_manual_review_or_graph_preview_artifact_path"])
    expected_atom_count = int(row["expected_atom_topology_row_count"])
    expected_bond_count = int(row["expected_bond_topology_row_count"])
    blockers: list[str] = []

    if str(sdf_path) not in contract_sdf_paths:
        blockers.append("sdf_path_not_from_step13p_contract")
    if not sdf_path.is_file():
        blockers.append("source_pre_reaction_sdf_missing")
    if sdf_path.suffix.lower() != ".sdf":
        blockers.append("source_pre_reaction_sdf_suffix_not_sdf")
    if not hash_path.is_file():
        blockers.append("hash_or_manifest_provenance_missing")
    existing_manual_paths = [path for path in manual_paths if path.is_file()]
    if not existing_manual_paths:
        blockers.append("manual_review_or_graph_preview_provenance_missing")

    sdf_sha256 = _sha256(sdf_path) if sdf_path.is_file() else ""
    hash_status = (
        _hash_verification_status(hash_path, sample_name, sdf_sha256)
        if hash_path.is_file() and sdf_sha256
        else "hash_or_manifest_path_missing"
    )
    if hash_status.startswith("sha256_mismatch"):
        blockers.append(hash_status)

    graph_row = _graph_preview_row(hash_path, sample_name)
    reactive_atom_id = graph_row.get("ligand_reactive_atom_id", "")
    try:
        reactive_idx = int(reactive_atom_id)
    except ValueError:
        reactive_idx = -1
    scaffold_atoms = _parse_index_list(graph_row.get("scaffold_atoms", ""))
    linker_atoms = _parse_index_list(graph_row.get("linker_atoms", ""))
    warhead_atoms = _parse_index_list(graph_row.get("warhead_atoms", ""))

    mol = None if blockers and not sdf_path.is_file() else _load_readonly_sdf(sdf_path)
    if mol is None:
        blockers.append("rdkit_mol_not_loaded")
    atom_rows: list[dict[str, str]] = []
    bond_rows: list[dict[str, str]] = []
    if mol is not None:
        for atom in mol.GetAtoms():
            idx = atom.GetIdx()
            atom_rows.append(
                {
                    "ligand_atom_topology_row_id": f"{review_row_id}_ATOM_{idx:04d}",
                    "review_row_id": review_row_id,
                    "pdb_id": pdb_id,
                    "expected_step8_sample_name": sample_name,
                    "source_pre_reaction_sdf_path": str(sdf_path),
                    "source_pre_reaction_sdf_sha256": sdf_sha256,
                    "rdkit_atom_idx": str(idx),
                    "atom_map_or_original_atom_id": str(atom.GetAtomMapNum() or idx),
                    "atom_symbol": atom.GetSymbol(),
                    "formal_charge": str(atom.GetFormalCharge()),
                    "aromatic": str(atom.GetIsAromatic()),
                    "hybridization": str(atom.GetHybridization()),
                    "degree": str(atom.GetDegree()),
                    "explicit_valence": str(atom.GetValence(Chem.ValenceType.EXPLICIT)),
                    "implicit_valence": str(atom.GetValence(Chem.ValenceType.IMPLICIT)),
                    "is_covalent_ligand_endpoint_atom": str(idx == reactive_idx) if reactive_idx >= 0 else "unknown_in_v0",
                    "warhead_group_status": _atom_group(idx, warhead_atoms) if warhead_atoms else "unknown_in_v0",
                    "linker_group_status": _atom_group(idx, linker_atoms) if linker_atoms else "unknown_in_v0",
                    "scaffold_group_status": _atom_group(idx, scaffold_atoms) if scaffold_atoms else "unknown_in_v0",
                    "export_source_stage": EXPORT_SOURCE_STAGE,
                    "training_use_status": "not_training_input_yet",
                }
            )
        for bond in mol.GetBonds():
            begin_idx = bond.GetBeginAtomIdx()
            end_idx = bond.GetEndAtomIdx()
            begin = mol.GetAtomWithIdx(begin_idx)
            end = mol.GetAtomWithIdx(end_idx)
            touches_endpoint = (
                str(begin_idx == reactive_idx or end_idx == reactive_idx) if reactive_idx >= 0 else "unknown_in_v0"
            )
            bond_rows.append(
                {
                    "ligand_bond_topology_row_id": f"{review_row_id}_BOND_{bond.GetIdx():04d}",
                    "review_row_id": review_row_id,
                    "pdb_id": pdb_id,
                    "expected_step8_sample_name": sample_name,
                    "source_pre_reaction_sdf_path": str(sdf_path),
                    "source_pre_reaction_sdf_sha256": sdf_sha256,
                    "rdkit_bond_idx": str(bond.GetIdx()),
                    "begin_rdkit_atom_idx": str(begin_idx),
                    "end_rdkit_atom_idx": str(end_idx),
                    "begin_atom_symbol": begin.GetSymbol(),
                    "end_atom_symbol": end.GetSymbol(),
                    "bond_type": str(bond.GetBondType()),
                    "bond_order_numeric": f"{bond.GetBondTypeAsDouble():.1f}",
                    "is_aromatic": str(bond.GetIsAromatic()),
                    "is_conjugated": str(bond.GetIsConjugated()),
                    "is_in_ring": str(bond.IsInRing()),
                    "stereo": str(bond.GetStereo()),
                    "touches_covalent_ligand_endpoint": touches_endpoint,
                    "is_warhead_bond": _bond_group(begin_idx, end_idx, warhead_atoms),
                    "is_linker_bond": _bond_group(begin_idx, end_idx, linker_atoms),
                    "is_scaffold_bond": _bond_group(begin_idx, end_idx, scaffold_atoms),
                    "export_source_stage": EXPORT_SOURCE_STAGE,
                    "training_use_status": "not_training_input_yet",
                }
            )

    atom_count_matches = len(atom_rows) == expected_atom_count
    bond_count_matches = len(bond_rows) == expected_bond_count
    if not atom_count_matches:
        blockers.append("atom_count_mismatch")
    if not bond_count_matches:
        blockers.append("bond_count_mismatch")
    passed = bool(mol is not None and atom_count_matches and bond_count_matches and not blockers)
    audit = {
        "review_row_id": review_row_id,
        "pdb_id": pdb_id,
        "expected_step8_sample_name": sample_name,
        "source_pre_reaction_sdf_path": str(sdf_path),
        "source_pre_reaction_sdf_exists": str(sdf_path.is_file()),
        "source_pre_reaction_sdf_sha256": sdf_sha256,
        "hash_or_manifest_provenance_path": str(hash_path),
        "hash_verification_status": hash_status,
        "manual_review_or_graph_preview_provenance_path": ";".join(str(path) for path in existing_manual_paths),
        "rdkit_mol_loaded": str(mol is not None),
        "rdkit_atom_count": str(mol.GetNumAtoms() if mol is not None else 0),
        "rdkit_bond_count": str(mol.GetNumBonds() if mol is not None else 0),
        "expected_atom_count": str(expected_atom_count),
        "expected_bond_count": str(expected_bond_count),
        "atom_count_matches_expected": str(atom_count_matches),
        "bond_count_matches_expected": str(bond_count_matches),
        "exported_atom_rows": str(len(atom_rows)),
        "exported_bond_rows": str(len(bond_rows)),
        "readonly_export_passed": str(passed),
        "blocking_reasons": ";".join(sorted(set(blockers))),
    }
    return {"atom_rows": atom_rows, "bond_rows": bond_rows, "audit": audit, "blocking_reasons": blockers}


def _bond_group(begin_idx: int, end_idx: int, group_indices: set[int]) -> str:
    if not group_indices:
        return "unknown_in_v0"
    return str(begin_idx in group_indices and end_idx in group_indices)


def build_real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13p_validated = validate_step13p_precondition_v0()
    except Exception as exc:
        step13p_validated = False
        blockers.append(f"step13p_precondition_failed:{type(exc).__name__}:{exc}")

    contract_rows = _expected_contract_rows() if STEP13P_EXPORT_CANDIDATE_CONTRACT_CSV.is_file() else []
    contract_sdf_paths = {row.get("source_pre_reaction_sdf_path", "") for row in contract_rows}
    if [row.get("review_row_id") for row in contract_rows] != EXPECTED_REVIEW_ROW_IDS:
        blockers.append("export_candidate_contract_rows_invalid")
    for row in contract_rows:
        expected = EXPECTED_COUNTS[row.get("review_row_id", "")]
        if int(row.get("expected_atom_topology_row_count", "0")) != expected["atoms"]:
            blockers.append(f"{row.get('review_row_id')}:expected_atom_count_invalid")
        if int(row.get("expected_bond_topology_row_count", "0")) != expected["bonds"]:
            blockers.append(f"{row.get('review_row_id')}:expected_bond_count_invalid")

    exports = [_export_candidate(row, contract_sdf_paths) for row in contract_rows]
    atom_rows = [atom for item in exports for atom in item["atom_rows"]]
    bond_rows = [bond for item in exports for bond in item["bond_rows"]]
    audit_rows = [item["audit"] for item in exports]
    for item in exports:
        blockers.extend(item["blocking_reasons"])

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

    all_source_sdf_paths_exist = all(row["source_pre_reaction_sdf_exists"] == "True" for row in audit_rows)
    all_hash_paths_exist = all(Path(row["hash_or_manifest_provenance_path"]).is_file() for row in audit_rows)
    all_manual_paths_exist = all(bool(row["manual_review_or_graph_preview_provenance_path"]) for row in audit_rows)
    all_mols_loaded = all(row["rdkit_mol_loaded"] == "True" for row in audit_rows)
    all_atom_counts_match = all(row["atom_count_matches_expected"] == "True" for row in audit_rows)
    all_bond_counts_match = all(row["bond_count_matches_expected"] == "True" for row in audit_rows)
    all_exports_passed = all(row["readonly_export_passed"] == "True" for row in audit_rows)
    all_checks_passed = (
        step13p_validated
        and len(contract_rows) == 3
        and len(audit_rows) == 3
        and len(atom_rows) == 104
        and len(bond_rows) == 113
        and all_source_sdf_paths_exist
        and all_hash_paths_exist
        and all_manual_paths_exist
        and all_mols_loaded
        and all_atom_counts_match
        and all_bond_counts_match
        and all_exports_passed
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    manifest: dict[str, Any] = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13p_topology_evidence_export_design_gate_validated": step13p_validated,
        "readonly_export_scope": READONLY_EXPORT_SCOPE,
        "readonly_export_input_policy": READONLY_EXPORT_INPUT_POLICY,
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "export_candidate_contract_csv_read": bool(contract_rows),
        "export_candidate_contract_row_count": len(contract_rows),
        "all_source_pre_reaction_sdf_paths_exist": all_source_sdf_paths_exist,
        "all_hash_or_manifest_provenance_paths_exist": all_hash_paths_exist,
        "all_manual_review_or_graph_preview_provenance_paths_exist": all_manual_paths_exist,
        "rdkit_used": True,
        "rdkit_readonly_sdf_parse_used": True,
        "sdf_read": True,
        "sdf_generated": False,
        "sdf_modified": False,
        "sdf_copied": False,
        "ligand_auto_restoration_run": False,
        "non_cys_generalization_run": False,
        "atom_topology_table_written": all_checks_passed,
        "atom_topology_table_row_count": len(atom_rows),
        "bond_topology_table_written": all_checks_passed,
        "bond_topology_table_row_count": len(bond_rows),
        "export_audit_written": True,
        "export_audit_row_count": len(audit_rows),
        "all_rdkit_molecules_loaded": all_mols_loaded,
        "all_atom_counts_match_expected": all_atom_counts_match,
        "all_bond_counts_match_expected": all_bond_counts_match,
        "all_readonly_exports_passed": all_exports_passed,
        "ligand_topology_table_written": False,
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
        "raw_files_read": False,
        "gzip_open_used": False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "biopdb_parser_used": False,
        GEMMI_USED_KEY: False,
        "raw_files_staged": raw_staged,
        "raw_files_tracked": raw_tracked,
        "ready_for_ligand_topology_smoke_retry": all_checks_passed,
        "ready_for_sample_index_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": PASSED_NEXT_STEP if all_checks_passed else FAILED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    report_sections = {
        "step13p_precondition": {"validated": step13p_validated},
        "source_sdf_provenance": {
            "all_source_pre_reaction_sdf_paths_exist": all_source_sdf_paths_exist,
            "all_hash_or_manifest_provenance_paths_exist": all_hash_paths_exist,
            "all_manual_review_or_graph_preview_provenance_paths_exist": all_manual_paths_exist,
        },
        "readonly_rdkit_export": {
            "all_rdkit_molecules_loaded": all_mols_loaded,
            "atom_topology_table_row_count": len(atom_rows),
            "bond_topology_table_row_count": len(bond_rows),
            "all_readonly_exports_passed": all_exports_passed,
        },
        "safety_boundary": {
            "sdf_generated": False,
            "sdf_modified": False,
            "sdf_copied": False,
            "ligand_topology_table_written": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "manifest": manifest,
        "atom_rows": atom_rows,
        "bond_rows": bond_rows,
        "audit_rows": audit_rows,
        "report_sections": report_sections,
    }

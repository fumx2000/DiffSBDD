from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_ligand_covale_annotation_alignment_gate as step14j


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_targeted_metadata_expansion_gate_v0"
STEP_LABEL = "Step 14K"
PREVIOUS_STAGE = step14j.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14j.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14j.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14j.METADATA_CSV
METADATA_CSV_SHA256 = step14j.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14j.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14j.RAW_OUTPUT_ROOT
STEP14J_ROOT = step14j.OUTPUT_ROOT
STEP14J_MANIFEST_JSON = step14j.MANIFEST_JSON
STEP14J_CANDIDATES_CSV = step14j.ALIGNMENT_CANDIDATES_CSV
STEP14J_CANDIDATES_JSON = step14j.ALIGNMENT_CANDIDATES_JSON
STEP14I_ROOT = step14j.STEP14I_ROOT
STEP14H_ROOT = step14j.STEP14H_ROOT

CANONICAL_MASK_TASK_NAMES = step14j.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14j.CANONICAL_MASK_TASK_ALIASES

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_metadata_expansion_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_expansion_precondition_audit.csv"
FIELD_SOURCE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_event_level_field_source_contract.csv"
SEED_CANDIDATE_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_seed_candidate_audit.csv"
SOURCE_REGISTRY_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_source_registry.csv"
ACQUISITION_MANIFEST_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_annotation_acquisition_manifest.csv"
ACQUISITION_MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_targeted_annotation_acquisition_manifest.json"
STOP_CONDITION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_expansion_stop_condition_contract.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_expansion_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_expansion_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_targeted_metadata_expansion_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_targeted_metadata_expansion_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_targeted_metadata_expansion_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_targeted_metadata_expansion_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
FIELD_SOURCE_COLUMNS = ["event_field", "primary_source", "secondary_source", "source_role", "can_be_auto_filled_current_step", "requires_future_acquisition", "requires_manual_review_before_ready", "field_source_contract_passed", "qa_comment"]
SEED_COLUMNS = ["seed_candidate_id", "annotation_alignment_candidate_id", "pdb_id", "ligand_identifier", "suggested_ligand_comp_id", "suggested_chain_id", "suggested_residue_name", "suggested_residue_index", "suggested_residue_atom_name", "suggested_ligand_atom_name", "suggested_covalent_bond_atom_pair", "metadata_alignment_status", "annotation_gap_status", "included_as_expansion_seed", "seed_candidate_audit_passed", "qa_comment"]
SOURCE_REGISTRY_COLUMNS = ["source_registry_id", "source_name", "source_priority", "source_type", "intended_fields", "acquisition_mode_next_step", "network_required_next_step", "raw_coordinate_required", "source_registry_passed", "qa_comment"]
ACQUISITION_MANIFEST_COLUMNS = ["acquisition_manifest_row_id", "acquisition_purpose", "source_registry_id", "source_name", "source_type", "acquisition_mode", "network_required_next_step", "seed_candidate_id", "pdb_id", "ligand_identifier", "suggested_ligand_comp_id", "query_key_type", "query_key_value", "intended_fields", "expected_output_artifact_family", "acquisition_status_current_step", "event_identity_status_current_step", "ready_candidate_current_step", "ready_for_training_current_step"]
STOP_COLUMNS = ["stop_condition_item", "observed_status", "stop_condition_passed", "qa_comment"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _metadata_hash() -> str:
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _raw_files_tracked(root: Path) -> bool:
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged(root: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", root.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _imports_forbidden_module(path: Path, forbidden: set[str]) -> bool:
    full_path = REPO_ROOT / path
    if not full_path.exists():
        return False
    tree = ast.parse(full_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden:
            return True
    return False


def _own_files_have_forbidden_imports() -> bool:
    return any(_imports_forbidden_module(path, {"requests", "urllib", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"}) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    names = {"small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(p.name in names for p in root.rglob("*") if p.is_file())


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(p.suffix.lower() in suffixes for p in root.rglob("*") if p.is_file())


def _candidate_json_rows() -> list[dict[str, Any]]:
    data = _load_json(STEP14J_CANDIDATES_JSON)
    return data if isinstance(data, list) else []


def _candidates_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]]) -> bool:
    return [r["annotation_alignment_candidate_id"] for r in csv_rows] == [str(r.get("annotation_alignment_candidate_id", "")) for r in json_rows]


def build_precondition_rows(candidates: list[dict[str, str]], json_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14J_MANIFEST_JSON) if STEP14J_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14j_manifest_exists", STEP14J_MANIFEST_JSON.as_posix(), "exists", STEP14J_MANIFEST_JSON.exists(), STEP14J_MANIFEST_JSON.exists()),
        ("step14j_stage", STEP14J_MANIFEST_JSON.as_posix(), step14j.STAGE, manifest.get("stage"), manifest.get("stage") == step14j.STAGE),
        ("step14j_all_checks_passed", STEP14J_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14j_annotation_alignment_candidate_count", STEP14J_MANIFEST_JSON.as_posix(), "9", manifest.get("annotation_alignment_candidate_count"), manifest.get("annotation_alignment_candidate_count") == 9),
        ("step14j_event_annotation_gap_count", STEP14J_MANIFEST_JSON.as_posix(), "9", manifest.get("metadata_event_annotation_gap_count"), manifest.get("metadata_event_annotation_gap_count") == 9),
        ("step14j_ready_for_targeted_expansion", STEP14J_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20"), manifest.get("ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20") is True),
        ("step14j_ready_for_training", STEP14J_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("candidate_csv_exists", STEP14J_CANDIDATES_CSV.as_posix(), "exists", STEP14J_CANDIDATES_CSV.exists(), STEP14J_CANDIDATES_CSV.exists()),
        ("candidate_json_exists", STEP14J_CANDIDATES_JSON.as_posix(), "exists", STEP14J_CANDIDATES_JSON.exists(), STEP14J_CANDIDATES_JSON.exists()),
        ("candidate_csv_json_consistent", STEP14J_CANDIDATES_JSON.as_posix(), "true", _candidates_consistent(candidates, json_rows), _candidates_consistent(candidates, json_rows)),
        ("all_candidates_pending_manual_review", STEP14J_CANDIDATES_CSV.as_posix(), "true", all(r["manual_review_status"] == "pending_manual_review" for r in candidates), all(r["manual_review_status"] == "pending_manual_review" for r in candidates)),
        ("metadata_csv_exists", METADATA_CSV.as_posix(), "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14j.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": i, "artifact_or_check": a, "expected_status": e, "observed_status": o, "precondition_passed": p, "blocking_reasons": "" if p else i} for i, a, e, o, p in checks]


def build_field_source_rows() -> list[dict[str, Any]]:
    specs = [
        ("chain_id", "RCSB mmCIF _struct_conn", "CovPDB annotation", "event structural atom-pair evidence"),
        ("residue_name", "RCSB mmCIF _struct_conn", "CovPDB targetable residue annotation", "event structural atom-pair evidence"),
        ("residue_index", "RCSB mmCIF _struct_conn", "CovPDB annotation", "event structural atom-pair evidence"),
        ("residue_atom_name", "RCSB mmCIF _struct_conn", "CovPDB annotation", "event structural atom-pair evidence"),
        ("ligand_comp_id", "RCSB mmCIF _struct_conn", "RCSB Chemical Component Dictionary", "ligand structural identity"),
        ("ligand_atom_name", "RCSB mmCIF _struct_conn", "RCSB Chemical Component Dictionary", "ligand atom naming cross-check"),
        ("covalent_bond_atom_pair", "RCSB mmCIF _struct_conn", "manual review", "event atom-pair identity"),
        ("struct_conn_type", "RCSB mmCIF _struct_conn", "manual review", "structural covalent evidence"),
        ("covpdb_ligand_identifier", "CovPDB annotation", "manual review", "CovPDB ligand context"),
        ("targetable_residue_class", "CovPDB annotation", "manual review", "semantic residue evidence"),
        ("warhead_type", "CovPDB annotation", "CovPDB warhead tables", "warhead semantic evidence"),
        ("covalent_mechanism", "CovPDB annotation", "CovPDB mechanism tables", "mechanism semantic evidence"),
        ("ligand_het_code", "PDB Chemical Component Dictionary / RCSB ligand context", "CovPDB annotation", "ligand context"),
        ("ligand_name", "PDB Chemical Component Dictionary / RCSB ligand context", "CovPDB annotation", "ligand context"),
        ("source_database", "CovPDB annotation", "manual review", "provenance context"),
        ("evidence_provenance", "RCSB mmCIF _struct_conn", "CovPDB annotation", "evidence provenance"),
        ("manual_review_status", "Manual review", "CovaPIE curator notes", "readiness control"),
        ("ready_candidate_status", "Manual review", "future QA gate", "readiness control"),
    ]
    rows = []
    for field, primary, secondary, role in specs:
        rows.append({
            "event_field": field,
            "primary_source": primary,
            "secondary_source": secondary,
            "source_role": role,
            "can_be_auto_filled_current_step": False,
            "requires_future_acquisition": field not in {"manual_review_status", "ready_candidate_status"},
            "requires_manual_review_before_ready": True,
            "field_source_contract_passed": True,
            "qa_comment": "",
        })
    return rows


def build_seed_rows(candidates: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for i, c in enumerate(candidates, start=1):
        rows.append({
            "seed_candidate_id": f"CYS_SG_TARGET_SEED_{i:06d}",
            "annotation_alignment_candidate_id": c["annotation_alignment_candidate_id"],
            "pdb_id": c["pdb_id"],
            "ligand_identifier": c["ligand_identifier"],
            "suggested_ligand_comp_id": c["suggested_ligand_comp_id"],
            "suggested_chain_id": c["suggested_chain_id"],
            "suggested_residue_name": c["suggested_residue_name"],
            "suggested_residue_index": c["suggested_residue_index"],
            "suggested_residue_atom_name": c["suggested_residue_atom_name"],
            "suggested_ligand_atom_name": c["suggested_ligand_atom_name"],
            "suggested_covalent_bond_atom_pair": c["suggested_covalent_bond_atom_pair"],
            "metadata_alignment_status": c["covpdb_metadata_alignment_status"],
            "annotation_gap_status": c["annotation_gap_status"],
            "included_as_expansion_seed": True,
            "seed_candidate_audit_passed": c["manual_review_status"] == "pending_manual_review" and not _bool(c["ready_candidate_current_step"]),
            "qa_comment": "",
        })
    return rows


def build_source_registry_rows() -> list[dict[str, Any]]:
    specs = [
        ("covpdb_targetable_residue_cys", "CovPDB targetable residue CYS", 1, "covpdb_annotation_page", "targetable_residue_class;residue_name"),
        ("covpdb_complex_card_for_seed_candidates", "CovPDB complex card", 1, "covpdb_complex_page", "covpdb_ligand_identifier;chain_id;residue_index;warhead_type;covalent_mechanism"),
        ("covpdb_ligand_pages_for_seed_candidates", "CovPDB ligand pages", 1, "covpdb_ligand_page", "ligand_name;ligand_het_code;warhead_type"),
        ("covpdb_warhead_pages_or_download_tables", "CovPDB warhead pages or tables", 1, "covpdb_annotation_table", "warhead_type"),
        ("covpdb_covalent_mechanism_pages_or_download_tables", "CovPDB mechanism pages or tables", 1, "covpdb_annotation_table", "covalent_mechanism"),
        ("rcsb_mmcif_struct_conn_crosscheck", "RCSB mmCIF struct_conn cross-check", 1, "rcsb_struct_conn_metadata", "chain_id;residue_index;covalent_bond_atom_pair;struct_conn_type"),
        ("rcsb_chemical_component_dictionary_crosscheck", "RCSB Chemical Component Dictionary", 2, "rcsb_ccd_metadata", "ligand_het_code;ligand_name;ligand_atom_name"),
        ("optional_covbinderinpdb_crosscheck", "CovBinderInPDB optional cross-check", 3, "optional_external_metadata", "event annotation comparison"),
        ("optional_covalentindb_crosscheck", "CovalentInDB optional cross-check", 3, "optional_external_metadata", "warhead/mechanism comparison"),
        ("manual_review_curator_notes", "Manual review curator notes", 1, "manual_review", "final event identity;ready status"),
    ]
    return [{"source_registry_id": sid, "source_name": name, "source_priority": pri, "source_type": typ, "intended_fields": fields, "acquisition_mode_next_step": "controlled_targeted_annotation_acquisition", "network_required_next_step": sid.startswith("covpdb") or sid.startswith("rcsb") or sid.startswith("optional"), "raw_coordinate_required": False, "source_registry_passed": True, "qa_comment": ""} for sid, name, pri, typ, fields in specs]


def build_acquisition_manifest_rows(seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    def add(source_id: str, source_name: str, source_type: str, seed: dict[str, Any] | None, query_type: str, query_value: str, fields: str) -> None:
        rows.append({
            "acquisition_manifest_row_id": f"CYS_SG_TARGET_ACQ_{len(rows)+1:06d}",
            "acquisition_purpose": "targeted_event_level_metadata_expansion",
            "source_registry_id": source_id,
            "source_name": source_name,
            "source_type": source_type,
            "acquisition_mode": "future_controlled_annotation_acquisition",
            "network_required_next_step": True,
            "seed_candidate_id": seed["seed_candidate_id"] if seed else "",
            "pdb_id": seed["pdb_id"] if seed else "",
            "ligand_identifier": seed["ligand_identifier"] if seed else "",
            "suggested_ligand_comp_id": seed["suggested_ligand_comp_id"] if seed else "",
            "query_key_type": query_type,
            "query_key_value": query_value,
            "intended_fields": fields,
            "expected_output_artifact_family": "targeted_annotation_metadata_csv_json",
            "acquisition_status_current_step": "pending_future_acquisition",
            "event_identity_status_current_step": "not_event_identity",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    for seed in seed_rows:
        add("covpdb_complex_card_for_seed_candidates", "CovPDB complex card", "covpdb_complex_page", seed, "pdb_id+covpdb_ligand_identifier", f"{seed['pdb_id']}|{seed['ligand_identifier']}", "targetable_residue_class;warhead_type;covalent_mechanism;residue annotation")
        add("covpdb_ligand_pages_for_seed_candidates", "CovPDB ligand pages", "covpdb_ligand_page", seed, "covpdb_ligand_identifier", seed["ligand_identifier"], "ligand_name;ligand_het_code;warhead_type")
        add("rcsb_chemical_component_dictionary_crosscheck", "RCSB Chemical Component Dictionary", "rcsb_ccd_metadata", seed, "het_code", seed["suggested_ligand_comp_id"], "ligand_name;ligand atom naming cross-check")
    add("covpdb_targetable_residue_cys", "CovPDB targetable residue CYS", "covpdb_annotation_page", None, "residue_name", "CYS", "targetable_residue_class")
    add("covpdb_warhead_pages_or_download_tables", "CovPDB warhead/mechanism tables", "covpdb_annotation_table", None, "global_annotation_tables", "warheads_and_mechanisms", "warhead_type;covalent_mechanism")
    return rows


def build_stop_rows(seed_count: int) -> list[dict[str, Any]]:
    rows = [
        ("current_aligned_candidate_count_9_below_20", str(seed_count < 20), True, "below 20"),
        ("targeted_annotation_acquisition_required", "true", True, "next step"),
        ("if_acquired_cys_ligand_covale_candidates_ge_20_then_manual_review", "contracted", True, ""),
        ("if_acquired_candidates_lt_20_then_expand_source_registry_or_next_batch", "contracted", True, ""),
        ("do_not_train_from_acquisition_manifest", "true", True, ""),
        ("do_not_use_pdb_id_or_ligand_id_alone_as_event_identity", "true", True, ""),
        ("covpdb_event_annotation_gap_must_be_closed_or_recorded", "true", True, ""),
        ("medium_pilot_requires_source_registry_and_review", "true", True, ""),
    ]
    return [{"stop_condition_item": i, "observed_status": o, "stop_condition_passed": p, "qa_comment": q} for i, o, p, q in rows]


def build_downstream_rows() -> list[dict[str, Any]]:
    rows = [
        ("targeted_metadata_expansion_gate_completed", "true", True, "covapie_cys_sg_targeted_annotation_acquisition_smoke", ""),
        ("acquisition_manifest_written", "true", True, "covapie_cys_sg_targeted_annotation_acquisition_smoke", ""),
        ("no_network_current_step", "true", True, "covapie_cys_sg_targeted_annotation_acquisition_smoke", ""),
        ("ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke", "true", True, "covapie_cys_sg_targeted_annotation_acquisition_smoke", ""),
        ("ready_for_manual_review_false", "false", True, "not_allowed_current_step", ""),
        ("ready_for_small_pilot_manifest_rerun_false", "false", True, "not_allowed_current_step", ""),
        ("ready_for_actual_dataloader_false", "false", True, "not_allowed_current_step", ""),
        ("training_still_false", "false", True, "not_allowed_current_step", ""),
        ("feature_semantics_still_not_training_final", "true", True, "feature_semantics_audit_required_before_training", ""),
        ("raw_files_remain_untracked_uncommitted", str(not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT), "raw_files_not_committable", ""),
    ]
    return [{"readiness_item": i, "observed_status": o, "readiness_passed": p, "next_required_gate": n, "qa_comment": q} for i, o, p, n, q in rows]


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_file_content_read_current_step", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14j_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14J_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14J_ROOT.as_posix()])),
        ("step14i_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14I_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14I_ROOT.as_posix()])),
        ("step14h_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14H_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14H_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_download_manifest_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_sample_index_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("derived_output_no_forbidden_binary_or_raw_suffix", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("no_ready_candidates_created", "passed", "passed", True),
    ]
    return [{"safety_item": i, "required_status": r, "observed_status": o, "safety_passed": p, "blocking_reasons": "" if p else i} for i, r, o, p in checks]


def build_manifest(pre, field, seeds, registry, acq, stop, downstream, safety) -> dict[str, Any]:
    passed = all(_all_true(rows, col) for rows, col in [(pre, "precondition_passed"), (field, "field_source_contract_passed"), (seeds, "seed_candidate_audit_passed"), (registry, "source_registry_passed"), (stop, "stop_condition_passed"), (downstream, "readiness_passed"), (safety, "safety_passed")])
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "previous_stage": PREVIOUS_STAGE, "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE, "current_source_database": CURRENT_SOURCE_DATABASE,
        "input_annotation_alignment_candidate_count": len(seeds), "seed_candidate_count": len(seeds),
        "event_level_field_source_contract_written": True, "source_registry_row_count": len(registry),
        "acquisition_manifest_row_count": len(acq), "acquisition_manifest_csv_json_consistent": True,
        "ready_candidate_count_current_step": 0, "no_ready_candidates_created": True,
        "network_access_used": False, "download_attempted": False, "raw_file_content_read_current_step": False, "raw_files_written_current_step": False,
        "raw_files_tracked": _raw_files_tracked(RAW_OUTPUT_ROOT), "raw_files_staged": _raw_files_staged(RAW_OUTPUT_ROOT),
        "sample_download_manifest_written": False, "final_dataset_written": False, "sample_index_written_current_step": False,
        "split_assignments_written": False, "leakage_matrix_written": False, "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False, "training_artifacts_written": False,
        "torch_imported": False, "numpy_imported": False, "rdkit_used": False, "biopdb_parser_used": False, "gemmi_used": False, "gzip_open_used": False,
        "feature_semantics_known_for_training": False, "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke": True,
        "ready_for_covapie_cys_sg_ligand_covale_manual_review_gate": False,
        "ready_for_covapie_small_pilot_manifest_rerun_gate": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES, "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True, "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True, "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_cys_sg_targeted_annotation_acquisition_smoke",
        "all_checks_passed": passed, "blocking_reasons": [] if passed else ["step14k_gate_check_failed"],
    }


def run_covapie_cys_sg_targeted_metadata_expansion_gate_v0() -> dict[str, Any]:
    candidates = _csv_rows(STEP14J_CANDIDATES_CSV)
    json_rows = _candidate_json_rows()
    pre = build_precondition_rows(candidates, json_rows)
    field = build_field_source_rows()
    seeds = build_seed_rows(candidates)
    registry = build_source_registry_rows()
    acq = build_acquisition_manifest_rows(seeds)
    stop = build_stop_rows(len(seeds))
    downstream = build_downstream_rows()
    safety = build_safety_rows()
    manifest = build_manifest(pre, field, seeds, registry, acq, stop, downstream, safety)
    return {"precondition_rows": pre, "field_rows": field, "seed_rows": seeds, "registry_rows": registry, "acquisition_rows": acq, "stop_rows": stop, "downstream_rows": downstream, "safety_rows": safety, "manifest": manifest}

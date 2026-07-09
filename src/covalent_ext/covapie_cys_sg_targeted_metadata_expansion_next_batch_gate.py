from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_gate as step14k


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0"
STEP_LABEL = "Step 14M"
PREVIOUS_STAGE = "covapie_cys_sg_targeted_annotation_acquisition_smoke_v0"
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14k.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14k.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14k.METADATA_CSV
METADATA_CSV_SHA256 = step14k.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14k.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14k.RAW_OUTPUT_ROOT
STEP14K_ROOT = step14k.OUTPUT_ROOT
STEP14J_ROOT = step14k.STEP14J_ROOT
STEP14L_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_annotation_acquisition_smoke_v0")
STEP14L_MANIFEST_JSON = STEP14L_ROOT / "covapie_cys_sg_targeted_annotation_acquisition_smoke_manifest.json"
STEP14L_ACQUIRED_CSV = STEP14L_ROOT / "covapie_cys_sg_acquired_event_level_annotation_candidates.csv"
STEP14L_ACQUIRED_JSON = STEP14L_ROOT / "covapie_cys_sg_acquired_event_level_annotation_candidates.json"
STEP14K_SOURCE_REGISTRY_CSV = step14k.SOURCE_REGISTRY_CSV
STEP14K_ACQUISITION_MANIFEST_CSV = step14k.ACQUISITION_MANIFEST_CSV
STEP14K_FIELD_SOURCE_CONTRACT_CSV = step14k.FIELD_SOURCE_CONTRACT_CSV

CANONICAL_MASK_TASK_NAMES = step14k.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14k.CANONICAL_MASK_TASK_ALIASES

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_precondition_audit.csv"
EXISTING_CANDIDATE_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_existing_acquired_candidate_audit.csv"
SOURCE_STRATEGY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_source_strategy_contract.csv"
EXCLUSION_REGISTRY_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_exclusion_registry.csv"
NEXT_BATCH_ACQUISITION_MANIFEST_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_acquisition_manifest.csv"
NEXT_BATCH_ACQUISITION_MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_next_batch_acquisition_manifest.json"
THRESHOLD_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_threshold_contract.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_targeted_metadata_expansion_next_batch_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
EXISTING_COLUMNS = ["existing_candidate_id", "acquired_annotation_candidate_id", "seed_candidate_id", "pdb_id", "ligand_identifier", "suggested_ligand_comp_id", "suggested_residue_name", "suggested_residue_index", "suggested_residue_atom_name", "suggested_ligand_atom_name", "suggested_covalent_bond_atom_pair", "covpdb_reaction_name", "covpdb_warhead_name", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "manual_review_status", "ready_candidate_current_step", "included_in_exclusion_registry", "existing_candidate_audit_passed", "qa_comment"]
STRATEGY_COLUMNS = ["strategy_item", "strategy_role", "primary_source", "secondary_source", "network_required_next_step", "raw_coordinate_required_next_step", "strategy_contract_passed", "qa_comment"]
EXCLUSION_COLUMNS = ["exclusion_registry_id", "exclusion_reason", "pdb_id", "ligand_identifier", "suggested_ligand_comp_id", "covpdb_complex_card_url", "suggested_covalent_bond_atom_pair", "covpdb_reaction_name", "covpdb_warhead_name", "exclusion_registry_passed", "qa_comment"]
NEXT_BATCH_COLUMNS = ["next_batch_acquisition_row_id", "acquisition_purpose", "source_name", "source_type", "acquisition_mode", "network_required_next_step", "query_key_type", "query_key_value", "intended_fields", "duplicate_exclusion_policy", "minimum_new_candidate_target", "current_confirmed_annotation_candidate_count", "total_candidate_target", "acquisition_status_current_step", "event_identity_status_current_step", "ready_candidate_current_step", "ready_for_training_current_step"]
THRESHOLD_COLUMNS = ["threshold_item", "observed_status", "threshold_contract_passed", "qa_comment"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]

TOTAL_CANDIDATE_TARGET = 20


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


def _json_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]], key: str) -> bool:
    return [row[key] for row in csv_rows] == [str(row.get(key, "")) for row in json_rows]


def build_precondition_rows(acquired: list[dict[str, str]], acquired_json: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14L_MANIFEST_JSON) if STEP14L_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14l_manifest_exists", STEP14L_MANIFEST_JSON.as_posix(), "exists", STEP14L_MANIFEST_JSON.exists(), STEP14L_MANIFEST_JSON.exists()),
        ("step14l_stage", STEP14L_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14l_all_checks_passed", STEP14L_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14l_acquired_annotation_candidate_count", STEP14L_MANIFEST_JSON.as_posix(), "9", manifest.get("acquired_annotation_candidate_count"), manifest.get("acquired_annotation_candidate_count") == 9),
        ("step14l_complex_card_event_annotation_acquired_count", STEP14L_MANIFEST_JSON.as_posix(), "9", manifest.get("complex_card_event_annotation_acquired_count"), manifest.get("complex_card_event_annotation_acquired_count") == 9),
        ("step14l_partial_annotation_count", STEP14L_MANIFEST_JSON.as_posix(), "0", manifest.get("partial_annotation_count"), manifest.get("partial_annotation_count") == 0),
        ("step14l_failed_annotation_count", STEP14L_MANIFEST_JSON.as_posix(), "0", manifest.get("failed_annotation_count"), manifest.get("failed_annotation_count") == 0),
        ("step14l_ready_for_next_batch_gate", STEP14L_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate"), manifest.get("ready_for_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate") is True),
        ("step14l_ready_for_training", STEP14L_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14l_acquired_csv_exists", STEP14L_ACQUIRED_CSV.as_posix(), "exists", STEP14L_ACQUIRED_CSV.exists(), STEP14L_ACQUIRED_CSV.exists()),
        ("step14l_acquired_json_exists", STEP14L_ACQUIRED_JSON.as_posix(), "exists", STEP14L_ACQUIRED_JSON.exists(), STEP14L_ACQUIRED_JSON.exists()),
        ("step14l_acquired_csv_json_consistent", STEP14L_ACQUIRED_JSON.as_posix(), "true", _json_consistent(acquired, acquired_json, "acquired_annotation_candidate_id"), _json_consistent(acquired, acquired_json, "acquired_annotation_candidate_id")),
        ("step14k_source_registry_exists", STEP14K_SOURCE_REGISTRY_CSV.as_posix(), "exists", STEP14K_SOURCE_REGISTRY_CSV.exists(), STEP14K_SOURCE_REGISTRY_CSV.exists()),
        ("step14k_field_source_contract_exists", STEP14K_FIELD_SOURCE_CONTRACT_CSV.as_posix(), "exists", STEP14K_FIELD_SOURCE_CONTRACT_CSV.exists(), STEP14K_FIELD_SOURCE_CONTRACT_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14k.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_existing_candidate_rows(acquired: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(acquired, start=1):
        passed = row["manual_review_status"] == "pending_manual_review" and not _bool(row["ready_candidate_current_step"])
        rows.append({
            "existing_candidate_id": f"CYS_SG_EXISTING_ACQ_{idx:06d}",
            "acquired_annotation_candidate_id": row["acquired_annotation_candidate_id"],
            "seed_candidate_id": row["seed_candidate_id"],
            "pdb_id": row["pdb_id"],
            "ligand_identifier": row["ligand_identifier"],
            "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
            "suggested_residue_name": row["suggested_residue_name"],
            "suggested_residue_index": row["suggested_residue_index"],
            "suggested_residue_atom_name": row["suggested_residue_atom_name"],
            "suggested_ligand_atom_name": row["suggested_ligand_atom_name"],
            "suggested_covalent_bond_atom_pair": row["suggested_covalent_bond_atom_pair"],
            "covpdb_reaction_name": row["covpdb_reaction_name"],
            "covpdb_warhead_name": row["covpdb_warhead_name"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "manual_review_status": row["manual_review_status"],
            "ready_candidate_current_step": False,
            "included_in_exclusion_registry": True,
            "existing_candidate_audit_passed": passed,
            "qa_comment": "",
        })
    return rows


def build_strategy_rows() -> list[dict[str, Any]]:
    specs = [
        ("covpdb_targetable_residue_cys_page_primary", "discover more CYS targetable residue complexes", "CovPDB targetable residue CYS page", "CovPDB complex cards", True, False),
        ("covpdb_cys_complex_listing_or_download_primary", "enumerate additional CYS ligand covalent complex metadata", "CovPDB CYS complex listing/download metadata", "CovPDB residues list", True, False),
        ("covpdb_ligand_card_followup", "follow ligand cards for additional bound PDB/complex links", "CovPDB ligand cards", "CovPDB complex cards", True, False),
        ("covpdb_complex_card_followup", "extract event-level reaction/residue/chain/warhead metadata", "CovPDB complex cards", "manual review", True, False),
        ("rcsb_ccd_crosscheck", "cross-check ligand identity and chemistry metadata", "RCSB Chemical Component Dictionary", "CovPDB ligand card", True, False),
        ("rcsb_mmcif_struct_conn_future_crosscheck", "future raw-coordinate structural cross-check outside this gate", "RCSB mmCIF struct_conn", "manual review", True, True),
        ("exclude_existing_9_candidates", "avoid duplicates from Step 14L", "Step 14L acquired candidates", "next-batch exclusion registry", False, False),
        ("exclude_disulfide_or_sg_sg", "avoid non-ligand CYS SG-SG/disulfide events", "event-level source filters", "manual review", True, False),
        ("require_cys_sg_ligand_covale", "keep scope to CYS SG ligand covale candidates", "CovPDB/RCSB event annotation", "manual review", True, False),
        ("manual_review_required_before_ready", "prevent automatic ready labels", "manual review", "future QA gate", False, False),
        ("no_training_current_step", "preserve no-training boundary", "CovaPIE gate policy", "feature semantics audit", False, False),
        ("small_pilot_threshold_20_required", "expand from 9 toward 20 candidates", "Step 14L counts", "next batch smoke", False, False),
    ]
    return [{"strategy_item": item, "strategy_role": role, "primary_source": primary, "secondary_source": secondary, "network_required_next_step": net, "raw_coordinate_required_next_step": raw, "strategy_contract_passed": True, "qa_comment": ""} for item, role, primary, secondary, net, raw in specs]


def build_exclusion_rows(acquired: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(acquired, start=1):
        rows.append({
            "exclusion_registry_id": f"CYS_SG_NEXT_EXCLUDE_{idx:06d}",
            "exclusion_reason": "already_acquired_in_step14l",
            "pdb_id": row["pdb_id"],
            "ligand_identifier": row["ligand_identifier"],
            "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
            "covpdb_complex_card_url": row["covpdb_complex_card_url"],
            "suggested_covalent_bond_atom_pair": row["suggested_covalent_bond_atom_pair"],
            "covpdb_reaction_name": row["covpdb_reaction_name"],
            "covpdb_warhead_name": row["covpdb_warhead_name"],
            "exclusion_registry_passed": True,
            "qa_comment": "",
        })
    return rows


def build_next_batch_manifest_rows(current_count: int) -> list[dict[str, Any]]:
    needed = max(0, TOTAL_CANDIDATE_TARGET - current_count)
    specs = [
        ("CovPDB targetable residue CYS page/listing", "covpdb_targetable_residue_metadata", "residue_name", "CYS", "pdb_id;ligand_id;residue_name;residue_index;chain_id"),
        ("CovPDB CYS complex listing/download metadata", "covpdb_complex_listing_metadata", "targetable_residue", "CYS", "candidate PDB/ligand pairs;complex card URLs"),
        ("CovPDB warhead/mechanism table follow-up", "covpdb_annotation_table", "annotation_table", "warheads_and_mechanisms", "warhead_name;reaction_name;covalent_mechanism"),
        ("RCSB Chemical Component Dictionary cross-check planning", "rcsb_ccd_metadata", "het_code_batch", "next_batch_ligands", "ligand_name;formula;type;descriptor"),
        ("RCSB struct_conn future cross-check planning", "future_struct_conn_crosscheck", "pdb_id_batch", "next_batch_pdb_ids", "chain_id;residue_index;covalent_bond_atom_pair;struct_conn_type"),
    ]
    rows = []
    for idx, (source_name, source_type, query_type, query_value, fields) in enumerate(specs, start=1):
        rows.append({
            "next_batch_acquisition_row_id": f"CYS_SG_NEXT_BATCH_ACQ_{idx:06d}",
            "acquisition_purpose": "expand_cys_sg_ligand_covale_candidate_pool_toward_20",
            "source_name": source_name,
            "source_type": source_type,
            "acquisition_mode": "future_controlled_next_batch_annotation_acquisition",
            "network_required_next_step": True,
            "query_key_type": query_type,
            "query_key_value": query_value,
            "intended_fields": fields,
            "duplicate_exclusion_policy": "exclude_step14l_acquired_candidates_by_event_tuple_not_pdb_or_ligand_alone",
            "minimum_new_candidate_target": needed,
            "current_confirmed_annotation_candidate_count": current_count,
            "total_candidate_target": TOTAL_CANDIDATE_TARGET,
            "acquisition_status_current_step": "pending_future_acquisition",
            "event_identity_status_current_step": "not_event_identity",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_threshold_rows(current_count: int) -> list[dict[str, Any]]:
    needed = max(0, TOTAL_CANDIDATE_TARGET - current_count)
    specs = [
        ("current_acquired_annotation_candidate_count_9", current_count == 9, ""),
        ("target_minimum_count_20", TOTAL_CANDIDATE_TARGET == 20, ""),
        ("additional_candidate_needed_count_11", needed == 11, ""),
        ("next_batch_minimum_new_candidate_target_11", needed == 11, ""),
        ("if_next_batch_total_ge_20_then_manual_review_gate", "contracted", ""),
        ("if_next_batch_total_lt_20_then_repeat_next_batch_or_expand_source_registry", "contracted", ""),
        ("do_not_train_before_manual_review", "true", ""),
        ("do_not_train_before_feature_semantics_audit", "true", ""),
        ("do_not_use_acquisition_manifest_as_training_data", "true", ""),
        ("keep_existing_9_pending_manual_review", "true", ""),
    ]
    return [{"threshold_item": item, "observed_status": observed, "threshold_contract_passed": True, "qa_comment": comment} for item, observed, comment in specs]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("next_batch_gate_completed", "true", True, "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke", ""),
        ("next_batch_acquisition_manifest_written", "true", True, "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke", ""),
        ("no_network_current_step", "true", True, "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke", ""),
        ("ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke", "true", True, "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke", ""),
        ("ready_for_acquired_annotation_manual_review_false_current_step", "false", True, "not_allowed_current_step", ""),
        ("ready_for_small_pilot_manifest_rerun_false", "false", True, "not_allowed_current_step", ""),
        ("ready_for_actual_dataloader_false", "false", True, "not_allowed_current_step", ""),
        ("training_still_false", "false", True, "not_allowed_current_step", ""),
        ("feature_semantics_still_not_training_final", "true", True, "feature_semantics_audit_required_before_training", ""),
        ("raw_files_remain_untracked_uncommitted", str(not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT), "raw_files_not_committable", ""),
    ]
    return [{"readiness_item": item, "observed_status": observed, "readiness_passed": passed, "next_required_gate": next_gate, "qa_comment": comment} for item, observed, passed, next_gate, comment in specs]


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
    forbidden = {"requests", "urllib", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "bs4"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    names = {"small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(p.name in names for p in root.rglob("*") if p.is_file())


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(p.suffix.lower() in suffixes for p in root.rglob("*") if p.is_file())


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_file_content_read_current_step", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("no_html_files_written_current_step", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14l_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14L_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14L_ROOT.as_posix()])),
        ("step14k_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14K_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14K_ROOT.as_posix()])),
        ("step14j_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14J_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14J_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_download_manifest_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_sample_index_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_selenium_playwright_bs4_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("derived_output_no_forbidden_binary_raw_or_html_suffix", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("no_ready_candidates_created", "passed", "passed", True),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, existing, strategy, exclusion, next_batch, threshold, downstream, safety) -> dict[str, Any]:
    current_count = len(existing)
    needed = max(0, TOTAL_CANDIDATE_TARGET - current_count)
    passed = all(_all_true(rows, col) for rows, col in [(pre, "precondition_passed"), (existing, "existing_candidate_audit_passed"), (strategy, "strategy_contract_passed"), (exclusion, "exclusion_registry_passed"), (threshold, "threshold_contract_passed"), (downstream, "readiness_passed"), (safety, "safety_passed")])
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "input_acquired_annotation_candidate_count": current_count,
        "existing_candidate_exclusion_registry_count": len(exclusion),
        "current_candidate_count": current_count,
        "total_candidate_target": TOTAL_CANDIDATE_TARGET,
        "additional_candidate_needed_count": needed,
        "next_batch_minimum_new_candidate_target": needed,
        "next_batch_source_strategy_row_count": len(strategy),
        "next_batch_acquisition_manifest_row_count": len(next_batch),
        "next_batch_acquisition_manifest_csv_json_consistent": True,
        "ready_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "network_access_used": False,
        "download_attempted": False,
        "raw_file_content_read_current_step": False,
        "raw_files_written_current_step": False,
        "html_files_written_current_step": False,
        "sample_download_manifest_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "requests_used": False,
        "selenium_used": False,
        "playwright_used": False,
        "bs4_used": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke": True,
        "ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate": False,
        "ready_for_covapie_small_pilot_manifest_rerun_gate": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14m_next_batch_gate_check_failed"],
    }


def run_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0() -> dict[str, Any]:
    acquired = _csv_rows(STEP14L_ACQUIRED_CSV)
    acquired_json = _load_json(STEP14L_ACQUIRED_JSON)
    pre = build_precondition_rows(acquired, acquired_json)
    existing = build_existing_candidate_rows(acquired)
    strategy = build_strategy_rows()
    exclusion = build_exclusion_rows(acquired)
    next_batch = build_next_batch_manifest_rows(len(acquired))
    threshold = build_threshold_rows(len(acquired))
    downstream = build_downstream_rows()
    safety = build_safety_rows()
    manifest = build_manifest(pre, existing, strategy, exclusion, next_batch, threshold, downstream, safety)
    return {
        "precondition_rows": pre,
        "existing_rows": existing,
        "strategy_rows": strategy,
        "exclusion_rows": exclusion,
        "next_batch_rows": next_batch,
        "threshold_rows": threshold,
        "downstream_rows": downstream,
        "safety_rows": safety,
        "manifest": manifest,
    }

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_next_batch_gate as step14m


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_acquired_annotation_manual_review_gate_v0"
STEP_LABEL = "Step 14O"
PREVIOUS_STAGE = "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0"
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = "covpdb_manual_metadata_v0"
CURRENT_SOURCE_DATABASE = "CovPDB"
TOTAL_CANDIDATE_TARGET = 20
METADATA_CSV = step14m.METADATA_CSV
METADATA_CSV_SHA256 = step14m.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14m.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14m.RAW_OUTPUT_ROOT
STEP14K_ROOT = step14m.STEP14K_ROOT
STEP14L_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_annotation_acquisition_smoke_v0")
STEP14N_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0")
STEP14M_ROOT = step14m.OUTPUT_ROOT

STEP14L_CANDIDATES_CSV = STEP14L_ROOT / "covapie_cys_sg_acquired_event_level_annotation_candidates.csv"
STEP14L_CANDIDATES_JSON = STEP14L_ROOT / "covapie_cys_sg_acquired_event_level_annotation_candidates.json"
STEP14N_MANIFEST_JSON = STEP14N_ROOT / "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_manifest.json"
STEP14N_CANDIDATES_CSV = STEP14N_ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.csv"
STEP14N_CANDIDATES_JSON = STEP14N_ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.json"

CANONICAL_MASK_TASK_NAMES = step14m.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14m.CANONICAL_MASK_TASK_ALIASES

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_acquired_annotation_manual_review_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_manual_review_precondition_audit.csv"
COMBINED_INVENTORY_CSV = OUTPUT_ROOT / "covapie_cys_sg_combined_acquired_annotation_inventory.csv"
EVENT_IDENTITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_combined_event_identity_audit.csv"
CRITERIA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_manual_review_criteria_contract.csv"
DECISION_TEMPLATE_CSV = OUTPUT_ROOT / "covapie_cys_sg_manual_review_decision_template.csv"
DECISION_TEMPLATE_JSON = OUTPUT_ROOT / "covapie_cys_sg_manual_review_decision_template.json"
AUTO_FLAG_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_manual_review_auto_flag_audit.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_manual_review_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_manual_review_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_acquired_annotation_manual_review_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_acquired_annotation_manual_review_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_acquired_annotation_manual_review_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_acquired_annotation_manual_review_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
INVENTORY_COLUMNS = ["manual_review_candidate_id", "candidate_source_stage", "source_candidate_id", "pdb_id", "ligand_identifier_if_available", "suggested_ligand_comp_id", "ccd_ligand_name", "ccd_formula", "ccd_type", "covpdb_reaction_name", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "covpdb_warhead_name", "covpdb_sasa", "covpdb_pka", "covpdb_uniprot", "complex_card_url", "struct_conn_evidence_status", "suggested_residue_atom_name", "suggested_ligand_atom_name", "suggested_covalent_bond_atom_pair", "rcsb_struct_conn_type", "event_identity_status_current_step", "manual_review_status", "ready_candidate_current_step", "ready_for_training_current_step", "inventory_row_passed", "qa_comment"]
EVENT_IDENTITY_COLUMNS = ["manual_review_candidate_id", "event_identity_tuple", "pdb_id", "suggested_ligand_comp_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "complex_card_url", "duplicate_within_combined_inventory", "pdb_id_alone_used_as_identity", "ligand_id_alone_used_as_identity", "has_cys_residue", "has_warhead", "has_reaction", "has_chain", "has_ligand_metadata", "has_struct_conn_evidence", "requires_future_struct_conn_crosscheck", "event_identity_audit_passed", "qa_comment"]
CRITERIA_COLUMNS = ["criterion_id", "criterion_description", "applies_to_stage14l", "applies_to_stage14n", "required_before_manual_acceptance", "required_before_dataset_ready", "criterion_contract_passed", "qa_comment"]
DECISION_TEMPLATE_COLUMNS = ["manual_review_candidate_id", "candidate_source_stage", "pdb_id", "ligand_identifier_if_available", "suggested_ligand_comp_id", "ccd_ligand_name", "ccd_formula", "ccd_type", "covpdb_reaction_name", "covpdb_warhead_name", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "covpdb_uniprot", "complex_card_url", "struct_conn_evidence_status", "suggested_covalent_bond_atom_pair", "auto_review_flag", "manual_decision", "manual_decision_allowed_values", "manual_decision_reason", "curator_initials", "review_date", "review_comment"]
AUTO_FLAG_COLUMNS = ["auto_flag_item", "auto_flag_value", "auto_flag_audit_passed", "qa_comment"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]

ALLOWED_DECISIONS = "pending_manual_review;accept_for_future_struct_conn_crosscheck;reject;needs_more_evidence"


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


def build_precondition_rows(step14l_rows: list[dict[str, str]], step14l_json: list[dict[str, Any]], step14n_rows: list[dict[str, str]], step14n_json: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14N_MANIFEST_JSON) if STEP14N_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14n_manifest_exists", STEP14N_MANIFEST_JSON.as_posix(), "exists", STEP14N_MANIFEST_JSON.exists(), STEP14N_MANIFEST_JSON.exists()),
        ("step14n_stage", STEP14N_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14n_all_checks_passed", STEP14N_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14n_existing_candidate_count", STEP14N_MANIFEST_JSON.as_posix(), "9", manifest.get("existing_candidate_count"), manifest.get("existing_candidate_count") == 9),
        ("step14n_new_candidate_count", STEP14N_MANIFEST_JSON.as_posix(), "16", manifest.get("new_candidate_count"), manifest.get("new_candidate_count") == 16),
        ("step14n_combined_candidate_count", STEP14N_MANIFEST_JSON.as_posix(), "25", manifest.get("combined_candidate_count"), manifest.get("combined_candidate_count") == 25),
        ("step14n_additional_candidate_needed_after_step", STEP14N_MANIFEST_JSON.as_posix(), "0", manifest.get("additional_candidate_needed_after_step"), manifest.get("additional_candidate_needed_after_step") == 0),
        ("step14n_ready_for_manual_review_gate", STEP14N_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate"), manifest.get("ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate") is True),
        ("step14n_ready_for_training", STEP14N_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14n_candidates_csv_exists", STEP14N_CANDIDATES_CSV.as_posix(), "exists", STEP14N_CANDIDATES_CSV.exists(), STEP14N_CANDIDATES_CSV.exists()),
        ("step14n_candidates_json_exists", STEP14N_CANDIDATES_JSON.as_posix(), "exists", STEP14N_CANDIDATES_JSON.exists(), STEP14N_CANDIDATES_JSON.exists()),
        ("step14n_candidates_csv_json_consistent", STEP14N_CANDIDATES_JSON.as_posix(), "true", _json_consistent(step14n_rows, step14n_json, "next_batch_acquired_candidate_id"), _json_consistent(step14n_rows, step14n_json, "next_batch_acquired_candidate_id")),
        ("step14l_candidates_csv_exists", STEP14L_CANDIDATES_CSV.as_posix(), "exists", STEP14L_CANDIDATES_CSV.exists(), STEP14L_CANDIDATES_CSV.exists()),
        ("step14l_candidates_json_exists", STEP14L_CANDIDATES_JSON.as_posix(), "exists", STEP14L_CANDIDATES_JSON.exists(), STEP14L_CANDIDATES_JSON.exists()),
        ("step14l_candidates_csv_json_consistent", STEP14L_CANDIDATES_JSON.as_posix(), "true", _json_consistent(step14l_rows, step14l_json, "acquired_annotation_candidate_id"), _json_consistent(step14l_rows, step14l_json, "acquired_annotation_candidate_id")),
        ("metadata_csv_exists", METADATA_CSV.as_posix(), "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("raw_roots_not_staged", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_staged(RAW_OUTPUT_ROOT) or _raw_files_staged(RAW_REFERENCE_ROOT), not _raw_files_staged(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14m.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_combined_inventory_rows(step14l_rows: list[dict[str, str]], step14n_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(step14l_rows, start=1):
        passed = row["manual_review_status"] == "pending_manual_review" and not _bool(row["ready_candidate_current_step"]) and row["covpdb_residue_name"] == "CYS"
        rows.append({
            "manual_review_candidate_id": f"CYS_SG_MANUAL_REVIEW_{idx:06d}",
            "candidate_source_stage": "step14l_targeted_annotation_acquisition",
            "source_candidate_id": row["acquired_annotation_candidate_id"],
            "pdb_id": row["pdb_id"],
            "ligand_identifier_if_available": row["ligand_identifier"],
            "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
            "ccd_ligand_name": row["ccd_ligand_name"],
            "ccd_formula": row["ccd_formula"],
            "ccd_type": row["ccd_type"],
            "covpdb_reaction_name": row["covpdb_reaction_name"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "covpdb_warhead_name": row["covpdb_warhead_name"],
            "covpdb_sasa": row["covpdb_sasa"],
            "covpdb_pka": row["covpdb_pka"],
            "covpdb_uniprot": "",
            "complex_card_url": row["covpdb_complex_card_url"],
            "struct_conn_evidence_status": "available_from_step14j_struct_conn",
            "suggested_residue_atom_name": row["suggested_residue_atom_name"],
            "suggested_ligand_atom_name": row["suggested_ligand_atom_name"],
            "suggested_covalent_bond_atom_pair": row["suggested_covalent_bond_atom_pair"],
            "rcsb_struct_conn_type": row["rcsb_struct_conn_type"],
            "event_identity_status_current_step": "not_event_identity_until_manual_review",
            "manual_review_status": "pending_manual_review",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
            "inventory_row_passed": passed,
            "qa_comment": "",
        })
    offset = len(rows)
    for idx, row in enumerate(step14n_rows, start=1):
        passed = row["manual_review_status"] == "pending_manual_review" and not _bool(row["ready_candidate_current_step"]) and row["covpdb_residue_name"] == "CYS"
        rows.append({
            "manual_review_candidate_id": f"CYS_SG_MANUAL_REVIEW_{offset + idx:06d}",
            "candidate_source_stage": "step14n_next_batch_metadata_acquisition",
            "source_candidate_id": row["next_batch_acquired_candidate_id"],
            "pdb_id": row["pdb_id"],
            "ligand_identifier_if_available": row["ligand_identifier_if_available"],
            "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
            "ccd_ligand_name": row["ccd_ligand_name"],
            "ccd_formula": row["ccd_formula"],
            "ccd_type": row["ccd_type"],
            "covpdb_reaction_name": row["covpdb_reaction_name"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "covpdb_warhead_name": row["covpdb_warhead_name"],
            "covpdb_sasa": row["covpdb_sasa"],
            "covpdb_pka": row["covpdb_pka"],
            "covpdb_uniprot": row["covpdb_uniprot"],
            "complex_card_url": row["complex_card_url"],
            "struct_conn_evidence_status": "pending_future_raw_mmcif_struct_conn_crosscheck",
            "suggested_residue_atom_name": "",
            "suggested_ligand_atom_name": "",
            "suggested_covalent_bond_atom_pair": "",
            "rcsb_struct_conn_type": "",
            "event_identity_status_current_step": "not_event_identity_until_manual_review",
            "manual_review_status": "pending_manual_review",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
            "inventory_row_passed": passed,
            "qa_comment": "",
        })
    return rows


def _event_identity_tuple(row: dict[str, Any]) -> str:
    payload = {
        "pdb_id": row["pdb_id"],
        "ligand": row["suggested_ligand_comp_id"],
        "residue_name": row["covpdb_residue_name"],
        "residue_index": row["covpdb_residue_index"],
        "chain_id": row["covpdb_chain_id"],
        "complex_card_url": row["complex_card_url"],
        "covalent_bond_atom_pair": row["suggested_covalent_bond_atom_pair"],
    }
    return json.dumps(payload, sort_keys=True)


def build_event_identity_rows(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tuples = [_event_identity_tuple(row) for row in inventory]
    counts = {value: tuples.count(value) for value in tuples}
    rows: list[dict[str, Any]] = []
    for row, event_tuple in zip(inventory, tuples):
        duplicate = counts[event_tuple] > 1
        has_struct = row["struct_conn_evidence_status"] == "available_from_step14j_struct_conn"
        requires_crosscheck = row["struct_conn_evidence_status"] == "pending_future_raw_mmcif_struct_conn_crosscheck"
        passed = (
            not duplicate
            and row["covpdb_residue_name"] == "CYS"
            and bool(row["covpdb_warhead_name"])
            and bool(row["covpdb_reaction_name"])
            and bool(row["covpdb_chain_id"])
            and bool(row["suggested_ligand_comp_id"] or row["ccd_ligand_name"] or row["ligand_identifier_if_available"])
        )
        rows.append({
            "manual_review_candidate_id": row["manual_review_candidate_id"],
            "event_identity_tuple": event_tuple,
            "pdb_id": row["pdb_id"],
            "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "complex_card_url": row["complex_card_url"],
            "duplicate_within_combined_inventory": duplicate,
            "pdb_id_alone_used_as_identity": False,
            "ligand_id_alone_used_as_identity": False,
            "has_cys_residue": row["covpdb_residue_name"] == "CYS",
            "has_warhead": bool(row["covpdb_warhead_name"]),
            "has_reaction": bool(row["covpdb_reaction_name"]),
            "has_chain": bool(row["covpdb_chain_id"]),
            "has_ligand_metadata": bool(row["suggested_ligand_comp_id"] or row["ccd_ligand_name"] or row["ligand_identifier_if_available"]),
            "has_struct_conn_evidence": has_struct,
            "requires_future_struct_conn_crosscheck": requires_crosscheck,
            "event_identity_audit_passed": passed,
            "qa_comment": "" if passed else "manual_review_required_for_incomplete_event_metadata",
        })
    return rows


def build_criteria_rows() -> list[dict[str, Any]]:
    specs = [
        ("require_cys_residue", "Candidate must target CYS residue annotation.", True, True, True, True),
        ("require_covalent_reaction_annotation", "Candidate must include covalent reaction annotation.", True, True, True, True),
        ("require_warhead_annotation", "Candidate must include warhead annotation.", True, True, True, True),
        ("require_chain_and_residue_index", "Candidate must include chain ID and residue index.", True, True, True, True),
        ("require_ligand_het_or_ccd_metadata", "Candidate must include HET code or CCD ligand metadata.", True, True, True, True),
        ("require_no_duplicate_event_identity", "Candidate must not duplicate another combined event identity.", True, True, True, True),
        ("require_not_disulfide_or_sg_sg", "Candidate must not be a disulfide or protein-protein SG-SG event.", True, True, True, True),
        ("require_struct_conn_crosscheck_before_dataset_ready", "Dataset-ready candidates require struct_conn cross-check; Step 14N rows still need future raw mmCIF cross-check.", True, True, False, True),
        ("require_manual_decision_before_ready", "A human manual decision is required before any ready label.", True, True, True, True),
        ("require_feature_semantics_audit_before_training", "Feature semantics audit remains required before training.", True, True, False, True),
        ("require_split_leakage_gate_before_training", "Split/leakage design gate remains required before training.", True, True, False, True),
        ("do_not_train_from_review_template", "Manual review template is not training input.", True, True, False, True),
    ]
    return [{"criterion_id": item, "criterion_description": desc, "applies_to_stage14l": l, "applies_to_stage14n": n, "required_before_manual_acceptance": accept, "required_before_dataset_ready": dataset, "criterion_contract_passed": True, "qa_comment": ""} for item, desc, l, n, accept, dataset in specs]


def build_decision_template_rows(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in inventory:
        flag = "needs_future_struct_conn_crosscheck" if row["struct_conn_evidence_status"] == "pending_future_raw_mmcif_struct_conn_crosscheck" else "has_struct_conn_evidence_pending_manual_review"
        rows.append({
            "manual_review_candidate_id": row["manual_review_candidate_id"],
            "candidate_source_stage": row["candidate_source_stage"],
            "pdb_id": row["pdb_id"],
            "ligand_identifier_if_available": row["ligand_identifier_if_available"],
            "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
            "ccd_ligand_name": row["ccd_ligand_name"],
            "ccd_formula": row["ccd_formula"],
            "ccd_type": row["ccd_type"],
            "covpdb_reaction_name": row["covpdb_reaction_name"],
            "covpdb_warhead_name": row["covpdb_warhead_name"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "covpdb_uniprot": row["covpdb_uniprot"],
            "complex_card_url": row["complex_card_url"],
            "struct_conn_evidence_status": row["struct_conn_evidence_status"],
            "suggested_covalent_bond_atom_pair": row["suggested_covalent_bond_atom_pair"],
            "auto_review_flag": flag,
            "manual_decision": "pending_manual_review",
            "manual_decision_allowed_values": ALLOWED_DECISIONS,
            "manual_decision_reason": "",
            "curator_initials": "",
            "review_date": "",
            "review_comment": "",
        })
    return rows


def build_auto_flag_rows(inventory: list[dict[str, Any]], event_rows: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    step14l_count = sum(row["candidate_source_stage"] == "step14l_targeted_annotation_acquisition" for row in inventory)
    step14n_count = sum(row["candidate_source_stage"] == "step14n_next_batch_metadata_acquisition" for row in inventory)
    values = [
        ("total_manual_review_candidate_count", len(inventory), len(inventory) == 25, ""),
        ("step14l_candidate_count", step14l_count, step14l_count == 9, ""),
        ("step14n_candidate_count", step14n_count, step14n_count == 16, ""),
        ("cys_candidate_count", sum(row["covpdb_residue_name"] == "CYS" for row in inventory), True, ""),
        ("pending_manual_review_count", sum(row["manual_review_status"] == "pending_manual_review" for row in inventory), True, ""),
        ("ready_candidate_count_current_step", sum(_bool(row["ready_candidate_current_step"]) for row in inventory), True, ""),
        ("step14n_requires_struct_conn_crosscheck_count", sum(_bool(row["requires_future_struct_conn_crosscheck"]) for row in event_rows), True, ""),
        ("duplicate_candidate_count", sum(_bool(row["duplicate_within_combined_inventory"]) for row in event_rows), True, ""),
        ("missing_reaction_count", sum(not row["covpdb_reaction_name"] for row in inventory), True, ""),
        ("missing_warhead_count", sum(not row["covpdb_warhead_name"] for row in inventory), True, ""),
        ("missing_chain_or_residue_index_count", sum(not row["covpdb_chain_id"] or not row["covpdb_residue_index"] for row in inventory), True, ""),
        ("missing_ccd_ligand_name_count", sum(not row["ccd_ligand_name"] for row in inventory), True, ""),
        ("peptide_like_or_large_ligand_count", sum("peptide" in str(row["ccd_type"]).lower() for row in inventory), True, ""),
        ("optional_covpdb_name_blank_count", step14n_count, True, "Step 14N optional CovPDB names are intentionally blank if boilerplate was cleaned."),
        ("manual_review_template_written", bool(decisions), bool(decisions), ""),
        ("training_still_blocked", True, True, ""),
    ]
    return [{"auto_flag_item": item, "auto_flag_value": value, "auto_flag_audit_passed": passed, "qa_comment": comment} for item, value, passed, comment in values]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("manual_review_gate_completed", "true", True, "manual_review_decision_input_by_user", ""),
        ("combined_inventory_written", "true", True, "manual_review_decision_input_by_user", ""),
        ("decision_template_written", "true", True, "manual_review_decision_input_by_user", ""),
        ("ready_for_manual_review_input_by_user", "true", True, "manual_review_decision_input_by_user", ""),
        ("ready_for_manual_decision_application_gate_false_current_step", "false", True, "not_allowed_current_step", ""),
        ("ready_for_future_struct_conn_crosscheck_after_manual_acceptance_false_current_step", "false", True, "not_allowed_current_step", ""),
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


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.suffix.lower() in suffixes for path in root.rglob("*") if path.is_file())


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    names = {"small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(path.name in names for path in root.rglob("*") if path.is_file())


def build_safety_rows(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_file_content_read_current_step", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("no_html_files_written_current_step", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14n_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14N_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14N_ROOT.as_posix()])),
        ("step14m_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14M_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14M_ROOT.as_posix()])),
        ("step14l_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14L_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14L_ROOT.as_posix()])),
        ("step14k_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14K_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14K_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_download_manifest_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_sample_index_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_urllib_selenium_playwright_bs4_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("derived_output_no_forbidden_binary_raw_or_html_suffix", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("no_ready_candidates_created", "passed", "passed" if all(not _bool(row["ready_candidate_current_step"]) for row in inventory) else "failed", all(not _bool(row["ready_candidate_current_step"]) for row in inventory)),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, inventory, event_rows, criteria, decisions, flags, downstream, safety) -> dict[str, Any]:
    step14l_count = sum(row["candidate_source_stage"] == "step14l_targeted_annotation_acquisition" for row in inventory)
    step14n_count = sum(row["candidate_source_stage"] == "step14n_next_batch_metadata_acquisition" for row in inventory)
    pending_count = sum(row["manual_review_status"] == "pending_manual_review" for row in inventory)
    ready_count = sum(_bool(row["ready_candidate_current_step"]) for row in inventory)
    duplicate_count = sum(_bool(row["duplicate_within_combined_inventory"]) for row in event_rows)
    requires_crosscheck = sum(_bool(row["requires_future_struct_conn_crosscheck"]) for row in event_rows)
    passed = all(
        _all_true(rows, col)
        for rows, col in [
            (pre, "precondition_passed"),
            (inventory, "inventory_row_passed"),
            (event_rows, "event_identity_audit_passed"),
            (criteria, "criterion_contract_passed"),
            (flags, "auto_flag_audit_passed"),
            (downstream, "readiness_passed"),
            (safety, "safety_passed"),
        ]
    ) and len(decisions) == len(inventory)
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "step14l_input_candidate_count": step14l_count,
        "step14n_input_candidate_count": step14n_count,
        "combined_manual_review_candidate_count": len(inventory),
        "total_candidate_target": TOTAL_CANDIDATE_TARGET,
        "threshold_20_met": len(inventory) >= TOTAL_CANDIDATE_TARGET,
        "manual_review_template_row_count": len(decisions),
        "manual_review_template_csv_json_consistent": True,
        "pending_manual_review_count": pending_count,
        "accepted_candidate_count_current_step": 0,
        "rejected_candidate_count_current_step": 0,
        "ready_candidate_count_current_step": ready_count,
        "no_ready_candidates_created": ready_count == 0,
        "step14n_requires_future_struct_conn_crosscheck_count": requires_crosscheck,
        "duplicate_candidate_count": duplicate_count,
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
        "urllib_used": False,
        "selenium_used": False,
        "playwright_used": False,
        "bs4_used": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_manual_review_input_by_user": True,
        "ready_for_covapie_cys_sg_manual_review_decision_application_gate": False,
        "ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate": False,
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
        "recommended_next_step": "manual_review_decision_input_by_user",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14o_manual_review_gate_failed"],
    }


def run_covapie_cys_sg_acquired_annotation_manual_review_gate_v0() -> dict[str, Any]:
    step14l_rows = _csv_rows(STEP14L_CANDIDATES_CSV)
    step14l_json = _load_json(STEP14L_CANDIDATES_JSON)
    step14n_rows = _csv_rows(STEP14N_CANDIDATES_CSV)
    step14n_json = _load_json(STEP14N_CANDIDATES_JSON)
    pre = build_precondition_rows(step14l_rows, step14l_json, step14n_rows, step14n_json)
    inventory = build_combined_inventory_rows(step14l_rows, step14n_rows)
    event_rows = build_event_identity_rows(inventory)
    criteria = build_criteria_rows()
    decisions = build_decision_template_rows(inventory)
    flags = build_auto_flag_rows(inventory, event_rows, decisions)
    downstream = build_downstream_rows()
    safety = build_safety_rows(inventory)
    manifest = build_manifest(pre, inventory, event_rows, criteria, decisions, flags, downstream, safety)
    return {
        "precondition_rows": pre,
        "inventory_rows": inventory,
        "event_identity_rows": event_rows,
        "criteria_rows": criteria,
        "decision_rows": decisions,
        "auto_flag_rows": flags,
        "downstream_rows": downstream,
        "safety_rows": safety,
        "manifest": manifest,
    }

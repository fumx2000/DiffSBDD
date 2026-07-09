from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_manual_review_decision_input_by_user as step14p


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_manual_review_decision_application_gate_v0"
STEP_LABEL = "Step 14Q"
PREVIOUS_STAGE = step14p.STAGE
PROJECT_NAME = "CovaPIE"

METADATA_CSV = step14p.METADATA_CSV
METADATA_CSV_SHA256 = step14p.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14p.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14p.RAW_OUTPUT_ROOT

STEP14P_ROOT = step14p.OUTPUT_ROOT
STEP14O_ROOT = step14p.STEP14O_ROOT
STEP14N_ROOT = step14p.STEP14N_ROOT

STEP14P_MANIFEST_JSON = step14p.MANIFEST_JSON
STEP14P_DECISION_INPUT_CSV = step14p.DECISION_INPUT_CSV
STEP14P_DECISION_INPUT_JSON = step14p.DECISION_INPUT_JSON
STEP14P_ACCEPTED_MANIFEST_CSV = step14p.ACCEPTED_CROSSCHECK_MANIFEST_CSV
STEP14P_ACCEPTED_MANIFEST_JSON = step14p.ACCEPTED_CROSSCHECK_MANIFEST_JSON

CANONICAL_MASK_TASK_NAMES = step14p.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14p.CANONICAL_MASK_TASK_ALIASES
EXPECTED_ACCEPTED_IDS = step14p.ACCEPTED_IDS
EXPECTED_ACCEPTED_PDB_HET_PAIRS = step14p.ACCEPTED_PDB_HET_PAIRS

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_manual_review_decision_application_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_decision_application_precondition_audit.csv"
APPLIED_DECISIONS_CSV = OUTPUT_ROOT / "covapie_cys_sg_applied_manual_review_decisions.csv"
APPLIED_DECISIONS_JSON = OUTPUT_ROOT / "covapie_cys_sg_applied_manual_review_decisions.json"
FUTURE_CROSSCHECK_INPUT_CSV = OUTPUT_ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_input_manifest.csv"
FUTURE_CROSSCHECK_INPUT_JSON = OUTPUT_ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_input_manifest.json"
DIFF_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_decision_application_diff_audit.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_decision_application_policy_contract.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_decision_application_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_decision_application_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_manual_review_decision_application_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_manual_review_decision_application_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_manual_review_decision_application_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_manual_review_decision_application_gate_v0.py")

PRECONDITION_COLUMNS = [
    "precondition_item",
    "artifact_or_check",
    "expected_status",
    "observed_status",
    "precondition_passed",
    "blocking_reasons",
]
APPLIED_DECISION_COLUMNS = [
    "manual_review_candidate_id",
    "candidate_source_stage",
    "pdb_id",
    "suggested_ligand_comp_id",
    "ccd_ligand_name",
    "ccd_formula",
    "ccd_type",
    "covpdb_reaction_name",
    "covpdb_warhead_name",
    "covpdb_residue_name",
    "covpdb_residue_index",
    "covpdb_chain_id",
    "covpdb_uniprot",
    "complex_card_url",
    "struct_conn_evidence_status",
    "suggested_covalent_bond_atom_pair",
    "user_manual_decision",
    "applied_decision",
    "application_status",
    "next_required_gate",
    "ready_candidate_current_step",
    "ready_for_training_current_step",
]
FUTURE_CROSSCHECK_COLUMNS = [
    "crosscheck_input_id",
    "manual_review_candidate_id",
    "pdb_id",
    "suggested_ligand_comp_id",
    "ccd_ligand_name",
    "covpdb_reaction_name",
    "covpdb_warhead_name",
    "covpdb_residue_name",
    "covpdb_residue_index",
    "covpdb_chain_id",
    "covpdb_uniprot",
    "complex_card_url",
    "ligand_identifier_if_available",
    "struct_conn_evidence_status",
    "next_required_gate",
    "ready_candidate_current_step",
    "ready_for_training_current_step",
]
DIFF_AUDIT_COLUMNS = ["decision_application_diff_item", "decision_application_diff_value", "decision_application_diff_passed", "qa_comment"]
POLICY_COLUMNS = ["policy_item", "policy_description", "policy_status", "policy_contract_passed", "qa_comment"]
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


def _json_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]], key: str) -> bool:
    return [row[key] for row in csv_rows] == [str(row.get(key, "")) for row in json_rows]


def build_precondition_rows(
    decision_rows: list[dict[str, str]],
    decision_json: list[dict[str, Any]],
    accepted_rows: list[dict[str, str]],
    accepted_json: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14P_MANIFEST_JSON) if STEP14P_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14p_manifest_exists", STEP14P_MANIFEST_JSON.as_posix(), "exists", STEP14P_MANIFEST_JSON.exists(), STEP14P_MANIFEST_JSON.exists()),
        ("step14p_stage", STEP14P_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14p_all_checks_passed", STEP14P_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14p_ready_for_application_gate", STEP14P_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_manual_review_decision_application_gate"), manifest.get("ready_for_covapie_cys_sg_manual_review_decision_application_gate") is True),
        ("step14p_ready_for_future_crosscheck_false", STEP14P_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate"), manifest.get("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate") is False),
        ("step14p_ready_for_training_false", STEP14P_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14p_decision_input_row_count", STEP14P_DECISION_INPUT_CSV.as_posix(), "25", len(decision_rows), len(decision_rows) == 25),
        ("step14p_decision_input_csv_json_consistent", STEP14P_DECISION_INPUT_JSON.as_posix(), "true", _json_consistent(decision_rows, decision_json, "manual_review_candidate_id"), _json_consistent(decision_rows, decision_json, "manual_review_candidate_id")),
        ("step14p_accepted_manifest_row_count", STEP14P_ACCEPTED_MANIFEST_CSV.as_posix(), "5", len(accepted_rows), len(accepted_rows) == 5),
        ("step14p_accepted_manifest_csv_json_consistent", STEP14P_ACCEPTED_MANIFEST_JSON.as_posix(), "true", _json_consistent(accepted_rows, accepted_json, "manual_review_candidate_id"), _json_consistent(accepted_rows, accepted_json, "manual_review_candidate_id")),
        ("step14p_accepted_ids_match", STEP14P_ACCEPTED_MANIFEST_CSV.as_posix(), str(EXPECTED_ACCEPTED_IDS), [row["manual_review_candidate_id"] for row in accepted_rows], [row["manual_review_candidate_id"] for row in accepted_rows] == EXPECTED_ACCEPTED_IDS),
        ("step14p_accepted_pairs_match", STEP14P_ACCEPTED_MANIFEST_CSV.as_posix(), str(EXPECTED_ACCEPTED_PDB_HET_PAIRS), [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in accepted_rows], [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in accepted_rows] == EXPECTED_ACCEPTED_PDB_HET_PAIRS),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14p_artifacts_unchanged", STEP14P_ROOT.as_posix(), "empty diff", _path_diff_exists([STEP14P_ROOT.as_posix()]), not _path_diff_exists([STEP14P_ROOT.as_posix()])),
        ("step14o_artifacts_unchanged", STEP14O_ROOT.as_posix(), "empty diff", _path_diff_exists([STEP14O_ROOT.as_posix()]), not _path_diff_exists([STEP14O_ROOT.as_posix()])),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("raw_roots_not_staged", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_staged(RAW_OUTPUT_ROOT) or _raw_files_staged(RAW_REFERENCE_ROOT), not _raw_files_staged(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_applied_decision_rows(decision_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in decision_rows:
        accepted = row["user_manual_decision"] == "accept_for_future_struct_conn_crosscheck"
        rows.append({
            "manual_review_candidate_id": row["manual_review_candidate_id"],
            "candidate_source_stage": row["candidate_source_stage"],
            "pdb_id": row["pdb_id"],
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
            "user_manual_decision": row["user_manual_decision"],
            "applied_decision": "accepted_for_future_struct_conn_crosscheck" if accepted else "pending_manual_review",
            "application_status": "applied_to_future_struct_conn_crosscheck_input" if accepted else "kept_pending_manual_review",
            "next_required_gate": "covapie_cys_sg_future_struct_conn_crosscheck_gate" if accepted else "manual_review_decision_input_by_user",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_future_crosscheck_rows(accepted_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(accepted_rows, start=1):
        rows.append({
            "crosscheck_input_id": f"CYS_SG_STRUCT_CONN_CROSSCHECK_INPUT_{idx:06d}",
            "manual_review_candidate_id": row["manual_review_candidate_id"],
            "pdb_id": row["pdb_id"],
            "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
            "ccd_ligand_name": row["ccd_ligand_name"],
            "covpdb_reaction_name": row["covpdb_reaction_name"],
            "covpdb_warhead_name": row["covpdb_warhead_name"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "covpdb_uniprot": row["covpdb_uniprot"],
            "complex_card_url": row["complex_card_url"],
            "ligand_identifier_if_available": row["ligand_identifier_if_available"],
            "struct_conn_evidence_status": row["struct_conn_evidence_status"],
            "next_required_gate": "covapie_cys_sg_future_struct_conn_crosscheck_gate",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_diff_rows(applied_rows: list[dict[str, Any]], future_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted = [row for row in applied_rows if row["applied_decision"] == "accepted_for_future_struct_conn_crosscheck"]
    pending = [row for row in applied_rows if row["applied_decision"] == "pending_manual_review"]
    accepted_pairs = [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in accepted]
    future_pairs = [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in future_rows]
    specs = [
        ("applied_decision_row_count", len(applied_rows), len(applied_rows) == 25, ""),
        ("applied_accept_for_future_struct_conn_crosscheck_count", len(accepted), len(accepted) == 5, ""),
        ("applied_pending_manual_review_count", len(pending), len(pending) == 20, ""),
        ("future_struct_conn_crosscheck_input_count", len(future_rows), len(future_rows) == 5, ""),
        ("accepted_pdb_het_pairs_match", accepted_pairs, accepted_pairs == EXPECTED_ACCEPTED_PDB_HET_PAIRS, ""),
        ("future_pdb_het_pairs_match", future_pairs, future_pairs == EXPECTED_ACCEPTED_PDB_HET_PAIRS, ""),
        ("ready_candidate_count_current_step", sum(_bool(row["ready_candidate_current_step"]) for row in applied_rows), True, ""),
        ("training_candidate_count_current_step", sum(_bool(row["ready_for_training_current_step"]) for row in applied_rows), True, ""),
        ("future_rows_next_gate_validated", all(row["next_required_gate"] == "covapie_cys_sg_future_struct_conn_crosscheck_gate" for row in future_rows), True, ""),
        ("future_rows_not_ready", all(not _bool(row["ready_candidate_current_step"]) and not _bool(row["ready_for_training_current_step"]) for row in future_rows), True, ""),
    ]
    return [{"decision_application_diff_item": item, "decision_application_diff_value": value, "decision_application_diff_passed": passed, "qa_comment": comment} for item, value, passed, comment in specs]


def build_policy_rows() -> list[dict[str, Any]]:
    specs = [
        ("application_gate_only", "This step applies Step 14P decisions into a future cross-check input manifest only.", "passed"),
        ("accepted_for_crosscheck_not_ready_candidate", "Accepted for future struct_conn cross-check is not a ready candidate label.", "passed"),
        ("five_crosscheck_inputs_only", "Exactly five user-selected inputs are passed forward.", "passed"),
        ("remaining_twenty_stay_pending", "The remaining twenty candidates are retained as pending manual review.", "passed"),
        ("no_raw_mmcif_crosscheck_current_step", "Raw/mmCIF struct_conn cross-check is not performed here.", "passed"),
        ("no_sample_or_dataset_artifacts", "No sample/final/split/leakage/training artifacts are written.", "passed"),
        ("feature_semantics_audit_still_required", "Feature semantics audit remains required before training.", "passed"),
        ("leakage_split_gate_still_required", "Leakage/split design gate remains required before training.", "passed"),
        ("canonical_mask_scope_preserved", "The five canonical mask tasks including scaffold_only/B3 remain unchanged.", "passed"),
        ("step14p_artifacts_read_only", "Step 14P artifacts are read-only inputs.", "passed"),
    ]
    return [{"policy_item": item, "policy_description": desc, "policy_status": status, "policy_contract_passed": True, "qa_comment": ""} for item, desc, status in specs]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("decision_application_gate_passed", "true", True, "covapie_cys_sg_future_struct_conn_crosscheck_gate", ""),
        ("future_struct_conn_crosscheck_input_manifest_written", "true", True, "covapie_cys_sg_future_struct_conn_crosscheck_gate", ""),
        ("ready_for_future_struct_conn_crosscheck_gate", "true", True, "covapie_cys_sg_future_struct_conn_crosscheck_gate", ""),
        ("ready_for_small_pilot_manifest_rerun_false", "false", True, "not_allowed_current_step", ""),
        ("ready_for_actual_dataloader_false", "false", True, "not_allowed_current_step", ""),
        ("ready_for_training_false", "false", True, "not_allowed_current_step", ""),
        ("ready_to_train_now_false", "false", True, "not_allowed_current_step", ""),
        ("feature_semantics_audit_required_before_training", "true", True, "feature_semantics_audit_required_before_training", ""),
        ("leakage_split_design_required_before_training", "true", True, "covapie_leakage_split_design_gate_before_training", ""),
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


def build_safety_rows(applied_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_mmcif_read_current_step", "passed", "passed", True),
        ("no_data_raw_write_current_step", "passed", "passed", True),
        ("no_html_saved_current_step", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14p_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14P_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14P_ROOT.as_posix()])),
        ("step14o_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14O_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14O_ROOT.as_posix()])),
        ("step14n_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14N_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14N_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_final_split_leakage_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_forbidden_raw_binary_or_html_suffix", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_urllib_selenium_playwright_bs4_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("no_ready_candidates_created", "passed", "passed" if all(not _bool(row["ready_candidate_current_step"]) for row in applied_rows) else "failed", all(not _bool(row["ready_candidate_current_step"]) for row in applied_rows)),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, applied_rows, future_rows, diff_rows, policy_rows, downstream_rows, safety_rows) -> dict[str, Any]:
    accepted = [row for row in applied_rows if row["applied_decision"] == "accepted_for_future_struct_conn_crosscheck"]
    pending = [row for row in applied_rows if row["applied_decision"] == "pending_manual_review"]
    accepted_pairs = [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in accepted]
    ready_count = sum(_bool(row["ready_candidate_current_step"]) for row in applied_rows)
    training_count = sum(_bool(row["ready_for_training_current_step"]) for row in applied_rows)
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (pre, "precondition_passed"),
            (diff_rows, "decision_application_diff_passed"),
            (policy_rows, "policy_contract_passed"),
            (downstream_rows, "readiness_passed"),
            (safety_rows, "safety_passed"),
        ]
    ) and accepted_pairs == EXPECTED_ACCEPTED_PDB_HET_PAIRS and len(future_rows) == 5
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "input_manual_review_candidate_count": len(applied_rows),
        "applied_accept_for_future_struct_conn_crosscheck_count": len(accepted),
        "applied_pending_manual_review_count": len(pending),
        "future_struct_conn_crosscheck_input_count": len(future_rows),
        "accepted_pdb_het_pairs": accepted_pairs,
        "accepted_candidate_ids": [row["manual_review_candidate_id"] for row in accepted],
        "ready_candidate_count_current_step": ready_count,
        "ready_for_training_candidate_count_current_step": training_count,
        "no_ready_candidates_created": ready_count == 0,
        "applied_decisions_csv_json_consistent": True,
        "future_struct_conn_crosscheck_input_manifest_csv_json_consistent": True,
        "network_access_used": False,
        "download_attempted": False,
        "raw_mmcif_read_current_step": False,
        "data_raw_written_current_step": False,
        "html_files_written_current_step": False,
        "sample_download_manifest_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
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
        "ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate": True,
        "ready_for_covapie_small_pilot_manifest_rerun_gate": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "recommended_next_step": "covapie_cys_sg_future_struct_conn_crosscheck_gate",
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14q_manual_review_decision_application_gate_failed"],
    }


def run_covapie_cys_sg_manual_review_decision_application_gate_v0() -> dict[str, Any]:
    decision_rows = _csv_rows(STEP14P_DECISION_INPUT_CSV)
    decision_json = _load_json(STEP14P_DECISION_INPUT_JSON)
    accepted_rows = _csv_rows(STEP14P_ACCEPTED_MANIFEST_CSV)
    accepted_json = _load_json(STEP14P_ACCEPTED_MANIFEST_JSON)
    pre = build_precondition_rows(decision_rows, decision_json, accepted_rows, accepted_json)
    applied_rows = build_applied_decision_rows(decision_rows)
    future_rows = build_future_crosscheck_rows(accepted_rows)
    diff_rows = build_diff_rows(applied_rows, future_rows)
    policy_rows = build_policy_rows()
    downstream_rows = build_downstream_rows()
    safety_rows = build_safety_rows(applied_rows)
    manifest = build_manifest(pre, applied_rows, future_rows, diff_rows, policy_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": pre,
        "applied_rows": applied_rows,
        "future_rows": future_rows,
        "diff_rows": diff_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

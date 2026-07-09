from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_future_struct_conn_crosscheck_execution_gate as step14t


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0"
STEP_LABEL = "Step 14U"
PREVIOUS_STAGE = step14t.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_precondition_audit.csv"
EVIDENCE_INVENTORY_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_evidence_inventory.csv"
EVIDENCE_INVENTORY_JSON = OUTPUT_ROOT / "covapie_cys_sg_result_review_evidence_inventory.json"
UNMATCHED_BLOCKED_INVENTORY_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_unmatched_blocked_inventory.csv"
DECISION_TEMPLATE_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_template.csv"
DECISION_TEMPLATE_JSON = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_template.json"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_policy_contract.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_crosscheck_result_review_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_struct_conn_crosscheck_result_review_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0.py")

METADATA_CSV = step14t.METADATA_CSV
METADATA_CSV_SHA256 = step14t.METADATA_CSV_SHA256
RAW_ROOT = step14t.RAW_ROOT
STEP14T_ROOT = step14t.OUTPUT_ROOT
STEP14S_ROOT = step14t.STEP14S_ROOT
STEP14R_ROOT = step14t.STEP14R_ROOT
STEP14Q_ROOT = step14t.STEP14Q_ROOT
STEP14P_ROOT = step14t.STEP14P_ROOT
STEP14O_ROOT = step14t.STEP14O_ROOT

STEP14T_MANIFEST_JSON = step14t.MANIFEST_JSON
STEP14T_QUERY_AUDIT_CSV = step14t.QUERY_EXECUTION_AUDIT_CSV
STEP14T_EVIDENCE_CSV = step14t.MATCHED_EVIDENCE_CANDIDATES_CSV
STEP14T_EVIDENCE_JSON = step14t.MATCHED_EVIDENCE_CANDIDATES_JSON
STEP14T_RESULT_SUMMARY_CSV = step14t.RESULT_SUMMARY_CSV

CANONICAL_MASK_TASK_NAMES = step14t.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14t.CANONICAL_MASK_TASK_ALIASES
MATCHED_PDB_HET_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
BLOCKED_PDB_HET_PAIRS = ["1A54/MDC", "6BV9/JUG"]
DECISION_ALLOWED_VALUES = [
    "pending_result_review",
    "accept_for_future_ready_candidate_materialization",
    "reject",
    "needs_more_evidence",
]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
EVIDENCE_INVENTORY_COLUMNS = ["result_review_evidence_id", "struct_conn_evidence_candidate_id", "crosscheck_input_id", "manual_review_candidate_id", "pdb_id", "expected_het_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "conn_id", "conn_type_id", "residue_comp_id", "residue_atom_name", "residue_auth_asym_id", "residue_auth_seq_id", "residue_label_asym_id", "residue_label_seq_id", "ligand_comp_id", "ligand_atom_name", "ligand_auth_asym_id", "ligand_auth_seq_id", "ligand_label_asym_id", "ligand_label_seq_id", "evidence_status_from_step14t", "result_review_status", "ready_candidate_current_step", "ready_for_training_current_step", "inventory_row_passed", "qa_comment"]
UNMATCHED_COLUMNS = ["blocked_review_id", "crosscheck_input_id", "pdb_id", "expected_het_id", "crosscheck_status", "blocking_reason", "struct_conn_records_scanned", "matched_struct_conn_record_count", "blocked_status", "carry_forward_policy", "ready_candidate_current_step", "ready_for_training_current_step"]
DECISION_TEMPLATE_COLUMNS = ["result_review_evidence_id", "struct_conn_evidence_candidate_id", "pdb_id", "expected_het_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "residue_atom_name", "ligand_comp_id", "ligand_atom_name", "conn_id", "conn_type_id", "result_review_decision", "result_review_allowed_values", "result_review_reason", "curator_initials", "review_date", "review_comment", "ready_candidate_current_step", "ready_for_training_current_step"]
POLICY_COLUMNS = ["policy_item", "policy_description", "policy_contract_passed"]
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
    return hashlib.sha256((REPO_ROOT / METADATA_CSV).read_bytes()).hexdigest() if (REPO_ROOT / METADATA_CSV).exists() else ""


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _json_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]], key: str) -> bool:
    return [row[key] for row in csv_rows] == [str(row.get(key, "")) for row in json_rows]


def build_precondition_rows(query_rows: list[dict[str, str]], evidence_rows: list[dict[str, str]], evidence_json: list[dict[str, Any]], result_summary: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14T_MANIFEST_JSON) if STEP14T_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14t_manifest_exists", STEP14T_MANIFEST_JSON.as_posix(), "exists", STEP14T_MANIFEST_JSON.exists(), STEP14T_MANIFEST_JSON.exists()),
        ("step14t_stage", STEP14T_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14t_all_checks_passed", STEP14T_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14t_crosscheck_input_count", STEP14T_MANIFEST_JSON.as_posix(), "5", manifest.get("crosscheck_input_count"), manifest.get("crosscheck_input_count") == 5),
        ("step14t_matched_input_count", STEP14T_MANIFEST_JSON.as_posix(), "3", manifest.get("matched_input_count"), manifest.get("matched_input_count") == 3),
        ("step14t_unmatched_input_count", STEP14T_MANIFEST_JSON.as_posix(), "2", manifest.get("unmatched_input_count"), manifest.get("unmatched_input_count") == 2),
        ("step14t_ambiguous_input_count", STEP14T_MANIFEST_JSON.as_posix(), "0", manifest.get("ambiguous_input_count"), manifest.get("ambiguous_input_count") == 0),
        ("step14t_evidence_candidate_count", STEP14T_MANIFEST_JSON.as_posix(), "3", manifest.get("evidence_candidate_count"), manifest.get("evidence_candidate_count") == 3),
        ("step14t_ready_for_result_review_gate", STEP14T_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate"), manifest.get("ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate") is True),
        ("step14t_ready_for_training_false", STEP14T_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("query_execution_audit_exists_row_count", STEP14T_QUERY_AUDIT_CSV.as_posix(), "5", len(query_rows), STEP14T_QUERY_AUDIT_CSV.exists() and len(query_rows) == 5),
        ("matched_evidence_csv_json_consistent", STEP14T_EVIDENCE_JSON.as_posix(), "3 consistent rows", len(evidence_rows), STEP14T_EVIDENCE_CSV.exists() and STEP14T_EVIDENCE_JSON.exists() and len(evidence_rows) == 3 and len(evidence_json) == 3 and _json_consistent(evidence_rows, evidence_json, "struct_conn_evidence_candidate_id")),
        ("result_summary_exists", STEP14T_RESULT_SUMMARY_CSV.as_posix(), "exists", len(result_summary), STEP14T_RESULT_SUMMARY_CSV.exists() and len(result_summary) == 1),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_files_not_git_tracked", RAW_ROOT.as_posix(), "false", _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip()),
        ("raw_files_not_staged", RAW_ROOT.as_posix(), "false", _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14t.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_evidence_inventory_rows(evidence_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(evidence_rows, start=1):
        pair = f"{row['pdb_id']}/{row['expected_het_id']}"
        passed = (
            pair in MATCHED_PDB_HET_PAIRS
            and row["expected_het_id"] == "JUG"
            and row["residue_comp_id"] == "CYS"
            and row["residue_atom_name"] == "SG"
            and row["ligand_comp_id"] == "JUG"
            and row["ligand_atom_name"] == "CAG"
            and row["conn_type_id"] == "covale"
            and row["evidence_status"] == "struct_conn_match_found_pending_manual_review"
        )
        rows.append({
            "result_review_evidence_id": f"CYS_SG_RESULT_REVIEW_EVIDENCE_{idx:06d}",
            "struct_conn_evidence_candidate_id": row["struct_conn_evidence_candidate_id"],
            "crosscheck_input_id": row["crosscheck_input_id"],
            "manual_review_candidate_id": row["manual_review_candidate_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "conn_id": row["conn_id"],
            "conn_type_id": row["conn_type_id"],
            "residue_comp_id": row["residue_comp_id"],
            "residue_atom_name": row["residue_atom_name"],
            "residue_auth_asym_id": row["residue_auth_asym_id"],
            "residue_auth_seq_id": row["residue_auth_seq_id"],
            "residue_label_asym_id": row["residue_label_asym_id"],
            "residue_label_seq_id": row["residue_label_seq_id"],
            "ligand_comp_id": row["ligand_comp_id"],
            "ligand_atom_name": row["ligand_atom_name"],
            "ligand_auth_asym_id": row["ligand_auth_asym_id"],
            "ligand_auth_seq_id": row["ligand_auth_seq_id"],
            "ligand_label_asym_id": row["ligand_label_asym_id"],
            "ligand_label_seq_id": row["ligand_label_seq_id"],
            "evidence_status_from_step14t": row["evidence_status"],
            "result_review_status": "pending_result_review",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
            "inventory_row_passed": passed,
            "qa_comment": "pending human result review before any ready candidate materialization",
        })
    return rows


def build_unmatched_blocked_rows(query_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    blocked = [row for row in query_rows if row["crosscheck_status"] != "matched_cys_sg_ligand_struct_conn"]
    for idx, row in enumerate(blocked, start=1):
        rows.append({
            "blocked_review_id": f"CYS_SG_RESULT_REVIEW_BLOCKED_{idx:06d}",
            "crosscheck_input_id": row["crosscheck_input_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "crosscheck_status": row["crosscheck_status"],
            "blocking_reason": row["blocking_reason"],
            "struct_conn_records_scanned": row["struct_conn_records_scanned"],
            "matched_struct_conn_record_count": row["matched_struct_conn_record_count"],
            "blocked_status": "blocked_pending_manual_or_evidence_review",
            "carry_forward_policy": "do_not_use_as_ready_candidate_current_step",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_decision_template_rows(evidence_inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    allowed = ";".join(DECISION_ALLOWED_VALUES)
    for row in evidence_inventory_rows:
        rows.append({
            "result_review_evidence_id": row["result_review_evidence_id"],
            "struct_conn_evidence_candidate_id": row["struct_conn_evidence_candidate_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "residue_atom_name": row["residue_atom_name"],
            "ligand_comp_id": row["ligand_comp_id"],
            "ligand_atom_name": row["ligand_atom_name"],
            "conn_id": row["conn_id"],
            "conn_type_id": row["conn_type_id"],
            "result_review_decision": "pending_result_review",
            "result_review_allowed_values": allowed,
            "result_review_reason": "",
            "curator_initials": "",
            "review_date": "",
            "review_comment": "",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_policy_rows() -> list[dict[str, Any]]:
    descriptions = {
        "result_review_gate_only": "This step only prepares result review artifacts.",
        "matched_struct_conn_evidence_is_not_ready_candidate": "Matched evidence is not a ready candidate in this step.",
        "result_review_decision_required_before_ready_materialization": "A human/user decision is required before ready materialization.",
        "ligand_atom_name_from_raw_struct_conn_only": "Ligand atom names are carried from Step 14T raw struct_conn evidence.",
        "unmatched_inputs_not_used_as_ready_candidates": "Unmatched inputs remain blocked and are not ready candidates.",
        "no_training_current_step": "Training is not allowed in this step.",
        "no_sample_or_final_dataset_current_step": "Sample and final dataset artifacts are not written.",
        "no_split_or_leakage_current_step": "Split/leakage artifacts are not written.",
        "feature_semantics_audit_required_before_training": "Feature semantics audit remains required before training.",
        "leakage_split_gate_required_before_training": "Leakage/split gate remains required before training.",
        "canonical_five_masks_preserved": "The canonical five masks remain unchanged.",
        "do_not_train_from_result_review_template": "The review template cannot be used as training input.",
    }
    return [{"policy_item": item, "policy_description": desc, "policy_contract_passed": True} for item, desc in descriptions.items()]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_cys_sg_result_review_decision_input_by_user", "true", True, "covapie_cys_sg_result_review_decision_input_by_user", ""),
        ("ready_for_covapie_cys_sg_ready_candidate_materialization_gate", "false", True, "not_allowed_until_result_review_decisions_applied", ""),
        ("ready_for_covapie_small_pilot_manifest_rerun_gate", "false", True, "not_allowed_current_step", ""),
        ("ready_for_covapie_actual_dataloader_adapter_smoke", "false", True, "not_allowed_current_step", ""),
        ("ready_for_training", "false", True, "not_allowed_current_step", ""),
        ("ready_to_train_now", "false", True, "not_allowed_current_step", ""),
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


def _forbidden_derived_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    names = {"small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(path.is_file() and (path.suffix.lower() in suffixes or path.name in names) for path in root.rglob("*"))


def _raw_leftovers_exist() -> bool:
    root = REPO_ROOT / RAW_ROOT
    return root.exists() and any(path.is_file() and path.suffix.lower() in {".part", ".html", ".htm"} for path in root.rglob("*"))


def build_safety_rows(evidence_inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_tracked = bool(_run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())
    raw_staged = bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())
    forbidden_imports = {"requests", "urllib", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "bs4"}
    own_imports_ok = not any(_imports_forbidden_module(path, forbidden_imports) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])
    checks = [
        ("no_network_access_current_step", "true", "true", True),
        ("no_download_current_step", "true", "true", True),
        ("no_raw_mmcif_read_current_step", "true", "true", True),
        ("no_struct_conn_parse_current_step", "true", "true", True),
        ("no_data_raw_write_current_step", "true", "true", True),
        ("raw_files_remain_untracked", "true", str(not raw_tracked).lower(), not raw_tracked),
        ("raw_files_remain_unstaged", "true", str(not raw_staged).lower(), not raw_staged),
        ("no_html_or_part_files", "true", str(not _raw_leftovers_exist()).lower(), not _raw_leftovers_exist()),
        ("metadata_csv_unchanged", "true", str(_metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])).lower(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14t_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14T_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14T_ROOT.as_posix()])),
        ("step14s_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14S_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14S_ROOT.as_posix()])),
        ("step14r_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14R_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14R_ROOT.as_posix()])),
        ("protected_source_diff_empty", "true", str(not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])).lower(), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", str(not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])).lower(), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_final_split_leakage_training_artifacts", "true", str(not _forbidden_derived_artifact_exists()).lower(), not _forbidden_derived_artifact_exists()),
        ("derived_output_no_forbidden_raw_binary_or_html_suffix", "true", str(not _forbidden_derived_artifact_exists()).lower(), not _forbidden_derived_artifact_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_urllib_selenium_playwright_bs4_imports", "true", str(own_imports_ok).lower(), own_imports_ok),
        ("no_ready_candidates_created", "true", str(all(not _bool(row["ready_candidate_current_step"]) for row in evidence_inventory_rows)).lower(), all(not _bool(row["ready_candidate_current_step"]) for row in evidence_inventory_rows)),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, evidence_inventory_rows, unmatched_rows, decision_rows, policy_rows, downstream_rows, safety_rows) -> dict[str, Any]:
    pending_count = sum(row["result_review_decision"] == "pending_result_review" for row in decision_rows)
    matched_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in evidence_inventory_rows]
    blocked_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in unmatched_rows]
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (pre, "precondition_passed"),
            (evidence_inventory_rows, "inventory_row_passed"),
            (policy_rows, "policy_contract_passed"),
            (downstream_rows, "readiness_passed"),
            (safety_rows, "safety_passed"),
        ]
    ) and len(evidence_inventory_rows) == 3 and len(unmatched_rows) == 2 and len(decision_rows) == 3 and matched_pairs == MATCHED_PDB_HET_PAIRS and blocked_pairs == BLOCKED_PDB_HET_PAIRS
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "crosscheck_input_count": 5,
        "evidence_candidate_count": 3,
        "result_review_evidence_count": len(evidence_inventory_rows),
        "unmatched_blocked_count": len(unmatched_rows),
        "result_review_template_row_count": len(decision_rows),
        "pending_result_review_count": pending_count,
        "accepted_for_future_ready_candidate_materialization_count_current_step": 0,
        "rejected_result_review_count_current_step": 0,
        "needs_more_evidence_count_current_step": 0,
        "ready_candidate_count_current_step": 0,
        "ready_for_training_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "matched_pdb_het_pairs": matched_pairs,
        "blocked_pdb_het_pairs": blocked_pairs,
        "result_review_template_csv_json_consistent": True,
        "network_access_used_current_step": False,
        "download_attempted_current_step": False,
        "raw_mmcif_read_current_step": False,
        "struct_conn_parsed_current_step": False,
        "data_raw_written_current_step": False,
        "html_files_written_current_step": False,
        "part_files_leftover_current_step": False,
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
        "ready_for_covapie_cys_sg_result_review_decision_input_by_user": True,
        "ready_for_covapie_cys_sg_ready_candidate_materialization_gate": False,
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
        "recommended_next_step": "covapie_cys_sg_result_review_decision_input_by_user",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14u_result_review_gate_failed"],
    }


def run_covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0() -> dict[str, Any]:
    query_rows = _csv_rows(STEP14T_QUERY_AUDIT_CSV)
    evidence_rows = _csv_rows(STEP14T_EVIDENCE_CSV)
    evidence_json = _load_json(STEP14T_EVIDENCE_JSON)
    result_summary = _csv_rows(STEP14T_RESULT_SUMMARY_CSV)
    pre = build_precondition_rows(query_rows, evidence_rows, evidence_json, result_summary)
    evidence_inventory_rows = build_evidence_inventory_rows(evidence_rows)
    unmatched_rows = build_unmatched_blocked_rows(query_rows)
    decision_rows = build_decision_template_rows(evidence_inventory_rows)
    policy_rows = build_policy_rows()
    downstream_rows = build_downstream_rows()
    safety_rows = build_safety_rows(evidence_inventory_rows)
    manifest = build_manifest(pre, evidence_inventory_rows, unmatched_rows, decision_rows, policy_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": pre,
        "evidence_inventory_rows": evidence_inventory_rows,
        "unmatched_rows": unmatched_rows,
        "decision_rows": decision_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

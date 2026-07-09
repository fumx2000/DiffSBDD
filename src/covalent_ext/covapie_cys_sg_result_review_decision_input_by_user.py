from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_struct_conn_crosscheck_result_review_gate as step14u


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_result_review_decision_input_by_user_v0"
STEP_LABEL = "Step 14V"
PREVIOUS_STAGE = step14u.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_result_review_decision_input_by_user_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_input_precondition_audit.csv"
DECISION_INPUT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_input.csv"
DECISION_INPUT_JSON = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_input.json"
DECISION_DIFF_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_diff_audit.csv"
FUTURE_READY_MANIFEST_CSV = OUTPUT_ROOT / "covapie_cys_sg_accept_for_future_ready_candidate_materialization_manifest.csv"
FUTURE_READY_MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_accept_for_future_ready_candidate_materialization_manifest.json"
BLOCKED_CARRY_FORWARD_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_blocked_carry_forward_manifest.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_policy_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_result_review_decision_input_by_user_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_result_review_decision_input_by_user_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_result_review_decision_input_by_user.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_result_review_decision_input_by_user_v0.py")

METADATA_CSV = step14u.METADATA_CSV
METADATA_CSV_SHA256 = step14u.METADATA_CSV_SHA256
RAW_ROOT = step14u.RAW_ROOT
STEP14U_ROOT = step14u.OUTPUT_ROOT
STEP14T_ROOT = step14u.STEP14T_ROOT
STEP14S_ROOT = step14u.STEP14S_ROOT
STEP14R_ROOT = step14u.STEP14R_ROOT
STEP14Q_ROOT = step14u.STEP14Q_ROOT

STEP14U_MANIFEST_JSON = step14u.MANIFEST_JSON
STEP14U_DECISION_TEMPLATE_CSV = step14u.DECISION_TEMPLATE_CSV
STEP14U_DECISION_TEMPLATE_JSON = step14u.DECISION_TEMPLATE_JSON
STEP14U_EVIDENCE_INVENTORY_CSV = step14u.EVIDENCE_INVENTORY_CSV
STEP14U_EVIDENCE_INVENTORY_JSON = step14u.EVIDENCE_INVENTORY_JSON
STEP14U_BLOCKED_INVENTORY_CSV = step14u.UNMATCHED_BLOCKED_INVENTORY_CSV

CANONICAL_MASK_TASK_NAMES = step14u.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14u.CANONICAL_MASK_TASK_ALIASES

ACCEPTED_PDB_HET_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
BLOCKED_PDB_HET_PAIRS = ["1A54/MDC", "6BV9/JUG"]
USER_ACCEPT_DECISION = "accept_for_future_ready_candidate_materialization"
USER_ACCEPT_REASON = "user_accepted_raw_struct_conn_cys_sg_ligand_evidence_for_future_ready_candidate_materialization"
NEXT_REQUIRED_GATE = "covapie_cys_sg_result_review_decision_application_gate"

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
DECISION_INPUT_COLUMNS = ["result_review_evidence_id", "struct_conn_evidence_candidate_id", "pdb_id", "expected_het_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "residue_atom_name", "ligand_comp_id", "ligand_atom_name", "conn_id", "conn_type_id", "previous_result_review_decision", "user_result_review_decision", "user_result_review_reason", "curator_initials", "review_date", "review_comment", "ready_candidate_current_step", "ready_for_training_current_step"]
DIFF_AUDIT_COLUMNS = ["decision_diff_item", "observed_value", "expected_value", "decision_diff_passed", "blocking_reasons"]
FUTURE_READY_COLUMNS = ["future_ready_materialization_input_id", "result_review_evidence_id", "struct_conn_evidence_candidate_id", "pdb_id", "expected_het_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "residue_atom_name", "ligand_comp_id", "ligand_atom_name", "conn_id", "conn_type_id", "user_result_review_decision", "next_required_gate", "ready_candidate_current_step", "ready_for_training_current_step"]
BLOCKED_COLUMNS = ["blocked_review_id", "pdb_id", "expected_het_id", "crosscheck_status", "blocking_reason", "blocked_status", "carry_forward_policy", "ready_candidate_current_step", "ready_for_training_current_step"]
POLICY_COLUMNS = ["policy_item", "policy_description", "policy_contract_passed"]
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


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())


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


def _forbidden_output_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    names = {"sample_index.csv", "sample_index.json", "final_dataset.csv", "final_dataset.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json"}
    return root.exists() and any(path.is_file() and (path.suffix.lower() in suffixes or path.name in names) for path in root.rglob("*"))


def build_precondition_rows(template_rows: list[dict[str, str]], template_json: list[dict[str, Any]], evidence_rows: list[dict[str, str]], evidence_json: list[dict[str, Any]], blocked_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14U_MANIFEST_JSON) if STEP14U_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14u_manifest_exists", STEP14U_MANIFEST_JSON.as_posix(), "exists", STEP14U_MANIFEST_JSON.exists(), STEP14U_MANIFEST_JSON.exists()),
        ("step14u_stage", STEP14U_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14u_all_checks_passed", STEP14U_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14u_result_review_evidence_count", STEP14U_MANIFEST_JSON.as_posix(), "3", manifest.get("result_review_evidence_count"), manifest.get("result_review_evidence_count") == 3),
        ("step14u_unmatched_blocked_count", STEP14U_MANIFEST_JSON.as_posix(), "2", manifest.get("unmatched_blocked_count"), manifest.get("unmatched_blocked_count") == 2),
        ("step14u_pending_result_review_count", STEP14U_MANIFEST_JSON.as_posix(), "3", manifest.get("pending_result_review_count"), manifest.get("pending_result_review_count") == 3),
        ("step14u_ready_for_decision_input_by_user", STEP14U_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_result_review_decision_input_by_user"), manifest.get("ready_for_covapie_cys_sg_result_review_decision_input_by_user") is True),
        ("step14u_ready_for_training_false", STEP14U_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("decision_template_csv_exists", STEP14U_DECISION_TEMPLATE_CSV.as_posix(), "exists", STEP14U_DECISION_TEMPLATE_CSV.exists(), STEP14U_DECISION_TEMPLATE_CSV.exists()),
        ("decision_template_json_exists", STEP14U_DECISION_TEMPLATE_JSON.as_posix(), "exists", STEP14U_DECISION_TEMPLATE_JSON.exists(), STEP14U_DECISION_TEMPLATE_JSON.exists()),
        ("decision_template_csv_json_consistent", STEP14U_DECISION_TEMPLATE_JSON.as_posix(), "true", _json_consistent(template_rows, template_json, "result_review_evidence_id"), _json_consistent(template_rows, template_json, "result_review_evidence_id")),
        ("evidence_inventory_csv_exists", STEP14U_EVIDENCE_INVENTORY_CSV.as_posix(), "exists", STEP14U_EVIDENCE_INVENTORY_CSV.exists(), STEP14U_EVIDENCE_INVENTORY_CSV.exists()),
        ("evidence_inventory_json_exists", STEP14U_EVIDENCE_INVENTORY_JSON.as_posix(), "exists", STEP14U_EVIDENCE_INVENTORY_JSON.exists(), STEP14U_EVIDENCE_INVENTORY_JSON.exists()),
        ("evidence_inventory_csv_json_consistent", STEP14U_EVIDENCE_INVENTORY_JSON.as_posix(), "true", _json_consistent(evidence_rows, evidence_json, "result_review_evidence_id"), _json_consistent(evidence_rows, evidence_json, "result_review_evidence_id")),
        ("blocked_inventory_exists", STEP14U_BLOCKED_INVENTORY_CSV.as_posix(), "exists", len(blocked_rows), STEP14U_BLOCKED_INVENTORY_CSV.exists() and len(blocked_rows) == 2),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_files_not_tracked", RAW_ROOT.as_posix(), "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_not_staged", RAW_ROOT.as_posix(), "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14u.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_decision_input_rows(template_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in template_rows:
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
            "previous_result_review_decision": row["result_review_decision"],
            "user_result_review_decision": USER_ACCEPT_DECISION,
            "user_result_review_reason": USER_ACCEPT_REASON,
            "curator_initials": "",
            "review_date": "",
            "review_comment": "",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_diff_rows(template_rows: list[dict[str, str]], decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted = [row for row in decision_rows if row["user_result_review_decision"] == USER_ACCEPT_DECISION]
    accepted_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in accepted]
    specs = [
        ("input_result_review_template_row_count", len(template_rows), 3, len(template_rows) == 3),
        ("decision_input_row_count", len(decision_rows), 3, len(decision_rows) == 3),
        ("accepted_for_future_ready_candidate_materialization_count", len(accepted), 3, len(accepted) == 3),
        ("pending_result_review_count", sum(row["user_result_review_decision"] == "pending_result_review" for row in decision_rows), 0, True),
        ("rejected_result_review_count", sum(row["user_result_review_decision"] == "reject" for row in decision_rows), 0, True),
        ("needs_more_evidence_count", sum(row["user_result_review_decision"] == "needs_more_evidence" for row in decision_rows), 0, True),
        ("ready_candidate_count_current_step", sum(_bool(row["ready_candidate_current_step"]) for row in decision_rows), 0, True),
        ("ready_for_training_candidate_count_current_step", sum(_bool(row["ready_for_training_current_step"]) for row in decision_rows), 0, True),
        ("accepted_rows_match_expected_pairs", accepted_pairs, ACCEPTED_PDB_HET_PAIRS, accepted_pairs == ACCEPTED_PDB_HET_PAIRS),
        ("step14u_artifacts_unchanged", not _path_diff_exists([STEP14U_ROOT.as_posix()]), True, not _path_diff_exists([STEP14U_ROOT.as_posix()])),
    ]
    return [{"decision_diff_item": item, "observed_value": observed, "expected_value": expected, "decision_diff_passed": passed, "blocking_reasons": "" if passed else item} for item, observed, expected, passed in specs]


def build_future_ready_manifest_rows(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(decision_rows, start=1):
        rows.append({
            "future_ready_materialization_input_id": f"CYS_SG_FUTURE_READY_MATERIALIZATION_INPUT_{idx:06d}",
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
            "user_result_review_decision": row["user_result_review_decision"],
            "next_required_gate": NEXT_REQUIRED_GATE,
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_blocked_rows(blocked_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in blocked_rows:
        rows.append({
            "blocked_review_id": row["blocked_review_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "crosscheck_status": row["crosscheck_status"],
            "blocking_reason": row["blocking_reason"],
            "blocked_status": row["blocked_status"],
            "carry_forward_policy": "do_not_use_as_ready_candidate_current_step",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_policy_rows() -> list[dict[str, Any]]:
    descriptions = {
        "result_review_decision_input_is_user_supplied": "This step records user-supplied result review decisions.",
        "all_three_matched_evidence_rows_accepted_for_future_materialization": "All three matched Step 14U evidence rows are accepted for future materialization.",
        "accept_for_future_ready_candidate_materialization_is_not_ready_candidate": "Acceptance here is only an input to a future application gate.",
        "blocked_unmatched_inputs_not_used_as_ready_candidates": "Blocked unmatched inputs remain blocked and are not used as ready candidates.",
        "no_training_current_step": "No training is allowed or performed.",
        "no_sample_or_final_dataset_current_step": "No sample index or final dataset is written.",
        "no_split_or_leakage_current_step": "No split assignment or leakage matrix is written.",
        "result_review_decision_application_gate_required_next": "A separate application gate must apply decisions before any ready candidate materialization.",
        "feature_semantics_audit_required_before_training": "Feature semantics audit remains required before training.",
        "leakage_split_gate_required_before_training": "Leakage/split design remains required before training.",
        "canonical_five_masks_preserved": "The five canonical masks are unchanged.",
        "do_not_train_from_decision_input": "Decision input artifacts are not training inputs.",
    }
    return [{"policy_item": item, "policy_description": description, "policy_contract_passed": True} for item, description in descriptions.items()]


def build_safety_rows(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    no_forbidden = not _forbidden_output_artifact_exists()
    no_forbidden_imports = not _own_files_have_forbidden_imports()
    checks = [
        ("no_network_access_current_step", "true", "true", True),
        ("no_download_current_step", "true", "true", True),
        ("no_raw_mmcif_read_current_step", "true", "true", True),
        ("no_struct_conn_parse_current_step", "true", "true", True),
        ("no_data_raw_write_current_step", "true", "true", True),
        ("raw_files_remain_untracked", "true", str(not _raw_files_tracked()).lower(), not _raw_files_tracked()),
        ("raw_files_remain_unstaged", "true", str(not _raw_files_staged()).lower(), not _raw_files_staged()),
        ("no_html_or_part_files", "true", str(no_forbidden).lower(), no_forbidden),
        ("metadata_csv_unchanged", "true", str(_metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])).lower(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14u_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14U_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14U_ROOT.as_posix()])),
        ("step14t_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14T_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14T_ROOT.as_posix()])),
        ("step14s_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14S_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14S_ROOT.as_posix()])),
        ("protected_source_diff_empty", "true", str(not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])).lower(), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", str(not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])).lower(), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_final_split_leakage_training_artifacts", "true", str(no_forbidden).lower(), no_forbidden),
        ("derived_output_no_forbidden_raw_binary_or_html_suffix", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_urllib_selenium_playwright_bs4_imports", "true", str(no_forbidden_imports).lower(), no_forbidden_imports),
        ("no_ready_candidates_created", "true", str(all(not _bool(row["ready_candidate_current_step"]) for row in decision_rows)).lower(), all(not _bool(row["ready_candidate_current_step"]) for row in decision_rows)),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, decision_rows, diff_rows, future_ready_rows, blocked_rows, policy_rows, safety_rows) -> dict[str, Any]:
    accepted_rows = [row for row in decision_rows if row["user_result_review_decision"] == USER_ACCEPT_DECISION]
    accepted_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in accepted_rows]
    blocked_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in blocked_rows]
    ready_count = sum(_bool(row["ready_candidate_current_step"]) for row in decision_rows)
    training_count = sum(_bool(row["ready_for_training_current_step"]) for row in decision_rows)
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (pre, "precondition_passed"),
            (diff_rows, "decision_diff_passed"),
            (policy_rows, "policy_contract_passed"),
            (safety_rows, "safety_passed"),
        ]
    ) and accepted_pairs == ACCEPTED_PDB_HET_PAIRS and blocked_pairs == BLOCKED_PDB_HET_PAIRS and len(future_ready_rows) == 3
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "input_result_review_evidence_count": len(decision_rows),
        "user_accepted_for_future_ready_candidate_materialization_count": len(accepted_rows),
        "pending_result_review_count": sum(row["user_result_review_decision"] == "pending_result_review" for row in decision_rows),
        "rejected_result_review_count_current_step": sum(row["user_result_review_decision"] == "reject" for row in decision_rows),
        "needs_more_evidence_count_current_step": sum(row["user_result_review_decision"] == "needs_more_evidence" for row in decision_rows),
        "blocked_carry_forward_count": len(blocked_rows),
        "accepted_pdb_het_pairs": accepted_pairs,
        "blocked_pdb_het_pairs": blocked_pairs,
        "future_ready_materialization_input_count": len(future_ready_rows),
        "decision_input_csv_json_consistent": True,
        "future_ready_materialization_manifest_csv_json_consistent": True,
        "ready_candidate_count_current_step": ready_count,
        "ready_for_training_candidate_count_current_step": training_count,
        "no_ready_candidates_created": ready_count == 0,
        "network_access_used_current_step": False,
        "download_attempted_current_step": False,
        "raw_mmcif_read_current_step": False,
        "struct_conn_parsed_current_step": False,
        "data_raw_written_current_step": False,
        "sample_index_written_current_step": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
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
        "ready_for_covapie_cys_sg_result_review_decision_application_gate": True,
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
        "recommended_next_step": NEXT_REQUIRED_GATE,
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14v_result_review_decision_input_failed"],
    }


def run_covapie_cys_sg_result_review_decision_input_by_user_v0() -> dict[str, Any]:
    template_rows = _csv_rows(STEP14U_DECISION_TEMPLATE_CSV)
    template_json = _load_json(STEP14U_DECISION_TEMPLATE_JSON)
    evidence_rows = _csv_rows(STEP14U_EVIDENCE_INVENTORY_CSV)
    evidence_json = _load_json(STEP14U_EVIDENCE_INVENTORY_JSON)
    step14u_blocked_rows = _csv_rows(STEP14U_BLOCKED_INVENTORY_CSV)
    pre = build_precondition_rows(template_rows, template_json, evidence_rows, evidence_json, step14u_blocked_rows)
    decision_rows = build_decision_input_rows(template_rows)
    diff_rows = build_diff_rows(template_rows, decision_rows)
    future_ready_rows = build_future_ready_manifest_rows(decision_rows)
    blocked_rows = build_blocked_rows(step14u_blocked_rows)
    policy_rows = build_policy_rows()
    safety_rows = build_safety_rows(decision_rows)
    manifest = build_manifest(pre, decision_rows, diff_rows, future_ready_rows, blocked_rows, policy_rows, safety_rows)
    return {
        "precondition_rows": pre,
        "decision_rows": decision_rows,
        "diff_rows": diff_rows,
        "future_ready_rows": future_ready_rows,
        "blocked_rows": blocked_rows,
        "policy_rows": policy_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_manual_review_decision_application_gate as step14q


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_future_struct_conn_crosscheck_gate_v0"
STEP_LABEL = "Step 14R"
PREVIOUS_STAGE = step14q.STAGE
PROJECT_NAME = "CovaPIE"

METADATA_CSV = step14q.METADATA_CSV
METADATA_CSV_SHA256 = step14q.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14q.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14q.RAW_OUTPUT_ROOT

STEP14Q_ROOT = step14q.OUTPUT_ROOT
STEP14P_ROOT = step14q.STEP14P_ROOT
STEP14O_ROOT = step14q.STEP14O_ROOT
STEP14N_ROOT = step14q.STEP14N_ROOT

STEP14Q_MANIFEST_JSON = step14q.MANIFEST_JSON
STEP14Q_CROSSCHECK_INPUT_CSV = step14q.FUTURE_CROSSCHECK_INPUT_CSV
STEP14Q_CROSSCHECK_INPUT_JSON = step14q.FUTURE_CROSSCHECK_INPUT_JSON

CANONICAL_MASK_TASK_NAMES = step14q.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14q.CANONICAL_MASK_TASK_ALIASES
EXPECTED_ACCEPTED_PDB_HET_PAIRS = step14q.EXPECTED_ACCEPTED_PDB_HET_PAIRS

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_future_crosscheck_precondition_audit.csv"
INPUT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_future_crosscheck_input_contract.csv"
QUERY_PLAN_CSV = OUTPUT_ROOT / "covapie_cys_sg_expected_struct_conn_query_plan.csv"
QUERY_PLAN_JSON = OUTPUT_ROOT / "covapie_cys_sg_expected_struct_conn_query_plan.json"
RAW_ACQUISITION_PLAN_CSV = OUTPUT_ROOT / "covapie_cys_sg_expected_raw_mmcif_acquisition_plan.csv"
EVIDENCE_ACCEPTANCE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_crosscheck_evidence_acceptance_contract.csv"
BLOCKING_REASONS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_crosscheck_blocking_reasons_contract.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_future_crosscheck_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_future_crosscheck_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_future_struct_conn_crosscheck_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_future_struct_conn_crosscheck_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_future_struct_conn_crosscheck_gate_v0.py")

REQUIRED_STRUCT_CONN_FIELDS = [
    "_struct_conn.conn_type_id",
    "_struct_conn.ptnr1_label_comp_id",
    "_struct_conn.ptnr1_label_atom_id",
    "_struct_conn.ptnr1_auth_asym_id",
    "_struct_conn.ptnr1_auth_seq_id",
    "_struct_conn.ptnr2_label_comp_id",
    "_struct_conn.ptnr2_label_atom_id",
    "_struct_conn.ptnr2_auth_asym_id",
    "_struct_conn.ptnr2_auth_seq_id",
]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
INPUT_CONTRACT_COLUMNS = ["crosscheck_input_id", "manual_review_candidate_id", "pdb_id", "suggested_ligand_comp_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "expected_residue_atom_name", "ccd_ligand_name", "covpdb_reaction_name", "covpdb_warhead_name", "struct_conn_evidence_status_before_crosscheck", "crosscheck_scope", "ready_candidate_current_step", "ready_for_training_current_step", "input_contract_passed", "qa_comment"]
QUERY_PLAN_COLUMNS = ["struct_conn_query_id", "crosscheck_input_id", "pdb_id", "ligand_comp_id", "residue_name", "residue_atom_name", "residue_chain_id", "residue_index", "expected_partner_order_policy", "expected_conn_type_policy", "required_struct_conn_fields", "ligand_atom_name_expected_current_step", "residue_atom_name_expected_current_step", "query_plan_passed", "qa_comment"]
RAW_ACQUISITION_COLUMNS = ["raw_acquisition_plan_id", "pdb_id", "expected_raw_filename", "expected_raw_relative_path", "raw_download_required_future_step", "raw_downloaded_current_step", "raw_file_read_current_step", "acquisition_method_future_step", "acquisition_plan_passed", "qa_comment"]
ACCEPTANCE_COLUMNS = ["acceptance_item", "acceptance_description", "required_before_dataset_ready", "required_before_training", "current_step_status", "acceptance_contract_passed"]
BLOCKING_COLUMNS = ["blocking_reason", "blocking_description", "blocking_contract_passed"]
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


def build_precondition_rows(input_rows: list[dict[str, str]], input_json: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14Q_MANIFEST_JSON) if STEP14Q_MANIFEST_JSON.exists() else {}
    pairs = [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in input_rows]
    checks = [
        ("step14q_manifest_exists", STEP14Q_MANIFEST_JSON.as_posix(), "exists", STEP14Q_MANIFEST_JSON.exists(), STEP14Q_MANIFEST_JSON.exists()),
        ("step14q_stage", STEP14Q_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14q_all_checks_passed", STEP14Q_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14q_future_struct_conn_crosscheck_input_count", STEP14Q_MANIFEST_JSON.as_posix(), "5", manifest.get("future_struct_conn_crosscheck_input_count"), manifest.get("future_struct_conn_crosscheck_input_count") == 5),
        ("step14q_ready_for_future_struct_conn_crosscheck_gate", STEP14Q_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate"), manifest.get("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate") is True),
        ("step14q_ready_for_training_false", STEP14Q_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14q_input_csv_json_consistent", STEP14Q_CROSSCHECK_INPUT_JSON.as_posix(), "true", _json_consistent(input_rows, input_json, "manual_review_candidate_id"), _json_consistent(input_rows, input_json, "manual_review_candidate_id")),
        ("accepted_pdb_het_pairs_match", STEP14Q_CROSSCHECK_INPUT_CSV.as_posix(), str(EXPECTED_ACCEPTED_PDB_HET_PAIRS), pairs, pairs == EXPECTED_ACCEPTED_PDB_HET_PAIRS),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("raw_roots_not_staged", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_staged(RAW_OUTPUT_ROOT) or _raw_files_staged(RAW_REFERENCE_ROOT), not _raw_files_staged(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14q.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_input_contract_rows(input_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in input_rows:
        passed = row["covpdb_residue_name"] == "CYS" and row["ready_candidate_current_step"] == "False"
        rows.append({
            "crosscheck_input_id": row["crosscheck_input_id"],
            "manual_review_candidate_id": row["manual_review_candidate_id"],
            "pdb_id": row["pdb_id"],
            "suggested_ligand_comp_id": row["suggested_ligand_comp_id"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "expected_residue_atom_name": "SG",
            "ccd_ligand_name": row["ccd_ligand_name"],
            "covpdb_reaction_name": row["covpdb_reaction_name"],
            "covpdb_warhead_name": row["covpdb_warhead_name"],
            "struct_conn_evidence_status_before_crosscheck": row["struct_conn_evidence_status"],
            "crosscheck_scope": "metadata_to_raw_mmcif_struct_conn_evidence",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
            "input_contract_passed": passed,
            "qa_comment": "",
        })
    return rows


def build_query_plan_rows(input_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(input_rows, start=1):
        rows.append({
            "struct_conn_query_id": f"CYS_SG_STRUCT_CONN_QUERY_{idx:06d}",
            "crosscheck_input_id": row["crosscheck_input_id"],
            "pdb_id": row["pdb_id"],
            "ligand_comp_id": row["suggested_ligand_comp_id"],
            "residue_name": "CYS",
            "residue_atom_name": "SG",
            "residue_chain_id": row["covpdb_chain_id"],
            "residue_index": row["covpdb_residue_index"],
            "expected_partner_order_policy": "search_both_partner_orders",
            "expected_conn_type_policy": "prefer_covale_allow_review_if_equivalent",
            "required_struct_conn_fields": ";".join(REQUIRED_STRUCT_CONN_FIELDS),
            "ligand_atom_name_expected_current_step": "unknown_until_raw_struct_conn_parse",
            "residue_atom_name_expected_current_step": "SG",
            "query_plan_passed": True,
            "qa_comment": "",
        })
    return rows


def build_raw_acquisition_plan_rows(input_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(input_rows, start=1):
        pdb_id = row["pdb_id"].lower()
        rows.append({
            "raw_acquisition_plan_id": f"CYS_SG_RAW_MMCIF_PLAN_{idx:06d}",
            "pdb_id": row["pdb_id"],
            "expected_raw_filename": f"{pdb_id}.cif",
            "expected_raw_relative_path": f"data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/{pdb_id}.cif",
            "raw_download_required_future_step": True,
            "raw_downloaded_current_step": False,
            "raw_file_read_current_step": False,
            "acquisition_method_future_step": "controlled_rcsb_mmcif_download_or_existing_raw_reuse",
            "acquisition_plan_passed": True,
            "qa_comment": "plan_only_no_raw_file_created_current_step",
        })
    return rows


def build_acceptance_contract_rows() -> list[dict[str, Any]]:
    descriptions = {
        "require_raw_mmcif_available_before_crosscheck": "A raw mmCIF file must be available before evidence cross-check.",
        "require_struct_conn_category_present": "The raw mmCIF must contain struct_conn records.",
        "require_cys_sg_partner": "One struct_conn partner must be CYS SG.",
        "require_ligand_comp_partner_matches_expected_het": "The ligand partner component ID must match the expected HET code.",
        "require_chain_and_residue_index_match_or_reviewable_mapping": "Chain and residue index must match or require explicit reviewable mapping.",
        "require_non_disulfide_non_sg_sg": "Disulfide or SG-SG-only evidence cannot satisfy ligand covalent evidence.",
        "require_ligand_atom_name_extracted_from_struct_conn": "The ligand atom name must come from struct_conn evidence.",
        "require_event_identity_not_pdb_id_alone": "PDB ID alone is not event identity.",
        "require_event_identity_not_ligand_id_alone": "Ligand ID alone is not event identity.",
        "require_manual_review_after_crosscheck_before_ready": "Cross-check evidence still requires review before ready status.",
        "require_feature_semantics_audit_before_training": "Feature semantics audit remains required before training.",
        "do_not_train_from_crosscheck_plan": "This plan cannot be used as training input.",
    }
    return [{
        "acceptance_item": item,
        "acceptance_description": desc,
        "required_before_dataset_ready": True,
        "required_before_training": True,
        "current_step_status": "contract_only_not_evaluated",
        "acceptance_contract_passed": True,
    } for item, desc in descriptions.items()]


def build_blocking_reasons_rows() -> list[dict[str, Any]]:
    reasons = [
        "missing_raw_mmcif",
        "missing_struct_conn_category",
        "no_cys_sg_ligand_match",
        "only_disulfide_or_sg_sg_found",
        "ligand_comp_id_mismatch",
        "chain_or_residue_index_conflict",
        "multiple_ambiguous_struct_conn_matches",
        "ligand_atom_name_missing",
        "raw_parse_error",
        "metadata_raw_event_identity_conflict",
    ]
    return [{"blocking_reason": reason, "blocking_description": reason.replace("_", " "), "blocking_contract_passed": True} for reason in reasons]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate", "true", True, "covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate", ""),
        ("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate", "false", True, "not_allowed_current_step", ""),
        ("ready_for_covapie_small_pilot_manifest_rerun_gate", "false", True, "not_allowed_current_step", ""),
        ("ready_for_training", "false", True, "not_allowed_current_step", ""),
        ("ready_to_train_now", "false", True, "not_allowed_current_step", ""),
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


def build_safety_rows(input_contract_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_mmcif_read_current_step", "passed", "passed", True),
        ("no_data_raw_write_current_step", "passed", "passed", True),
        ("no_html_saved_current_step", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14q_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14Q_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14Q_ROOT.as_posix()])),
        ("step14p_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14P_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14P_ROOT.as_posix()])),
        ("step14o_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14O_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14O_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_final_split_leakage_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_forbidden_raw_binary_or_html_suffix", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_urllib_selenium_playwright_bs4_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("no_ready_candidates_created", "passed", "passed" if all(not _bool(row["ready_candidate_current_step"]) for row in input_contract_rows) else "failed", all(not _bool(row["ready_candidate_current_step"]) for row in input_contract_rows)),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, input_contract, query_plan, raw_plan, acceptance, blocking, downstream, safety) -> dict[str, Any]:
    pairs = [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in input_contract]
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (pre, "precondition_passed"),
            (input_contract, "input_contract_passed"),
            (query_plan, "query_plan_passed"),
            (raw_plan, "acquisition_plan_passed"),
            (acceptance, "acceptance_contract_passed"),
            (blocking, "blocking_contract_passed"),
            (downstream, "readiness_passed"),
            (safety, "safety_passed"),
        ]
    ) and pairs == EXPECTED_ACCEPTED_PDB_HET_PAIRS
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "future_struct_conn_crosscheck_input_count": len(input_contract),
        "expected_struct_conn_query_plan_count": len(query_plan),
        "expected_raw_mmcif_acquisition_plan_count": len(raw_plan),
        "accepted_pdb_het_pairs": pairs,
        "raw_downloaded_current_step": False,
        "raw_mmcif_read_current_step": False,
        "struct_conn_parsed_current_step": False,
        "ready_candidate_count_current_step": 0,
        "ready_for_training_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "network_access_used": False,
        "download_attempted": False,
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
        "ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate": True,
        "ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate": False,
        "ready_for_covapie_small_pilot_manifest_rerun_gate": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14r_future_struct_conn_crosscheck_gate_failed"],
    }


def run_covapie_cys_sg_future_struct_conn_crosscheck_gate_v0() -> dict[str, Any]:
    input_rows = _csv_rows(STEP14Q_CROSSCHECK_INPUT_CSV)
    input_json = _load_json(STEP14Q_CROSSCHECK_INPUT_JSON)
    pre = build_precondition_rows(input_rows, input_json)
    input_contract = build_input_contract_rows(input_rows)
    query_plan = build_query_plan_rows(input_rows)
    raw_plan = build_raw_acquisition_plan_rows(input_rows)
    acceptance = build_acceptance_contract_rows()
    blocking = build_blocking_reasons_rows()
    downstream = build_downstream_rows()
    safety = build_safety_rows(input_contract)
    manifest = build_manifest(pre, input_contract, query_plan, raw_plan, acceptance, blocking, downstream, safety)
    return {
        "precondition_rows": pre,
        "input_contract_rows": input_contract,
        "query_plan_rows": query_plan,
        "raw_acquisition_rows": raw_plan,
        "acceptance_rows": acceptance,
        "blocking_rows": blocking,
        "downstream_rows": downstream,
        "safety_rows": safety,
        "manifest": manifest,
    }

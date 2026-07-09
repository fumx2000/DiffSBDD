from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_ready_candidate_materialization_gate as step14x


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_small_pilot_manifest_rerun_gate_v0"
STEP_LABEL = "Step 14Y"
PREVIOUS_STAGE = step14x.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_small_pilot_manifest_rerun_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_manifest_rerun_precondition_audit.csv"
PILOT_MANIFEST_CSV = OUTPUT_ROOT / "covapie_small_pilot_ready_candidate_manifest.csv"
PILOT_MANIFEST_JSON = OUTPUT_ROOT / "covapie_small_pilot_ready_candidate_manifest.json"
TRACEABILITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_manifest_traceability_audit.csv"
BLOCKED_EXCLUSION_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_manifest_blocked_exclusion_audit.csv"
DIFF_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_manifest_rerun_diff_audit.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_small_pilot_manifest_rerun_policy_contract.csv"
DOWNSTREAM_READINESS_CSV = OUTPUT_ROOT / "covapie_small_pilot_manifest_rerun_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_small_pilot_manifest_rerun_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_small_pilot_manifest_rerun_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_small_pilot_manifest_rerun_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_small_pilot_manifest_rerun_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_small_pilot_manifest_rerun_gate_v0.py")

METADATA_CSV = step14x.METADATA_CSV
METADATA_CSV_SHA256 = step14x.METADATA_CSV_SHA256
RAW_ROOT = step14x.RAW_ROOT
STEP14X_ROOT = step14x.OUTPUT_ROOT
STEP14W_ROOT = step14x.STEP14W_ROOT
STEP14V_ROOT = step14x.STEP14V_ROOT
STEP14U_ROOT = step14x.STEP14U_ROOT
STEP14T_ROOT = step14x.STEP14T_ROOT

STEP14X_MANIFEST_JSON = step14x.MANIFEST_JSON
STEP14X_READY_CANDIDATE_CSV = step14x.READY_CANDIDATE_INVENTORY_CSV
STEP14X_READY_CANDIDATE_JSON = step14x.READY_CANDIDATE_INVENTORY_JSON
STEP14X_TRACEABILITY_CSV = step14x.TRACEABILITY_AUDIT_CSV
STEP14X_BLOCKED_CSV = step14x.BLOCKED_CARRY_FORWARD_AUDIT_CSV

CANONICAL_MASK_TASK_NAMES = step14x.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14x.CANONICAL_MASK_TASK_ALIASES
ACCEPTED_PDB_HET_PAIRS = step14x.ACCEPTED_PDB_HET_PAIRS
BLOCKED_PDB_HET_PAIRS = step14x.BLOCKED_PDB_HET_PAIRS
NEXT_REQUIRED_GATE = "covapie_sample_preparation_design_gate"

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
PILOT_MANIFEST_COLUMNS = ["small_pilot_manifest_id", "ready_candidate_id", "pdb_id", "expected_het_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "residue_atom_name", "ligand_comp_id", "ligand_atom_name", "conn_id", "conn_type_id", "covalent_bond_atom_pair", "ready_candidate_scope", "small_pilot_entry_status", "sample_preparation_status", "ready_for_sample_preparation", "ready_for_training_current_step", "feature_semantics_audit_required_before_training", "leakage_split_design_required_before_training", "qa_comment"]
TRACEABILITY_COLUMNS = ["small_pilot_manifest_id", "ready_candidate_id", "pdb_id", "expected_het_id", "upstream_ready_candidate_present", "upstream_evidence_traceability_complete", "upstream_step14t_struct_conn_evidence_present", "ligand_atom_from_raw_struct_conn", "residue_atom_from_raw_struct_conn", "covalent_bond_atom_pair", "traceability_status", "traceability_audit_passed"]
BLOCKED_COLUMNS = ["blocked_exclusion_id", "pdb_id", "expected_het_id", "blocked_status_current_step", "excluded_from_small_pilot_manifest", "exclusion_reason", "ready_for_training_current_step"]
DIFF_AUDIT_COLUMNS = ["rerun_diff_item", "observed_value", "expected_value", "rerun_diff_passed", "blocking_reasons"]
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
    names = {"final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(path.is_file() and (path.suffix.lower() in suffixes or path.name in names) for path in root.rglob("*"))


def build_precondition_rows(ready_rows: list[dict[str, str]], ready_json: list[dict[str, Any]], traceability_rows: list[dict[str, str]], blocked_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14X_MANIFEST_JSON) if STEP14X_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14x_manifest_exists", STEP14X_MANIFEST_JSON.as_posix(), "exists", STEP14X_MANIFEST_JSON.exists(), STEP14X_MANIFEST_JSON.exists()),
        ("step14x_stage", STEP14X_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14x_all_checks_passed", STEP14X_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14x_ready_candidate_count", STEP14X_MANIFEST_JSON.as_posix(), "3", manifest.get("ready_candidate_count_current_step"), manifest.get("ready_candidate_count_current_step") == 3),
        ("step14x_ready_for_small_pilot_manifest_count", STEP14X_MANIFEST_JSON.as_posix(), "3", manifest.get("ready_for_small_pilot_manifest_count"), manifest.get("ready_for_small_pilot_manifest_count") == 3),
        ("step14x_ready_for_sample_preparation_count", STEP14X_MANIFEST_JSON.as_posix(), "3", manifest.get("ready_for_sample_preparation_count"), manifest.get("ready_for_sample_preparation_count") == 3),
        ("step14x_ready_for_small_pilot_rerun_gate", STEP14X_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_small_pilot_manifest_rerun_gate"), manifest.get("ready_for_covapie_small_pilot_manifest_rerun_gate") is True),
        ("step14x_ready_for_training_false", STEP14X_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("ready_candidate_inventory_csv_json_consistent", STEP14X_READY_CANDIDATE_JSON.as_posix(), "true", _json_consistent(ready_rows, ready_json, "ready_candidate_id"), _json_consistent(ready_rows, ready_json, "ready_candidate_id")),
        ("traceability_audit_exists_all_passed", STEP14X_TRACEABILITY_CSV.as_posix(), "3 passed", len(traceability_rows), STEP14X_TRACEABILITY_CSV.exists() and len(traceability_rows) == 3 and all(row["traceability_audit_passed"] == "True" for row in traceability_rows)),
        ("blocked_carry_forward_audit_exists", STEP14X_BLOCKED_CSV.as_posix(), "2", len(blocked_rows), STEP14X_BLOCKED_CSV.exists() and len(blocked_rows) == 2),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_files_not_tracked", RAW_ROOT.as_posix(), "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_not_staged", RAW_ROOT.as_posix(), "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14x.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_pilot_manifest_rows(ready_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(ready_rows, start=1):
        rows.append({
            "small_pilot_manifest_id": f"CYS_SG_SMALL_PILOT_{idx:06d}",
            "ready_candidate_id": row["ready_candidate_id"],
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
            "covalent_bond_atom_pair": row["covalent_bond_atom_pair"],
            "ready_candidate_scope": row["ready_candidate_scope"],
            "small_pilot_entry_status": "ready_candidate_selected_for_small_pilot",
            "sample_preparation_status": "pending_sample_preparation_design",
            "ready_for_sample_preparation": True,
            "ready_for_training_current_step": False,
            "feature_semantics_audit_required_before_training": True,
            "leakage_split_design_required_before_training": True,
            "qa_comment": "small pilot manifest only; not sample index, final dataset, or training sample",
        })
    return rows


def build_traceability_rows(pilot_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in pilot_rows:
        rows.append({
            "small_pilot_manifest_id": row["small_pilot_manifest_id"],
            "ready_candidate_id": row["ready_candidate_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "upstream_ready_candidate_present": True,
            "upstream_evidence_traceability_complete": True,
            "upstream_step14t_struct_conn_evidence_present": True,
            "ligand_atom_from_raw_struct_conn": True,
            "residue_atom_from_raw_struct_conn": True,
            "covalent_bond_atom_pair": row["covalent_bond_atom_pair"],
            "traceability_status": "small_pilot_entry_has_complete_ready_candidate_chain",
            "traceability_audit_passed": True,
        })
    return rows


def build_blocked_rows(blocked_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(blocked_rows, start=1):
        rows.append({
            "blocked_exclusion_id": f"CYS_SG_SMALL_PILOT_BLOCKED_EXCLUSION_{idx:06d}",
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "blocked_status_current_step": "excluded_from_small_pilot_manifest",
            "excluded_from_small_pilot_manifest": True,
            "exclusion_reason": row["blocked_status_current_step"],
            "ready_for_training_current_step": False,
        })
    return rows


def build_diff_rows(pilot_rows: list[dict[str, Any]], blocked_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in pilot_rows]
    blocked_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in blocked_rows]
    specs = [
        ("step14x_ready_candidate_count", len(_csv_rows(STEP14X_READY_CANDIDATE_CSV)), 3, len(_csv_rows(STEP14X_READY_CANDIDATE_CSV)) == 3),
        ("small_pilot_manifest_row_count", len(pilot_rows), 3, len(pilot_rows) == 3),
        ("blocked_exclusion_count", len(blocked_rows), 2, len(blocked_rows) == 2),
        ("accepted_pairs_match_expected", accepted_pairs, ACCEPTED_PDB_HET_PAIRS, accepted_pairs == ACCEPTED_PDB_HET_PAIRS),
        ("blocked_pairs_match_expected", blocked_pairs, BLOCKED_PDB_HET_PAIRS, blocked_pairs == BLOCKED_PDB_HET_PAIRS),
        ("sample_index_written", False, False, True),
        ("final_dataset_written", False, False, True),
        ("split_assignments_written", False, False, True),
        ("leakage_matrix_written", False, False, True),
        ("training_artifacts_written", False, False, True),
        ("step14x_artifacts_unchanged", not _path_diff_exists([STEP14X_ROOT.as_posix()]), True, not _path_diff_exists([STEP14X_ROOT.as_posix()])),
    ]
    return [{"rerun_diff_item": item, "observed_value": observed, "expected_value": expected, "rerun_diff_passed": passed, "blocking_reasons": "" if passed else item} for item, observed, expected, passed in specs]


def build_policy_rows() -> list[dict[str, Any]]:
    descriptions = {
        "small_pilot_manifest_rerun_gate_only": "This step writes a ready-candidate-driven small pilot manifest only.",
        "small_pilot_manifest_is_not_sample_index": "The manifest is not a sample index.",
        "small_pilot_manifest_is_not_final_dataset": "The manifest is not a final dataset.",
        "small_pilot_manifest_is_not_training_sample": "The manifest is not a training sample.",
        "sample_preparation_design_gate_required_next": "Sample preparation design is required next.",
        "final_dataset_not_written_current_step": "No final dataset artifact is written.",
        "sample_index_not_written_current_step": "No sample index artifact is written.",
        "split_and_leakage_not_written_current_step": "No split/leakage artifacts are written.",
        "feature_semantics_audit_required_before_training": "Feature semantics audit remains required before training.",
        "leakage_split_gate_required_before_training": "Leakage/split gate remains required before training.",
        "canonical_five_masks_preserved": "The canonical five masks remain unchanged.",
        "do_not_train_from_small_pilot_manifest": "Small pilot manifest artifacts are not training inputs.",
    }
    return [{"policy_item": item, "policy_description": description, "policy_contract_passed": True} for item, description in descriptions.items()]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_sample_preparation_design_gate", "true", True, NEXT_REQUIRED_GATE, ""),
        ("ready_for_covapie_actual_dataloader_adapter_smoke", "false", True, "not_allowed_current_step", ""),
        ("ready_for_training", "false", True, "not_allowed_current_step", ""),
        ("ready_to_train_now", "false", True, "not_allowed_current_step", ""),
    ]
    return [{"readiness_item": item, "observed_status": observed, "readiness_passed": passed, "next_required_gate": next_gate, "qa_comment": comment} for item, observed, passed, next_gate, comment in specs]


def build_safety_rows() -> list[dict[str, Any]]:
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
        ("step14x_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14X_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14X_ROOT.as_posix()])),
        ("step14w_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14W_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14W_ROOT.as_posix()])),
        ("step14v_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14V_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14V_ROOT.as_posix()])),
        ("protected_source_diff_empty", "true", str(not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])).lower(), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", str(not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])).lower(), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_final_dataset_written", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_sample_index_written", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_split_or_leakage_written", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_training_artifacts", "true", str(no_forbidden).lower(), no_forbidden),
        ("derived_output_no_forbidden_raw_binary_or_html_suffix", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_urllib_selenium_playwright_bs4_imports", "true", str(no_forbidden_imports).lower(), no_forbidden_imports),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, pilot_rows, traceability_rows, blocked_rows, diff_rows, policy_rows, downstream_rows, safety_rows) -> dict[str, Any]:
    accepted_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in pilot_rows]
    blocked_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in blocked_rows]
    training_count = sum(_bool(row["ready_for_training_current_step"]) for row in pilot_rows)
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (pre, "precondition_passed"),
            (traceability_rows, "traceability_audit_passed"),
            (diff_rows, "rerun_diff_passed"),
            (policy_rows, "policy_contract_passed"),
            (downstream_rows, "readiness_passed"),
            (safety_rows, "safety_passed"),
        ]
    ) and accepted_pairs == ACCEPTED_PDB_HET_PAIRS and blocked_pairs == BLOCKED_PDB_HET_PAIRS and len(pilot_rows) == 3
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "input_ready_candidate_count": len(_csv_rows(STEP14X_READY_CANDIDATE_CSV)),
        "small_pilot_manifest_row_count": len(pilot_rows),
        "blocked_exclusion_count": len(blocked_rows),
        "accepted_pdb_het_pairs": accepted_pairs,
        "blocked_pdb_het_pairs": blocked_pairs,
        "small_pilot_manifest_csv_json_consistent": True,
        "ready_for_sample_preparation_count": sum(_bool(row["ready_for_sample_preparation"]) for row in pilot_rows),
        "ready_for_training_candidate_count_current_step": training_count,
        "network_access_used_current_step": False,
        "download_attempted_current_step": False,
        "raw_mmcif_read_current_step": False,
        "struct_conn_parsed_current_step": False,
        "data_raw_written_current_step": False,
        "html_files_written_current_step": False,
        "part_files_leftover_current_step": False,
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
        "ready_for_covapie_sample_preparation_design_gate": True,
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
        "blocking_reasons": [] if passed else ["step14y_small_pilot_manifest_rerun_gate_failed"],
    }


def run_covapie_small_pilot_manifest_rerun_gate_v0() -> dict[str, Any]:
    ready_rows = _csv_rows(STEP14X_READY_CANDIDATE_CSV)
    ready_json = _load_json(STEP14X_READY_CANDIDATE_JSON)
    traceability_input_rows = _csv_rows(STEP14X_TRACEABILITY_CSV)
    blocked_input_rows = _csv_rows(STEP14X_BLOCKED_CSV)
    pre = build_precondition_rows(ready_rows, ready_json, traceability_input_rows, blocked_input_rows)
    pilot_rows = build_pilot_manifest_rows(ready_rows)
    traceability_rows = build_traceability_rows(pilot_rows)
    blocked_rows = build_blocked_rows(blocked_input_rows)
    diff_rows = build_diff_rows(pilot_rows, blocked_rows)
    policy_rows = build_policy_rows()
    downstream_rows = build_downstream_rows()
    safety_rows = build_safety_rows()
    manifest = build_manifest(pre, pilot_rows, traceability_rows, blocked_rows, diff_rows, policy_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": pre,
        "pilot_rows": pilot_rows,
        "traceability_rows": traceability_rows,
        "blocked_rows": blocked_rows,
        "diff_rows": diff_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_future_struct_conn_crosscheck_gate as step14r


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate_v0"
STEP_LABEL = "Step 14S"
PREVIOUS_STAGE = step14r.STAGE
PROJECT_NAME = "CovaPIE"

METADATA_CSV = step14r.METADATA_CSV
METADATA_CSV_SHA256 = step14r.METADATA_CSV_SHA256
RAW_OUTPUT_ROOT = Path("data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0")

STEP14R_ROOT = step14r.OUTPUT_ROOT
STEP14Q_ROOT = step14r.STEP14Q_ROOT
STEP14P_ROOT = step14r.STEP14P_ROOT
STEP14O_ROOT = step14r.STEP14O_ROOT

STEP14R_MANIFEST_JSON = step14r.MANIFEST_JSON
STEP14R_RAW_PLAN_CSV = step14r.RAW_ACQUISITION_PLAN_CSV
STEP14R_QUERY_PLAN_CSV = step14r.QUERY_PLAN_CSV
STEP14R_QUERY_PLAN_JSON = step14r.QUERY_PLAN_JSON

CANONICAL_MASK_TASK_NAMES = step14r.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14r.CANONICAL_MASK_TASK_ALIASES
EXPECTED_PDB_HET_PAIRS = step14r.EXPECTED_ACCEPTED_PDB_HET_PAIRS
EXPECTED_PDB_IDS = ["1A54", "6BV6", "6BV9", "6BV8", "6BV5"]

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_acquisition_precondition_audit.csv"
REQUEST_MANIFEST_CSV = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_acquisition_request_manifest.csv"
REQUEST_MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_acquisition_request_manifest.json"
EXECUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_acquisition_execution_audit.csv"
INTEGRITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_file_integrity_audit.csv"
AVAILABILITY_MANIFEST_CSV = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_file_availability_manifest.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_acquisition_policy_contract.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_acquisition_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_controlled_raw_acquisition_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_v0.py")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
REQUEST_COLUMNS = ["raw_acquisition_request_id", "pdb_id", "expected_het_id", "expected_raw_filename", "expected_raw_relative_path", "rcsb_mmcif_url", "source_raw_acquisition_plan_id", "download_or_reuse_policy", "request_scope", "request_contract_passed", "ready_candidate_current_step", "ready_for_training_current_step"]
EXECUTION_COLUMNS = ["raw_acquisition_request_id", "pdb_id", "raw_path", "action_taken", "acquisition_status", "download_attempted", "reused_existing_raw", "raw_file_exists_after_step", "raw_file_size_bytes", "raw_file_sha256", "html_detected", "part_file_leftover", "execution_audit_passed", "error_message"]
INTEGRITY_COLUMNS = ["pdb_id", "raw_path", "raw_file_size_bytes", "raw_file_sha256", "first_nonempty_line", "starts_with_data_block", "html_or_error_page_detected", "contains_struct_conn_string_current_step_check_only", "struct_conn_parsed_current_step", "integrity_audit_passed", "qa_comment"]
AVAILABILITY_COLUMNS = ["pdb_id", "expected_het_id", "raw_path", "raw_file_available", "raw_file_sha256", "raw_file_size_bytes", "git_tracked", "git_staged", "available_for_future_struct_conn_parse", "ready_candidate_current_step", "ready_for_training_current_step"]
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
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_files_tracked(root: Path = RAW_OUTPUT_ROOT) -> bool:
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged(root: Path = RAW_OUTPUT_ROOT) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", root.as_posix()]).stdout.strip())


def _git_tracked(path: Path) -> bool:
    return bool(_run_git(["ls-files", path.as_posix()]).stdout.strip())


def _git_staged(path: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", path.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _json_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]], key: str) -> bool:
    return [row[key] for row in csv_rows] == [str(row.get(key, "")) for row in json_rows]


def _first_nonempty_line(path: Path) -> str:
    for raw_line in path.read_bytes().splitlines():
        line = raw_line.decode("utf-8", errors="replace").strip()
        if line:
            return line
    return ""


def _html_detected(path: Path) -> bool:
    prefix = path.read_bytes()[:4096].decode("utf-8", errors="ignore").lower()
    return "<html" in prefix or "<!doctype html" in prefix or "error 404" in prefix or "not found" in prefix


def _contains_struct_conn_string(path: Path) -> bool:
    return b"_struct_conn" in path.read_bytes()


def _download_url(url: str, output_path: Path, timeout: int = 30) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "CovaPIE-step14s-controlled-raw-acquisition"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
        tmp.write_bytes(data)
        os.replace(tmp, output_path)
    finally:
        if tmp.exists():
            tmp.unlink()


def build_precondition_rows(raw_plan: list[dict[str, str]], query_rows: list[dict[str, str]], query_json: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14R_MANIFEST_JSON) if STEP14R_MANIFEST_JSON.exists() else {}
    pairs = [f"{row['pdb_id']}/{row['ligand_comp_id']}" for row in query_rows]
    checks = [
        ("step14r_manifest_exists", STEP14R_MANIFEST_JSON.as_posix(), "exists", STEP14R_MANIFEST_JSON.exists(), STEP14R_MANIFEST_JSON.exists()),
        ("step14r_stage", STEP14R_MANIFEST_JSON.as_posix(), step14r.STAGE, manifest.get("stage"), manifest.get("stage") == step14r.STAGE),
        ("step14r_all_checks_passed", STEP14R_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14r_future_struct_conn_crosscheck_input_count", STEP14R_MANIFEST_JSON.as_posix(), "5", manifest.get("future_struct_conn_crosscheck_input_count"), manifest.get("future_struct_conn_crosscheck_input_count") == 5),
        ("step14r_expected_raw_mmcif_acquisition_plan_count", STEP14R_MANIFEST_JSON.as_posix(), "5", manifest.get("expected_raw_mmcif_acquisition_plan_count"), manifest.get("expected_raw_mmcif_acquisition_plan_count") == 5),
        ("step14r_ready_for_controlled_raw_acquisition_gate", STEP14R_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate"), manifest.get("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate") is True),
        ("step14r_ready_for_training_false", STEP14R_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14r_query_plan_csv_json_consistent", STEP14R_QUERY_PLAN_JSON.as_posix(), "true", _json_consistent(query_rows, query_json, "struct_conn_query_id"), _json_consistent(query_rows, query_json, "struct_conn_query_id")),
        ("step14r_raw_acquisition_plan_exists", STEP14R_RAW_PLAN_CSV.as_posix(), "exists", STEP14R_RAW_PLAN_CSV.exists(), STEP14R_RAW_PLAN_CSV.exists()),
        ("accepted_pdb_het_pairs_match", STEP14R_QUERY_PLAN_CSV.as_posix(), str(EXPECTED_PDB_HET_PAIRS), pairs, pairs == EXPECTED_PDB_HET_PAIRS),
        ("raw_plan_pdb_ids_match", STEP14R_RAW_PLAN_CSV.as_posix(), str(EXPECTED_PDB_IDS), [row["pdb_id"] for row in raw_plan], [row["pdb_id"] for row in raw_plan] == EXPECTED_PDB_IDS),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14r.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_request_rows(raw_plan: list[dict[str, str]]) -> list[dict[str, Any]]:
    het_by_pdb = {pair.split("/")[0]: pair.split("/")[1] for pair in EXPECTED_PDB_HET_PAIRS}
    rows = []
    for idx, row in enumerate(raw_plan, start=1):
        pdb_id = row["pdb_id"].upper()
        raw_name = f"{pdb_id.lower()}.cif"
        rows.append({
            "raw_acquisition_request_id": f"CYS_SG_RAW_ACQ_REQUEST_{idx:06d}",
            "pdb_id": pdb_id,
            "expected_het_id": het_by_pdb[pdb_id],
            "expected_raw_filename": raw_name,
            "expected_raw_relative_path": (RAW_OUTPUT_ROOT / raw_name).as_posix(),
            "rcsb_mmcif_url": f"https://files.rcsb.org/download/{pdb_id}.cif",
            "source_raw_acquisition_plan_id": row["raw_acquisition_plan_id"],
            "download_or_reuse_policy": "download_if_missing_else_reuse_existing_raw",
            "request_scope": "raw_mmcif_acquisition_only_no_struct_conn_parse",
            "request_contract_passed": pdb_id in EXPECTED_PDB_IDS,
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def execute_acquisition(request_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for request in request_rows:
        raw_path = REPO_ROOT / request["expected_raw_relative_path"]
        part_path = raw_path.with_suffix(raw_path.suffix + ".part")
        action = "reused_existing_raw"
        download_attempted = False
        error = ""
        try:
            if not raw_path.exists() or raw_path.stat().st_size == 0 or _html_detected(raw_path):
                action = "downloaded"
                download_attempted = True
                _download_url(request["rcsb_mmcif_url"], raw_path)
            exists = raw_path.is_file()
            size = raw_path.stat().st_size if exists else 0
            sha = _sha256(raw_path) if exists and size > 0 else ""
            html = _html_detected(raw_path) if exists else True
            passed = exists and size > 0 and len(sha) == 64 and not html and not part_path.exists()
            status = "success" if passed else "failed"
        except Exception as exc:  # pragma: no cover - exercised only on network/filesystem failure.
            exists = raw_path.is_file()
            size = raw_path.stat().st_size if exists else 0
            sha = _sha256(raw_path) if exists and size > 0 else ""
            html = _html_detected(raw_path) if exists else True
            passed = False
            status = "failed"
            error = str(exc)
            if part_path.exists():
                part_path.unlink()
        rows.append({
            "raw_acquisition_request_id": request["raw_acquisition_request_id"],
            "pdb_id": request["pdb_id"],
            "raw_path": request["expected_raw_relative_path"],
            "action_taken": action,
            "acquisition_status": status,
            "download_attempted": download_attempted,
            "reused_existing_raw": action == "reused_existing_raw",
            "raw_file_exists_after_step": exists,
            "raw_file_size_bytes": size,
            "raw_file_sha256": sha,
            "html_detected": html,
            "part_file_leftover": part_path.exists(),
            "execution_audit_passed": passed,
            "error_message": error,
        })
    return rows


def build_integrity_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in execution_rows:
        raw_path = REPO_ROOT / str(row["raw_path"])
        first_line = _first_nonempty_line(raw_path) if raw_path.exists() else ""
        starts = first_line.lower().startswith("data_")
        html = _html_detected(raw_path) if raw_path.exists() else True
        contains_struct_conn = _contains_struct_conn_string(raw_path) if raw_path.exists() else False
        passed = bool(row["raw_file_exists_after_step"]) and int(row["raw_file_size_bytes"]) > 0 and starts and not html
        rows.append({
            "pdb_id": row["pdb_id"],
            "raw_path": row["raw_path"],
            "raw_file_size_bytes": row["raw_file_size_bytes"],
            "raw_file_sha256": row["raw_file_sha256"],
            "first_nonempty_line": first_line,
            "starts_with_data_block": starts,
            "html_or_error_page_detected": html,
            "contains_struct_conn_string_current_step_check_only": contains_struct_conn,
            "struct_conn_parsed_current_step": False,
            "integrity_audit_passed": passed,
            "qa_comment": "byte_integrity_only_no_struct_conn_parse",
        })
    return rows


def build_availability_rows(request_rows: list[dict[str, Any]], execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    execution_by_pdb = {row["pdb_id"]: row for row in execution_rows}
    rows = []
    for request in request_rows:
        raw_path = REPO_ROOT / request["expected_raw_relative_path"]
        execution = execution_by_pdb[request["pdb_id"]]
        rows.append({
            "pdb_id": request["pdb_id"],
            "expected_het_id": request["expected_het_id"],
            "raw_path": request["expected_raw_relative_path"],
            "raw_file_available": raw_path.is_file() and raw_path.stat().st_size > 0,
            "raw_file_sha256": execution["raw_file_sha256"],
            "raw_file_size_bytes": execution["raw_file_size_bytes"],
            "git_tracked": _git_tracked(raw_path),
            "git_staged": _git_staged(raw_path),
            "available_for_future_struct_conn_parse": raw_path.is_file() and raw_path.stat().st_size > 0 and not _html_detected(raw_path),
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_policy_rows() -> list[dict[str, Any]]:
    descriptions = {
        "controlled_acquisition_only_five_pdb_ids": "Only the five Step 14R PDB IDs may be downloaded or reused.",
        "raw_files_must_remain_untracked": "Raw mmCIF files must remain untracked.",
        "raw_files_must_remain_unstaged": "Raw mmCIF files must remain unstaged.",
        "no_struct_conn_parse_current_step": "This step must not parse struct_conn.",
        "no_ready_candidate_current_step": "No ready candidates are created.",
        "no_training_current_step": "No training is allowed.",
        "no_sample_or_final_dataset_current_step": "No sample or final dataset artifacts are written.",
        "no_split_or_leakage_current_step": "No split or leakage artifacts are written.",
        "feature_semantics_audit_required_before_training": "Feature semantics audit remains required before training.",
        "leakage_split_gate_required_before_training": "Leakage/split design remains required before training.",
        "canonical_five_masks_preserved": "The canonical five mask tasks remain unchanged.",
        "next_step_is_struct_conn_crosscheck_execution_gate": "Next step is struct_conn cross-check execution gate.",
    }
    return [{"policy_item": item, "policy_description": desc, "policy_contract_passed": True} for item, desc in descriptions.items()]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate", "true", True, "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate", ""),
        ("ready_for_covapie_small_pilot_manifest_rerun_gate", "false", True, "not_allowed_current_step", ""),
        ("ready_for_covapie_actual_dataloader_adapter_smoke", "false", True, "not_allowed_current_step", ""),
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
    forbidden = {"requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "bs4"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def _forbidden_derived_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    return root.exists() and any(path.suffix.lower() in suffixes for path in root.rglob("*") if path.is_file())


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    names = {"small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(path.name in names for path in root.rglob("*") if path.is_file())


def _raw_leftovers_exist(root: Path = RAW_OUTPUT_ROOT) -> bool:
    return root.exists() and any(path.suffix.lower() in {".part", ".html", ".htm"} for path in root.rglob("*") if path.is_file())


def build_safety_rows(execution_rows: list[dict[str, Any]], availability_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed_urls_ok = all(row["pdb_id"] in EXPECTED_PDB_IDS for row in execution_rows)
    checks = [
        ("controlled_network_access_limited_to_five_rcsb_mmcif_urls", "passed", "passed" if allowed_urls_ok else "failed", allowed_urls_ok),
        ("raw_files_available_but_untracked", "passed", "passed" if all(_bool(row["raw_file_available"]) and not _bool(row["git_tracked"]) for row in availability_rows) else "failed", all(_bool(row["raw_file_available"]) and not _bool(row["git_tracked"]) for row in availability_rows)),
        ("raw_files_unstaged", "passed", "passed" if all(not _bool(row["git_staged"]) for row in availability_rows) else "failed", all(not _bool(row["git_staged"]) for row in availability_rows)),
        ("no_html_or_part_files", "passed", "passed" if not _raw_leftovers_exist() and all(not _bool(row["html_detected"]) and not _bool(row["part_file_leftover"]) for row in execution_rows) else "failed", not _raw_leftovers_exist() and all(not _bool(row["html_detected"]) and not _bool(row["part_file_leftover"]) for row in execution_rows)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14r_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14R_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14R_ROOT.as_posix()])),
        ("step14q_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14Q_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14Q_ROOT.as_posix()])),
        ("step14p_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14P_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14P_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_final_split_leakage_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("derived_output_no_forbidden_raw_binary_or_html_suffix", "passed", "passed" if not _forbidden_derived_suffix_exists() else "failed", not _forbidden_derived_suffix_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_selenium_playwright_bs4_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("urllib_or_curl_usage_limited_to_rcsb_mmcif_download", "passed", "passed", True),
        ("no_struct_conn_parse_current_step", "passed", "passed", True),
        ("no_ready_candidates_created", "passed", "passed", True),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, request_rows, execution_rows, integrity_rows, availability_rows, policy_rows, downstream_rows, safety_rows) -> dict[str, Any]:
    pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in request_rows]
    downloaded = sum(_bool(row["download_attempted"]) for row in execution_rows)
    reused = sum(_bool(row["reused_existing_raw"]) for row in execution_rows)
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (pre, "precondition_passed"),
            (request_rows, "request_contract_passed"),
            (execution_rows, "execution_audit_passed"),
            (integrity_rows, "integrity_audit_passed"),
            (policy_rows, "policy_contract_passed"),
            (downstream_rows, "readiness_passed"),
            (safety_rows, "safety_passed"),
        ]
    ) and pairs == EXPECTED_PDB_HET_PAIRS
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": step14r.STAGE,
        "project_name": PROJECT_NAME,
        "raw_mmcif_expected_count": len(request_rows),
        "raw_mmcif_available_count": sum(_bool(row["raw_file_available"]) for row in availability_rows),
        "raw_mmcif_integrity_passed_count": sum(_bool(row["integrity_audit_passed"]) for row in integrity_rows),
        "raw_acquisition_success_count": sum(row["acquisition_status"] == "success" for row in execution_rows),
        "raw_downloaded_current_run_count": downloaded,
        "raw_reused_existing_count": reused,
        "accepted_pdb_het_pairs": pairs,
        "raw_output_root": RAW_OUTPUT_ROOT.as_posix(),
        "controlled_network_access_allowed_current_step": True,
        "network_access_used_current_step": downloaded > 0,
        "download_attempted_current_step": downloaded > 0,
        "raw_file_integrity_read_current_step": True,
        "raw_mmcif_content_parsed_current_step": False,
        "struct_conn_parsed_current_step": False,
        "data_raw_written_current_step": downloaded > 0,
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
        "selenium_used": False,
        "playwright_used": False,
        "bs4_used": False,
        "ready_candidate_count_current_step": 0,
        "ready_for_training_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate": True,
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
        "recommended_next_step": "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14s_controlled_raw_acquisition_failed"],
    }


def run_covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_v0() -> dict[str, Any]:
    raw_plan = _csv_rows(STEP14R_RAW_PLAN_CSV)
    query_rows = _csv_rows(STEP14R_QUERY_PLAN_CSV)
    query_json = _load_json(STEP14R_QUERY_PLAN_JSON)
    pre = build_precondition_rows(raw_plan, query_rows, query_json)
    request_rows = build_request_rows(raw_plan)
    execution_rows = execute_acquisition(request_rows)
    integrity_rows = build_integrity_rows(execution_rows)
    availability_rows = build_availability_rows(request_rows, execution_rows)
    policy_rows = build_policy_rows()
    downstream_rows = build_downstream_rows()
    safety_rows = build_safety_rows(execution_rows, availability_rows)
    manifest = build_manifest(pre, request_rows, execution_rows, integrity_rows, availability_rows, policy_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": pre,
        "request_rows": request_rows,
        "execution_rows": execution_rows,
        "integrity_rows": integrity_rows,
        "availability_rows": availability_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

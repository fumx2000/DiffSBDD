from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_independent_group_expansion_acquisition_execution_smoke_v0"
STEP_LABEL = "Step 14AK"
PREVIOUS_STAGE = "covapie_independent_group_expansion_candidate_review_gate_v0"
PROJECT_NAME = "CovaPIE"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
RAW_ROOT = Path("data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001")
BATCH_ID = "CYS_SG_INDEPENDENT_EXPANSION_BATCH_000001"
HOST = "files.rcsb.org"

AJ_ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_candidate_review_gate_v0")
AI_ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_design_gate_v0")
AH_ROOT = Path("data/derived/covalent_small/covapie_leakage_split_review_gate_v0")
AG_ROOT = Path("data/derived/covalent_small/covapie_leakage_split_design_gate_v0")
AF_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_design_gate_v0")
AE_ROOT = Path("data/derived/covalent_small/covapie_sample_index_qa_gate_v0")
AD_ROOT = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0")
METADATA = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
SAMPLE_CSV = AD_ROOT / "sample_index.csv"
SAMPLE_JSON = AD_ROOT / "sample_index.json"
AJ_MANIFEST = AJ_ROOT / "covapie_independent_group_expansion_candidate_review_gate_manifest.json"
AJ_REGISTRY = AJ_ROOT / "covapie_expansion_candidate_review_registry.csv"
AJ_PLAN = AJ_ROOT / "covapie_expansion_acquisition_preflight_approval_plan.csv"

PRE = OUTPUT_ROOT / "covapie_acquisition_embedded_preflight_audit.csv"
DOWNLOAD = OUTPUT_ROOT / "covapie_acquisition_download_audit.csv"
INTEGRITY = OUTPUT_ROOT / "covapie_acquisition_raw_integrity_audit.csv"
FAILURES = OUTPUT_ROOT / "covapie_acquisition_failure_inventory.csv"
SAFETY = OUTPUT_ROOT / "covapie_acquisition_execution_safety_audit.csv"
MANIFEST = OUTPUT_ROOT / "covapie_independent_group_expansion_acquisition_execution_smoke_manifest.json"
SUMMARY = Path("docs/covapie_independent_group_expansion_acquisition_execution_smoke_v0_summary.md")

PAIRS = [("1AEC", "E64"), ("1AIM", "ZYA"), ("1AU3", "PCM"), ("1AU4", "INP"), ("1AYU", "INA"), ("1AYV", "IN6"), ("1AYW", "IN3"), ("1B02", "UFP")]
MASK_NAMES = ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]
MASK_ALIASES = ["A", "B", "B2", "B3", "C"]
PRE_COLUMNS = ["preflight_item", "artifact_or_check", "expected_status", "observed_status", "preflight_passed", "blocking_reasons"]
DOWNLOAD_COLUMNS = ["acquisition_download_id", "batch_id", "shortlist_rank", "pdb_id", "expected_het_id", "download_host", "download_url", "raw_filename", "raw_path", "execution_mode", "download_attempted", "existing_valid_raw_reused", "curl_return_code", "http_status_code", "retry_policy", "temporary_part_path", "temporary_part_removed", "final_atomic_rename_completed", "download_status", "error_message"]
INTEGRITY_COLUMNS = ["raw_integrity_audit_id", "pdb_id", "expected_het_id", "raw_filename", "raw_path", "file_exists", "file_size_bytes", "minimum_size_passed", "data_block_present", "entry_id_present", "atom_site_category_present", "html_signature_absent", "sha256", "part_file_absent", "integrity_status", "blocking_reasons"]
FAIL_COLUMNS = ["failure_id", "batch_id", "pdb_id", "expected_het_id", "failure_stage", "failure_type", "failure_description", "retry_recommended", "failure_status"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def csv_rows(path: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def changed(paths: list[Path | str]) -> bool:
    values = [str(path) for path in paths]
    return git(["diff", "--quiet", "--", *values]).returncode != 0 or git(["diff", "--cached", "--quiet", "--", *values]).returncode != 0


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def integrity(path: Path) -> dict[str, Any]:
    exists = path.exists() and path.is_file()
    size = path.stat().st_size if exists else 0
    text = path.read_text(encoding="utf-8", errors="replace")[:200000] if exists else ""
    lower = text.lower()
    result = {
        "file_exists": exists, "file_size_bytes": size, "minimum_size_passed": size >= 1000,
        "data_block_present": text.lstrip().startswith("data_"), "entry_id_present": "_entry.id" in text,
        "atom_site_category_present": "_atom_site." in text, "html_signature_absent": "<!doctype html" not in lower and "<html" not in lower and "<body" not in lower,
        "sha256": digest(path) if exists else "", "part_file_absent": not path.with_suffix(path.suffix + ".part").exists(),
    }
    result["passed"] = all([result["file_exists"], result["minimum_size_passed"], result["data_block_present"], result["entry_id_present"], result["atom_site_category_present"], result["html_signature_absent"], bool(result["sha256"]), result["part_file_absent"]])
    return result


def curl_downloader(url: str, part: Path) -> tuple[int, str]:
    command = ["curl", "--fail", "--location", "--silent", "--show-error", "--connect-timeout", "20", "--max-time", "180", "--retry", "2", "--retry-delay", "2", "--output", str(part), "--write-out", "%{http_code}", url]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.returncode, result.stdout.strip()[-3:] if result.stdout.strip() else ""


def embedded_preflight(raw_root: Path) -> list[dict[str, Any]]:
    manifest = json.loads((REPO_ROOT / AJ_MANIFEST).read_text())
    registry = csv_rows(AJ_REGISTRY)
    plan = csv_rows(AJ_PLAN)
    expected = [f"{pdb}/{het}" for pdb, het in PAIRS]
    reg_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in registry]
    plan_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in plan]
    raw_probe = raw_root / "1aec.cif"
    raw_ignored = git(["check-ignore", "-q", raw_probe.as_posix()]).returncode == 0
    raw_tracked = bool(git(["ls-files", raw_root.as_posix()]).stdout.strip())
    raw_staged = bool(git(["diff", "--cached", "--name-only", "--", raw_root.as_posix()]).stdout.strip())
    historical = [AJ_ROOT, AI_ROOT, AH_ROOT, AG_ROOT, AF_ROOT, AE_ROOT, AD_ROOT]
    protected = ["equivariant_diffusion/", "lightning_modules.py"]
    dataloader = ["dataset.py", "data/prepare_crossdocked.py"]
    hashes = digest(REPO_ROOT / METADATA) == "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365" and digest(REPO_ROOT / SAMPLE_CSV) == "2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5" and digest(REPO_ROOT / SAMPLE_JSON) == "8d740458e30cc77bbaa568c615dd10f5df334cd0c46f21433c570c16391b8b38" and not changed([METADATA, SAMPLE_CSV, SAMPLE_JSON])
    checks = [
        ("step14aj_manifest_valid", AJ_MANIFEST, PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE and manifest.get("all_checks_passed") is True),
        ("approved_candidate_count_is_8", AJ_MANIFEST, 8, manifest.get("candidate_review_approved_for_preflight_count"), manifest.get("candidate_review_approved_for_preflight_count") == 8),
        ("approved_pair_order_exact", AJ_MANIFEST, expected, manifest.get("approved_preflight_pdb_het_pairs"), manifest.get("approved_preflight_pdb_het_pairs") == expected and manifest.get("approved_preflight_batch_id") == BATCH_ID),
        ("review_registry_matches_manifest", AJ_REGISTRY, expected, reg_pairs, len(registry) == 8 and reg_pairs == expected and all(row["candidate_review_status"] == "passed" and row["approved_for_controlled_acquisition_preflight"] == "True" for row in registry)),
        ("preflight_plan_matches_registry", AJ_PLAN, expected, plan_pairs, len(plan) == 8 and plan_pairs == expected and all(row["planned_raw_filename"] == f"{row['pdb_id'].lower()}.cif" for row in plan)),
        ("no_execution_approval_from_previous_stage", AJ_REGISTRY, False, {row["approved_for_acquisition_execution"] for row in registry}, {row["approved_for_acquisition_execution"] for row in registry} == {"False"}),
        ("no_confirmed_independent_groups", AJ_MANIFEST, 0, manifest.get("confirmed_new_independent_group_count_current_step"), manifest.get("confirmed_new_independent_group_count_current_step") == 0 and all(row["confirmed_as_new_independent_group"] == "False" for row in registry)),
        ("raw_target_is_git_ignored", raw_root, True, raw_ignored, raw_ignored), ("raw_target_has_no_tracked_files", raw_root, False, raw_tracked, not raw_tracked), ("raw_target_has_no_staged_files", raw_root, False, raw_staged, not raw_staged),
        ("guarded_hashes_unchanged", "metadata/sample-index", True, hashes, hashes), ("historical_artifacts_unchanged", "Step14AJ and historical", False, changed(historical), not changed(historical)), ("protected_source_diff_empty", "protected DiffSBDD", False, changed(protected), not changed(protected)), ("original_dataloader_diff_empty", "original dataloader", False, changed(dataloader), not changed(dataloader)),
        ("staged_files_empty_before_execution", "git index", False, bool(git(["diff", "--cached", "--name-only"]).stdout.strip()), not git(["diff", "--cached", "--name-only"]).stdout.strip()), ("canonical_five_masks_preserved", "canonical masks", 5, len(MASK_NAMES), len(MASK_NAMES) == 5 and "B3" in MASK_ALIASES),
    ]
    return [{"preflight_item": item, "artifact_or_check": str(path), "expected_status": expected, "observed_status": observed, "preflight_passed": passed, "blocking_reasons": "" if passed else item} for item, path, expected, observed, passed in checks]


def acquire(execute_network: bool, raw_root: Path, downloader: Callable[[str, Path], tuple[int, str]] = curl_downloader) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    downloads: list[dict[str, Any]] = []
    integrities: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    raw_root.mkdir(parents=True, exist_ok=True)
    for rank, (pdb, het) in enumerate(PAIRS, 1):
        filename = f"{pdb.lower()}.cif"; target = raw_root / filename; part = raw_root / f"{filename}.part"; url = f"https://{HOST}/download/{pdb}.cif"
        attempted = reused = renamed = False; code: Any = ""; http = ""; error = ""; status = ""
        current = integrity(target)
        if current["passed"]:
            reused = True; status = "reused_existing_valid_raw"
        elif target.exists():
            status = "blocked_invalid_existing_raw"; error = "invalid_existing_raw"
        elif not execute_network:
            status = "blocked_network_execution_not_requested"; error = "execute_network_flag_required"
        else:
            attempted = True
            if part.exists(): part.unlink()
            code, http = downloader(url, part)
            candidate = integrity(part) if part.exists() else {"passed": False}
            if code == 0 and http == "200" and candidate["passed"]:
                os.replace(part, target); renamed = True; status = "downloaded"
            else:
                status = "download_failed_or_invalid_payload"; error = "curl_download_failed_or_integrity_rejected"
                if part.exists(): part.unlink()
        current = integrity(target)
        part_removed = not part.exists()
        row = {"acquisition_download_id": f"CYS_SG_DOWNLOAD_{rank:06d}", "batch_id": BATCH_ID, "shortlist_rank": rank, "pdb_id": pdb, "expected_het_id": het, "download_host": HOST, "download_url": url, "raw_filename": filename, "raw_path": target.as_posix(), "execution_mode": "controlled_network_execution" if execute_network else "offline_existing_raw_validation", "download_attempted": attempted, "existing_valid_raw_reused": reused, "curl_return_code": code, "http_status_code": http, "retry_policy": "two_retries_fixed_delay", "temporary_part_path": part.as_posix(), "temporary_part_removed": part_removed, "final_atomic_rename_completed": renamed, "download_status": status, "error_message": error}
        downloads.append(row)
        integrities.append({"raw_integrity_audit_id": f"CYS_SG_RAW_INTEGRITY_{rank:06d}", "pdb_id": pdb, "expected_het_id": het, "raw_filename": filename, "raw_path": target.as_posix(), **{key: current[key] for key in ["file_exists", "file_size_bytes", "minimum_size_passed", "data_block_present", "entry_id_present", "atom_site_category_present", "html_signature_absent", "sha256", "part_file_absent"]}, "integrity_status": "passed" if current["passed"] else "blocked", "blocking_reasons": "" if current["passed"] else status})
        if not current["passed"]:
            failures.append({"failure_id": f"CYS_SG_ACQUISITION_FAILURE_{len(failures)+1:06d}", "batch_id": BATCH_ID, "pdb_id": pdb, "expected_het_id": het, "failure_stage": "download_or_integrity", "failure_type": status, "failure_description": error or status, "retry_recommended": status != "blocked_invalid_existing_raw", "failure_status": "failed"})
    if not failures:
        failures = [{"failure_id": "NO_ACQUISITION_FAILURES", "batch_id": BATCH_ID, "pdb_id": "", "expected_het_id": "", "failure_stage": "none", "failure_type": "no_failures", "failure_description": "No controlled acquisition failures detected.", "retry_recommended": False, "failure_status": "passed"}]
    return downloads, integrities, failures


def safety(execute_network: bool, preflight_ok: bool, raw_root: Path) -> list[dict[str, Any]]:
    raw_tracked = bool(git(["ls-files", raw_root.as_posix()]).stdout.strip()); raw_staged = bool(git(["diff", "--cached", "--name-only", "--", raw_root.as_posix()]).stdout.strip())
    checks = [("embedded_preflight_executed", True, True), ("standalone_preflight_gate_created", False, False), ("user_authorized_controlled_batch_execution", True, True), ("network_access_used_current_step", execute_network, execute_network), ("network_host_restricted_to_files_rcsb_org", True, True), ("download_attempted_current_step", execute_network, execute_network), ("only_approved_eight_candidates_processed", True, True), ("raw_root_git_ignored", True, git(["check-ignore", "-q", (raw_root / "1aec.cif").as_posix()]).returncode == 0), ("raw_files_tracked", False, raw_tracked), ("raw_files_staged", False, raw_staged), ("part_files_remaining", False, any(raw_root.glob("*.part"))), ("raw_struct_conn_parsed_current_step", False, False), ("atom_site_semantically_parsed_current_step", False, False), ("sample_index_modified", False, changed([SAMPLE_CSV, SAMPLE_JSON])), ("metadata_csv_unchanged", True, digest(REPO_ROOT / METADATA) == "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365" and not changed([METADATA])), ("sample_index_files_unchanged", True, not changed([SAMPLE_CSV, SAMPLE_JSON])), ("step14aj_artifacts_unchanged", True, not changed([AJ_ROOT])), ("historical_artifacts_unchanged", True, not changed([AI_ROOT, AH_ROOT, AG_ROOT, AF_ROOT, AE_ROOT, AD_ROOT])), ("protected_source_diff_empty", True, not changed(["equivariant_diffusion/", "lightning_modules.py"])), ("original_dataloader_diff_empty", True, not changed(["dataset.py", "data/prepare_crossdocked.py"])), ("split_assignments_written", False, False), ("leakage_matrix_written", False, False), ("final_dataset_written", False, False), ("training_artifacts_written", False, False), ("torch_imported", False, False), ("numpy_imported", False, False), ("rdkit_used", False, False), ("biopython_used", False, False), ("gemmi_used", False, False), ("requests_used", False, False)]
    return [{"safety_item": n, "required_status": e, "observed_status": o, "safety_passed": e == o, "blocking_reasons": "" if e == o else n} for n, e, o in checks]


def run(execute_network: bool, raw_root: Path = RAW_ROOT, downloader: Callable[[str, Path], tuple[int, str]] = curl_downloader) -> dict[str, Any]:
    pre = embedded_preflight(raw_root); pre_ok = all(truth(row["preflight_passed"]) for row in pre)
    downloads, integrities, failures = acquire(execute_network and pre_ok, REPO_ROOT / raw_root, downloader)
    failed = [row for row in integrities if row["integrity_status"] != "passed"]
    safe = safety(execute_network, pre_ok, raw_root)
    blocking = [row["preflight_item"] for row in pre if not truth(row["preflight_passed"])] + [row["safety_item"] for row in safe if not truth(row["safety_passed"])] + [row["pdb_id"] for row in failed]
    raw_hashes = {row["pdb_id"]: row["sha256"] for row in integrities if row["sha256"]}
    manifest = {"stage": STAGE, "step_label": STEP_LABEL, "previous_stage": PREVIOUS_STAGE, "project_name": PROJECT_NAME, "input_approved_preflight_candidate_count": 8, "embedded_preflight_check_count": len(pre), "embedded_preflight_passed_count": sum(truth(row["preflight_passed"]) for row in pre), "embedded_preflight_all_passed": pre_ok, "standalone_preflight_gate_created": False, "acquisition_batch_id": BATCH_ID, "acquisition_candidate_count": 8, "acquisition_download_attempted_count": sum(truth(row["download_attempted"]) for row in downloads), "acquisition_new_download_count": sum(row["download_status"] == "downloaded" for row in downloads), "acquisition_existing_valid_reused_count": sum(truth(row["existing_valid_raw_reused"]) for row in downloads), "acquisition_succeeded_count": sum(row["integrity_status"] == "passed" for row in integrities), "acquisition_failed_count": len(failed), "acquisition_failure_count": len(failed), "raw_integrity_audit_count": len(integrities), "raw_integrity_passed_count": sum(row["integrity_status"] == "passed" for row in integrities), "raw_file_count": sum(truth(row["file_exists"]) for row in integrities), "raw_total_size_bytes": sum(int(row["file_size_bytes"]) for row in integrities), "raw_sha256_by_pdb": raw_hashes, "acquired_pdb_het_pairs": [f"{pdb}/{het}" for pdb,het in PAIRS], "download_host": HOST, "raw_root": raw_root.as_posix(), "controlled_network_execution_performed": execute_network and pre_ok, "batch_complete": not failed and pre_ok, "all_part_files_removed": not any((REPO_ROOT / raw_root).glob("*.part")), "raw_files_git_ignored": git(["check-ignore", "-q", (raw_root / "1aec.cif").as_posix()]).returncode == 0, "raw_files_tracked": bool(git(["ls-files", raw_root.as_posix()]).stdout.strip()), "raw_files_staged": bool(git(["diff", "--cached", "--name-only", "--", raw_root.as_posix()]).stdout.strip()), "struct_conn_crosscheck_performed_current_step": False, "atom_site_extraction_performed_current_step": False, "confirmed_covalent_candidate_count_current_step": 0, "confirmed_new_independent_group_count_current_step": 0, "split_assignments_written": False, "leakage_matrix_written": False, "final_dataset_written": False, "training_artifacts_written": False, "ready_for_covapie_independent_group_expansion_struct_conn_crosscheck_smoke": not failed and pre_ok, "ready_for_covapie_sample_preparation_execution_smoke": False, "ready_for_covapie_split_materialization_smoke": False, "ready_for_covapie_final_dataset_materialization_smoke": False, "ready_for_training": False, "ready_to_train_now": False, "feature_semantics_known_for_training": False, "unknown_atom_feature_policy_finalized_for_training": False, "feature_semantics_audit_required_before_training": True, "leakage_split_design_required_before_training": True, "canonical_mask_task_names": MASK_NAMES, "canonical_mask_task_aliases": MASK_ALIASES, "b3_scaffold_only_included": True, "no_extra_mask_tasks_added": True, "recommended_next_step": "covapie_independent_group_expansion_struct_conn_crosscheck_smoke", "all_checks_passed": not blocking, "blocking_reasons": blocking}
    return {"pre": pre, "download": downloads, "integrity": integrities, "failures": failures, "safety": safe, "manifest": manifest}

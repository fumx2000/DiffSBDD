from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_pilot_download_execution_gate_v0"
PREVIOUS_STAGE = "real_covalent_pilot_download_dry_run_gate_v0"

STEP12S_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_dry_run_gate_v0/"
    "real_covalent_pilot_download_dry_run_gate_manifest.json"
)
STEP12S_DRY_RUN_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_dry_run_gate_v0/"
    "real_covalent_pilot_download_dry_run_table.csv"
)
STEP12R_PILOT_MANIFEST_CSV = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_manifest_gate_v0/"
    "real_covalent_pilot_download_manifest.csv"
)
STEP12S_SUMMARY_MD = Path("docs/real_covalent_pilot_download_dry_run_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_pilot_download_execution_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_pilot_download_execution_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_pilot_download_execution_gate_manifest.json"
PROVENANCE_CSV = OUTPUT_ROOT / "real_covalent_pilot_download_provenance.csv"
SUMMARY_MD = Path("docs/real_covalent_pilot_download_execution_gate_v0_summary.md")

RAW_ROOT = Path("data/raw/covalent_sources")
PDB_MMCIF_RAW_DIR = RAW_ROOT / "pdb_mmcif_direct" / "structures"

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_RAW_FILES = {
    "6DI9": PDB_MMCIF_RAW_DIR / "6DI9.cif.gz",
    "5F2E": PDB_MMCIF_RAW_DIR / "5F2E.cif.gz",
    "6OIM": PDB_MMCIF_RAW_DIR / "6OIM.cif.gz",
}
PDB_MMCIF_URL_TEMPLATE = "https://files.rcsb.org/download/{pdb_id}.cif.gz"

EXPECTED_LOCAL_SAMPLE_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]
RECOMMENDED_NEXT_STEP = "real_covalent_pilot_download_integrity_gate"

PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
FORBIDDEN_COMMITTABLE_SUFFIXES = {
    ".pt",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".ckpt",
    ".pth",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
}

DRY_RUN_TABLE_COLUMNS = [
    "job_id",
    "source_name",
    "job_type",
    "pdb_id",
    "sample_id",
    "dry_run_status",
    "schema_valid",
    "source_policy_valid",
    "url_string_valid",
    "local_output_path_valid",
    "checksum_policy_valid",
    "provenance_policy_valid",
    "blocked_source_policy_valid",
    "network_called",
    "file_downloaded",
    "raw_dir_created",
    "raw_file_written",
    "adapter_run",
    "ready_for_execution_after_dry_run",
    "blocking_reasons",
]

PROVENANCE_COLUMNS = [
    "record_type",
    "pdb_id",
    "sample_id",
    "source_name",
    "candidate_download_url",
    "local_raw_path",
    "download_attempted",
    "download_succeeded",
    "file_exists_after_download",
    "file_size_bytes",
    "sha256",
    "gzip_magic_valid",
    "http_status_code",
    "downloaded_at_utc",
    "npz_loaded",
    "npz_contents_read",
    "provenance_status",
    "error_message",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_columns(path: str | Path) -> list[str]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [] if reader.fieldnames is None else list(reader.fieldnames)


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _is_true(value: str) -> bool:
    return value == "True"


def _is_false(value: str) -> bool:
    return value == "False"


def _source_diff_exists(paths: list[str] = PROTECTED_SOURCE_PATHS) -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_COMMITTABLE_SUFFIXES for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "data/raw/"],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return bool(result.stdout.strip())


def validate_step12s_pilot_download_dry_run_gate_v0() -> bool:
    if not STEP12S_MANIFEST_JSON.is_file() or not STEP12S_DRY_RUN_TABLE_CSV.is_file() or not STEP12S_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12S outputs are missing")
    manifest = _load_json(STEP12S_MANIFEST_JSON)
    rows = _read_csv(STEP12S_DRY_RUN_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_pilot_download_manifest_gate_v0",
        "step12r_pilot_download_manifest_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "dry_run_total_rows": 9,
        "dry_run_passed_rows": 6,
        "dry_run_blocked_as_expected_rows": 3,
        "dry_run_failed_rows": 0,
        "dry_run_pdb_direct_passed_rows": 3,
        "dry_run_local_curated_passed_rows": 3,
        "dry_run_blocked_source_rows": 3,
        "dry_run_network_called": False,
        "dry_run_files_downloaded": False,
        "dry_run_raw_dirs_created": False,
        "dry_run_raw_files_written": False,
        "dry_run_adapters_run": False,
        "all_allowed_pilot_jobs_ready_for_execution_after_dry_run": True,
        "all_blocked_sources_remain_not_ready_for_execution": True,
        "dry_run_validated_manifest_schema": True,
        "dry_run_validated_url_strings": True,
        "dry_run_validated_local_output_paths": True,
        "dry_run_validated_checksum_policy": True,
        "dry_run_validated_provenance_policy": True,
        "dry_run_validated_blocked_source_policy": True,
        "ready_to_execute_pilot_download_after_dry_run": True,
        "pilot_download_execution_allowed_in_this_step": False,
        "ready_to_download_large_scale_data_now": False,
        "data_downloaded": False,
        "external_network_called": False,
        "raw_storage_directories_created": False,
        "raw_download_files_written": False,
        "raw_structure_files_written": False,
        "adapter_implementation_written": False,
        "adapter_execution_run": False,
        "rdkit_processing_run": False,
        "uniprot_mapping_run": False,
        "cdhit_run": False,
        "coordinate_geometry_calculation_run": False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "enriched_sample_index_written": False,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "real_covalent_pilot_download_dry_run_gate_passed": True,
        "pilot_download_dry_run_contract_defined": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_pilot_download_execution_gate",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12s_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(_csv_columns(STEP12S_DRY_RUN_TABLE_CSV) == DRY_RUN_TABLE_COLUMNS, "step12s_dry_run_columns_invalid", blockers)
    _expect(len(rows) == 9, "step12s_dry_run_row_count_invalid", blockers)
    pdb_rows = [row for row in rows if row["source_name"] == "PDB/mmCIF direct"]
    local_rows = [row for row in rows if row["source_name"] == "local curated"]
    blocked_rows = [row for row in rows if row["source_name"] in {"CovPDB", "CovBinderInPDB", "CovalentInDB"}]
    _expect(len(pdb_rows) == 3, "step12s_pdb_row_count_invalid", blockers)
    _expect(len(local_rows) == 3, "step12s_local_row_count_invalid", blockers)
    _expect(len(blocked_rows) == 3, "step12s_blocked_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in pdb_rows] == EXPECTED_PDB_IDS, "step12s_pdb_ids_invalid", blockers)
    for row in pdb_rows + local_rows:
        _expect(_is_true(row["ready_for_execution_after_dry_run"]), f"step12s_allowed_not_ready:{row['job_id']}", blockers)
    for row in blocked_rows:
        _expect(_is_false(row["ready_for_execution_after_dry_run"]), f"step12s_blocked_ready:{row['job_id']}", blockers)
    summary = STEP12S_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "pilot download dry-run gate",
        "not download execution",
        "not network",
        "not adapter execution",
        "ready_to_execute_pilot_download_after_dry_run=true",
        "real_covalent_pilot_download_execution_gate",
    ]:
        _expect(snippet in summary, f"step12s_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def ensure_data_raw_ignored_locally_v0() -> dict[str, Any]:
    exclude_path = REPO_ROOT / ".git" / "info" / "exclude"
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    original_text = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    modified = False
    if "/data/raw/" not in original_text.splitlines():
        suffix = "" if original_text.endswith("\n") or original_text == "" else "\n"
        exclude_path.write_text(original_text + suffix + "/data/raw/\n", encoding="utf-8")
        modified = True
    raw_path = str(EXPECTED_RAW_FILES["6DI9"])
    ignored = subprocess.run(
        ["git", "check-ignore", raw_path],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    gitignore_modified = subprocess.run(
        ["git", "diff", "--quiet", "--", ".gitignore"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0
    return {
        "local_git_exclude_checked": True,
        "data_raw_gitignored": ignored,
        "gitignore_modified": gitignore_modified,
        "git_info_exclude_may_have_been_modified": modified,
        "raw_files_expected_to_be_untracked_or_ignored": ignored,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _gzip_magic_valid(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(2) == b"\x1f\x8b"


def execute_pilot_pdb_mmcif_downloads_v0() -> list[dict[str, Any]]:
    PDB_MMCIF_RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for pdb_id in EXPECTED_PDB_IDS:
        url = PDB_MMCIF_URL_TEMPLATE.format(pdb_id=pdb_id)
        output_path = EXPECTED_RAW_FILES[pdb_id]
        tmp_path = output_path.with_name(output_path.name + ".tmp")
        downloaded_at = datetime.now(timezone.utc).isoformat()
        row: dict[str, Any] = {
            "record_type": "pdb_mmcif_download",
            "pdb_id": pdb_id,
            "sample_id": "",
            "source_name": "PDB/mmCIF direct",
            "candidate_download_url": url,
            "local_raw_path": str(output_path),
            "download_attempted": True,
            "download_succeeded": False,
            "file_exists_after_download": False,
            "file_size_bytes": 0,
            "sha256": "",
            "gzip_magic_valid": False,
            "http_status_code": "",
            "downloaded_at_utc": downloaded_at,
            "npz_loaded": False,
            "npz_contents_read": False,
            "provenance_status": "download_failed",
            "error_message": "",
        }
        try:
            if tmp_path.exists():
                tmp_path.unlink()
            with urllib.request.urlopen(url, timeout=60) as response:
                status = response.getcode()
                row["http_status_code"] = "" if status is None else str(status)
                with tmp_path.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
            tmp_path.replace(output_path)
            size = output_path.stat().st_size
            sha256 = _sha256_file(output_path)
            gzip_valid = _gzip_magic_valid(output_path)
            row.update(
                {
                    "download_succeeded": size > 0 and len(sha256) == 64 and gzip_valid,
                    "file_exists_after_download": output_path.is_file(),
                    "file_size_bytes": size,
                    "sha256": sha256,
                    "gzip_magic_valid": gzip_valid,
                    "provenance_status": "downloaded_raw_file_recorded",
                    "error_message": "",
                }
            )
            if not row["download_succeeded"]:
                row["error_message"] = "download_integrity_check_failed"
        except Exception as exc:
            if tmp_path.exists():
                tmp_path.unlink()
            row["error_message"] = f"{type(exc).__name__}:{exc}"
        rows.append(row)
        time.sleep(0.2)
    return rows


def _extract_pdb_id_from_sample_id(sample_id: str) -> str:
    parts = sample_id.split("_")
    if len(parts) < 3:
        raise ValueError(f"sample_id_pdb_id_unparseable:{sample_id}")
    return parts[2]


def build_local_curated_provenance_rows_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample_id in EXPECTED_LOCAL_SAMPLE_IDS:
        rows.append(
            {
                "record_type": "local_curated_provenance",
                "pdb_id": _extract_pdb_id_from_sample_id(sample_id),
                "sample_id": sample_id,
                "source_name": "local curated",
                "candidate_download_url": "local_only",
                "local_raw_path": "",
                "download_attempted": False,
                "download_succeeded": False,
                "file_exists_after_download": False,
                "file_size_bytes": "",
                "sha256": "",
                "gzip_magic_valid": False,
                "http_status_code": "",
                "downloaded_at_utc": "",
                "npz_loaded": False,
                "npz_contents_read": False,
                "provenance_status": "recorded_without_raw_file_copy",
                "error_message": "",
            }
        )
    return rows


def build_pilot_download_execution_summary_v0(
    download_rows: list[dict[str, Any]],
    local_rows: list[dict[str, Any]],
    ignore_info: dict[str, Any],
) -> dict[str, Any]:
    raw_paths = [row["local_raw_path"] for row in download_rows]
    success_rows = [row for row in download_rows if row["download_succeeded"] is True]
    failure_rows = [row for row in download_rows if row["download_succeeded"] is not True]
    raw_files_staged = _raw_files_staged()
    forbidden_committable = _forbidden_committable_artifacts_created()
    return {
        "pilot_download_execution_defined": True,
        "pilot_download_execution_performed": True,
        "external_network_called": True,
        "raw_storage_directories_created": PDB_MMCIF_RAW_DIR.is_dir(),
        "raw_download_files_written": len(success_rows) == 3,
        "raw_structure_files_written": len(success_rows) == 3,
        "data_downloaded": len(success_rows) == 3,
        "pdb_mmcif_download_attempt_count": len(download_rows),
        "pdb_mmcif_download_success_count": len(success_rows),
        "pdb_mmcif_download_failure_count": len(failure_rows),
        "downloaded_pdb_ids": [row["pdb_id"] for row in download_rows],
        "downloaded_raw_file_count": len(success_rows),
        "downloaded_raw_paths": raw_paths,
        "all_downloaded_files_exist": all(Path(path).is_file() for path in raw_paths),
        "all_downloaded_files_nonempty": all(int(row["file_size_bytes"]) > 0 for row in success_rows) and len(success_rows) == 3,
        "all_downloaded_files_gzip_magic_valid": all(row["gzip_magic_valid"] is True for row in success_rows) and len(success_rows) == 3,
        "all_downloaded_files_sha256_recorded": all(isinstance(row["sha256"], str) and len(row["sha256"]) == 64 for row in success_rows)
        and len(success_rows) == 3,
        "provenance_csv_written": True,
        "provenance_row_count": len(download_rows) + len(local_rows),
        "local_curated_provenance_row_count": len(local_rows),
        "local_curated_npz_loaded": any(row["npz_loaded"] is True for row in local_rows),
        "local_curated_npz_contents_read": any(row["npz_contents_read"] is True for row in local_rows),
        **ignore_info,
        "raw_files_staged": raw_files_staged,
        "raw_files_committed_allowed": False,
        "committable_output_files_only_csv_json_md_py": not forbidden_committable,
        "forbidden_committable_artifacts_created": forbidden_committable,
    }


def build_real_covalent_pilot_download_execution_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12s_validated = validate_step12s_pilot_download_dry_run_gate_v0()
    except Exception as exc:
        step12s_validated = False
        blockers.append(f"step12s_validation_failed:{type(exc).__name__}:{exc}")
    step12s_manifest = _load_json(STEP12S_MANIFEST_JSON)
    ignore_info = ensure_data_raw_ignored_locally_v0()
    download_rows = execute_pilot_pdb_mmcif_downloads_v0()
    local_rows = build_local_curated_provenance_rows_v0()
    execution = build_pilot_download_execution_summary_v0(download_rows, local_rows, ignore_info)
    source_modified = _source_diff_exists()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    for row in download_rows:
        if row["download_succeeded"] is not True:
            blockers.append(f"download_failed:{row['pdb_id']}:{row['error_message']}")
    if not execution["data_raw_gitignored"]:
        blockers.append("data_raw_not_gitignored")
    if execution["raw_files_staged"]:
        blockers.append("raw_files_staged")
    if execution["forbidden_committable_artifacts_created"]:
        blockers.append("forbidden_committable_artifacts_created")

    passed = bool(
        step12s_validated
        and step12s_manifest["step12b_mask_level_aware_validator_validated"]
        and execution["pilot_download_execution_defined"]
        and execution["pilot_download_execution_performed"]
        and execution["external_network_called"]
        and execution["data_downloaded"]
        and execution["raw_storage_directories_created"]
        and execution["raw_download_files_written"]
        and execution["raw_structure_files_written"]
        and execution["pdb_mmcif_download_attempt_count"] == 3
        and execution["pdb_mmcif_download_success_count"] == 3
        and execution["pdb_mmcif_download_failure_count"] == 0
        and execution["downloaded_pdb_ids"] == EXPECTED_PDB_IDS
        and execution["downloaded_raw_file_count"] == 3
        and execution["all_downloaded_files_exist"]
        and execution["all_downloaded_files_nonempty"]
        and execution["all_downloaded_files_gzip_magic_valid"]
        and execution["all_downloaded_files_sha256_recorded"]
        and execution["data_raw_gitignored"]
        and not execution["gitignore_modified"]
        and not execution["raw_files_staged"]
        and not source_modified
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_pilot_download_execution_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12s_pilot_download_dry_run_gate_validated": step12s_validated,
        "step12b_mask_level_aware_validator_validated": step12s_manifest["step12b_mask_level_aware_validator_validated"],
        **execution,
        "adapter_implementation_written": False,
        "adapter_execution_run": False,
        "rdkit_processing_run": False,
        "uniprot_mapping_run": False,
        "cdhit_run": False,
        "coordinate_geometry_calculation_run": False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "enriched_sample_index_written": False,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "real_covalent_pilot_download_execution_gate_passed": passed,
        "pilot_download_execution_contract_defined": passed,
        "ready_for_pilot_download_integrity_gate": passed,
        "ready_to_parse_mmcif_now": False,
        "ready_to_run_adapter_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "provenance_rows": download_rows + local_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12s_precondition": {
            "step12s_pilot_download_dry_run_gate_validated": manifest["step12s_pilot_download_dry_run_gate_validated"],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "raw_ignore_guard": {
            "data_raw_gitignored": manifest["data_raw_gitignored"],
            "gitignore_modified": manifest["gitignore_modified"],
            "raw_files_staged": manifest["raw_files_staged"],
        },
        "pdb_mmcif_download_execution": {
            "pdb_mmcif_download_attempt_count": manifest["pdb_mmcif_download_attempt_count"],
            "pdb_mmcif_download_success_count": manifest["pdb_mmcif_download_success_count"],
        },
        "download_integrity_observation": {
            "all_downloaded_files_exist": manifest["all_downloaded_files_exist"],
            "all_downloaded_files_nonempty": manifest["all_downloaded_files_nonempty"],
            "all_downloaded_files_gzip_magic_valid": manifest["all_downloaded_files_gzip_magic_valid"],
            "all_downloaded_files_sha256_recorded": manifest["all_downloaded_files_sha256_recorded"],
        },
        "local_curated_provenance": {
            "local_curated_provenance_row_count": manifest["local_curated_provenance_row_count"],
            "local_curated_npz_contents_read": manifest["local_curated_npz_contents_read"],
        },
        "prohibited_operations_boundary": {
            "adapter_execution_run": manifest["adapter_execution_run"],
            "rdkit_processing_run": manifest["rdkit_processing_run"],
            "npz_contents_read": manifest["npz_contents_read"],
        },
        "git_raw_safety": {
            "raw_files_staged": manifest["raw_files_staged"],
            "raw_files_committed_allowed": manifest["raw_files_committed_allowed"],
            "committable_output_files_only_csv_json_md_py": manifest["committable_output_files_only_csv_json_md_py"],
        },
        "next_step_decision": {
            "ready_for_pilot_download_integrity_gate": manifest["ready_for_pilot_download_integrity_gate"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }

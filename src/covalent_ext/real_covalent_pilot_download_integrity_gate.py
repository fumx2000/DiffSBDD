from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_pilot_download_integrity_gate_v0"
PREVIOUS_STAGE = "real_covalent_pilot_download_execution_gate_v0"

STEP12T_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_execution_gate_v0/"
    "real_covalent_pilot_download_execution_gate_manifest.json"
)
STEP12T_PROVENANCE_CSV = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_execution_gate_v0/"
    "real_covalent_pilot_download_provenance.csv"
)
STEP12T_SUMMARY_MD = Path("docs/real_covalent_pilot_download_execution_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_pilot_download_integrity_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_pilot_download_integrity_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_pilot_download_integrity_gate_manifest.json"
RAW_FILE_INTEGRITY_TABLE_CSV = OUTPUT_ROOT / "real_covalent_raw_file_integrity_table.csv"
SUMMARY_MD = Path("docs/real_covalent_pilot_download_integrity_gate_v0_summary.md")

RAW_ROOT = Path("data/raw/covalent_sources")
PDB_MMCIF_RAW_DIR = RAW_ROOT / "pdb_mmcif_direct" / "structures"

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]

EXPECTED_RAW_FILE_INFO = {
    "6DI9": {
        "path": PDB_MMCIF_RAW_DIR / "6DI9.cif.gz",
        "size_bytes": 75224,
        "sha256": "437901f354373a1cf5d20446e03409ed504899e8140a7ad819f2b609c6c5f81e",
    },
    "5F2E": {
        "path": PDB_MMCIF_RAW_DIR / "5F2E.cif.gz",
        "size_bytes": 97317,
        "sha256": "681eac8977ae235823a963ed859a0b76e923269361da8191c72f51b0d6411f58",
    },
    "6OIM": {
        "path": PDB_MMCIF_RAW_DIR / "6OIM.cif.gz",
        "size_bytes": 59163,
        "sha256": "fb1594808cb5ce47fe60260b8b28ac3bb8fb1d10dfd6759ca96bade5d4b67241",
    },
}

EXPECTED_LOCAL_SAMPLE_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]

RECOMMENDED_NEXT_STEP = "real_covalent_minimal_mmcif_parser_design_gate"

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

RAW_FILE_INTEGRITY_COLUMNS = [
    "pdb_id",
    "raw_path",
    "expected_size_bytes",
    "observed_size_bytes",
    "expected_sha256",
    "observed_sha256",
    "file_exists",
    "file_nonempty",
    "size_matches_expected",
    "sha256_matches_expected",
    "gzip_magic_valid",
    "path_under_data_raw",
    "git_check_ignore_passed",
    "git_staged",
    "git_tracked",
    "raw_commit_allowed",
    "mmcif_decompressed",
    "mmcif_parsed",
    "integrity_status",
    "blocking_reasons",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _is_true(value: str) -> bool:
    return value == "True"


def _is_false(value: str) -> bool:
    return value == "False"


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _source_diff_exists(paths: list[str] = PROTECTED_SOURCE_PATHS) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths])
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_COMMITTABLE_SUFFIXES for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/"]).stdout.strip())


def _path_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to((REPO_ROOT / root).resolve())
    except ValueError:
        return False
    return True


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _compressed_magic_valid(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(2) == b"\x1f\x8b"


def validate_step12t_pilot_download_execution_gate_v0() -> bool:
    if not STEP12T_MANIFEST_JSON.is_file() or not STEP12T_PROVENANCE_CSV.is_file() or not STEP12T_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12T outputs are missing")
    manifest = _load_json(STEP12T_MANIFEST_JSON)
    provenance_rows = _read_csv(STEP12T_PROVENANCE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_pilot_download_dry_run_gate_v0",
        "step12s_pilot_download_dry_run_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "pilot_download_execution_defined": True,
        "pilot_download_execution_performed": True,
        "external_network_called": True,
        "data_downloaded": True,
        "raw_storage_directories_created": True,
        "raw_download_files_written": True,
        "raw_structure_files_written": True,
        "pdb_mmcif_download_attempt_count": 3,
        "pdb_mmcif_download_success_count": 3,
        "pdb_mmcif_download_failure_count": 0,
        "downloaded_pdb_ids": EXPECTED_PDB_IDS,
        "downloaded_raw_file_count": 3,
        "all_downloaded_files_exist": True,
        "all_downloaded_files_nonempty": True,
        "all_downloaded_files_gzip_magic_valid": True,
        "all_downloaded_files_sha256_recorded": True,
        "provenance_csv_written": True,
        "provenance_row_count": 6,
        "local_curated_provenance_row_count": 3,
        "local_curated_npz_loaded": False,
        "local_curated_npz_contents_read": False,
        "data_raw_gitignored": True,
        "raw_files_staged": False,
        "raw_files_committed_allowed": False,
        "committable_output_files_only_csv_json_md_py": True,
        "forbidden_committable_artifacts_created": False,
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
        "real_covalent_pilot_download_execution_gate_passed": True,
        "pilot_download_execution_contract_defined": True,
        "ready_for_pilot_download_integrity_gate": True,
        "ready_to_parse_mmcif_now": False,
        "ready_to_run_adapter_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_pilot_download_integrity_gate",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12t_{key}_invalid:{manifest[key]!r}", blockers)

    _expect(len(provenance_rows) == 6, "step12t_provenance_row_count_invalid", blockers)
    pdb_rows = [row for row in provenance_rows if row["record_type"] == "pdb_mmcif_download"]
    local_rows = [row for row in provenance_rows if row["record_type"] == "local_curated_provenance"]
    _expect(len(pdb_rows) == 3, "step12t_pdb_provenance_row_count_invalid", blockers)
    _expect(len(local_rows) == 3, "step12t_local_provenance_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in pdb_rows] == EXPECTED_PDB_IDS, "step12t_pdb_ids_invalid", blockers)
    for row in pdb_rows:
        info = EXPECTED_RAW_FILE_INFO[row["pdb_id"]]
        _expect(_is_true(row["download_attempted"]), f"step12t_download_not_attempted:{row['pdb_id']}", blockers)
        _expect(_is_true(row["download_succeeded"]), f"step12t_download_not_succeeded:{row['pdb_id']}", blockers)
        _expect(_is_true(row["file_exists_after_download"]), f"step12t_download_file_missing:{row['pdb_id']}", blockers)
        _expect(int(row["file_size_bytes"]) == info["size_bytes"], f"step12t_size_invalid:{row['pdb_id']}", blockers)
        _expect(row["sha256"] == info["sha256"], f"step12t_sha_invalid:{row['pdb_id']}", blockers)
        _expect(_is_true(row["gzip_magic_valid"]), f"step12t_magic_invalid:{row['pdb_id']}", blockers)
        _expect(row["provenance_status"] == "downloaded_raw_file_recorded", f"step12t_status_invalid:{row['pdb_id']}", blockers)
    for row in local_rows:
        _expect(_is_false(row["npz_loaded"]), f"step12t_local_npz_loaded:{row['sample_id']}", blockers)
        _expect(_is_false(row["npz_contents_read"]), f"step12t_local_npz_read:{row['sample_id']}", blockers)
        _expect(
            row["provenance_status"] == "recorded_without_raw_file_copy",
            f"step12t_local_status_invalid:{row['sample_id']}",
            blockers,
        )
    summary = STEP12T_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "pilot download execution gate",
        "actually used the network",
        "6DI9",
        "5F2E",
        "6OIM",
        "Raw files are not committed and must never be committed",
        "SHA256",
        "file size",
        "gzip magic validation",
        "download provenance",
        "No mmCIF parsing",
        "No adapters",
        "RDKit/UniProt/CD-HIT/geometry",
        "training",
        "real_covalent_pilot_download_integrity_gate",
        "should still not parse mmCIF",
    ]:
        _expect(snippet in summary, f"step12t_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def recompute_raw_file_integrity_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pdb_id in EXPECTED_PDB_IDS:
        info = EXPECTED_RAW_FILE_INFO[pdb_id]
        raw_path = Path(info["path"])
        absolute_path = REPO_ROOT / raw_path
        blockers: list[str] = []
        file_exists = absolute_path.is_file()
        observed_size = absolute_path.stat().st_size if file_exists else 0
        observed_sha = _sha256_file(absolute_path) if file_exists else ""
        magic_valid = _compressed_magic_valid(absolute_path) if file_exists else False
        git_check_ignore_passed = _run_git(["check-ignore", str(raw_path)]).returncode == 0
        git_staged = str(raw_path) in _run_git(["diff", "--cached", "--name-only", "--", str(raw_path)]).stdout.splitlines()
        git_tracked = _run_git(["ls-files", "--error-unmatch", str(raw_path)]).returncode == 0
        size_matches = observed_size == info["size_bytes"]
        sha_matches = observed_sha == info["sha256"]
        path_under_data_raw = _path_under(raw_path, RAW_ROOT)
        checks = {
            "file_missing": file_exists,
            "file_empty": observed_size > 0,
            "size_mismatch": size_matches,
            "sha256_mismatch": sha_matches,
            "gzip_magic_invalid": magic_valid,
            "path_not_under_data_raw": path_under_data_raw,
            "git_check_ignore_failed": git_check_ignore_passed,
            "raw_file_staged": not git_staged,
            "raw_file_tracked": not git_tracked,
        }
        for reason, passed in checks.items():
            if not passed:
                blockers.append(reason)
        rows.append(
            {
                "pdb_id": pdb_id,
                "raw_path": str(raw_path),
                "expected_size_bytes": info["size_bytes"],
                "observed_size_bytes": observed_size,
                "expected_sha256": info["sha256"],
                "observed_sha256": observed_sha,
                "file_exists": file_exists,
                "file_nonempty": observed_size > 0,
                "size_matches_expected": size_matches,
                "sha256_matches_expected": sha_matches,
                "gzip_magic_valid": magic_valid,
                "path_under_data_raw": path_under_data_raw,
                "git_check_ignore_passed": git_check_ignore_passed,
                "git_staged": git_staged,
                "git_tracked": git_tracked,
                "raw_commit_allowed": False,
                "mmcif_decompressed": False,
                "mmcif_parsed": False,
                "integrity_status": "passed" if not blockers else "failed",
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def build_git_raw_safety_summary_v0(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gitignore_modified = _run_git(["diff", "--quiet", "--", ".gitignore"]).returncode != 0
    return {
        "raw_file_integrity_table_written": True,
        "raw_file_integrity_row_count": len(rows),
        "all_raw_files_exist": all(row["file_exists"] for row in rows),
        "all_raw_files_nonempty": all(row["file_nonempty"] for row in rows),
        "all_raw_file_sizes_match_expected": all(row["size_matches_expected"] for row in rows),
        "all_raw_sha256_match_expected": all(row["sha256_matches_expected"] for row in rows),
        "all_raw_gzip_magic_valid": all(row["gzip_magic_valid"] for row in rows),
        "all_raw_paths_under_data_raw": all(row["path_under_data_raw"] for row in rows),
        "all_raw_files_gitignored": all(row["git_check_ignore_passed"] for row in rows),
        "no_raw_files_staged": not any(row["git_staged"] for row in rows) and not _raw_files_staged(),
        "no_raw_files_tracked": not any(row["git_tracked"] for row in rows),
        "raw_files_commit_allowed": False,
        "data_raw_gitignore_is_local_exclude_only": not gitignore_modified and all(row["git_check_ignore_passed"] for row in rows),
        "gitignore_modified": gitignore_modified,
    }


def build_provenance_cross_check_summary_v0(
    raw_rows: list[dict[str, Any]], provenance_rows: list[dict[str, str]]
) -> dict[str, Any]:
    raw_by_pdb = {row["pdb_id"]: row for row in raw_rows}
    pdb_rows = [row for row in provenance_rows if row["record_type"] == "pdb_mmcif_download"]
    local_rows = [row for row in provenance_rows if row["record_type"] == "local_curated_provenance"]
    rows_match = (
        [row["pdb_id"] for row in pdb_rows] == EXPECTED_PDB_IDS
        and all(row["local_raw_path"] == raw_by_pdb[row["pdb_id"]]["raw_path"] for row in pdb_rows)
        and all(_is_true(row["file_exists_after_download"]) for row in pdb_rows)
    )
    sha_match = all(row["sha256"] == raw_by_pdb[row["pdb_id"]]["observed_sha256"] for row in pdb_rows)
    size_match = all(int(row["file_size_bytes"]) == raw_by_pdb[row["pdb_id"]]["observed_size_bytes"] for row in pdb_rows)
    local_without_npz = all(
        row["provenance_status"] == "recorded_without_raw_file_copy"
        and _is_false(row["npz_loaded"])
        and _is_false(row["npz_contents_read"])
        for row in local_rows
    )
    passed = len(provenance_rows) == 6 and len(pdb_rows) == 3 and len(local_rows) == 3 and rows_match and sha_match and size_match and local_without_npz
    return {
        "provenance_cross_check_defined": True,
        "provenance_csv_read": True,
        "provenance_row_count": len(provenance_rows),
        "pdb_download_provenance_row_count": len(pdb_rows),
        "local_curated_provenance_row_count": len(local_rows),
        "all_pdb_download_rows_match_raw_files": rows_match,
        "all_pdb_download_rows_sha256_match_raw_recompute": sha_match,
        "all_pdb_download_rows_size_match_raw_recompute": size_match,
        "all_local_curated_rows_recorded_without_npz_read": local_without_npz,
        "provenance_cross_check_passed": passed,
    }


def build_real_covalent_pilot_download_integrity_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12t_validated = validate_step12t_pilot_download_execution_gate_v0()
    except Exception as exc:
        step12t_validated = False
        blockers.append(f"step12t_validation_failed:{type(exc).__name__}:{exc}")
    step12t_manifest = _load_json(STEP12T_MANIFEST_JSON)
    provenance_rows = _read_csv(STEP12T_PROVENANCE_CSV)
    raw_rows = recompute_raw_file_integrity_v0()
    git_summary = build_git_raw_safety_summary_v0(raw_rows)
    provenance_summary = build_provenance_cross_check_summary_v0(raw_rows, provenance_rows)
    source_modified = _source_diff_exists()
    forbidden_committable = _forbidden_committable_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_committable:
        blockers.append("forbidden_committable_artifacts_created")
    for row in raw_rows:
        if row["integrity_status"] != "passed":
            blockers.append(f"raw_integrity_failed:{row['pdb_id']}:{row['blocking_reasons']}")
    if not provenance_summary["provenance_cross_check_passed"]:
        blockers.append("provenance_cross_check_failed")

    passed = bool(
        step12t_validated
        and step12t_manifest["step12b_mask_level_aware_validator_validated"]
        and git_summary["raw_file_integrity_row_count"] == 3
        and git_summary["all_raw_files_exist"]
        and git_summary["all_raw_files_nonempty"]
        and git_summary["all_raw_file_sizes_match_expected"]
        and git_summary["all_raw_sha256_match_expected"]
        and git_summary["all_raw_gzip_magic_valid"]
        and git_summary["all_raw_paths_under_data_raw"]
        and git_summary["all_raw_files_gitignored"]
        and git_summary["no_raw_files_staged"]
        and git_summary["no_raw_files_tracked"]
        and not git_summary["raw_files_commit_allowed"]
        and git_summary["data_raw_gitignore_is_local_exclude_only"]
        and not git_summary["gitignore_modified"]
        and provenance_summary["provenance_cross_check_passed"]
        and not source_modified
        and not forbidden_committable
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_pilot_download_integrity_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12t_pilot_download_execution_gate_validated": step12t_validated,
        "step12b_mask_level_aware_validator_validated": step12t_manifest["step12b_mask_level_aware_validator_validated"],
        **git_summary,
        **provenance_summary,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "raw_storage_directories_created": False,
        "raw_download_files_written": False,
        "raw_structure_files_written": False,
        "mmcif_decompressed": False,
        "mmcif_parsed": False,
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
        "forbidden_committable_artifacts_created": forbidden_committable,
        "real_covalent_pilot_download_integrity_gate_passed": passed,
        "pilot_download_integrity_contract_defined": passed,
        "ready_for_minimal_mmcif_parser_design_gate": passed,
        "ready_to_parse_mmcif_now": False,
        "ready_to_run_adapter_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "raw_file_integrity_rows": raw_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12t_precondition": {
            "step12t_pilot_download_execution_gate_validated": manifest["step12t_pilot_download_execution_gate_validated"],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "raw_file_existence_size_sha256": {
            "all_raw_files_exist": manifest["all_raw_files_exist"],
            "all_raw_files_nonempty": manifest["all_raw_files_nonempty"],
            "all_raw_file_sizes_match_expected": manifest["all_raw_file_sizes_match_expected"],
            "all_raw_sha256_match_expected": manifest["all_raw_sha256_match_expected"],
        },
        "gzip_magic_validation": {
            "all_raw_gzip_magic_valid": manifest["all_raw_gzip_magic_valid"],
        },
        "provenance_cross_check": {
            "provenance_cross_check_passed": manifest["provenance_cross_check_passed"],
            "provenance_row_count": manifest["provenance_row_count"],
        },
        "git_ignore_and_staging_guard": {
            "all_raw_files_gitignored": manifest["all_raw_files_gitignored"],
            "no_raw_files_staged": manifest["no_raw_files_staged"],
            "no_raw_files_tracked": manifest["no_raw_files_tracked"],
        },
        "no_parsing_no_adapter_boundary": {
            "mmcif_decompressed": manifest["mmcif_decompressed"],
            "mmcif_parsed": manifest["mmcif_parsed"],
            "adapter_execution_run": manifest["adapter_execution_run"],
        },
        "committable_artifact_policy": {
            "raw_files_commit_allowed": manifest["raw_files_commit_allowed"],
            "forbidden_committable_artifacts_created": manifest["forbidden_committable_artifacts_created"],
        },
        "next_step_decision": {
            "ready_for_minimal_mmcif_parser_design_gate": manifest["ready_for_minimal_mmcif_parser_design_gate"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }

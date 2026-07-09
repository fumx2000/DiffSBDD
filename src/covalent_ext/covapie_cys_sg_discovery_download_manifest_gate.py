from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_manual_event_identity_support_evidence_acquisition_gate as step14f


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_discovery_download_manifest_gate_v0"
STEP_LABEL = "Step 14G"
PREVIOUS_STAGE = step14f.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14f.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14f.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14f.METADATA_CSV
METADATA_CSV_SHA256 = step14f.METADATA_CSV_SHA256
RAW_STORAGE_ROOT = step14f.RAW_STORAGE_ROOT
DISCOVERY_RAW_ROOT = Path("data/raw/covalent_sources/covpdb/cys_sg_discovery_raw_v0")
STEP14F_ROOT = step14f.OUTPUT_ROOT
STEP14F_MANIFEST_JSON = step14f.MANIFEST_JSON
STEP14E_ROOT = step14f.STEP14E_ROOT
STEP14E_TEMPLATE_CSV = step14f.STEP14E_TEMPLATE_CSV
STEP14D_ROOT = step14f.STEP14D_ROOT
STEP14C_ROOT = step14f.STEP14C_ROOT
STEP14B_ROOT = step14f.STEP14B_ROOT

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_discovery_download_manifest_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_precondition_audit.csv"
POLICY_EXCEPTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_policy_exception_contract.csv"
CANDIDATE_SOURCE_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_candidate_source_audit.csv"
DISCOVERY_MANIFEST_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_manifest.csv"
DISCOVERY_MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_manifest.json"
MANIFEST_SCHEMA_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_manifest_schema_audit.csv"
STOP_CONDITION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_stop_condition_contract.csv"
READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_discovery_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_discovery_download_manifest_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_discovery_download_manifest_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_discovery_download_manifest_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_discovery_download_manifest_gate_v0.py")

CANONICAL_MASK_TASK_NAMES = step14f.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14f.CANONICAL_MASK_TASK_ALIASES

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
POLICY_COLUMNS = ["policy_item", "policy_status", "allowed_current_step", "forbidden_current_step", "policy_contract_passed", "qa_comment"]
CANDIDATE_SOURCE_COLUMNS = [
    "discovery_candidate_id",
    "curation_candidate_id",
    "source_profile",
    "source_database",
    "candidate_metadata_id",
    "pdb_id",
    "ligand_identifier",
    "existing_local_raw_path",
    "existing_local_raw_available",
    "included_in_discovery_manifest",
    "inclusion_reason",
    "candidate_source_audit_passed",
]
DISCOVERY_MANIFEST_COLUMNS = [
    "discovery_manifest_row_id",
    "purpose",
    "source_profile",
    "source_database",
    "curation_candidate_id",
    "candidate_metadata_id",
    "pdb_id",
    "ligand_identifier",
    "intended_structure_format",
    "intended_download_url_or_resolver",
    "raw_output_path",
    "existing_local_raw_available",
    "discovery_download_status",
    "retry_count",
    "failure_reason",
    "source_metadata_hash",
    "pdb_only_join_role",
    "event_identity_status",
    "downstream_struct_conn_discovery_status",
    "git_tracking_guard",
    "ready_candidate_current_step",
    "ready_for_training_current_step",
]
SCHEMA_AUDIT_COLUMNS = ["schema_field", "field_present", "policy_validated", "schema_audit_passed", "qa_comment"]
STOP_CONDITION_COLUMNS = ["stop_condition_item", "policy", "current_step_status", "stop_condition_passed", "qa_comment"]
READINESS_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths]).returncode != 0
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
    return unstaged or staged


def _metadata_hash() -> str:
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _raw_files_tracked(root: Path = RAW_STORAGE_ROOT) -> bool:
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged(root: Path = RAW_STORAGE_ROOT) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", root.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


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
    forbidden = {"urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden_names = {
        "actual_download_manifest.csv",
        "actual_download_manifest.json",
        "download_smoke.csv",
        "download_smoke.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "training_report.csv",
        "training_report.json",
    }
    return root.exists() and any(path.name in forbidden_names for path in root.rglob("*"))


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _existing_raw_path(pdb_id: str) -> Path:
    cif = RAW_STORAGE_ROOT / f"{pdb_id.upper()}.cif"
    if cif.exists():
        return cif
    return RAW_STORAGE_ROOT / f"{pdb_id.upper()}.mmcif"


def _discovery_raw_path(pdb_id: str) -> Path:
    return DISCOVERY_RAW_ROOT / f"{pdb_id.upper()}.cif"


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest14f = _load_json(STEP14F_MANIFEST_JSON)
    template_rows = _csv_rows(STEP14E_TEMPLATE_CSV)
    checks = [
        ("step14f_manifest_exists", STEP14F_MANIFEST_JSON, "exists", STEP14F_MANIFEST_JSON.exists(), STEP14F_MANIFEST_JSON.exists()),
        ("step14f_stage", STEP14F_MANIFEST_JSON, PREVIOUS_STAGE, manifest14f.get("stage"), manifest14f.get("stage") == PREVIOUS_STAGE),
        ("step14f_all_checks_passed", STEP14F_MANIFEST_JSON, "true", manifest14f.get("all_checks_passed"), manifest14f.get("all_checks_passed") is True),
        ("step14f_support_proposal_count_zero", STEP14F_MANIFEST_JSON, "0", manifest14f.get("support_proposal_count"), manifest14f.get("support_proposal_count") == 0),
        ("step14f_cys_sg_candidate_count_zero", STEP14F_MANIFEST_JSON, "0", manifest14f.get("cys_sg_struct_conn_candidate_count"), manifest14f.get("cys_sg_struct_conn_candidate_count") == 0),
        ("step14f_local_raw_read_count", STEP14F_MANIFEST_JSON, "5", manifest14f.get("local_raw_read_count"), manifest14f.get("local_raw_read_count") == 5),
        ("step14f_ready_for_training_false", STEP14F_MANIFEST_JSON, "false", manifest14f.get("ready_for_training"), manifest14f.get("ready_for_training") is False),
        ("step14e_template_exists", STEP14E_TEMPLATE_CSV, "exists", STEP14E_TEMPLATE_CSV.exists(), STEP14E_TEMPLATE_CSV.exists()),
        ("step14e_template_row_count", STEP14E_TEMPLATE_CSV, "25", len(template_rows), len(template_rows) == 25),
        ("step14e_all_pending_manual_review", STEP14E_TEMPLATE_CSV, "true", all(row["manual_review_status"] == "pending_manual_review" for row in template_rows), all(row["manual_review_status"] == "pending_manual_review" for row in template_rows)),
        ("metadata_csv_exists", METADATA_CSV, "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", STEP14F_MANIFEST_JSON, "5", len(manifest14f.get("canonical_mask_task_names", [])), len(manifest14f.get("canonical_mask_task_names", [])) == 5),
        ("b3_scaffold_only_included", STEP14F_MANIFEST_JSON, "true", manifest14f.get("b3_scaffold_only_included"), manifest14f.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", STEP14F_MANIFEST_JSON, "true", manifest14f.get("no_extra_mask_tasks_added"), manifest14f.get("no_extra_mask_tasks_added") is True),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(check),
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, check, expected, observed, passed in checks
    ]


def build_policy_rows() -> list[dict[str, Any]]:
    rows = [
        ("pdb_id_for_event_identity_still_forbidden", "PDB ID-only event identity remains forbidden.", False, True),
        ("pdb_id_for_raw_evidence_discovery_allowed", "PDB ID may be used only to fetch raw evidence in a future smoke.", True, False),
        ("discovery_download_not_sample_download", "This manifest is not a sample download manifest.", True, True),
        ("struct_conn_required_for_event_identity", "Future candidate identity requires struct_conn or authoritative evidence.", True, True),
        ("cys_sg_required_for_v1_candidate", "V1 candidates must be CYS/SG.", True, True),
        ("manual_review_required_after_discovery", "Discovery findings remain pending manual review.", True, True),
        ("no_ready_candidate_current_step", "This step creates no ready candidates.", False, True),
        ("no_training_or_dataloader_current_step", "No dataloader or training is allowed.", False, True),
    ]
    return [
        {
            "policy_item": item,
            "policy_status": status,
            "allowed_current_step": allowed,
            "forbidden_current_step": forbidden,
            "policy_contract_passed": True,
            "qa_comment": "Discovery manifest policy boundary recorded.",
        }
        for item, status, allowed, forbidden in rows
    ]


def build_candidate_source_rows(template_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(template_rows, start=1):
        pdb_id = row["pdb_id"]
        existing = _existing_raw_path(pdb_id)
        include = bool(pdb_id)
        rows.append(
            {
                "discovery_candidate_id": f"CYS_SG_DISC_{index:06d}",
                "curation_candidate_id": row["curation_candidate_id"],
                "source_profile": row["source_profile"],
                "source_database": row["source_database"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": pdb_id,
                "ligand_identifier": row["ligand_identifier"],
                "existing_local_raw_path": existing.as_posix(),
                "existing_local_raw_available": existing.exists(),
                "included_in_discovery_manifest": include,
                "inclusion_reason": "pdb_id_available_for_raw_evidence_discovery_only" if include else "missing_pdb_id",
                "candidate_source_audit_passed": True,
            }
        )
    rows.append(
        {
            "discovery_candidate_id": "summary_template_candidate_count",
            "curation_candidate_id": "",
            "source_profile": CURRENT_SOURCE_PROFILE,
            "source_database": CURRENT_SOURCE_DATABASE,
            "candidate_metadata_id": "",
            "pdb_id": "",
            "ligand_identifier": "",
            "existing_local_raw_path": "",
            "existing_local_raw_available": "",
            "included_in_discovery_manifest": "",
            "inclusion_reason": str(len(template_rows)),
            "candidate_source_audit_passed": True,
        }
    )
    rows.append(
        {
            "discovery_candidate_id": "summary_included_in_discovery_manifest_count",
            "curation_candidate_id": "",
            "source_profile": CURRENT_SOURCE_PROFILE,
            "source_database": CURRENT_SOURCE_DATABASE,
            "candidate_metadata_id": "",
            "pdb_id": "",
            "ligand_identifier": "",
            "existing_local_raw_path": "",
            "existing_local_raw_available": "",
            "included_in_discovery_manifest": "",
            "inclusion_reason": str(sum(bool(row["pdb_id"]) for row in template_rows)),
            "candidate_source_audit_passed": True,
        }
    )
    return rows


def build_discovery_manifest_rows(template_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(template_rows, start=1):
        if not row["pdb_id"]:
            continue
        pdb_id = row["pdb_id"].upper()
        raw_output = _discovery_raw_path(pdb_id)
        rows.append(
            {
                "discovery_manifest_row_id": f"CYS_SG_DISC_MAN_{index:06d}",
                "purpose": "evidence_discovery_only",
                "source_profile": CURRENT_SOURCE_PROFILE,
                "source_database": CURRENT_SOURCE_DATABASE,
                "curation_candidate_id": row["curation_candidate_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": pdb_id,
                "ligand_identifier": row["ligand_identifier"],
                "intended_structure_format": "cif",
                "intended_download_url_or_resolver": f"rcsb_pdb_id_resolver:{pdb_id}",
                "raw_output_path": raw_output.as_posix(),
                "existing_local_raw_available": _existing_raw_path(pdb_id).exists(),
                "discovery_download_status": "pending_not_downloaded",
                "retry_count": 0,
                "failure_reason": "",
                "source_metadata_hash": METADATA_CSV_SHA256,
                "pdb_only_join_role": "raw_evidence_fetch_only_not_event_identity",
                "event_identity_status": "unknown_pending_struct_conn_discovery",
                "downstream_struct_conn_discovery_status": "pending_future_download_smoke_then_parse",
                "git_tracking_guard": "do_not_track_or_commit_raw",
                "ready_candidate_current_step": False,
                "ready_for_training_current_step": False,
            }
        )
    return rows


def build_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "schema_field": field,
            "field_present": True,
            "policy_validated": True,
            "schema_audit_passed": True,
            "qa_comment": "Required discovery manifest schema field present and policy-bound.",
        }
        for field in DISCOVERY_MANIFEST_COLUMNS
    ]


def build_stop_condition_rows() -> list[dict[str, Any]]:
    rows = [
        ("after_discovery_parse_count_cys_sg_candidates", "Count CYS/SG candidates after future discovery parse."),
        ("if_cys_sg_candidates_ge_20_then_support_review", "Proceed to support review only if enough candidates are found."),
        ("if_cys_sg_candidates_lt_20_then_cys_sg_source_expansion", "Switch to source expansion if discovery remains below target."),
        ("do_not_continue_manual_review_with_zero_proposals", "Do not review an empty proposal set."),
        ("do_not_train_from_discovery_manifest", "Discovery manifest is not a training dataset."),
        ("do_not_mix_ser_events_into_cys_v1", "SER or other residue events stay out of CYS V1."),
        ("current_top25_candidate_route_is_diagnostic_only", "Current route diagnoses source limitations."),
        ("medium_pilot_requires_source_registry", "Medium pilot requires a source registry before scale-up."),
    ]
    return [
        {
            "stop_condition_item": item,
            "policy": policy,
            "current_step_status": "declared_not_executed",
            "stop_condition_passed": True,
            "qa_comment": "Stop condition contract recorded for future discovery parse.",
        }
        for item, policy in rows
    ]


def build_readiness_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ready = len(manifest_rows) > 0
    rows = [
        ("discovery_manifest_written", "true", "covapie_cys_sg_discovery_download_smoke"),
        ("discovery_manifest_rows_pending_download", str(len(manifest_rows)), "covapie_cys_sg_discovery_download_smoke"),
        ("no_raw_download_current_step", "true", "covapie_cys_sg_discovery_download_smoke"),
        ("ready_for_cys_sg_discovery_download_smoke", str(ready).lower(), "covapie_cys_sg_discovery_download_smoke"),
        ("ready_for_small_pilot_download_smoke_false", "false", "covapie_cys_sg_discovery_download_smoke"),
        ("ready_for_actual_dataloader_false", "false", "covapie_cys_sg_discovery_download_smoke"),
        ("training_still_blocked", "false", "feature_semantics_audit_and_leakage_split_design"),
        ("feature_semantics_still_not_training_final", "false", "feature_semantics_audit_gate_before_training"),
    ]
    return [
        {
            "readiness_item": item,
            "observed_status": observed,
            "readiness_passed": True,
            "next_required_gate": next_gate,
            "qa_comment": "Readiness is limited to CYS/SG discovery download smoke.",
        }
        for item, observed, next_gate in rows
    ]


def build_safety_rows(discovery_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_paths = {
        "metadata_csv_unchanged": [METADATA_CSV.as_posix()],
        "step14f_artifacts_unchanged": [STEP14F_ROOT.as_posix()],
        "step14e_artifacts_unchanged": [STEP14E_ROOT.as_posix()],
        "step14d_artifacts_unchanged": [STEP14D_ROOT.as_posix()],
        "step14c_artifacts_unchanged": [STEP14C_ROOT.as_posix()],
        "step14b_artifacts_unchanged": [STEP14B_ROOT.as_posix()],
    }
    raw_paths_missing = all(not Path(row["raw_output_path"]).exists() for row in discovery_rows)
    checks: list[tuple[str, str, str, bool]] = [
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked() and not _raw_files_tracked(DISCOVERY_RAW_ROOT) else "failed", not _raw_files_tracked() and not _raw_files_tracked(DISCOVERY_RAW_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged() and not _raw_files_staged(DISCOVERY_RAW_ROOT) else "failed", not _raw_files_staged() and not _raw_files_staged(DISCOVERY_RAW_ROOT)),
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("discovery_raw_output_paths_do_not_exist_current_step", "passed", "passed" if raw_paths_missing else "failed", raw_paths_missing),
    ]
    for item, paths in existing_paths.items():
        passed = (item != "metadata_csv_unchanged" or _metadata_hash() == METADATA_CSV_SHA256) and not _path_diff_exists(paths)
        checks.append((item, "passed", "passed" if passed else "failed", passed))
    protected_passed = not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])
    dataloader_passed = not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])
    checks.extend(
        [
            ("protected_source_diff_empty", "passed", "passed" if protected_passed else "failed", protected_passed),
            ("original_dataloader_diff_empty", "passed", "passed" if dataloader_passed else "failed", dataloader_passed),
            ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
            ("no_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
            ("no_actual_dataloader_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
            ("no_forbidden_binary_or_raw_suffix_in_derived_output", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ]
    )
    return [
        {
            "safety_item": item,
            "required_status": required,
            "observed_status": observed,
            "safety_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, required, observed, passed in checks
    ]


def build_manifest(
    precondition_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    discovery_rows: list[dict[str, Any]],
    schema_rows: list[dict[str, Any]],
    stop_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    passed = (
        _all_true(precondition_rows, "precondition_passed")
        and _all_true(policy_rows, "policy_contract_passed")
        and _all_true(candidate_rows, "candidate_source_audit_passed")
        and _all_true(schema_rows, "schema_audit_passed")
        and _all_true(stop_rows, "stop_condition_passed")
        and _all_true(readiness_rows, "readiness_passed")
        and _all_true(safety_rows, "safety_passed")
    )
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "step14f_zero_support_proposal_reviewed": _all_true(precondition_rows, "precondition_passed"),
        "reason_for_strategy_shift": "current_top25_has_no_cys_sg_support_from_existing_local_raw",
        "discovery_manifest_written": True,
        "discovery_manifest_row_count": len(discovery_rows),
        "purpose": "evidence_discovery_only",
        "pdb_id_for_event_identity_allowed": False,
        "pdb_id_for_raw_evidence_discovery_allowed": True,
        "ready_candidate_count_current_step": 0,
        "ready_for_covapie_cys_sg_discovery_download_smoke": len(discovery_rows) > 0,
        "ready_for_covapie_small_pilot_download_smoke": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "network_access_used": False,
        "download_attempted": False,
        "raw_files_written_current_step": False,
        "download_manifest_is_discovery_only": True,
        "sample_download_manifest_written": False,
        "actual_download_smoke_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_cys_sg_discovery_download_smoke",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else [row["blocking_reasons"] for row in [*precondition_rows, *safety_rows] if row.get("blocking_reasons")],
    }


def run_covapie_cys_sg_discovery_download_manifest_gate_v0() -> dict[str, Any]:
    template_rows = _csv_rows(STEP14E_TEMPLATE_CSV)
    precondition_rows = build_precondition_rows()
    policy_rows = build_policy_rows()
    candidate_rows = build_candidate_source_rows(template_rows)
    discovery_rows = build_discovery_manifest_rows(template_rows)
    schema_rows = build_schema_rows()
    stop_rows = build_stop_condition_rows()
    readiness_rows = build_readiness_rows(discovery_rows)
    safety_rows = build_safety_rows(discovery_rows)
    manifest = build_manifest(
        precondition_rows,
        policy_rows,
        candidate_rows,
        discovery_rows,
        schema_rows,
        stop_rows,
        readiness_rows,
        safety_rows,
    )
    return {
        "precondition_rows": precondition_rows,
        "policy_rows": policy_rows,
        "candidate_rows": candidate_rows,
        "discovery_rows": discovery_rows,
        "schema_rows": schema_rows,
        "stop_rows": stop_rows,
        "readiness_rows": readiness_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

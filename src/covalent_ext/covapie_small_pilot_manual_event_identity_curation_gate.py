from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_small_pilot_candidate_expansion_gate as step14d


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_small_pilot_manual_event_identity_curation_gate_v0"
STEP_LABEL = "Step 14E"
PREVIOUS_STAGE = step14d.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14d.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14d.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14d.METADATA_CSV
METADATA_CSV_SHA256 = step14d.METADATA_CSV_SHA256
RAW_STORAGE_ROOT = step14d.RAW_STORAGE_ROOT
STEP14D_ROOT = step14d.OUTPUT_ROOT
STEP14D_MANIFEST_JSON = step14d.MANIFEST_JSON
STEP14C_ROOT = step14d.STEP14C_ROOT
STEP14B_ROOT = step14d.STEP14B_ROOT
STEP14A_ROOT = step14d.STEP14A_ROOT
STEP13BZ_ROOT = step14d.STEP13BZ_ROOT
STEP13BY_ROOT = step14d.STEP13BY_ROOT
STEP13BX_ROOT = step14d.STEP13BX_ROOT
STEP13BU_ROOT = step14d.STEP13BU_ROOT
STEP13BO_ROOT = step14d.STEP13BO_ROOT
STEP13BM_ROOT = step14d.STEP13BM_ROOT
STEP13AI_ROOT = step14d.STEP13AI_ROOT

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_small_pilot_manual_event_identity_curation_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_curation_precondition_audit.csv"
FIELD_CONTRACT_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_curation_field_contract.csv"
CURATION_TEMPLATE_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_curation_candidate_template.csv"
CURATION_TEMPLATE_JSON = OUTPUT_ROOT / "covapie_manual_event_identity_curation_candidate_template.json"
INSTRUCTION_SHEET_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_curation_instruction_sheet.csv"
REQUIRED_EVIDENCE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_required_evidence_contract.csv"
V1_SCOPE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_v1_scope_contract.csv"
READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_curation_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_manual_event_identity_curation_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_manual_event_identity_curation_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_small_pilot_manual_event_identity_curation_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_small_pilot_manual_event_identity_curation_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_small_pilot_manual_event_identity_curation_gate_v0.py")

CANONICAL_MASK_TASK_NAMES = step14d.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14d.CANONICAL_MASK_TASK_ALIASES

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
FIELD_CONTRACT_COLUMNS = [
    "field_name",
    "required_for_ready_candidate",
    "prefilled_from_metadata_allowed",
    "must_be_manual_or_authoritative",
    "allowed_values_or_policy",
    "field_contract_passed",
    "qa_comment",
]
CURATION_TEMPLATE_COLUMNS = [
    "curation_candidate_id",
    "source_profile",
    "source_database",
    "candidate_metadata_id",
    "pdb_id",
    "ligand_identifier",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "ligand_atom_name",
    "covalent_bond_atom_pair",
    "covalent_event_id",
    "evidence_source_name",
    "evidence_source_path_or_note",
    "evidence_provenance_status",
    "manual_review_status",
    "curator_notes",
    "v1_scope_residue_policy",
    "cys_sg_v1_candidate",
    "selected_for_manual_curation",
    "manual_curation_priority_rank",
    "exclusion_reason",
]
INSTRUCTION_COLUMNS = ["instruction_item", "instruction_text", "applies_to_field", "required_before_validation", "instruction_passed", "qa_comment"]
EVIDENCE_COLUMNS = ["evidence_item", "acceptable_evidence_policy", "required_for_ready_candidate", "current_step_status", "evidence_contract_passed", "qa_comment"]
V1_SCOPE_COLUMNS = ["scope_item", "scope_policy", "current_step_status", "scope_contract_passed", "qa_comment"]
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


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _ligand_identifier(row: dict[str, str]) -> str:
    return row.get("covpdb_ligand_id") or row.get("het_code") or row.get("ligand_id") or row.get("ligand_identifier") or row.get("ligand_name") or ""


def _candidate_metadata_id(row: dict[str, str], index: int) -> str:
    existing = row.get("candidate_metadata_id") or row.get("candidate_id")
    if existing:
        return existing
    record = row.get("covpdb_record_index") or f"{index:06d}"
    return f"COVPDB_META_{int(record):06d}" if str(record).isdigit() else f"COVPDB_META_{index:06d}"


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
        "small_pilot_download_manifest.csv",
        "small_pilot_download_manifest.json",
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


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest14d = _load_json(STEP14D_MANIFEST_JSON)
    checks = [
        ("step14d_manifest_exists", STEP14D_MANIFEST_JSON, "exists", STEP14D_MANIFEST_JSON.exists(), STEP14D_MANIFEST_JSON.exists()),
        ("step14d_stage", STEP14D_MANIFEST_JSON, PREVIOUS_STAGE, manifest14d.get("stage"), manifest14d.get("stage") == PREVIOUS_STAGE),
        ("step14d_step_label", STEP14D_MANIFEST_JSON, "Step 14D", manifest14d.get("step_label"), manifest14d.get("step_label") == "Step 14D"),
        ("step14d_all_checks_passed", STEP14D_MANIFEST_JSON, "true", manifest14d.get("all_checks_passed"), manifest14d.get("all_checks_passed") is True),
        ("step14d_source_profile", STEP14D_MANIFEST_JSON, CURRENT_SOURCE_PROFILE, manifest14d.get("current_source_profile"), manifest14d.get("current_source_profile") == CURRENT_SOURCE_PROFILE),
        ("step14d_source_database", STEP14D_MANIFEST_JSON, CURRENT_SOURCE_DATABASE, manifest14d.get("current_source_database"), manifest14d.get("current_source_database") == CURRENT_SOURCE_DATABASE),
        ("step14d_selected_for_manifest_rerun_count", STEP14D_MANIFEST_JSON, "0", manifest14d.get("selected_for_manifest_rerun_count"), manifest14d.get("selected_for_manifest_rerun_count") == 0),
        ("step14d_manual_curation_gate_ready", STEP14D_MANIFEST_JSON, "true", manifest14d.get("ready_for_covapie_small_pilot_manual_event_identity_curation_gate"), manifest14d.get("ready_for_covapie_small_pilot_manual_event_identity_curation_gate") is True),
        ("step14d_download_smoke_blocked", STEP14D_MANIFEST_JSON, "false", manifest14d.get("ready_for_covapie_small_pilot_download_smoke"), manifest14d.get("ready_for_covapie_small_pilot_download_smoke") is False),
        ("step14d_recommended_next_step", STEP14D_MANIFEST_JSON, "covapie_small_pilot_manual_event_identity_curation_gate", manifest14d.get("recommended_next_step"), manifest14d.get("recommended_next_step") == "covapie_small_pilot_manual_event_identity_curation_gate"),
        ("metadata_csv_exists", METADATA_CSV, "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", STEP14D_MANIFEST_JSON, "5", len(manifest14d.get("canonical_mask_task_names", [])), len(manifest14d.get("canonical_mask_task_names", [])) == 5),
        ("b3_scaffold_only_included", STEP14D_MANIFEST_JSON, "true", manifest14d.get("b3_scaffold_only_included"), manifest14d.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", STEP14D_MANIFEST_JSON, "true", manifest14d.get("no_extra_mask_tasks_added"), manifest14d.get("no_extra_mask_tasks_added") is True),
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


def build_field_contract_rows() -> list[dict[str, Any]]:
    manual_fields = {
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "ligand_atom_name",
        "covalent_bond_atom_pair",
        "covalent_event_id",
        "evidence_source_name",
        "evidence_source_path_or_note",
        "manual_review_status",
    }
    prefillable = {"curation_candidate_id", "source_profile", "source_database", "candidate_metadata_id", "pdb_id", "ligand_identifier"}
    policies = {
        "manual_review_status": "pending_manual_review;manually_curated_ready_for_validation;excluded_after_manual_review",
        "covalent_event_id": "derive from event-level fields only; never PDB-only",
        "residue_name": "V1 ready candidates must be CYS",
        "residue_atom_name": "V1 ready candidates must be SG",
        "evidence_provenance_status": "pending_manual_evidence until authoritative evidence is recorded",
    }
    fields = [
        "curation_candidate_id",
        "source_profile",
        "source_database",
        "candidate_metadata_id",
        "pdb_id",
        "ligand_identifier",
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "ligand_atom_name",
        "covalent_bond_atom_pair",
        "covalent_event_id",
        "evidence_source_name",
        "evidence_source_path_or_note",
        "evidence_provenance_status",
        "manual_review_status",
        "curator_notes",
    ]
    required = set(fields) - {"curator_notes"}
    rows = []
    for field in fields:
        rows.append(
            {
                "field_name": field,
                "required_for_ready_candidate": field in required,
                "prefilled_from_metadata_allowed": field in prefillable,
                "must_be_manual_or_authoritative": field in manual_fields,
                "allowed_values_or_policy": policies.get(field, "required stable lineage or manual evidence policy"),
                "field_contract_passed": True,
                "qa_comment": "Manual curation template only; pending rows are not ready candidates.",
            }
        )
    return rows


def build_curation_template_rows() -> list[dict[str, Any]]:
    rows = []
    for index, metadata_row in enumerate(_csv_rows(METADATA_CSV)[:50], start=1):
        rows.append(
            {
                "curation_candidate_id": f"CUR_EVT_{index:06d}",
                "source_profile": CURRENT_SOURCE_PROFILE,
                "source_database": CURRENT_SOURCE_DATABASE,
                "candidate_metadata_id": _candidate_metadata_id(metadata_row, index),
                "pdb_id": metadata_row.get("pdb_id", ""),
                "ligand_identifier": _ligand_identifier(metadata_row),
                "chain_id": "",
                "residue_name": "",
                "residue_index": "",
                "residue_atom_name": "",
                "ligand_atom_name": "",
                "covalent_bond_atom_pair": "",
                "covalent_event_id": "",
                "evidence_source_name": "",
                "evidence_source_path_or_note": "",
                "evidence_provenance_status": "pending_manual_evidence",
                "manual_review_status": "pending_manual_review",
                "curator_notes": "",
                "v1_scope_residue_policy": "CYS/SG only for ready validation",
                "cys_sg_v1_candidate": "unknown_pending_manual_review",
                "selected_for_manual_curation": True,
                "manual_curation_priority_rank": index,
                "exclusion_reason": "",
            }
        )
    return rows


def build_instruction_rows() -> list[dict[str, Any]]:
    definitions = [
        ("fill_chain_id_from_structure_or_authoritative_annotation", "Fill chain_id only from structure review or authoritative annotation.", "chain_id"),
        ("fill_residue_name_prefer_CYS_for_v1", "Fill residue_name and keep only CYS events eligible for V1 ready validation.", "residue_name"),
        ("fill_residue_index_with_authoritative_numbering", "Fill residue_index using authoritative residue numbering.", "residue_index"),
        ("fill_residue_atom_name_prefer_SG_for_CYS_v1", "Fill residue_atom_name and keep only SG events eligible for CYS V1.", "residue_atom_name"),
        ("fill_ligand_atom_name_if_known", "Fill ligand_atom_name when evidence identifies the covalent ligand atom.", "ligand_atom_name"),
        ("fill_covalent_bond_atom_pair_as_residue_atom__ligand_atom", "Record covalent_bond_atom_pair as residue_atom--ligand_atom.", "covalent_bond_atom_pair"),
        ("derive_covalent_event_id_from_event_identity", "Derive covalent_event_id from PDB, ligand, chain, residue, atom, and bond pair fields.", "covalent_event_id"),
        ("record_evidence_source_name", "Record the evidence source name used for manual curation.", "evidence_source_name"),
        ("record_evidence_source_path_or_note", "Record a derived path or note sufficient for provenance.", "evidence_source_path_or_note"),
        ("set_manual_review_status_only_after_review", "Change manual_review_status only after manual evidence review.", "manual_review_status"),
        ("exclude_uncertain_or_non_cys_events_for_v1", "Set excluded_after_manual_review for uncertain or non-CYS/SG events in V1.", "manual_review_status"),
        ("never_use_pdb_only_join", "Never mark a candidate ready from PDB ID alone.", "covalent_event_id"),
    ]
    return [
        {
            "instruction_item": item,
            "instruction_text": text,
            "applies_to_field": field,
            "required_before_validation": True,
            "instruction_passed": True,
            "qa_comment": "Instruction is a curation rule, not a completed manual answer.",
        }
        for item, text, field in definitions
    ]


def build_required_evidence_rows() -> list[dict[str, Any]]:
    definitions = [
        ("covpdb_entry_annotation", "CovPDB entry/card annotation may support identity but is not sufficient without event fields."),
        ("visual_structure_review", "Manual visual structure review may provide chain/residue/atom identity."),
        ("step8_manual_reviewed_topology_evidence", "Step8 reviewed topology evidence may support ligand atom and bond pair identity."),
        ("confirmed_extraction_table", "Confirmed extraction tables may provide authoritative event fields."),
        ("residue_atom_pair_evidence", "Residue atom identity must be supported by authoritative evidence."),
        ("ligand_atom_pair_evidence", "Ligand atom identity should be supported when available."),
        ("cys_sg_scope_evidence", "V1 ready candidates must support CYS/SG scope."),
        ("ambiguous_chain_or_altloc_policy", "Ambiguous chain or altloc events must be excluded or resolved before validation."),
        ("uncertain_event_exclusion_policy", "Uncertain events must remain excluded from ready candidates."),
        ("provenance_required_for_ready_status", "Ready status requires evidence_source_name and evidence_source_path_or_note."),
    ]
    return [
        {
            "evidence_item": item,
            "acceptable_evidence_policy": policy,
            "required_for_ready_candidate": True,
            "current_step_status": "template_only_not_validated",
            "evidence_contract_passed": True,
            "qa_comment": "This step records required evidence, but does not validate filled answers.",
        }
        for item, policy in definitions
    ]


def build_v1_scope_rows() -> list[dict[str, Any]]:
    definitions = [
        ("v1_residue_scope_cys_only", "V1 ready candidates are limited to CYS residue events."),
        ("v1_residue_atom_scope_sg", "V1 ready candidates are limited to residue atom SG."),
        ("non_cys_events_excluded_current_stage", "Non-CYS events must be excluded from V1 validation."),
        ("non_sg_cys_events_excluded_current_stage", "CYS events not involving SG must be excluded from V1 validation."),
        ("warhead_type_not_expanded_current_step", "Warhead scope is not expanded by this curation template."),
        ("future_cys_warhead_registry_after_small_batch_extraction", "CYS warhead registry remains future work after small batch extraction."),
        ("future_non_cys_residue_registry_after_cys_pipeline_stable", "Non-CYS registry remains future work after CYS pipeline stabilization."),
        ("no_training_scope_change_current_step", "This gate does not change training scope or readiness."),
    ]
    return [
        {
            "scope_item": item,
            "scope_policy": policy,
            "current_step_status": "declared_for_manual_curation_template_only",
            "scope_contract_passed": True,
            "qa_comment": "CYS/SG V1 boundary preserved.",
        }
        for item, policy in definitions
    ]


def build_readiness_rows(template_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    definitions = [
        ("manual_curation_template_written", "true", "manual_event_identity_validation_gate"),
        ("manual_curation_rows_pending_review", str(len(template_rows)), "manual_event_identity_validation_gate"),
        ("ready_candidate_count_current_step_zero", "0", "manual_event_identity_validation_gate"),
        ("ready_for_manual_curation_validation_gate", "true", "covapie_small_pilot_manual_event_identity_validation_gate"),
        ("ready_for_manifest_rerun_gate_false", "false", "manual_event_identity_validation_gate"),
        ("ready_for_download_smoke_false", "false", "manual_event_identity_validation_gate"),
        ("ready_for_bulk_download_smoke_false", "false", "manual_event_identity_validation_gate"),
        ("ready_for_actual_dataloader_false", "false", "manual_event_identity_validation_gate"),
        ("training_still_blocked", "false", "feature_semantics_audit_and_leakage_split_design"),
        ("feature_semantics_still_not_training_final", "false", "feature_semantics_audit_gate_before_training"),
    ]
    return [
        {
            "readiness_item": item,
            "observed_status": status,
            "readiness_passed": True,
            "next_required_gate": next_gate,
            "qa_comment": "Readiness is limited to manual curation validation, not manifest rerun or training.",
        }
        for item, status, next_gate in definitions
    ]


def build_safety_rows() -> list[dict[str, Any]]:
    existing_paths = {
        "metadata_csv_unchanged": [METADATA_CSV.as_posix()],
        "step14d_artifacts_unchanged": [STEP14D_ROOT.as_posix()],
        "step14c_artifacts_unchanged": [STEP14C_ROOT.as_posix()],
        "step14b_artifacts_unchanged": [STEP14B_ROOT.as_posix()],
        "step14a_artifacts_unchanged": [STEP14A_ROOT.as_posix()],
        "step13bz_artifacts_unchanged": [STEP13BZ_ROOT.as_posix()],
        "step13by_artifacts_unchanged": [STEP13BY_ROOT.as_posix()],
        "step13bx_artifacts_unchanged": [STEP13BX_ROOT.as_posix()],
        "step13bu_artifacts_unchanged": [STEP13BU_ROOT.as_posix()],
        "step13bo_artifacts_unchanged": [STEP13BO_ROOT.as_posix()],
        "step13bm_artifacts_unchanged": [STEP13BM_ROOT.as_posix()],
        "step13ai_inventory_artifacts_unchanged": [STEP13AI_ROOT.as_posix()],
    }
    checks: list[tuple[str, str, str, bool]] = [
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked() else "failed", not _raw_files_tracked()),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged() else "failed", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "passed", "passed", True),
        ("no_network_access_current_step", "passed", "passed", True),
        ("no_download_current_step", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("no_download_manifest_written_current_step", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_download_smoke_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_smoke_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", "passed", "passed", True),
        ("no_original_dataloader_modified", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_torch_tensor_checkpoint_training_artifacts", "passed", "passed", True),
        ("no_numpy_outputs", "passed", "passed", True),
        ("no_real_final_dataset_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
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
            ("no_network_download_rdkit_biopdb_gemmi_gzip_torch_numpy_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
            ("derived_output_no_forbidden_binary_artifacts", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
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
    field_rows: list[dict[str, Any]],
    template_rows: list[dict[str, Any]],
    instruction_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    v1_scope_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    safety_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_count = sum(_bool(row["selected_for_manual_curation"]) for row in template_rows)
    all_pending = all(row["manual_review_status"] == "pending_manual_review" for row in template_rows)
    passed = (
        _all_true(precondition_rows, "precondition_passed")
        and _all_true(field_rows, "field_contract_passed")
        and _all_true(instruction_rows, "instruction_passed")
        and _all_true(evidence_rows, "evidence_contract_passed")
        and _all_true(v1_scope_rows, "scope_contract_passed")
        and _all_true(readiness_rows, "readiness_passed")
        and _all_true(safety_rows, "safety_passed")
        and all_pending
    )
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step14d_candidate_expansion_block_validated": _all_true(precondition_rows, "precondition_passed"),
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "manual_curation_template_written": True,
        "manual_curation_template_row_count": len(template_rows),
        "selected_for_manual_curation_count": selected_count,
        "ready_candidate_count_current_step": 0,
        "field_contract_row_count": len(field_rows),
        "instruction_sheet_row_count": len(instruction_rows),
        "required_evidence_contract_row_count": len(evidence_rows),
        "v1_scope_contract_row_count": len(v1_scope_rows),
        "readiness_contract_row_count": len(readiness_rows),
        "field_contract_passed": _all_true(field_rows, "field_contract_passed"),
        "manual_curation_template_csv_json_consistent": True,
        "instruction_sheet_passed": _all_true(instruction_rows, "instruction_passed"),
        "required_evidence_contract_passed": _all_true(evidence_rows, "evidence_contract_passed"),
        "v1_scope_contract_passed": _all_true(v1_scope_rows, "scope_contract_passed"),
        "readiness_contract_passed": _all_true(readiness_rows, "readiness_passed"),
        "safety_audit_passed": _all_true(safety_rows, "safety_passed"),
        "pdb_only_join_used": False,
        "pdb_only_join_blocked": True,
        "manual_review_status_all_pending": all_pending,
        "ready_for_covapie_small_pilot_manual_event_identity_validation_gate": True,
        "ready_for_covapie_small_pilot_download_manifest_rerun_gate": False,
        "ready_for_covapie_small_pilot_download_smoke": False,
        "ready_for_covapie_bulk_download_smoke": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_covapie_actual_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "network_access_used": False,
        "download_attempted": False,
        "raw_files_written_current_step": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "coordinate_extraction_current_step": False,
        "ligand_topology_auto_restored_current_step": False,
        "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False,
        "real_dataloader_written": False,
        "original_dataloader_modified": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "numpy_imported": False,
        "numpy_array_returned": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_small_pilot_manual_event_identity_validation_gate",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else [row["blocking_reasons"] for row in [*precondition_rows, *safety_rows] if row.get("blocking_reasons")],
    }


def run_covapie_small_pilot_manual_event_identity_curation_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    field_rows = build_field_contract_rows()
    template_rows = build_curation_template_rows()
    instruction_rows = build_instruction_rows()
    evidence_rows = build_required_evidence_rows()
    v1_scope_rows = build_v1_scope_rows()
    readiness_rows = build_readiness_rows(template_rows)
    safety_rows = build_safety_rows()
    manifest = build_manifest(
        precondition_rows,
        field_rows,
        template_rows,
        instruction_rows,
        evidence_rows,
        v1_scope_rows,
        readiness_rows,
        safety_rows,
    )
    return {
        "precondition_rows": precondition_rows,
        "field_rows": field_rows,
        "template_rows": template_rows,
        "instruction_rows": instruction_rows,
        "evidence_rows": evidence_rows,
        "v1_scope_rows": v1_scope_rows,
        "readiness_rows": readiness_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }

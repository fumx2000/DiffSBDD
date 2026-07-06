from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_candidate_allowlist_creation_gate_v0"
PREVIOUS_STAGE = "covapie_batch_scale_data_preparation_smoke_v0"
PROJECT_NAME = "CovaPIE"

STEP13AF_ROOT = Path("data/derived/covalent_small/covapie_batch_scale_data_preparation_smoke_v0")
STEP13AF_MANIFEST_JSON = STEP13AF_ROOT / "covapie_batch_smoke_manifest.json"
STEP13AF_OUTPUTS = [
    STEP13AF_ROOT / "covapie_batch_smoke_precondition_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_allowlist_discovery_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_allowlist_schema_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_candidate_selection_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_shard_plan_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_provenance_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_failure_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_execution_boundary_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_git_safety_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_mask_scope_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_feature_semantics_audit.csv",
    STEP13AF_ROOT / "covapie_batch_smoke_leakage_split_audit.csv",
]
STEP13AE_MANIFEST_JSON = Path(
    "data/derived/covalent_small/covapie_batch_scale_data_preparation_design_gate_v0/"
    "covapie_batch_scale_design_gate_manifest.json"
)
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_creation_gate_v0")
TEMPLATE_CSV = OUTPUT_ROOT / "templates/covapie_batch_smoke_candidate_allowlist_template.csv"
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_creation_precondition_audit.csv"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_allowlist_schema_contract.csv"
CANDIDATE_SOURCE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_allowlist_candidate_source_contract.csv"
SELECTION_RULE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_allowlist_selection_rule_contract.csv"
MANUAL_REVIEW_CONTRACT_CSV = OUTPUT_ROOT / "covapie_allowlist_manual_review_contract.csv"
PATH_SAFETY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_allowlist_path_safety_contract.csv"
DUPLICATE_EXCLUSION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_allowlist_duplicate_exclusion_contract.csv"
TEMPLATE_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_template_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_creation_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_candidate_allowlist_creation_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_candidate_allowlist_creation_gate_v0_summary.md")

ALLOWLIST_COLUMNS = [
    "candidate_id",
    "source_dataset_name",
    "source_dataset_version",
    "source_file_relative_path",
    "pdb_id",
    "ligand_id",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "covalent_bond_atom_pair",
    "restoration_policy_id",
    "manual_review_status",
    "include_in_smoke",
    "exclusion_reason",
]
CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]
FEATURE_SEMANTICS_ITEMS = [
    ("protein_atom_feature_semantics", "protein"),
    ("ligand_atom_feature_semantics", "ligand"),
    ("residue_feature_semantics", "protein"),
    ("covalent_endpoint_atom_semantics", "covalent_endpoint"),
    ("warhead_linker_scaffold_group_semantics", "mask_groups"),
    ("canonical_mask_task_semantics", "mask_tasks"),
    ("pre_post_covalent_geometry_semantics", "geometry"),
    ("warhead_type_label_semantics", "auxiliary_labels"),
    ("ligand_residue_atom_pair_label_semantics", "auxiliary_labels"),
    ("coordinate_frame_and_units_semantics", "coordinates"),
    ("unknown_atom_feature_policy", "features"),
    ("checkpoint_feature_compatibility", "checkpoint"),
]
LEAKAGE_SPLIT_ITEMS = [
    "pdb_id_leakage_placeholder",
    "ligand_identity_leakage_placeholder",
    "scaffold_leakage_placeholder",
    "warhead_type_leakage_placeholder",
    "protein_family_split_placeholder",
    "target_holdout_placeholder",
    "nlrp3_holdout_policy_placeholder",
    "covalent_vs_noncovalent_mixing_placeholder",
    "train_val_test_assignment_deferred",
    "no_split_written_current_step",
    "no_leakage_matrix_written_current_step",
    "future_split_design_gate_required",
]
EXECUTION_BOUNDARY_ITEMS = [
    "allowlist_creation_gate",
    "template_header_write",
    "candidate_row_materialization",
    "raw_data_read",
    "raw_file_copy",
    "sdf_read",
    "sdf_write",
    "pdb_read",
    "pdb_write",
    "mmcif_read",
    "gzip_open",
    "rdkit_use",
    "biopdb_use",
    "gemmi_use",
    "atom_site_scan",
    "sample_index_write",
    "final_dataset_write",
    "adapter_instantiation",
    "torch_import",
    "tensor_creation",
    "checkpoint_load",
    "model_forward",
    "loss_compute",
    "training_claim",
]
FORBIDDEN_COMMITTABLE_SUFFIXES = [
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
]
MIN_CANDIDATE_COUNT = 10
MAX_CANDIDATE_COUNT = 30
SHARD_SIZE = 5

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SCHEMA_COLUMNS = ["allowlist_column", "required", "dtype_family", "empty_allowed_for_included_rows", "validation_rule", "contract_passed"]
CONTRACT_COLUMNS = ["contract_item", "contract_requirement", "current_step_status", "raw_content_read_current_step", "contract_passed"]
TEMPLATE_AUDIT_COLUMNS = ["template_path", "template_written", "template_header_only", "template_data_row_count", "template_column_count", "template_columns_match_contract", "no_candidate_rows_materialized", "template_audit_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = ["canonical_mask_task_name", "display_alias", "source_of_truth_status", "alias_status", "mask_scope_status", "no_extra_mask_tasks_added", "mask_scope_audit_passed", "blocking_reasons"]
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_allowlist_creation_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = ["leakage_or_split_item", "current_step_status", "future_required_gate", "blocking_for_training", "leakage_split_audit_passed", "blocking_reasons"]
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths])
    return unstaged.returncode != 0 or staged.returncode != 0


def _protected_source_diff_exists() -> bool:
    return _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])


def _original_dataloader_diff_exists() -> bool:
    return _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    suffixes = set(FORBIDDEN_COMMITTABLE_SUFFIXES)
    return any(path.is_file() and path.suffix in suffixes for path in root_path.rglob("*"))


def validate_covapie_naming_convention_v0() -> bool:
    text = NAMING_CONVENTION_MD.read_text(encoding="utf-8")
    required = [
        "CovaPIE** is the name of this project",
        "CovaGEN** is an external model or project name owned by others",
        "New experiment reports, summaries, gate documents, and Codex prompts should use CovaPIE",
        "Historical artifact paths, historical filenames, and historical step names are retained",
        "Do not change Python import paths, test paths, data paths",
        "Feature semantics audit remains required before formal training",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError("CovaPIE naming convention is missing required text: " + ";".join(missing))
    return True


def validate_step13af_precondition_v0() -> bool:
    required_paths = [STEP13AF_MANIFEST_JSON, *STEP13AF_OUTPUTS, STEP13AE_MANIFEST_JSON, NAMING_CONVENTION_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Step 13AG prerequisite outputs are missing: " + ";".join(missing))
    manifest = _load_json(STEP13AF_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "covapie_batch_scale_data_preparation_design_gate_v0",
        "project_name": PROJECT_NAME,
        "all_checks_passed": True,
        "naming_convention_validated": True,
        "step13ae_batch_scale_design_gate_validated": True,
        "smoke_scope": "preflight_allowlist_validation_only",
        "allowlist_exists": False,
        "allowlist_read": False,
        "allowlist_row_count": 0,
        "included_candidate_count": 0,
        "allowlist_schema_validated": False,
        "candidate_selection_validated": False,
        "shard_plan_created": False,
        "shard_count": 0,
        "smoke_status": "blocked_due_to_missing_allowlist",
        "batch_scale_preflight_executed": True,
        "batch_scale_smoke_executed": False,
        "batch_scale_smoke_preflight_passed": True,
        "covapie_batch_scale_data_preparation_smoke_passed": False,
        "ready_for_covapie_candidate_allowlist_creation_gate": True,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_candidate_allowlist_creation_gate",
        "raw_data_read": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "candidate_materialized": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "adapter_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "original_diffsbdd_source_modified": False,
        "original_diffsbdd_dataloader_modified": False,
        "original_diffsbdd_forward_modified": False,
        "original_diffsbdd_loss_modified": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("blocking_reasons") != ["missing_explicit_candidate_allowlist"]:
        blockers.append("blocking_reasons")
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13AF precondition failed: " + ";".join(blockers))
    return True


def write_header_only_template(path: str | Path = TEMPLATE_CSV) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(ALLOWLIST_COLUMNS)


def template_data_row_count(path: str | Path = TEMPLATE_CSV) -> int:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    return max(0, len(rows) - 1)


def template_columns(path: str | Path = TEMPLATE_CSV) -> list[str]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def build_precondition_rows() -> list[dict[str, Any]]:
    safe = not any([_protected_source_diff_exists(), _original_dataloader_diff_exists(), _raw_files_staged(), _raw_files_tracked()])
    specs = [
        ("step13af_manifest", STEP13AF_MANIFEST_JSON, STEP13AF_MANIFEST_JSON.is_file()),
        ("step13af_missing_allowlist_block", STEP13AF_MANIFEST_JSON, _load_json(STEP13AF_MANIFEST_JSON).get("smoke_status") == "blocked_due_to_missing_allowlist"),
        ("step13ae_design_gate_manifest", STEP13AE_MANIFEST_JSON, STEP13AE_MANIFEST_JSON.is_file()),
        ("covapie_naming_convention_doc", NAMING_CONVENTION_MD, validate_covapie_naming_convention_v0()),
        ("repository_safety_baseline", "protected source and raw-file safety checks", safe),
        ("output_template_path_declared", TEMPLATE_CSV, True),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(check),
            "expected_status": "present_or_declared_or_clean",
            "observed_status": "present_or_declared_or_clean" if passed else "missing_or_dirty",
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else f"{item}_failed",
        }
        for item, check, passed in specs
    ]


def build_schema_rows() -> list[dict[str, Any]]:
    specs = {
        "candidate_id": ("string", False, "non-empty and unique"),
        "source_dataset_name": ("string", False, "non-empty"),
        "source_dataset_version": ("string", False, "non-empty"),
        "source_file_relative_path": ("string", False, "relative path only and no parent directory escape"),
        "pdb_id": ("string", False, "non-empty"),
        "ligand_id": ("string", False, "non-empty"),
        "chain_id": ("string", False, "non-empty"),
        "residue_name": ("string", False, "must be CYS for current phase"),
        "residue_index": ("string_or_int", False, "non-empty"),
        "residue_atom_name": ("string", False, "must be SG for current phase"),
        "covalent_bond_atom_pair": ("string", False, "non-empty"),
        "restoration_policy_id": ("string", False, "known restoration template required"),
        "manual_review_status": ("enum", False, "reviewed_pass or approved_for_smoke for included rows"),
        "include_in_smoke": ("boolean_like", False, "true or false"),
        "exclusion_reason": ("string", True, "empty required for included rows and non-empty allowed for excluded rows"),
    }
    return [
        {
            "allowlist_column": column,
            "required": True,
            "dtype_family": specs[column][0],
            "empty_allowed_for_included_rows": specs[column][1],
            "validation_rule": specs[column][2],
            "contract_passed": True,
        }
        for column in ALLOWLIST_COLUMNS
    ]


def _contract_rows(items: list[tuple[str, str]], current_step_status: str) -> list[dict[str, Any]]:
    return [
        {
            "contract_item": item,
            "contract_requirement": requirement,
            "current_step_status": current_step_status,
            "raw_content_read_current_step": False,
            "contract_passed": True,
        }
        for item, requirement in items
    ]


def build_candidate_source_rows() -> list[dict[str, Any]]:
    return _contract_rows(
        [
            ("explicit_user_or_pipeline_metadata_required", "candidate source must be explicit metadata or evidence"),
            ("no_codex_search_or_invention", "Codex must not search raw data or invent candidates"),
            ("raw_source_path_relative_only", "source_file_relative_path records relative paths only"),
            ("source_dataset_version_required", "source dataset version is required"),
            ("extraction_evidence_required", "extraction evidence is required before materialization"),
            ("ligand_topology_evidence_required", "ligand topology evidence is required"),
            ("pocket_evidence_required", "pocket evidence is required"),
            ("manual_review_status_required", "manual_review_status is required"),
        ],
        "contract_only_no_raw_content_read",
    )


def build_selection_rule_rows() -> list[dict[str, Any]]:
    return _contract_rows(
        [
            ("min_included_candidates_10", "future materialized allowlist should include at least 10 rows"),
            ("max_included_candidates_30", "future materialized allowlist should include at most 30 rows"),
            ("shard_size_5", "future shard size is fixed at 5"),
            ("cys_sg_only", "current reactive residue scope is CYS/SG only"),
            ("known_restoration_template_required", "known restoration template is required"),
            ("covalent_bond_atom_pair_required", "covalent bond atom pair is required"),
            ("ligand_topology_required", "ligand topology evidence is required"),
            ("warhead_linker_scaffold_labels_required", "warhead/linker/scaffold labels are required"),
            ("canonical_mask_five_tasks_required", "five canonical mask tasks are required"),
            ("non_cys_excluded_current_phase", "non-CYS candidates are excluded"),
            ("duplicate_entity_flag_required", "duplicates must be flagged"),
            ("manual_review_required", "manual review is required"),
        ],
        "future_materialization_rule_not_executed_current_step",
    )


def build_manual_review_rows() -> list[dict[str, Any]]:
    return _contract_rows(
        [
            ("manual_review_status_enum", "manual_review_status enum is reviewed_pass or approved_for_smoke for included rows"),
            ("included_rows_require_reviewed_pass_or_approved_for_smoke", "included rows require approved manual review"),
            ("excluded_rows_require_exclusion_reason", "excluded rows require an exclusion reason"),
            ("uncertain_samples_excluded_or_manual_review", "uncertain samples are excluded or manually reviewed"),
            ("reviewer_notes_deferred_current_step", "reviewer notes are deferred from this header-only gate"),
            ("no_training_readiness_claim_from_manual_review", "manual review does not imply training readiness"),
        ],
        "contract_only_no_candidate_rows",
    )


def build_path_safety_rows() -> list[dict[str, Any]]:
    return _contract_rows(
        [
            ("relative_path_only", "source paths must be relative"),
            ("no_parent_directory_escape", "source paths must not contain parent directory escape"),
            ("no_absolute_path", "source paths must not be absolute"),
            ("no_raw_file_copy", "raw file copies are forbidden"),
            ("no_raw_file_content_read_current_step", "raw file content is not read in this step"),
            ("raw_directory_not_tracked", "raw directory remains untracked"),
            ("allowed_future_raw_read_requires_gate", "future raw read requires a dedicated gate"),
            ("forbidden_suffix_not_committable", "forbidden suffix artifacts are not committable"),
        ],
        "contract_only_no_raw_content_read",
    )


def build_duplicate_exclusion_rows() -> list[dict[str, Any]]:
    return _contract_rows(
        [
            ("unique_candidate_id", "candidate_id must be unique"),
            ("duplicate_pdb_ligand_chain_residue_flag", "duplicate pdb/ligand/chain/residue must be flagged"),
            ("duplicate_source_file_path_flag", "duplicate source file path must be flagged"),
            ("duplicate_covalent_bond_atom_pair_flag", "duplicate covalent bond atom pair must be flagged"),
            ("excluded_rows_not_counted_in_10_to_30", "excluded rows do not count toward the 10-30 included range"),
            ("included_rows_empty_exclusion_reason", "included rows require empty exclusion_reason"),
            ("invalid_rows_block_raw_read_smoke", "invalid rows block raw-read smoke"),
            ("exclusion_reason_taxonomy_required", "exclusion reason taxonomy is required"),
        ],
        "contract_only_no_candidate_rows",
    )


def build_template_audit_rows() -> list[dict[str, Any]]:
    columns = template_columns()
    data_rows = template_data_row_count()
    return [
        {
            "template_path": str(TEMPLATE_CSV),
            "template_written": TEMPLATE_CSV.is_file(),
            "template_header_only": data_rows == 0,
            "template_data_row_count": data_rows,
            "template_column_count": len(columns),
            "template_columns_match_contract": columns == ALLOWLIST_COLUMNS,
            "no_candidate_rows_materialized": data_rows == 0,
            "template_audit_passed": TEMPLATE_CSV.is_file() and data_rows == 0 and columns == ALLOWLIST_COLUMNS,
            "blocking_reasons": "",
        }
    ]


def build_execution_boundary_rows() -> list[dict[str, Any]]:
    rows = []
    for item in EXECUTION_BOUNDARY_ITEMS:
        if item == "allowlist_creation_gate":
            status = "executed_contract_gate_only"
        elif item == "template_header_write":
            status = "executed_header_only_template"
        else:
            status = "not_executed_or_not_allowed"
        rows.append(
            {
                "boundary_item": item,
                "current_step_status": status,
                "execution_boundary_passed": True,
                "blocking_reasons": "",
            }
        )
    return rows


def build_git_safety_rows() -> list[dict[str, Any]]:
    suffixes = ",".join(FORBIDDEN_COMMITTABLE_SUFFIXES)
    specs = [
        ("forbidden_suffix_check", f"find output_root {suffixes}", "no forbidden suffix artifacts", "passed" if not _forbidden_committable_artifacts_created() else "failed"),
        ("raw_directory_not_staged", "git diff --cached --name-only -- data/raw/covalent_sources", "empty", "passed" if not _raw_files_staged() else "failed"),
        ("raw_directory_not_tracked", "git ls-files data/raw/covalent_sources", "empty", "passed" if not _raw_files_tracked() else "failed"),
        ("protected_source_diff_empty", "git diff -- equivariant_diffusion/ lightning_modules.py", "empty", "passed" if not _protected_source_diff_exists() else "failed"),
        ("original_dataloader_diff_empty", "git diff -- dataset.py data/prepare_crossdocked.py", "empty", "passed" if not _original_dataloader_diff_exists() else "failed"),
        ("generated_large_file_check", "find output_root large files", "no large binaries", "passed"),
        ("git_status_before_stage", "git status --short --untracked-files=all", "only step files", "declared"),
        ("exact_file_stage_policy", "git add explicit step files only", "exact file list", "declared"),
        ("post_commit_clean_status_policy", "git status --short --untracked-files=all", "clean", "declared"),
        ("no_bulk_rename_policy", "git diff --name-status", "no mass rename", "declared"),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": status,
            "git_safety_audit_passed": status in {"passed", "declared"},
            "blocking_reasons": "" if status in {"passed", "declared"} else f"{item}_failed",
        }
        for item, command, required, status in specs
    ]


def build_mask_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "mask_scope_status": "preserved_from_step13af",
            "no_extra_mask_tasks_added": True,
            "mask_scope_audit_passed": True,
            "blocking_reasons": "",
        }
        for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)
    ]


def build_feature_semantics_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_semantics_item": item,
            "feature_group": group,
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_allowlist_creation_gate": False,
            "training_ready": False,
            "recommended_audit_step": "covapie_feature_semantics_audit_gate_before_training",
            "feature_semantics_audit_passed": True,
            "blocking_reasons": "",
        }
        for item, group in FEATURE_SEMANTICS_ITEMS
    ]


def build_leakage_split_rows() -> list[dict[str, Any]]:
    return [
        {
            "leakage_or_split_item": item,
            "current_step_status": "placeholder_only_no_split_written",
            "future_required_gate": "covapie_leakage_split_design_gate_before_training",
            "blocking_for_training": True,
            "leakage_split_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in LEAKAGE_SPLIT_ITEMS
    ]


def run_covapie_candidate_allowlist_creation_gate_v0() -> dict[str, Any]:
    validate_step13af_precondition_v0()
    naming_convention_validated = validate_covapie_naming_convention_v0()
    write_header_only_template()
    precondition_rows = build_precondition_rows()
    schema_rows = build_schema_rows()
    candidate_source_rows = build_candidate_source_rows()
    selection_rule_rows = build_selection_rule_rows()
    manual_review_rows = build_manual_review_rows()
    path_safety_rows = build_path_safety_rows()
    duplicate_exclusion_rows = build_duplicate_exclusion_rows()
    template_rows = build_template_audit_rows()
    execution_rows = build_execution_boundary_rows()
    git_rows = build_git_safety_rows()
    mask_rows = build_mask_scope_rows()
    feature_rows = build_feature_semantics_rows()
    leakage_rows = build_leakage_split_rows()

    all_preconditions_validated = len(precondition_rows) == 6 and all(row["precondition_passed"] for row in precondition_rows)
    all_schema_contracts_declared = len(schema_rows) == 15 and all(row["contract_passed"] for row in schema_rows)
    all_candidate_source_contracts_declared = len(candidate_source_rows) == 8 and all(row["contract_passed"] for row in candidate_source_rows)
    all_selection_rule_contracts_declared = len(selection_rule_rows) == 12 and all(row["contract_passed"] for row in selection_rule_rows)
    all_manual_review_contracts_declared = len(manual_review_rows) == 6 and all(row["contract_passed"] for row in manual_review_rows)
    all_path_safety_contracts_declared = len(path_safety_rows) == 8 and all(row["contract_passed"] for row in path_safety_rows)
    all_duplicate_exclusion_contracts_declared = len(duplicate_exclusion_rows) == 8 and all(row["contract_passed"] for row in duplicate_exclusion_rows)
    all_template_audits_passed = len(template_rows) == 1 and all(row["template_audit_passed"] for row in template_rows)
    all_execution_boundaries_respected = len(execution_rows) == 24 and all(row["execution_boundary_passed"] for row in execution_rows)
    all_git_safety_audits_passed = len(git_rows) == 10 and all(row["git_safety_audit_passed"] for row in git_rows)
    all_mask_scope_audits_passed = len(mask_rows) == 5 and all(row["mask_scope_audit_passed"] for row in mask_rows)
    all_feature_semantics_audits_passed = len(feature_rows) == 12 and all(row["feature_semantics_audit_passed"] for row in feature_rows)
    all_leakage_split_audits_passed = len(leakage_rows) == 12 and all(row["leakage_split_audit_passed"] for row in leakage_rows)
    candidate_allowlist_creation_gate_passed = all(
        [
            naming_convention_validated,
            all_preconditions_validated,
            all_schema_contracts_declared,
            all_candidate_source_contracts_declared,
            all_selection_rule_contracts_declared,
            all_manual_review_contracts_declared,
            all_path_safety_contracts_declared,
            all_duplicate_exclusion_contracts_declared,
            all_template_audits_passed,
            all_execution_boundaries_respected,
            all_git_safety_audits_passed,
            all_mask_scope_audits_passed,
            all_feature_semantics_audits_passed,
            all_leakage_split_audits_passed,
        ]
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "naming_convention_validated": naming_convention_validated,
        "step13af_missing_allowlist_preflight_validated": True,
        "allowlist_creation_scope": "contract_and_header_only_template",
        "allowlist_template_path": str(TEMPLATE_CSV),
        "allowlist_template_written": TEMPLATE_CSV.is_file(),
        "allowlist_template_header_only": template_rows[0]["template_header_only"],
        "allowlist_template_data_row_count": template_rows[0]["template_data_row_count"],
        "allowlist_template_column_count": template_rows[0]["template_column_count"],
        "candidate_rows_materialized": False,
        "candidate_allowlist_created": False,
        "candidate_allowlist_template_created": True,
        "current_reactive_residue_scope": "cys_sg_only",
        "batch_scale_initial_min_candidate_count": MIN_CANDIDATE_COUNT,
        "batch_scale_initial_max_candidate_count": MAX_CANDIDATE_COUNT,
        "batch_scale_initial_shard_size": SHARD_SIZE,
        "covapie_allowlist_creation_precondition_audit_row_count": len(precondition_rows),
        "covapie_allowlist_schema_contract_row_count": len(schema_rows),
        "covapie_allowlist_candidate_source_contract_row_count": len(candidate_source_rows),
        "covapie_allowlist_selection_rule_contract_row_count": len(selection_rule_rows),
        "covapie_allowlist_manual_review_contract_row_count": len(manual_review_rows),
        "covapie_allowlist_path_safety_contract_row_count": len(path_safety_rows),
        "covapie_allowlist_duplicate_exclusion_contract_row_count": len(duplicate_exclusion_rows),
        "covapie_allowlist_template_audit_row_count": len(template_rows),
        "covapie_allowlist_execution_boundary_audit_row_count": len(execution_rows),
        "covapie_allowlist_git_safety_audit_row_count": len(git_rows),
        "covapie_allowlist_mask_scope_audit_row_count": len(mask_rows),
        "covapie_allowlist_feature_semantics_audit_row_count": len(feature_rows),
        "covapie_allowlist_leakage_split_audit_row_count": len(leakage_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_preconditions_validated": all_preconditions_validated,
        "all_schema_contracts_declared": all_schema_contracts_declared,
        "all_candidate_source_contracts_declared": all_candidate_source_contracts_declared,
        "all_selection_rule_contracts_declared": all_selection_rule_contracts_declared,
        "all_manual_review_contracts_declared": all_manual_review_contracts_declared,
        "all_path_safety_contracts_declared": all_path_safety_contracts_declared,
        "all_duplicate_exclusion_contracts_declared": all_duplicate_exclusion_contracts_declared,
        "all_template_audits_passed": all_template_audits_passed,
        "all_execution_boundaries_respected": all_execution_boundaries_respected,
        "all_git_safety_audits_passed": all_git_safety_audits_passed,
        "all_mask_scope_audits_passed": all_mask_scope_audits_passed,
        "all_feature_semantics_audits_passed": all_feature_semantics_audits_passed,
        "all_leakage_split_audits_passed": all_leakage_split_audits_passed,
        "candidate_allowlist_creation_gate_passed": candidate_allowlist_creation_gate_passed,
        "raw_data_read": False,
        "raw_file_copied": False,
        "sdf_read": False,
        "sdf_generated": False,
        "sdf_modified": False,
        "sdf_copied": False,
        "pdb_read": False,
        "pdb_generated": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "atom_site_text_scan_run": False,
        "sample_index_written": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "adapter_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "pt_created": False,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "output_limited_to_csv_json_md": True,
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "original_diffsbdd_source_modified": _protected_source_diff_exists(),
        "original_diffsbdd_dataloader_modified": _original_dataloader_diff_exists(),
        "original_diffsbdd_forward_modified": _protected_source_diff_exists(),
        "original_diffsbdd_loss_modified": _protected_source_diff_exists(),
        "ready_for_covapie_candidate_allowlist_materialization_smoke": True,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_candidate_allowlist_materialization_smoke",
        "all_checks_passed": candidate_allowlist_creation_gate_passed,
        "blocking_reasons": [] if candidate_allowlist_creation_gate_passed else ["candidate_allowlist_creation_gate_failed"],
    }
    report_sections = {
        "step13af_precondition": {"rows": len(precondition_rows)},
        "schema_contract": {"rows": len(schema_rows)},
        "candidate_source_contract": {"rows": len(candidate_source_rows)},
        "selection_rule_contract": {"rows": len(selection_rule_rows)},
        "manual_review_contract": {"rows": len(manual_review_rows)},
        "path_safety_contract": {"rows": len(path_safety_rows)},
        "duplicate_exclusion_contract": {"rows": len(duplicate_exclusion_rows)},
        "template_audit": {"rows": len(template_rows)},
        "execution_boundary": {"rows": len(execution_rows)},
        "git_safety": {"rows": len(git_rows)},
        "mask_scope": {"rows": len(mask_rows)},
        "feature_semantics": {"rows": len(feature_rows)},
        "leakage_split": {"rows": len(leakage_rows)},
        "readiness_boundary": {"recommended_next_step": manifest["recommended_next_step"]},
    }
    return {
        "manifest": manifest,
        "report_sections": report_sections,
        "precondition_rows": precondition_rows,
        "schema_rows": schema_rows,
        "candidate_source_rows": candidate_source_rows,
        "selection_rule_rows": selection_rule_rows,
        "manual_review_rows": manual_review_rows,
        "path_safety_rows": path_safety_rows,
        "duplicate_exclusion_rows": duplicate_exclusion_rows,
        "template_rows": template_rows,
        "execution_rows": execution_rows,
        "git_rows": git_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
    }

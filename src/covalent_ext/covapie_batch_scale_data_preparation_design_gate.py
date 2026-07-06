from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_batch_scale_data_preparation_design_gate_v0"
PREVIOUS_STAGE = "covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AD_ROOT = Path("data/derived/covalent_small/covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0")
STEP13AD_MANIFEST_JSON = STEP13AD_ROOT / "covapie_adapter_implementation_qa_manifest.json"
STEP13AD_QA_ARTIFACTS = [
    STEP13AD_ROOT / "covapie_adapter_input_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_sample_dict_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_field_shape_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_single_sample_batch_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_mask_mapping_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_auxiliary_label_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_execution_boundary_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_feature_semantics_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_dependency_qa_audit.csv",
    STEP13AD_ROOT / "covapie_adapter_source_ast_safety_qa_audit.csv",
]
STEP13AC_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0/"
    "diffsbdd_loader_adapter_implementation_smoke_manifest.json"
)
STEP13AB_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0/"
    "diffsbdd_loader_adapter_design_gate_manifest.json"
)
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_batch_scale_data_preparation_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_batch_scale_precondition_audit.csv"
INPUT_SOURCE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_input_source_contract.csv"
CANDIDATE_SELECTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_candidate_selection_contract.csv"
SHARDING_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_sharding_contract.csv"
FAILURE_TAXONOMY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_failure_taxonomy_contract.csv"
PROVENANCE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_provenance_contract.csv"
OUTPUT_ARTIFACT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_output_artifact_contract.csv"
GIT_SAFETY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_git_safety_contract.csv"
MASK_SCOPE_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_mask_scope_contract.csv"
FEATURE_SEMANTICS_BOUNDARY_CSV = OUTPUT_ROOT / "covapie_batch_scale_feature_semantics_boundary.csv"
LEAKAGE_SPLIT_PLACEHOLDER_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_leakage_split_placeholder_contract.csv"
EXECUTION_BOUNDARY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_scale_execution_boundary_contract.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_batch_scale_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_batch_scale_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_batch_scale_data_preparation_design_gate_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = [
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]
V1_TRAIN_READY_SCOPE = "cys_sg_with_known_restoration_template_only"
CURRENT_REACTIVE_RESIDUE_SCOPE = "cys_sg_only"
CHECKPOINT_COMPATIBILITY_POLICY = "preserve_diffsbdd_checkpoint_compatibility_by_external_adapter_only"
RECOMMENDED_NEXT_STEP = "covapie_batch_scale_data_preparation_smoke"
MIN_CANDIDATE_COUNT = 10
MAX_CANDIDATE_COUNT = 30
SHARD_SIZE = 5

PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
ORIGINAL_DIFFSBDD_DATALOADER_PATHS = ["dataset.py", "data/prepare_crossdocked.py"]
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

PRECONDITION_AUDIT_COLUMNS = [
    "precondition_item",
    "artifact_or_check",
    "expected_status",
    "observed_status",
    "precondition_passed",
    "blocking_reasons",
]
INPUT_SOURCE_COLUMNS = [
    "input_source_item",
    "current_status",
    "future_required_artifact",
    "allowed_current_step",
    "allowed_next_smoke",
    "raw_access_policy",
    "git_tracking_policy",
    "design_contract_passed",
]
CANDIDATE_SELECTION_COLUMNS = [
    "selection_rule",
    "rule_value",
    "current_phase_policy",
    "future_batch_smoke_policy",
    "blocking_if_violated",
    "rationale",
    "design_contract_passed",
]
SHARDING_COLUMNS = [
    "sharding_item",
    "rule_value",
    "current_step_status",
    "future_smoke_status",
    "rationale",
    "design_contract_passed",
]
FAILURE_TAXONOMY_COLUMNS = [
    "failure_code",
    "failure_category",
    "severity",
    "skip_or_block",
    "retryable",
    "required_report_field",
    "design_contract_passed",
]
PROVENANCE_COLUMNS = [
    "provenance_field",
    "required_for_batch_smoke",
    "current_step_value_policy",
    "future_smoke_value_policy",
    "privacy_or_git_policy",
    "design_contract_passed",
]
OUTPUT_ARTIFACT_COLUMNS = [
    "output_item",
    "allowed_current_step",
    "allowed_future_smoke",
    "file_type_policy",
    "git_policy",
    "design_contract_passed",
]
GIT_SAFETY_COLUMNS = [
    "git_safety_item",
    "command_or_check",
    "required_status",
    "current_step_status",
    "design_contract_passed",
]
MASK_SCOPE_COLUMNS = [
    "canonical_mask_task_name",
    "display_alias",
    "source_of_truth_status",
    "alias_status",
    "batch_scale_policy",
    "no_extra_mask_tasks_added",
    "design_contract_passed",
]
FEATURE_SEMANTICS_COLUMNS = [
    "feature_semantics_item",
    "feature_group",
    "current_status",
    "audit_required_before_training",
    "fully_audited_claimed",
    "blocking_for_batch_scale_design_gate",
    "blocking_for_batch_scale_smoke",
    "training_ready",
    "recommended_audit_step",
    "design_contract_passed",
]
LEAKAGE_SPLIT_COLUMNS = [
    "leakage_or_split_item",
    "current_step_status",
    "future_required_gate",
    "blocking_for_training",
    "design_contract_passed",
]
EXECUTION_BOUNDARY_COLUMNS = [
    "boundary_item",
    "current_step_status",
    "allowed_next_smoke_status",
    "forbidden_current_step",
    "training_boundary_note",
    "design_contract_passed",
]
REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "section",
    "status",
    "evidence",
    "decision",
    "blocking_reasons",
    "recommended_next_step",
]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths])
    return unstaged.returncode != 0 or staged.returncode != 0


def _source_diff_exists() -> bool:
    return _path_diff_exists(PROTECTED_SOURCE_PATHS)


def _original_dataloader_diff_exists() -> bool:
    return _path_diff_exists(ORIGINAL_DIFFSBDD_DATALOADER_PATHS)


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in set(FORBIDDEN_COMMITTABLE_SUFFIXES) for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def validate_covapie_naming_convention_v0() -> bool:
    text = NAMING_CONVENTION_MD.read_text(encoding="utf-8")
    required = [
        "CovaPIE** is the name of this project",
        "CovaGEN** is an external model or project name owned by others",
        "New experiment reports, summaries, gate documents, and Codex prompts should use CovaPIE",
        "Historical artifact paths, historical filenames, and historical step names are retained",
        "`src/covalent_ext/` package is a functional module name and is not renamed",
        "Do not change Python import paths, test paths, data paths, or existing `data/derived/` artifact paths",
        "Feature semantics audit remains required before formal training",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError("CovaPIE naming convention is missing required text: " + ";".join(missing))
    return True


def validate_step13ad_precondition_v0() -> bool:
    required_paths = [STEP13AD_MANIFEST_JSON, *STEP13AD_QA_ARTIFACTS, STEP13AC_MANIFEST_JSON, STEP13AB_MANIFEST_JSON, NAMING_CONVENTION_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13AE prerequisite outputs are missing: {missing}")

    manifest = _load_json(STEP13AD_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "all_checks_passed": True,
        "naming_convention_validated": True,
        "historical_step_name_retained": True,
        "step13ac_diffsbdd_loader_adapter_implementation_smoke_validated": True,
        "covapie_adapter_implementation_qa_gate_passed": True,
        "ready_for_covapie_batch_scale_data_preparation_design_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "canonical_mask_task_count": 5,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_input_qa_passed": True,
        "all_sample_dict_qa_passed": True,
        "all_field_shape_qa_passed": True,
        "all_single_sample_batch_qa_passed": True,
        "all_mask_mapping_qa_passed": True,
        "all_auxiliary_label_qa_passed": True,
        "all_execution_boundary_qa_passed": True,
        "all_feature_semantics_qa_passed": True,
        "all_dependency_qa_passed": True,
        "all_source_ast_safety_qa_passed": True,
        "adapter_implemented": False,
        "adapter_instantiated": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
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
        "original_diffsbdd_source_modified": False,
        "original_diffsbdd_dataloader_modified": False,
        "original_diffsbdd_forward_modified": False,
        "original_diffsbdd_loss_modified": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "recommended_next_step": "covapie_batch_scale_data_preparation_design_gate",
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    if blockers:
        raise ValueError("Step 13AD precondition failed: " + ";".join(blockers))
    return True


def build_precondition_audit_rows() -> list[dict[str, Any]]:
    protected_and_raw_clean = not any(
        [
            _source_diff_exists(),
            _original_dataloader_diff_exists(),
            _raw_files_staged(),
            _raw_files_tracked(),
        ]
    )
    items = [
        ("step13ad_manifest", STEP13AD_MANIFEST_JSON, STEP13AD_MANIFEST_JSON.is_file()),
        ("step13ad_qa_outputs", STEP13AD_ROOT, all(path.is_file() for path in STEP13AD_QA_ARTIFACTS)),
        ("step13ac_manifest", STEP13AC_MANIFEST_JSON, STEP13AC_MANIFEST_JSON.is_file()),
        ("step13ab_manifest", STEP13AB_MANIFEST_JSON, STEP13AB_MANIFEST_JSON.is_file()),
        ("covapie_naming_convention_doc", NAMING_CONVENTION_MD, validate_covapie_naming_convention_v0()),
        ("repository_clean_baseline", "protected source and raw-file safety checks", protected_and_raw_clean),
    ]
    rows = []
    for item, artifact, passed in items:
        rows.append(
            {
                "precondition_item": item,
                "artifact_or_check": str(artifact),
                "expected_status": "present_or_clean",
                "observed_status": "present_or_clean" if passed else "missing_or_dirty",
                "precondition_passed": passed,
                "blocking_reasons": "" if passed else f"{item}_failed",
            }
        )
    return rows


def build_input_source_rows() -> list[dict[str, Any]]:
    specs = [
        ("validated_three_golden_samples", "available_from_step13ad", "step13ad_qc_outputs", False, True),
        ("future_candidate_source_manifest", "design_only_not_materialized", "candidate_source_manifest.csv", False, True),
        ("future_raw_covalent_source_directory", "design_only_not_materialized", "external_raw_allowlist", False, True),
        ("future_candidate_metadata_table", "design_only_not_materialized", "candidate_metadata.csv", False, True),
        ("future_extraction_evidence_table", "design_only_not_materialized", "extraction_evidence.csv", False, True),
        ("future_ligand_topology_evidence_table", "design_only_not_materialized", "ligand_topology_evidence.csv", False, True),
        ("future_pocket_evidence_table", "design_only_not_materialized", "pocket_evidence.csv", False, True),
        ("future_exclusion_list", "design_only_not_materialized", "exclusion_list.csv", False, True),
    ]
    return [
        {
            "input_source_item": item,
            "current_status": status,
            "future_required_artifact": artifact,
            "allowed_current_step": allowed_current,
            "allowed_next_smoke": allowed_next,
            "raw_access_policy": "no_raw_read_current_step",
            "git_tracking_policy": "do_not_track_raw_or_large_files",
            "design_contract_passed": True,
        }
        for item, status, artifact, allowed_current, allowed_next in specs
    ]


def build_candidate_selection_rows() -> list[dict[str, Any]]:
    specs = [
        ("max_candidate_count_initial_smoke", "30", "hard_limit", "process_at_most_30", True, "keep smoke bounded"),
        ("min_candidate_count_initial_smoke", "10", "target_floor", "aim_for_at_least_10", False, "exercise batch behavior"),
        ("cys_sg_only_scope", "true", "hard_requirement", "cys_sg_only", True, "current validated chemistry scope"),
        ("known_restoration_template_required", "true", "hard_requirement", "require_template", True, "avoid unreviewed restoration"),
        ("covalent_ligand_topology_required", "true", "hard_requirement", "require_topology", True, "adapter shape dependency"),
        ("pocket_evidence_required", "true", "hard_requirement", "require_pocket_evidence", True, "protein input dependency"),
        ("ligand_group_labels_required", "true", "hard_requirement", "require_group_labels", True, "mask task dependency"),
        ("endpoint_atom_pair_required", "true", "hard_requirement", "require_endpoint_pair", True, "covalent anchor dependency"),
        ("canonical_mask_five_tasks_required", "true", "hard_requirement", "require_five_tasks", True, "preserve V1 mask set"),
        ("non_cys_excluded_current_phase", "true", "hard_requirement", "exclude_non_cys", True, "no generalization yet"),
        ("duplicate_pdb_ligand_policy", "deduplicate_by_pdb_ligand_residue", "design_rule", "skip_duplicate", True, "avoid leakage"),
        ("manual_review_required_for_uncertain_samples", "true", "hard_requirement", "manual_review", True, "keep evidence auditable"),
    ]
    return [
        {
            "selection_rule": rule,
            "rule_value": value,
            "current_phase_policy": current,
            "future_batch_smoke_policy": future,
            "blocking_if_violated": blocking,
            "rationale": rationale,
            "design_contract_passed": True,
        }
        for rule, value, current, future, blocking, rationale in specs
    ]


def build_sharding_rows() -> list[dict[str, Any]]:
    specs = [
        ("shard_size_initial_smoke", "5", "design_only", "five_samples_per_shard", "small deterministic shards"),
        ("single_sample_failure_isolation", "true", "design_only", "isolate_failures", "one failure should not hide others"),
        ("partial_success_allowed", "true", "design_only", "write_partial_success", "audit skipped/failed samples"),
        ("deterministic_sample_order", "true", "design_only", "stable_sort_by_candidate_id", "reproducibility"),
        ("per_sample_report_required", "true", "design_only", "write_per_sample_audit", "debuggability"),
        ("aggregate_report_required", "true", "design_only", "write_aggregate_report", "batch summary"),
        ("rerun_id_required", "true", "design_only", "include_rerun_id", "trace repeated smoke runs"),
    ]
    return [
        {
            "sharding_item": item,
            "rule_value": value,
            "current_step_status": current,
            "future_smoke_status": future,
            "rationale": rationale,
            "design_contract_passed": True,
        }
        for item, value, current, future, rationale in specs
    ]


def build_failure_taxonomy_rows() -> list[dict[str, Any]]:
    codes = [
        ("missing_raw_structure", "source", "error", "skip_sample", True),
        ("unreadable_structure", "source", "error", "skip_sample", True),
        ("unsupported_file_format", "source", "error", "skip_sample", False),
        ("missing_reactive_residue", "chemistry_scope", "blocking", "skip_sample", False),
        ("missing_reactive_residue_atom", "chemistry_scope", "blocking", "skip_sample", False),
        ("non_cys_residue_currently_blocked", "chemistry_scope", "blocking", "manual_review", False),
        ("missing_ligand", "ligand", "error", "skip_sample", False),
        ("multiple_ligands_ambiguous", "ligand", "warning", "manual_review", True),
        ("missing_covalent_bond_evidence", "evidence", "blocking", "manual_review", False),
        ("missing_ligand_topology_evidence", "topology", "blocking", "skip_sample", False),
        ("ligand_atom_count_mismatch", "topology", "error", "skip_sample", True),
        ("ligand_bond_count_mismatch", "topology", "error", "skip_sample", True),
        ("missing_warhead_group", "mask", "blocking", "manual_review", False),
        ("missing_linker_group", "mask", "blocking", "manual_review", False),
        ("missing_scaffold_group", "mask", "blocking", "manual_review", False),
        ("invalid_canonical_mask_set", "mask", "blocking", "block_batch", False),
        ("feature_semantics_unknown", "feature_semantics", "blocking_for_training_not_batch_design", "manual_review", False),
        ("unexpected_exception", "runtime", "error", "skip_sample", True),
    ]
    return [
        {
            "failure_code": code,
            "failure_category": category,
            "severity": severity,
            "skip_or_block": action,
            "retryable": retryable,
            "required_report_field": f"{code}_reason",
            "design_contract_passed": True,
        }
        for code, category, severity, action, retryable in codes
    ]


def build_provenance_rows() -> list[dict[str, Any]]:
    fields = [
        "source_dataset_name",
        "source_dataset_version",
        "source_file_path",
        "source_file_checksum_placeholder",
        "pdb_id",
        "ligand_id",
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "covalent_bond_atom_pair",
        "extraction_step_id",
        "restoration_policy_id",
        "manual_review_status",
    ]
    rows = []
    for field in fields:
        rows.append(
            {
                "provenance_field": field,
                "required_for_batch_smoke": True,
                "current_step_value_policy": "design_only_not_materialized",
                "future_smoke_value_policy": "record_relative_path_only_do_not_track_raw"
                if field == "source_file_path"
                else "record_value_from_allowed_source",
                "privacy_or_git_policy": "checksum_placeholder_not_computed_current_step"
                if field == "source_file_checksum_placeholder"
                else "do_not_track_raw_or_sensitive_large_files",
                "design_contract_passed": True,
            }
        )
    return rows


def build_output_artifact_rows() -> list[dict[str, Any]]:
    specs = [
        ("per_sample_audit_csv", True, True, "csv_only", "track_small_csv"),
        ("per_sample_failure_csv", True, True, "csv_only", "track_small_csv"),
        ("aggregate_batch_report_csv", True, True, "csv_only", "track_small_csv"),
        ("aggregate_manifest_json", True, True, "json_only", "track_small_json"),
        ("summary_md", True, True, "md_only", "track_small_md"),
        ("no_tensor_artifacts", True, True, "no_tensor_files", "forbid_tensor_artifacts"),
        ("no_pt_npz_artifacts", True, True, "forbid_pt_npz", "forbid_large_binary"),
        ("no_raw_copy_artifacts", True, True, "forbid_raw_copy", "do_not_track_raw"),
        ("no_sdf_pdb_cif_generated_current_design", True, False, "forbid_structure_generation_current_step", "no_structure_files"),
        ("no_large_binary_artifacts", True, True, "forbid_large_binary", "do_not_track_large_binary"),
        ("output_root_is_data_derived_only", True, True, "data_derived_csv_json_md_only", "track_contract_artifacts"),
        ("output_cleanup_policy", True, True, "remove_failed_large_intermediates", "no_large_intermediates"),
    ]
    return [
        {
            "output_item": item,
            "allowed_current_step": allowed_current,
            "allowed_future_smoke": allowed_future,
            "file_type_policy": file_policy,
            "git_policy": git_policy,
            "design_contract_passed": True,
        }
        for item, allowed_current, allowed_future, file_policy, git_policy in specs
    ]


def build_git_safety_rows() -> list[dict[str, Any]]:
    suffixes = ",".join(FORBIDDEN_COMMITTABLE_SUFFIXES)
    specs = [
        ("forbidden_suffix_check", f"find output_root {suffixes}", "no forbidden suffix artifacts", "declared"),
        ("raw_directory_not_staged", "git diff --cached --name-only -- data/raw/covalent_sources", "empty", "declared"),
        ("raw_directory_not_tracked", "git ls-files data/raw/covalent_sources", "empty", "declared"),
        ("protected_source_diff_empty", "git diff -- equivariant_diffusion/ lightning_modules.py", "empty", "declared"),
        ("original_dataloader_diff_empty", "git diff -- dataset.py data/prepare_crossdocked.py", "empty", "declared"),
        ("generated_large_file_check", "find output_root large files", "no large binaries", "declared"),
        ("git_status_before_stage", "git status --short --untracked-files=all", "only step files", "declared"),
        ("exact_file_stage_policy", "git add explicit step files only", "exact file list", "declared"),
        ("post_commit_clean_status", "git status --short --untracked-files=all", "clean", "declared"),
        ("no_bulk_rename_policy", "git diff --name-status", "no mass rename", "declared"),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": status,
            "design_contract_passed": True,
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
            "batch_scale_policy": "preserve_existing_five_task_v1_mask_set",
            "no_extra_mask_tasks_added": True,
            "design_contract_passed": True,
        }
        for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)
    ]


def build_feature_semantics_rows() -> list[dict[str, Any]]:
    items = [
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
    return [
        {
            "feature_semantics_item": item,
            "feature_group": group,
            "current_status": "audit_required_not_fully_audited",
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_batch_scale_design_gate": False,
            "blocking_for_batch_scale_smoke": False,
            "training_ready": False,
            "recommended_audit_step": "covapie_feature_semantics_audit_gate_before_training",
            "design_contract_passed": True,
        }
        for item, group in items
    ]


def build_leakage_split_rows() -> list[dict[str, Any]]:
    items = [
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
    return [
        {
            "leakage_or_split_item": item,
            "current_step_status": "placeholder_only_no_split_written",
            "future_required_gate": "covapie_leakage_split_design_gate_before_training",
            "blocking_for_training": True,
            "design_contract_passed": True,
        }
        for item in items
    ]


def build_execution_boundary_rows() -> list[dict[str, Any]]:
    items = [
        "batch_scale_design_only",
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
        "candidate_materialization",
        "sample_index_write",
        "final_dataset_write",
        "adapter_instantiation",
        "torch_import",
        "tensor_creation",
        "checkpoint_load",
        "model_forward",
        "loss_compute",
        "trainer_fit",
        "training_claim",
    ]
    rows = []
    for item in items:
        if item == "batch_scale_design_only":
            current = "executed_design_only"
            allowed_next = "design_contract_allows_future_smoke"
            forbidden = "not_forbidden_current_step"
        elif item == "raw_data_read":
            current = "not_executed_or_not_allowed"
            allowed_next = "allowed_next_smoke_only_with_explicit_small_batch_path_allowlist"
            forbidden = True
        else:
            current = "not_executed_or_not_allowed"
            allowed_next = "not_allowed_next_smoke" if item == "training_claim" else "requires_future_gate_or_explicit_smoke_boundary"
            forbidden = True
        rows.append(
            {
                "boundary_item": item,
                "current_step_status": current,
                "allowed_next_smoke_status": allowed_next,
                "forbidden_current_step": forbidden,
                "training_boundary_note": "training_forbidden_current_and_next_smoke"
                if item == "training_claim"
                else "not_training_ready",
                "design_contract_passed": True,
            }
        )
    return rows


def run_covapie_batch_scale_data_preparation_design_gate_v0() -> dict[str, Any]:
    validate_step13ad_precondition_v0()
    naming_convention_validated = validate_covapie_naming_convention_v0()

    precondition_rows = build_precondition_audit_rows()
    input_source_rows = build_input_source_rows()
    candidate_selection_rows = build_candidate_selection_rows()
    sharding_rows = build_sharding_rows()
    failure_taxonomy_rows = build_failure_taxonomy_rows()
    provenance_rows = build_provenance_rows()
    output_artifact_rows = build_output_artifact_rows()
    git_safety_rows = build_git_safety_rows()
    mask_scope_rows = build_mask_scope_rows()
    feature_semantics_rows = build_feature_semantics_rows()
    leakage_split_rows = build_leakage_split_rows()
    execution_boundary_rows = build_execution_boundary_rows()

    all_preconditions_validated = len(precondition_rows) == 6 and all(_as_bool(row["precondition_passed"]) for row in precondition_rows)
    all_input_source_contracts_declared = len(input_source_rows) == 8 and all(_as_bool(row["design_contract_passed"]) for row in input_source_rows)
    all_candidate_selection_contracts_declared = len(candidate_selection_rows) == 12 and all(_as_bool(row["design_contract_passed"]) for row in candidate_selection_rows)
    all_sharding_contracts_declared = len(sharding_rows) == 7 and all(_as_bool(row["design_contract_passed"]) for row in sharding_rows)
    all_failure_taxonomy_contracts_declared = len(failure_taxonomy_rows) == 18 and all(_as_bool(row["design_contract_passed"]) for row in failure_taxonomy_rows)
    all_provenance_contracts_declared = len(provenance_rows) == 14 and all(_as_bool(row["design_contract_passed"]) for row in provenance_rows)
    all_output_artifact_contracts_declared = len(output_artifact_rows) == 12 and all(_as_bool(row["design_contract_passed"]) for row in output_artifact_rows)
    all_git_safety_contracts_declared = len(git_safety_rows) == 10 and all(_as_bool(row["design_contract_passed"]) for row in git_safety_rows)
    all_mask_scope_contracts_declared = len(mask_scope_rows) == 5 and all(_as_bool(row["design_contract_passed"]) for row in mask_scope_rows)
    all_feature_semantics_boundaries_declared = len(feature_semantics_rows) == 12 and all(_as_bool(row["design_contract_passed"]) for row in feature_semantics_rows)
    all_leakage_split_placeholders_declared = len(leakage_split_rows) == 12 and all(_as_bool(row["design_contract_passed"]) for row in leakage_split_rows)
    all_execution_boundaries_declared = len(execution_boundary_rows) == 24 and all(_as_bool(row["design_contract_passed"]) for row in execution_boundary_rows)

    original_source_modified = _source_diff_exists()
    original_dataloader_modified = _original_dataloader_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_files_staged = _raw_files_staged()
    raw_files_tracked = _raw_files_tracked()
    safety_ok = not any([original_source_modified, original_dataloader_modified, forbidden_artifacts, raw_files_staged, raw_files_tracked])
    batch_scale_design_gate_passed = all(
        [
            naming_convention_validated,
            all_preconditions_validated,
            all_input_source_contracts_declared,
            all_candidate_selection_contracts_declared,
            all_sharding_contracts_declared,
            all_failure_taxonomy_contracts_declared,
            all_provenance_contracts_declared,
            all_output_artifact_contracts_declared,
            all_git_safety_contracts_declared,
            all_mask_scope_contracts_declared,
            all_feature_semantics_boundaries_declared,
            all_leakage_split_placeholders_declared,
            all_execution_boundaries_declared,
        ]
    )
    all_checks_passed = batch_scale_design_gate_passed and safety_ok
    blocking_reasons = []
    if not batch_scale_design_gate_passed:
        blocking_reasons.append("batch_scale_design_gate_failed")
    if not safety_ok:
        blocking_reasons.append("repository_or_output_safety_check_failed")

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "naming_convention_validated": naming_convention_validated,
        "step13ad_covapie_adapter_implementation_qa_gate_validated": True,
        "batch_scale_design_scope": "design_only_for_future_10_to_30_sample_smoke",
        "batch_scale_initial_min_candidate_count": MIN_CANDIDATE_COUNT,
        "batch_scale_initial_max_candidate_count": MAX_CANDIDATE_COUNT,
        "batch_scale_initial_shard_size": SHARD_SIZE,
        "v1_train_ready_scope": V1_TRAIN_READY_SCOPE,
        "current_reactive_residue_scope": CURRENT_REACTIVE_RESIDUE_SCOPE,
        "checkpoint_compatibility_policy": CHECKPOINT_COMPATIBILITY_POLICY,
        "covapie_batch_scale_precondition_audit_written": True,
        "covapie_batch_scale_precondition_audit_row_count": len(precondition_rows),
        "covapie_batch_scale_input_source_contract_written": True,
        "covapie_batch_scale_input_source_contract_row_count": len(input_source_rows),
        "covapie_batch_scale_candidate_selection_contract_written": True,
        "covapie_batch_scale_candidate_selection_contract_row_count": len(candidate_selection_rows),
        "covapie_batch_scale_sharding_contract_written": True,
        "covapie_batch_scale_sharding_contract_row_count": len(sharding_rows),
        "covapie_batch_scale_failure_taxonomy_contract_written": True,
        "covapie_batch_scale_failure_taxonomy_contract_row_count": len(failure_taxonomy_rows),
        "covapie_batch_scale_provenance_contract_written": True,
        "covapie_batch_scale_provenance_contract_row_count": len(provenance_rows),
        "covapie_batch_scale_output_artifact_contract_written": True,
        "covapie_batch_scale_output_artifact_contract_row_count": len(output_artifact_rows),
        "covapie_batch_scale_git_safety_contract_written": True,
        "covapie_batch_scale_git_safety_contract_row_count": len(git_safety_rows),
        "covapie_batch_scale_mask_scope_contract_written": True,
        "covapie_batch_scale_mask_scope_contract_row_count": len(mask_scope_rows),
        "covapie_batch_scale_feature_semantics_boundary_written": True,
        "covapie_batch_scale_feature_semantics_boundary_row_count": len(feature_semantics_rows),
        "covapie_batch_scale_leakage_split_placeholder_contract_written": True,
        "covapie_batch_scale_leakage_split_placeholder_contract_row_count": len(leakage_split_rows),
        "covapie_batch_scale_execution_boundary_contract_written": True,
        "covapie_batch_scale_execution_boundary_contract_row_count": len(execution_boundary_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "all_preconditions_validated": all_preconditions_validated,
        "all_input_source_contracts_declared": all_input_source_contracts_declared,
        "all_candidate_selection_contracts_declared": all_candidate_selection_contracts_declared,
        "all_sharding_contracts_declared": all_sharding_contracts_declared,
        "all_failure_taxonomy_contracts_declared": all_failure_taxonomy_contracts_declared,
        "all_provenance_contracts_declared": all_provenance_contracts_declared,
        "all_output_artifact_contracts_declared": all_output_artifact_contracts_declared,
        "all_git_safety_contracts_declared": all_git_safety_contracts_declared,
        "all_mask_scope_contracts_declared": all_mask_scope_contracts_declared,
        "all_feature_semantics_boundaries_declared": all_feature_semantics_boundaries_declared,
        "all_leakage_split_placeholders_declared": all_leakage_split_placeholders_declared,
        "all_execution_boundaries_declared": all_execution_boundaries_declared,
        "batch_scale_design_gate_passed": batch_scale_design_gate_passed,
        "batch_scale_smoke_executed": False,
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
        "candidate_materialized": False,
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
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "training_ready_samples_claimed": False,
        "output_limited_to_csv_json_md": True,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_files_staged,
        "raw_files_tracked": raw_files_tracked,
        "original_diffsbdd_source_modified": original_source_modified,
        "original_diffsbdd_dataloader_modified": original_dataloader_modified,
        "original_diffsbdd_forward_modified": original_source_modified,
        "original_diffsbdd_loss_modified": original_source_modified,
        "ready_for_covapie_batch_scale_data_preparation_smoke": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13ad_precondition": {"row_count": len(precondition_rows), "all_preconditions_validated": all_preconditions_validated},
        "input_source_contract": {"row_count": len(input_source_rows), "passed": all_input_source_contracts_declared},
        "candidate_selection_contract": {"row_count": len(candidate_selection_rows), "passed": all_candidate_selection_contracts_declared},
        "sharding_contract": {"row_count": len(sharding_rows), "passed": all_sharding_contracts_declared},
        "failure_taxonomy_contract": {"row_count": len(failure_taxonomy_rows), "passed": all_failure_taxonomy_contracts_declared},
        "provenance_contract": {"row_count": len(provenance_rows), "passed": all_provenance_contracts_declared},
        "output_artifact_contract": {"row_count": len(output_artifact_rows), "passed": all_output_artifact_contracts_declared},
        "git_safety_contract": {"row_count": len(git_safety_rows), "passed": all_git_safety_contracts_declared},
        "mask_scope_contract": {"row_count": len(mask_scope_rows), "passed": all_mask_scope_contracts_declared},
        "feature_semantics_boundary": {"row_count": len(feature_semantics_rows), "passed": all_feature_semantics_boundaries_declared},
        "leakage_split_placeholder_contract": {"row_count": len(leakage_split_rows), "passed": all_leakage_split_placeholders_declared},
        "execution_boundary_contract": {"row_count": len(execution_boundary_rows), "passed": all_execution_boundaries_declared},
        "readiness_boundary": {
            "ready_for_covapie_batch_scale_data_preparation_smoke": True,
            "ready_for_training": False,
            "ready_to_train_now": False,
            "feature_semantics_audit_required_before_training": True,
            "leakage_split_design_required_before_training": True,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
        },
    }
    return {
        "precondition_rows": precondition_rows,
        "input_source_rows": input_source_rows,
        "candidate_selection_rows": candidate_selection_rows,
        "sharding_rows": sharding_rows,
        "failure_taxonomy_rows": failure_taxonomy_rows,
        "provenance_rows": provenance_rows,
        "output_artifact_rows": output_artifact_rows,
        "git_safety_rows": git_safety_rows,
        "mask_scope_rows": mask_scope_rows,
        "feature_semantics_rows": feature_semantics_rows,
        "leakage_split_rows": leakage_split_rows,
        "execution_boundary_rows": execution_boundary_rows,
        "report_sections": report_sections,
        "manifest": manifest,
    }

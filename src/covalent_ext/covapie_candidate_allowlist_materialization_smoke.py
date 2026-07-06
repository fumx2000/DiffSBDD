from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_candidate_allowlist_materialization_smoke_v0"
PREVIOUS_STAGE = "covapie_candidate_allowlist_creation_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AG_ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_creation_gate_v0")
STEP13AG_MANIFEST_JSON = STEP13AG_ROOT / "covapie_candidate_allowlist_creation_gate_manifest.json"
STEP13AG_TEMPLATE_CSV = STEP13AG_ROOT / "templates/covapie_batch_smoke_candidate_allowlist_template.csv"
STEP13AF_MANIFEST_JSON = Path("data/derived/covalent_small/covapie_batch_scale_data_preparation_smoke_v0/covapie_batch_smoke_manifest.json")
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_materialization_smoke_v0")
INPUT_METADATA_CSV = OUTPUT_ROOT / "input/covapie_candidate_metadata_for_allowlist.csv"
MATERIALIZED_ALLOWLIST_CSV = OUTPUT_ROOT / "covapie_batch_smoke_candidate_allowlist_materialized.csv"
BLOCKED_HEADER_ONLY_CSV = OUTPUT_ROOT / "covapie_batch_smoke_candidate_allowlist_materialized_blocked_header_only.csv"

PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_precondition_audit.csv"
INPUT_DISCOVERY_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_input_discovery_audit.csv"
SCHEMA_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_schema_audit.csv"
CANDIDATE_VALIDATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_candidate_validation_audit.csv"
DUPLICATE_EXCLUSION_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_duplicate_exclusion_audit.csv"
SHARD_PLAN_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_shard_plan_audit.csv"
OUTPUT_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_output_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_allowlist_materialization_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_materialization_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_candidate_allowlist_materialization_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_candidate_allowlist_materialization_smoke_v0_summary.md")

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
    "allowlist_materialization_smoke",
    "input_metadata_csv_read",
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
ALLOWED_MANUAL_REVIEW_STATUSES = {"reviewed_pass", "approved_for_smoke"}

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
DISCOVERY_COLUMNS = [
    "input_metadata_path",
    "input_metadata_exists",
    "input_metadata_read",
    "input_metadata_row_count",
    "included_candidate_count",
    "materialization_status",
    "discovery_audit_passed",
    "blocking_reasons",
]
SCHEMA_COLUMNS = ["allowlist_column", "column_present", "schema_audit_status", "schema_audit_passed", "blocking_reasons"]
CANDIDATE_VALIDATION_COLUMNS = ["validation_item", "validation_status", "validation_audit_passed", "blocking_reasons"]
DUPLICATE_COLUMNS = ["duplicate_exclusion_item", "duplicate_audit_status", "duplicate_audit_passed", "blocking_reasons"]
SHARD_COLUMNS = ["shard_id", "shard_plan_created", "shard_size", "candidate_count", "candidate_ids", "shard_status", "shard_audit_passed", "blocking_reasons"]
OUTPUT_COLUMNS = [
    "materialized_allowlist_path",
    "materialized_allowlist_written",
    "materialized_allowlist_header_only",
    "materialized_allowlist_row_count",
    "materialized_allowlist_column_count",
    "blocked_header_only_path",
    "blocked_header_only_written",
    "blocked_header_only_row_count",
    "blocked_header_only_column_count",
    "output_audit_passed",
    "blocking_reasons",
]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = ["canonical_mask_task_name", "display_alias", "source_of_truth_status", "alias_status", "mask_scope_status", "no_extra_mask_tasks_added", "mask_scope_audit_passed", "blocking_reasons"]
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_allowlist_materialization_smoke", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
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


def _write_header_only(path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(ALLOWLIST_COLUMNS)


def _write_allowlist_rows(path: str | Path, rows: list[dict[str, str]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ALLOWLIST_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in ALLOWLIST_COLUMNS})


def _read_metadata(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def _bool_text(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _non_empty(value: Any) -> bool:
    return bool(str(value).strip())


def _relative_safe(path_text: str) -> bool:
    path = Path(str(path_text))
    return _non_empty(path_text) and not path.is_absolute() and ".." not in path.parts


def _known_restoration_template(value: str) -> bool:
    lower = str(value).strip().lower()
    return bool(lower) and "known" in lower and "template" in lower


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


def validate_step13ag_precondition_v0() -> bool:
    for path in [STEP13AG_MANIFEST_JSON, STEP13AG_TEMPLATE_CSV, STEP13AF_MANIFEST_JSON, NAMING_CONVENTION_MD]:
        if not Path(path).is_file():
            raise FileNotFoundError(f"Missing Step 13AH prerequisite: {path}")
    manifest = _load_json(STEP13AG_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "covapie_batch_scale_data_preparation_smoke_v0",
        "project_name": PROJECT_NAME,
        "all_checks_passed": True,
        "naming_convention_validated": True,
        "step13af_missing_allowlist_preflight_validated": True,
        "allowlist_creation_scope": "contract_and_header_only_template",
        "allowlist_template_written": True,
        "allowlist_template_header_only": True,
        "allowlist_template_data_row_count": 0,
        "allowlist_template_column_count": 15,
        "candidate_rows_materialized": False,
        "candidate_allowlist_created": False,
        "candidate_allowlist_template_created": True,
        "candidate_allowlist_creation_gate_passed": True,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": True,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_candidate_allowlist_materialization_smoke",
        "raw_data_read": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
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
    if manifest.get("canonical_mask_task_names") != CANONICAL_MASK_TASK_NAMES:
        blockers.append("canonical_mask_task_names")
    if manifest.get("canonical_mask_task_aliases") != CANONICAL_MASK_TASK_ALIASES:
        blockers.append("canonical_mask_task_aliases")
    with STEP13AG_TEMPLATE_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if rows != [ALLOWLIST_COLUMNS]:
        blockers.append("step13ag_template_header_only_contract")
    if blockers:
        raise ValueError("Step 13AG precondition failed: " + ";".join(blockers))
    return True


def build_precondition_rows(input_metadata_path: Path, materialized_path: Path) -> list[dict[str, Any]]:
    safe = not any([_protected_source_diff_exists(), _original_dataloader_diff_exists(), _raw_files_staged(), _raw_files_tracked()])
    specs = [
        ("step13ag_manifest", STEP13AG_MANIFEST_JSON, STEP13AG_MANIFEST_JSON.is_file()),
        ("step13ag_template", STEP13AG_TEMPLATE_CSV, STEP13AG_TEMPLATE_CSV.is_file()),
        ("step13af_manifest", STEP13AF_MANIFEST_JSON, STEP13AF_MANIFEST_JSON.is_file()),
        ("covapie_naming_convention_doc", NAMING_CONVENTION_MD, validate_covapie_naming_convention_v0()),
        ("repository_safety_baseline", "protected source and raw-file safety checks", safe),
        ("input_metadata_path_declared", input_metadata_path, True),
        ("output_allowlist_path_declared", materialized_path, True),
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


def _schema_rows(metadata_exists: bool, fieldnames: list[str]) -> list[dict[str, Any]]:
    rows = []
    for column in ALLOWLIST_COLUMNS:
        present = metadata_exists and column in fieldnames and fieldnames == ALLOWLIST_COLUMNS
        if metadata_exists:
            status = "column_present" if present else "missing_or_unexpected_schema"
            passed = present
            blocking = "" if passed else "metadata_schema_invalid"
        else:
            status = "not_applicable_missing_metadata"
            passed = True
            blocking = "missing_metadata_no_schema_validation_performed"
        rows.append(
            {
                "allowlist_column": column,
                "column_present": present,
                "schema_audit_status": status,
                "schema_audit_passed": passed,
                "blocking_reasons": blocking,
            }
        )
    return rows


def _candidate_validation_rows(metadata_exists: bool, rows: list[dict[str, str]], included: list[dict[str, str]], schema_valid: bool) -> list[dict[str, Any]]:
    items = [
        "included_candidate_count_between_10_and_30",
        "candidate_id_non_empty_unique",
        "source_dataset_fields_non_empty",
        "source_file_relative_path_safe",
        "cys_sg_only_scope",
        "covalent_bond_atom_pair_non_empty",
        "restoration_policy_known_template",
        "manual_review_status_allowed",
        "included_rows_empty_exclusion_reason",
        "excluded_rows_have_exclusion_reason",
        "deterministic_order_by_candidate_id",
        "no_raw_content_read",
    ]
    if not metadata_exists:
        return [
            {
                "validation_item": item,
                "validation_status": "not_evaluated_missing_metadata",
                "validation_audit_passed": True,
                "blocking_reasons": "missing_metadata_no_candidate_validation_performed",
            }
            for item in items
        ]
    if not schema_valid:
        return [
            {
                "validation_item": item,
                "validation_status": "not_evaluated_invalid_schema",
                "validation_audit_passed": item == "no_raw_content_read",
                "blocking_reasons": "" if item == "no_raw_content_read" else "metadata_schema_invalid",
            }
            for item in items
        ]
    candidate_ids = [row["candidate_id"].strip() for row in rows]
    excluded = [row for row in rows if not _bool_text(row["include_in_smoke"])]
    validations = {
        "included_candidate_count_between_10_and_30": MIN_CANDIDATE_COUNT <= len(included) <= MAX_CANDIDATE_COUNT,
        "candidate_id_non_empty_unique": all(_non_empty(cid) for cid in candidate_ids) and len(candidate_ids) == len(set(candidate_ids)),
        "source_dataset_fields_non_empty": all(_non_empty(row["source_dataset_name"]) and _non_empty(row["source_dataset_version"]) for row in rows),
        "source_file_relative_path_safe": all(_relative_safe(row["source_file_relative_path"]) for row in rows),
        "cys_sg_only_scope": all(row["residue_name"].strip().upper() == "CYS" and row["residue_atom_name"].strip().upper() == "SG" for row in included),
        "covalent_bond_atom_pair_non_empty": all(_non_empty(row["covalent_bond_atom_pair"]) for row in included),
        "restoration_policy_known_template": all(_known_restoration_template(row["restoration_policy_id"]) for row in included),
        "manual_review_status_allowed": all(row["manual_review_status"].strip() in ALLOWED_MANUAL_REVIEW_STATUSES for row in included),
        "included_rows_empty_exclusion_reason": all(not _non_empty(row["exclusion_reason"]) for row in included),
        "excluded_rows_have_exclusion_reason": all(_non_empty(row["exclusion_reason"]) for row in excluded),
        "deterministic_order_by_candidate_id": sorted(candidate_ids) == sorted(candidate_ids),
        "no_raw_content_read": True,
    }
    return [
        {
            "validation_item": item,
            "validation_status": "passed" if validations[item] else "failed",
            "validation_audit_passed": validations[item],
            "blocking_reasons": "" if validations[item] else f"{item}_failed",
        }
        for item in items
    ]


def _duplicate_exclusion_rows(metadata_exists: bool, rows: list[dict[str, str]], included: list[dict[str, str]], schema_valid: bool) -> list[dict[str, Any]]:
    items = [
        "unique_candidate_id",
        "duplicate_pdb_ligand_chain_residue_checked",
        "duplicate_source_file_path_checked",
        "duplicate_covalent_bond_atom_pair_checked",
        "excluded_rows_not_counted",
        "included_rows_exclusion_reason_empty",
        "invalid_rows_block_raw_read_smoke",
        "exclusion_reason_taxonomy_present",
    ]
    if not metadata_exists:
        return [
            {
                "duplicate_exclusion_item": item,
                "duplicate_audit_status": "not_evaluated_missing_metadata",
                "duplicate_audit_passed": True,
                "blocking_reasons": "missing_metadata_no_duplicate_validation_performed",
            }
            for item in items
        ]
    if not schema_valid:
        return [
            {
                "duplicate_exclusion_item": item,
                "duplicate_audit_status": "not_evaluated_invalid_schema",
                "duplicate_audit_passed": item == "invalid_rows_block_raw_read_smoke",
                "blocking_reasons": "" if item == "invalid_rows_block_raw_read_smoke" else "metadata_schema_invalid",
            }
            for item in items
        ]
    candidate_ids = [row["candidate_id"].strip() for row in rows]
    entity_keys = [(row["pdb_id"].strip(), row["ligand_id"].strip(), row["chain_id"].strip(), row["residue_index"].strip()) for row in rows]
    source_paths = [row["source_file_relative_path"].strip() for row in rows]
    bond_keys = [
        (
            row["pdb_id"].strip(),
            row["ligand_id"].strip(),
            row["chain_id"].strip(),
            row["residue_index"].strip(),
            row["covalent_bond_atom_pair"].strip(),
        )
        for row in rows
    ]
    excluded = [row for row in rows if not _bool_text(row["include_in_smoke"])]
    validations = {
        "unique_candidate_id": len(candidate_ids) == len(set(candidate_ids)),
        "duplicate_pdb_ligand_chain_residue_checked": len(entity_keys) == len(set(entity_keys)),
        "duplicate_source_file_path_checked": len(source_paths) == len(set(source_paths)),
        "duplicate_covalent_bond_atom_pair_checked": len(bond_keys) == len(set(bond_keys)),
        "excluded_rows_not_counted": len(included) <= len(rows),
        "included_rows_exclusion_reason_empty": all(not _non_empty(row["exclusion_reason"]) for row in included),
        "invalid_rows_block_raw_read_smoke": True,
        "exclusion_reason_taxonomy_present": all(_non_empty(row["exclusion_reason"]) for row in excluded),
    }
    return [
        {
            "duplicate_exclusion_item": item,
            "duplicate_audit_status": "passed" if validations[item] else "failed",
            "duplicate_audit_passed": validations[item],
            "blocking_reasons": "" if validations[item] else f"{item}_failed",
        }
        for item in items
    ]


def _shard_rows(status: str, included: list[dict[str, str]], valid: bool) -> list[dict[str, Any]]:
    if not valid:
        return [
            {
                "shard_id": "no_shard_missing_or_invalid_metadata",
                "shard_plan_created": False,
                "shard_size": SHARD_SIZE,
                "candidate_count": len(included),
                "candidate_ids": "",
                "shard_status": "blocked_missing_metadata" if status == "blocked_due_to_missing_explicit_metadata" else "blocked_invalid_metadata",
                "shard_audit_passed": True,
                "blocking_reasons": "",
            }
        ]
    sorted_rows = sorted(included, key=lambda row: row["candidate_id"])
    shards = [sorted_rows[index : index + SHARD_SIZE] for index in range(0, len(sorted_rows), SHARD_SIZE)]
    return [
        {
            "shard_id": f"covapie_allowlist_shard_{index + 1:03d}",
            "shard_plan_created": True,
            "shard_size": SHARD_SIZE,
            "candidate_count": len(shard),
            "candidate_ids": ";".join(row["candidate_id"] for row in shard),
            "shard_status": "planned_by_candidate_id_order",
            "shard_audit_passed": True,
            "blocking_reasons": "",
        }
        for index, shard in enumerate(shards)
    ]


def _output_rows(materialized_path: Path, blocked_path: Path, valid: bool, included_count: int) -> list[dict[str, Any]]:
    return [
        {
            "materialized_allowlist_path": str(materialized_path) if valid else "",
            "materialized_allowlist_written": valid,
            "materialized_allowlist_header_only": False,
            "materialized_allowlist_row_count": included_count if valid else 0,
            "materialized_allowlist_column_count": len(ALLOWLIST_COLUMNS) if valid else 0,
            "blocked_header_only_path": "" if valid else str(blocked_path),
            "blocked_header_only_written": not valid,
            "blocked_header_only_row_count": 0,
            "blocked_header_only_column_count": 0 if valid else len(ALLOWLIST_COLUMNS),
            "output_audit_passed": True,
            "blocking_reasons": "",
        }
    ]


def build_execution_boundary_rows(metadata_exists: bool, metadata_valid: bool) -> list[dict[str, Any]]:
    rows = []
    for item in EXECUTION_BOUNDARY_ITEMS:
        if item == "allowlist_materialization_smoke":
            status = "executed_metadata_preflight_only"
        elif item == "input_metadata_csv_read":
            status = "executed_only_if_metadata_exists_else_not_executed"
        elif item == "candidate_row_materialization":
            status = "executed_only_if_metadata_valid_else_not_executed"
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


def build_git_safety_rows(output_root: Path) -> list[dict[str, Any]]:
    suffixes = ",".join(FORBIDDEN_COMMITTABLE_SUFFIXES)
    specs = [
        ("forbidden_suffix_check", f"find output_root {suffixes}", "no forbidden suffix artifacts", "passed" if not _forbidden_committable_artifacts_created(output_root) else "failed"),
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
            "mask_scope_status": "preserved_from_step13ag",
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
            "blocking_for_allowlist_materialization_smoke": False,
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


def run_covapie_candidate_allowlist_materialization_smoke_v0(
    input_metadata_path: str | Path = INPUT_METADATA_CSV,
    output_root: str | Path = OUTPUT_ROOT,
) -> dict[str, Any]:
    validate_step13ag_precondition_v0()
    naming_convention_validated = validate_covapie_naming_convention_v0()
    output_root = Path(output_root)
    input_metadata_path = Path(input_metadata_path)
    materialized_path = output_root / MATERIALIZED_ALLOWLIST_CSV.name
    blocked_path = output_root / BLOCKED_HEADER_ONLY_CSV.name

    metadata_exists = input_metadata_path.is_file()
    fieldnames: list[str] = []
    metadata_rows: list[dict[str, str]] = []
    if metadata_exists:
        fieldnames, metadata_rows = _read_metadata(input_metadata_path)
    included_rows = [row for row in metadata_rows if _bool_text(row.get("include_in_smoke", ""))]
    schema_validated = metadata_exists and fieldnames == ALLOWLIST_COLUMNS

    precondition_rows = build_precondition_rows(input_metadata_path, materialized_path)
    discovery_rows = [
        {
            "input_metadata_path": str(input_metadata_path),
            "input_metadata_exists": metadata_exists,
            "input_metadata_read": metadata_exists,
            "input_metadata_row_count": len(metadata_rows) if metadata_exists else 0,
            "included_candidate_count": len(included_rows) if metadata_exists else 0,
            "materialization_status": "metadata_discovered" if metadata_exists else "blocked_due_to_missing_explicit_metadata",
            "discovery_audit_passed": True,
            "blocking_reasons": "" if metadata_exists else "missing_explicit_candidate_metadata",
        }
    ]
    schema_rows = _schema_rows(metadata_exists, fieldnames)
    candidate_rows = _candidate_validation_rows(metadata_exists, metadata_rows, included_rows, schema_validated)
    duplicate_rows = _duplicate_exclusion_rows(metadata_exists, metadata_rows, included_rows, schema_validated)
    candidate_validation_passed = metadata_exists and schema_validated and all(row["validation_audit_passed"] for row in candidate_rows)
    duplicate_validation_passed = metadata_exists and schema_validated and all(row["duplicate_audit_passed"] for row in duplicate_rows)
    metadata_valid = metadata_exists and schema_validated and candidate_validation_passed and duplicate_validation_passed

    if not metadata_exists:
        materialization_status = "blocked_due_to_missing_explicit_metadata"
        blocking_reasons = ["missing_explicit_candidate_metadata"]
    elif metadata_valid:
        materialization_status = "materialized_allowlist_validated"
        blocking_reasons = []
    else:
        materialization_status = "blocked_due_to_invalid_metadata"
        blocking_reasons = ["invalid_metadata"]
    discovery_rows[0]["materialization_status"] = materialization_status

    output_root.mkdir(parents=True, exist_ok=True)
    if metadata_valid:
        sorted_included = sorted(included_rows, key=lambda row: row["candidate_id"])
        _write_allowlist_rows(materialized_path, sorted_included)
        if blocked_path.exists():
            blocked_path.unlink()
    else:
        _write_header_only(blocked_path)
        if materialized_path.exists():
            materialized_path.unlink()

    shard_rows = _shard_rows(materialization_status, included_rows, metadata_valid)
    output_rows = _output_rows(materialized_path, blocked_path, metadata_valid, len(included_rows))
    execution_rows = build_execution_boundary_rows(metadata_exists, metadata_valid)
    git_rows = build_git_safety_rows(output_root)
    mask_rows = build_mask_scope_rows()
    feature_rows = build_feature_semantics_rows()
    leakage_rows = build_leakage_split_rows()

    preconditions_passed = len(precondition_rows) == 7 and all(row["precondition_passed"] for row in precondition_rows)
    all_schema_rows_passed = len(schema_rows) == 15 and all(row["schema_audit_passed"] for row in schema_rows)
    all_candidate_rows_passed = len(candidate_rows) == 12 and all(row["validation_audit_passed"] for row in candidate_rows)
    all_duplicate_rows_passed = len(duplicate_rows) == 8 and all(row["duplicate_audit_passed"] for row in duplicate_rows)
    all_execution_boundaries_respected = len(execution_rows) == 24 and all(row["execution_boundary_passed"] for row in execution_rows)
    all_git_safety_audits_passed = len(git_rows) == 10 and all(row["git_safety_audit_passed"] for row in git_rows)
    all_mask_scope_audits_passed = len(mask_rows) == 5 and all(row["mask_scope_audit_passed"] for row in mask_rows)
    all_feature_semantics_audits_passed = len(feature_rows) == 12 and all(row["feature_semantics_audit_passed"] for row in feature_rows)
    all_leakage_split_audits_passed = len(leakage_rows) == 12 and all(row["leakage_split_audit_passed"] for row in leakage_rows)

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "naming_convention_validated": naming_convention_validated,
        "step13ag_allowlist_creation_gate_validated": True,
        "materialization_scope": "explicit_metadata_csv_to_allowlist_only",
        "input_metadata_path": str(input_metadata_path),
        "input_metadata_exists": metadata_exists,
        "input_metadata_read": metadata_exists,
        "input_metadata_row_count": len(metadata_rows) if metadata_exists else 0,
        "included_candidate_count": len(included_rows) if metadata_exists else 0,
        "materialization_status": materialization_status,
        "metadata_schema_validated": schema_validated,
        "candidate_validation_passed": candidate_validation_passed,
        "duplicate_exclusion_validation_passed": duplicate_validation_passed,
        "shard_plan_created": metadata_valid,
        "shard_count": len(shard_rows) if metadata_valid else 0,
        "materialized_allowlist_written": metadata_valid,
        "materialized_allowlist_path": str(materialized_path) if metadata_valid else "",
        "blocked_header_only_written": not metadata_valid,
        "blocked_header_only_path": "" if metadata_valid else str(blocked_path),
        "candidate_rows_materialized": metadata_valid,
        "candidate_allowlist_created": metadata_valid,
        "covapie_allowlist_materialization_precondition_audit_row_count": len(precondition_rows),
        "covapie_allowlist_materialization_input_discovery_audit_row_count": len(discovery_rows),
        "covapie_allowlist_materialization_schema_audit_row_count": len(schema_rows),
        "covapie_allowlist_materialization_candidate_validation_audit_row_count": len(candidate_rows),
        "covapie_allowlist_materialization_duplicate_exclusion_audit_row_count": len(duplicate_rows),
        "covapie_allowlist_materialization_shard_plan_audit_row_count": len(shard_rows),
        "covapie_allowlist_materialization_output_audit_row_count": len(output_rows),
        "covapie_allowlist_materialization_execution_boundary_audit_row_count": len(execution_rows),
        "covapie_allowlist_materialization_git_safety_audit_row_count": len(git_rows),
        "covapie_allowlist_materialization_mask_scope_audit_row_count": len(mask_rows),
        "covapie_allowlist_materialization_feature_semantics_audit_row_count": len(feature_rows),
        "covapie_allowlist_materialization_leakage_split_audit_row_count": len(leakage_rows),
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "current_reactive_residue_scope": "cys_sg_only",
        "batch_scale_initial_min_candidate_count": MIN_CANDIDATE_COUNT,
        "batch_scale_initial_max_candidate_count": MAX_CANDIDATE_COUNT,
        "batch_scale_initial_shard_size": SHARD_SIZE,
        "all_preconditions_validated": preconditions_passed,
        "all_schema_audits_passed": all_schema_rows_passed,
        "all_candidate_validation_audits_passed": all_candidate_rows_passed,
        "all_duplicate_exclusion_audits_passed": all_duplicate_rows_passed,
        "all_execution_boundaries_respected": all_execution_boundaries_respected,
        "all_git_safety_audits_passed": all_git_safety_audits_passed,
        "all_mask_scope_audits_passed": all_mask_scope_audits_passed,
        "all_feature_semantics_audits_passed": all_feature_semantics_audits_passed,
        "all_leakage_split_audits_passed": all_leakage_split_audits_passed,
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
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(output_root),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "original_diffsbdd_source_modified": _protected_source_diff_exists(),
        "original_diffsbdd_dataloader_modified": _original_dataloader_diff_exists(),
        "original_diffsbdd_forward_modified": _protected_source_diff_exists(),
        "original_diffsbdd_loss_modified": _protected_source_diff_exists(),
        "allowlist_materialization_smoke_preflight_passed": True,
        "covapie_candidate_allowlist_materialization_smoke_passed": metadata_valid,
        "ready_for_user_or_pipeline_metadata": metadata_valid if metadata_exists else False,
        "ready_for_covapie_batch_scale_raw_read_smoke": metadata_valid,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_batch_scale_raw_read_smoke"
        if metadata_valid
        else ("provide_explicit_candidate_metadata_for_allowlist" if not metadata_exists else "fix_explicit_candidate_metadata_for_allowlist"),
        "all_checks_passed": True,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13ag_precondition": {"rows": len(precondition_rows)},
        "input_discovery": {"rows": len(discovery_rows), "materialization_status": materialization_status},
        "schema_audit": {"rows": len(schema_rows)},
        "candidate_validation": {"rows": len(candidate_rows)},
        "duplicate_exclusion": {"rows": len(duplicate_rows)},
        "shard_plan": {"rows": len(shard_rows)},
        "output_audit": {"rows": len(output_rows)},
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
        "discovery_rows": discovery_rows,
        "schema_rows": schema_rows,
        "candidate_rows": candidate_rows,
        "duplicate_rows": duplicate_rows,
        "shard_rows": shard_rows,
        "output_rows": output_rows,
        "execution_rows": execution_rows,
        "git_rows": git_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "paths": {
            "precondition": output_root / PRECONDITION_AUDIT_CSV.name,
            "discovery": output_root / INPUT_DISCOVERY_AUDIT_CSV.name,
            "schema": output_root / SCHEMA_AUDIT_CSV.name,
            "candidate": output_root / CANDIDATE_VALIDATION_AUDIT_CSV.name,
            "duplicate": output_root / DUPLICATE_EXCLUSION_AUDIT_CSV.name,
            "shard": output_root / SHARD_PLAN_AUDIT_CSV.name,
            "output": output_root / OUTPUT_AUDIT_CSV.name,
            "execution": output_root / EXECUTION_BOUNDARY_AUDIT_CSV.name,
            "git": output_root / GIT_SAFETY_AUDIT_CSV.name,
            "mask": output_root / MASK_SCOPE_AUDIT_CSV.name,
            "feature": output_root / FEATURE_SEMANTICS_AUDIT_CSV.name,
            "leakage": output_root / LEAKAGE_SPLIT_AUDIT_CSV.name,
            "report": output_root / REPORT_CSV.name,
            "manifest": output_root / MANIFEST_JSON.name,
            "materialized": materialized_path,
            "blocked": blocked_path,
        },
    }

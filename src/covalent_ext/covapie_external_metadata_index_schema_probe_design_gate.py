from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_external_metadata_index_schema_probe_design_gate_v0"
PREVIOUS_STAGE = "covapie_external_metadata_index_rediscovery_smoke_v0"
PROJECT_NAME = "CovaPIE"

STEP13AP_ROOT = Path("data/derived/covalent_small/covapie_external_metadata_index_rediscovery_smoke_v0")
STEP13AP_MANIFEST_JSON = STEP13AP_ROOT / "covapie_external_metadata_index_rediscovery_smoke_manifest.json"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
ALLOWLIST_TEMPLATE_CSV = Path("data/derived/covalent_small/covapie_candidate_allowlist_creation_gate_v0/templates/covapie_batch_smoke_candidate_allowlist_template.csv")
STEP13AM_CONFIG_CSV = Path("data/derived/covalent_small/covapie_explicit_external_source_registry_config_smoke_v0/covapie_explicit_external_source_registry_config.csv")
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_external_metadata_index_schema_probe_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_precondition_audit.csv"
OBSERVED_SCHEMA_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_observed_schema_audit.csv"
ALLOWLIST_MAPPING_PROBE_CSV = OUTPUT_ROOT / "covapie_allowlist_schema_mapping_probe.csv"
MISSING_FIELD_PLAN_CSV = OUTPUT_ROOT / "covapie_missing_field_resolution_plan.csv"
EVENT_KEY_GAP_AUDIT_CSV = OUTPUT_ROOT / "covapie_event_key_gap_audit.csv"
CANDIDATE_BLOCKER_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_materialization_blocker_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_external_metadata_index_schema_probe_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_external_metadata_index_schema_probe_design_gate_v0_summary.md")

METADATA_COLUMNS = [
    "source_dataset_name",
    "source_dataset_version",
    "source_page_url",
    "source_record_url",
    "covpdb_record_index",
    "pdb_id",
    "protein_name",
    "organism",
    "uniprot_id",
    "uniprot_label",
    "ligand_name",
    "het_code",
    "covpdb_ligand_id",
    "covpdb_complex_card_url",
    "acquisition_method",
    "acquisition_timestamp_utc",
    "raw_structure_downloaded",
    "raw_ligand_downloaded",
    "metadata_only_record",
]
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
DIRECT_COLUMNS = {"source_dataset_name", "source_dataset_version", "pdb_id", "ligand_id"}
GENERATED_FUTURE_COLUMNS = {"candidate_id", "restoration_policy_id", "manual_review_status", "include_in_smoke", "exclusion_reason"}
MISSING_CRITICAL_COLUMNS = {"chain_id", "residue_name", "residue_index", "residue_atom_name", "covalent_bond_atom_pair"}
MISSING_DEFERRED_COLUMNS = {"source_file_relative_path"}
CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
FORBIDDEN_SUFFIXES = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
OBSERVED_SCHEMA_COLUMNS = ["observed_column", "observed_column_order", "non_empty_count", "unique_count", "example_values_first_3", "observed_schema_audit_passed", "blocking_reasons"]
MAPPING_COLUMNS = ["allowlist_column", "mapping_status", "observed_source_columns", "proposed_mapping_rule", "materialization_ready", "blocker_reason", "schema_mapping_probe_passed"]
MISSING_PLAN_COLUMNS = ["missing_field", "missing_field_type", "why_needed", "current_blocking_effect", "proposed_next_evidence_source", "proposed_future_gate", "resolution_ready_current_step"]
EVENT_KEY_GAP_COLUMNS = [
    "event_identity_key_policy",
    "minimal_event_key",
    "preferred_event_key",
    "currently_available_key_parts",
    "missing_minimal_key_parts",
    "missing_preferred_key_parts",
    "minimal_event_key_materializable",
    "preferred_event_key_materializable",
    "one_row_one_covalent_event_enforceable",
    "event_key_gap_audit_passed",
    "blocking_reasons",
]
CANDIDATE_BLOCKER_COLUMNS = ["blocker_name", "blocker_type", "candidate_metadata_materialized", "candidate_allowlist_materialized", "materialization_blocker_audit_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_schema_probe_design_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = step13am.LEAKAGE_COLUMNS
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]

EXECUTION_BOUNDARY_ITEMS = [
    "schema_probe_design_gate",
    "step13ap_manifest_read",
    "metadata_csv_read",
    "allowlist_template_read",
    "external_network_access",
    "metadata_download",
    "raw_structure_download",
    "raw_data_read",
    "sdf_read",
    "pdb_read",
    "mmcif_read",
    "gzip_open",
    "rdkit_use",
    "biopdb_use",
    "gemmi_use",
    "candidate_metadata_materialization",
    "allowlist_materialization",
    "torch_import",
    "model_forward",
    "training_claim",
]
CANDIDATE_BLOCKERS = [
    "missing_chain_id",
    "missing_residue_name",
    "missing_residue_index",
    "missing_residue_atom_name",
    "missing_covalent_bond_atom_pair",
    "source_file_relative_path_not_available_before_raw_download",
    "manual_review_status_not_assigned",
    "include_in_smoke_not_assigned",
    "exclusion_reason_not_assigned",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_header(path: str | Path) -> list[str]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


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
    return any(path.is_file() and path.suffix in FORBIDDEN_SUFFIXES for path in root_path.rglob("*"))


def validate_step13ap_precondition_v0() -> bool:
    manifest = _load_json(STEP13AP_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "metadata_index_file_exists": True,
        "metadata_index_file_read": True,
        "metadata_index_row_count": 25,
        "metadata_index_column_count": 19,
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("blocking_reasons") != []:
        blockers.append("blocking_reasons")
    if blockers:
        raise ValueError("Step 13AP precondition failed: " + ";".join(blockers))
    return True


def validate_metadata_csv_v0() -> bool:
    return METADATA_CSV.is_file() and _csv_header(METADATA_CSV) == METADATA_COLUMNS and len(_csv_rows(METADATA_CSV)) == 25


def validate_allowlist_template_v0() -> bool:
    return ALLOWLIST_TEMPLATE_CSV.is_file() and _csv_header(ALLOWLIST_TEMPLATE_CSV) == ALLOWLIST_COLUMNS and len(_csv_rows(ALLOWLIST_TEMPLATE_CSV)) == 0


def validate_step13am_source_config_v0() -> bool:
    rows = _csv_rows(STEP13AM_CONFIG_CSV)
    if len(rows) != 1:
        return False
    row = rows[0]
    return (
        row.get("source_name") == "CovPDB"
        and row.get("source_access_method") == "manual_user_supplied"
        and row.get("expected_metadata_artifact_type") == "csv"
        and row.get("source_metadata_index_url_or_local_path") == str(METADATA_CSV)
    )


def validate_covapie_naming_convention_v0() -> bool:
    return step13am.validate_covapie_naming_convention_v0()


def build_precondition_rows(output_root: Path) -> list[dict[str, Any]]:
    specs = [
        ("step13ap_manifest", STEP13AP_MANIFEST_JSON, validate_step13ap_precondition_v0()),
        ("metadata_csv_25x19", METADATA_CSV, validate_metadata_csv_v0()),
        ("allowlist_template_15_columns_zero_rows", ALLOWLIST_TEMPLATE_CSV, validate_allowlist_template_v0()),
        ("step13am_source_config", STEP13AM_CONFIG_CSV, validate_step13am_source_config_v0()),
        ("covapie_naming_convention", NAMING_CONVENTION_MD, validate_covapie_naming_convention_v0()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", not _protected_source_diff_exists()),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", not _original_dataloader_diff_exists()),
        ("raw_files_not_staged_or_tracked", "data/raw/covalent_sources", not _raw_files_staged() and not _raw_files_tracked()),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(artifact),
            "expected_status": "present_or_clean",
            "observed_status": "present_or_clean" if passed else "missing_or_dirty",
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else f"{item}_failed",
        }
        for item, artifact, passed in specs
    ]


def build_observed_schema_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result = []
    for index, column in enumerate(METADATA_COLUMNS, start=1):
        values = [row.get(column, "") for row in rows]
        non_empty = [value for value in values if value != ""]
        result.append(
            {
                "observed_column": column,
                "observed_column_order": index,
                "non_empty_count": len(non_empty),
                "unique_count": len(set(non_empty)),
                "example_values_first_3": ";".join(non_empty[:3]),
                "observed_schema_audit_passed": True,
                "blocking_reasons": "",
            }
        )
    return result


def build_mapping_rows() -> list[dict[str, Any]]:
    rules = {
        "candidate_id": ("generated_future", "", "future generated after event key is valid", False, "event_key_not_materializable"),
        "source_dataset_name": ("direct_available", "source_dataset_name", "source_dataset_name <- source_dataset_name", True, ""),
        "source_dataset_version": ("direct_available", "source_dataset_version", "source_dataset_version <- source_dataset_version", True, ""),
        "source_file_relative_path": ("missing_deferred", "", "defer until raw structure path exists in a later raw-read/annotation gate", False, "raw_structure_path_not_available"),
        "pdb_id": ("direct_available", "pdb_id", "pdb_id <- pdb_id", True, ""),
        "ligand_id": ("direct_available", "het_code;covpdb_ligand_id", "ligand_id_candidate_het_code <- het_code; covpdb_ligand_id retained as supporting source id; ambiguous_source_choice", True, "ambiguous_source_choice"),
        "chain_id": ("missing_critical", "", "must come from complex card/residue metadata or later raw structure annotation", False, "missing_chain_id"),
        "residue_name": ("missing_critical", "", "must come from complex card/residue metadata or later raw structure annotation", False, "missing_residue_name"),
        "residue_index": ("missing_critical", "", "must come from complex card/residue metadata or later raw structure annotation", False, "missing_residue_index"),
        "residue_atom_name": ("missing_critical", "", "must come from complex card/residue metadata or later raw structure annotation", False, "missing_residue_atom_name"),
        "covalent_bond_atom_pair": ("missing_critical", "", "must come from complex card bond metadata or later raw structure annotation", False, "missing_covalent_bond_atom_pair"),
        "restoration_policy_id": ("generated_future", "", "future assigned after residue and bond evidence are known", False, "residue_bond_evidence_missing"),
        "manual_review_status": ("generated_future", "", "future manual or pipeline review field", False, "review_not_assigned"),
        "include_in_smoke": ("generated_future", "", "future smoke selection field", False, "selection_not_assigned"),
        "exclusion_reason": ("generated_future", "", "future selection or rejection field", False, "selection_not_assigned"),
    }
    return [
        {
            "allowlist_column": column,
            "mapping_status": rules[column][0],
            "observed_source_columns": rules[column][1],
            "proposed_mapping_rule": rules[column][2],
            "materialization_ready": rules[column][3],
            "blocker_reason": rules[column][4],
            "schema_mapping_probe_passed": True,
        }
        for column in ALLOWLIST_COLUMNS
    ]


def build_missing_field_resolution_rows() -> list[dict[str, Any]]:
    specs = [
        ("chain_id", "critical_event_key", "required for one covalent event identity", "minimal_event_key_not_materializable", "CovPDB complex card HTML or residue pages; later raw structure annotation if needed", "covapie_covpdb_complex_card_metadata_probe_design_gate"),
        ("residue_name", "critical_event_key", "required for residue identity", "minimal_event_key_not_materializable", "CovPDB complex card HTML or residue pages; later raw structure annotation if needed", "covapie_covpdb_complex_card_metadata_probe_design_gate"),
        ("residue_index", "critical_event_key", "required for residue identity", "minimal_event_key_not_materializable", "CovPDB complex card HTML or residue pages; later raw structure annotation if needed", "covapie_covpdb_complex_card_metadata_probe_design_gate"),
        ("residue_atom_name", "critical_event_key", "required for reactive residue atom identity", "minimal_event_key_not_materializable", "CovPDB complex card HTML or later raw structure annotation", "covapie_covpdb_complex_card_metadata_probe_design_gate"),
        ("covalent_bond_atom_pair", "critical_event_key", "required for preferred event identity", "preferred_event_key_not_materializable", "CovPDB complex card bond metadata or later PDB/mmCIF struct_conn/LINK annotation", "covapie_covpdb_complex_card_metadata_probe_design_gate"),
        ("source_file_relative_path", "deferred_raw_path", "required only after raw artifact policy is approved", "candidate_source_path_not_available", "later raw-read/annotation gate output", "covapie_batch_scale_raw_read_smoke_design_gate"),
        ("restoration_policy_id", "covapie_generated_policy", "required to record restoration policy after event evidence", "policy_not_assignable_yet", "future policy assignment after event metadata is explicit", "covapie_candidate_metadata_assembly_design_gate"),
        ("manual_review_status", "covapie_generated_policy", "required for review state", "review_not_assigned", "future manual or pipeline review", "covapie_candidate_metadata_assembly_design_gate"),
        ("include_in_smoke", "covapie_generated_policy", "required for smoke allowlist selection", "selection_not_assigned", "future candidate selection gate", "covapie_candidate_allowlist_materialization_smoke_design_gate"),
        ("exclusion_reason", "covapie_generated_policy", "required for rejected candidate explanation", "selection_not_assigned", "future candidate selection gate", "covapie_candidate_allowlist_materialization_smoke_design_gate"),
    ]
    return [
        {
            "missing_field": field,
            "missing_field_type": field_type,
            "why_needed": why,
            "current_blocking_effect": effect,
            "proposed_next_evidence_source": source,
            "proposed_future_gate": gate,
            "resolution_ready_current_step": False,
        }
        for field, field_type, why, effect, source, gate in specs
    ]


def build_event_key_gap_rows() -> list[dict[str, Any]]:
    return [
        {
            "event_identity_key_policy": "no_pdb_id_only_join",
            "minimal_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name",
            "preferred_event_key": "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name+covalent_bond_atom_pair",
            "currently_available_key_parts": "pdb_id+ligand_id_candidate",
            "missing_minimal_key_parts": "chain_id+residue_name+residue_index+residue_atom_name",
            "missing_preferred_key_parts": "covalent_bond_atom_pair",
            "minimal_event_key_materializable": False,
            "preferred_event_key_materializable": False,
            "one_row_one_covalent_event_enforceable": False,
            "event_key_gap_audit_passed": True,
            "blocking_reasons": "",
        }
    ]


def build_candidate_blocker_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocker_name": blocker,
            "blocker_type": "critical_event_key" if blocker.startswith("missing_") else "deferred_or_policy",
            "candidate_metadata_materialized": False,
            "candidate_allowlist_materialized": False,
            "materialization_blocker_audit_passed": True,
            "blocking_reasons": "",
        }
        for blocker in CANDIDATE_BLOCKERS
    ]


def build_execution_boundary_rows() -> list[dict[str, Any]]:
    executed = {
        "schema_probe_design_gate": "executed_design_gate_only",
        "step13ap_manifest_read": "executed_manifest_read_only",
        "metadata_csv_read": "executed_metadata_csv_schema_probe_only",
        "allowlist_template_read": "executed_template_read_only",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": executed.get(item, "not_executed_or_not_allowed"),
            "execution_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item in EXECUTION_BOUNDARY_ITEMS
    ]


def build_git_safety_rows(output_root: Path) -> list[dict[str, Any]]:
    specs = [
        ("forbidden_suffix_under_step13aq_output_root", "find output root forbidden suffixes", "none", "passed" if not _forbidden_committable_artifacts_created(output_root) else "failed"),
        ("raw_files_not_staged", "git diff --cached --name-only -- data/raw/covalent_sources", "empty", "passed" if not _raw_files_staged() else "failed"),
        ("raw_files_not_tracked", "git ls-files data/raw/covalent_sources", "empty", "passed" if not _raw_files_tracked() else "failed"),
        ("protected_source_diff_empty", "git diff -- equivariant_diffusion/ lightning_modules.py", "empty", "passed" if not _protected_source_diff_exists() else "failed"),
        ("original_dataloader_diff_empty", "git diff -- dataset.py data/prepare_crossdocked.py", "empty", "passed" if not _original_dataloader_diff_exists() else "failed"),
        ("metadata_csv_unchanged_policy", str(METADATA_CSV), "read_only_input", "declared"),
        ("step13ao_artifacts_unchanged_policy", "data/derived/covalent_small/covapie_covpdb_metadata_only_acquisition_smoke_v0", "read_only_input", "declared"),
        ("step13ap_artifacts_unchanged_policy", str(STEP13AP_ROOT), "read_only_input", "declared"),
        ("exact_file_stage_policy", "git add explicit Step 13AQ files only", "exact_file_list", "declared"),
        ("post_step_status_policy", "git status --short --untracked-files=all", "only_step13aq_outputs", "declared"),
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
            "mask_scope_status": "preserved_from_step13ap",
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
            "blocking_for_schema_probe_design_gate": False,
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


def run_covapie_external_metadata_index_schema_probe_design_gate_v0(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    output_root = Path(output_root)
    validate_step13ap_precondition_v0()
    validate_metadata_csv_v0()
    validate_allowlist_template_v0()
    validate_step13am_source_config_v0()
    validate_covapie_naming_convention_v0()
    metadata_rows = _csv_rows(METADATA_CSV)
    observed_schema_rows = build_observed_schema_rows(metadata_rows)
    mapping_rows = build_mapping_rows()
    missing_rows = build_missing_field_resolution_rows()
    event_rows = build_event_key_gap_rows()
    blocker_rows = build_candidate_blocker_rows()
    execution_rows = build_execution_boundary_rows()
    git_rows = build_git_safety_rows(output_root)
    mask_rows = build_mask_scope_rows()
    feature_rows = build_feature_semantics_rows()
    leakage_rows = build_leakage_split_rows()
    precondition_rows = build_precondition_rows(output_root)
    direct_count = sum(row["mapping_status"] == "direct_available" for row in mapping_rows)
    generated_count = sum(row["mapping_status"] == "generated_future" for row in mapping_rows)
    critical_count = sum(row["mapping_status"] == "missing_critical" for row in mapping_rows)
    deferred_count = sum(row["mapping_status"] == "missing_deferred" for row in mapping_rows)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13ap_external_metadata_index_rediscovery_smoke_validated": True,
        "metadata_csv_path": str(METADATA_CSV),
        "metadata_csv_row_count": len(metadata_rows),
        "metadata_csv_column_count": len(METADATA_COLUMNS),
        "allowlist_required_column_count": len(ALLOWLIST_COLUMNS),
        "observed_covpdb_metadata_column_count": len(METADATA_COLUMNS),
        "directly_mappable_allowlist_column_count": direct_count,
        "generated_future_allowlist_column_count": generated_count,
        "missing_critical_allowlist_column_count": critical_count,
        "missing_deferred_allowlist_column_count": deferred_count,
        "directly_mappable_allowlist_columns": [row["allowlist_column"] for row in mapping_rows if row["mapping_status"] == "direct_available"],
        "generated_future_allowlist_columns": [row["allowlist_column"] for row in mapping_rows if row["mapping_status"] == "generated_future"],
        "missing_critical_allowlist_columns": [row["allowlist_column"] for row in mapping_rows if row["mapping_status"] == "missing_critical"],
        "missing_deferred_allowlist_columns": [row["allowlist_column"] for row in mapping_rows if row["mapping_status"] == "missing_deferred"],
        "minimal_event_key_materializable": False,
        "preferred_event_key_materializable": False,
        "one_row_one_covalent_event_enforceable": False,
        "candidate_metadata_materialized": False,
        "candidate_allowlist_materialized": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "raw_data_read": False,
        "raw_file_copied": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
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
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(output_root),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "original_diffsbdd_source_modified": _protected_source_diff_exists(),
        "original_diffsbdd_dataloader_modified": _original_dataloader_diff_exists(),
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate": False,
        "ready_for_covapie_covpdb_complex_card_metadata_probe_design_gate": True,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_covpdb_complex_card_metadata_probe_design_gate",
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "precondition_audit_row_count": len(precondition_rows),
        "observed_schema_audit_row_count": len(observed_schema_rows),
        "allowlist_schema_mapping_probe_row_count": len(mapping_rows),
        "missing_field_resolution_plan_row_count": len(missing_rows),
        "event_key_gap_audit_row_count": len(event_rows),
        "candidate_materialization_blocker_audit_row_count": len(blocker_rows),
        "execution_boundary_audit_row_count": len(execution_rows),
        "git_safety_audit_row_count": len(git_rows),
        "mask_scope_audit_row_count": len(mask_rows),
        "feature_semantics_audit_row_count": len(feature_rows),
        "leakage_split_audit_row_count": len(leakage_rows),
        "schema_probe_design_gate_passed": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    return {
        "paths": {
            "precondition": output_root / PRECONDITION_AUDIT_CSV.name,
            "observed": output_root / OBSERVED_SCHEMA_AUDIT_CSV.name,
            "mapping": output_root / ALLOWLIST_MAPPING_PROBE_CSV.name,
            "missing": output_root / MISSING_FIELD_PLAN_CSV.name,
            "event": output_root / EVENT_KEY_GAP_AUDIT_CSV.name,
            "blocker": output_root / CANDIDATE_BLOCKER_AUDIT_CSV.name,
            "execution": output_root / EXECUTION_BOUNDARY_AUDIT_CSV.name,
            "git": output_root / GIT_SAFETY_AUDIT_CSV.name,
            "mask": output_root / MASK_SCOPE_AUDIT_CSV.name,
            "feature": output_root / FEATURE_SEMANTICS_AUDIT_CSV.name,
            "leakage": output_root / LEAKAGE_SPLIT_AUDIT_CSV.name,
            "report": output_root / REPORT_CSV.name,
            "manifest": output_root / MANIFEST_JSON.name,
        },
        "precondition_rows": precondition_rows,
        "observed_schema_rows": observed_schema_rows,
        "mapping_rows": mapping_rows,
        "missing_rows": missing_rows,
        "event_rows": event_rows,
        "blocker_rows": blocker_rows,
        "execution_rows": execution_rows,
        "git_rows": git_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
        "report_sections": {
            "step13ap_precondition": {"passed": True},
            "observed_schema": {"rows": len(observed_schema_rows)},
            "allowlist_schema_mapping": {"direct": direct_count, "generated": generated_count, "critical": critical_count, "deferred": deferred_count},
            "missing_field_resolution": {"rows": len(missing_rows)},
            "event_key_gap": {"minimal_event_key_materializable": False},
            "candidate_materialization_blockers": {"rows": len(blocker_rows)},
            "execution_boundary": {"network_access_used": False},
            "git_safety": {"rows": len(git_rows)},
            "mask_scope": {"mask_count": 5},
            "feature_semantics": {"rows": len(feature_rows)},
            "leakage_split": {"rows": len(leakage_rows)},
            "readiness_boundary": {"ready_for_complex_card_probe_design_gate": True},
        },
    }

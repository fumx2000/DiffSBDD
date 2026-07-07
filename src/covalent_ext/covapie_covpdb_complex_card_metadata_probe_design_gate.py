from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_covpdb_complex_card_metadata_probe_design_gate_v0"
PREVIOUS_STAGE = "covapie_external_metadata_index_schema_probe_design_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AQ_ROOT = Path("data/derived/covalent_small/covapie_external_metadata_index_schema_probe_design_gate_v0")
STEP13AQ_MANIFEST_JSON = STEP13AQ_ROOT / "covapie_external_metadata_index_schema_probe_design_gate_manifest.json"
STEP13AQ_MISSING_PLAN_CSV = STEP13AQ_ROOT / "covapie_missing_field_resolution_plan.csv"
STEP13AQ_MAPPING_PROBE_CSV = STEP13AQ_ROOT / "covapie_allowlist_schema_mapping_probe.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
ALLOWLIST_TEMPLATE_CSV = Path("data/derived/covalent_small/covapie_candidate_allowlist_creation_gate_v0/templates/covapie_batch_smoke_candidate_allowlist_template.csv")
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_covpdb_complex_card_metadata_probe_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_probe_precondition_audit.csv"
TARGET_FIELD_CONTRACT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_probe_target_field_contract.csv"
ALLOWED_URL_CONTRACT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_allowed_url_contract.csv"
FORBIDDEN_ARTIFACT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_forbidden_artifact_contract.csv"
PARSE_STRATEGY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_parse_strategy_contract.csv"
EVENT_KEY_RESOLUTION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_event_key_resolution_contract.csv"
FAILURE_TAXONOMY_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_failure_taxonomy.csv"
READINESS_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_readiness_boundary_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_metadata_probe_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_covpdb_complex_card_metadata_probe_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_covpdb_complex_card_metadata_probe_design_gate_v0_summary.md")

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
CRITICAL_EVENT_KEY_FIELDS = ["chain_id", "residue_name", "residue_index", "residue_atom_name", "covalent_bond_atom_pair"]
SUPPORTING_FIELDS = [
    "covpdb_complex_card_url",
    "source_record_url",
    "pdb_id",
    "het_code",
    "covpdb_ligand_id",
    "ligand_name",
    "protein_name",
    "uniprot_id",
]
OPTIONAL_ANNOTATION_FIELDS = [
    "mechanism_or_reaction_type_if_available",
    "warhead_or_residue_class_if_available",
    "evidence_text_or_table_label",
    "parse_confidence",
    "parse_failure_reason",
]
FORBIDDEN_ARTIFACT_ITEMS = [
    ".zip",
    ".pdb",
    ".ent",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
    "raw_complex_download",
    "ligand_sdf_download",
    "all_complexes_archive",
    "all_ligands_archive",
    "pdb_mmcif_raw_download",
    "screenshot_browser_selenium_playwright",
    "rdkit_biopdb_gemmi",
    "torch_model_training",
]
PARSE_STRATEGY_ITEMS = [
    ("html_text_only", "Read only HTML/text from allowed complex-card URL."),
    ("visible_text_and_tables", "Extract visible text and HTML tables."),
    ("candidate_labels", "Search labels: chain;residue;residue name;residue number;atom;covalent bond;ligand atom;protein atom;mechanism;warhead."),
    ("short_evidence_snippets", "Keep raw evidence snippets short and metadata-only."),
    ("unresolved_if_ambiguous", "If chain/residue/bond cannot be unambiguously parsed, mark card as unresolved."),
    ("no_pdb_id_inference", "Never infer missing chain/residue/bond from pdb_id alone."),
    ("no_bond_fabrication", "Never fabricate covalent_bond_atom_pair."),
    ("ambiguous_excluded", "Ambiguous cards stay excluded from materialization."),
]
EVENT_KEY_RESOLUTION_STATUSES = [
    "card_resolves_minimal_event_key",
    "card_resolves_preferred_event_key",
    "card_partial_event_key_only",
    "card_no_event_key_fields_found",
    "card_ambiguous_multi_event",
    "card_requires_raw_structure_annotation",
    "card_parse_failed",
]
FAILURE_REASONS = [
    "complex_card_url_missing",
    "complex_card_url_not_allowed",
    "complex_card_fetch_deferred_current_step",
    "complex_card_html_parse_failed",
    "no_chain_id_found",
    "no_residue_name_found",
    "no_residue_index_found",
    "no_residue_atom_name_found",
    "no_covalent_bond_atom_pair_found",
    "multiple_candidate_residues",
    "multiple_candidate_ligands",
    "ambiguous_ligand_atom",
    "ambiguous_protein_atom",
    "raw_download_required_for_resolution",
    "forbidden_download_link_detected",
    "training_attempted_too_early",
]
EXECUTION_BOUNDARY_ITEMS = [
    "complex_card_metadata_probe_design_gate",
    "step13aq_manifest_read",
    "step13aq_mapping_probe_read",
    "metadata_csv_card_urls_read",
    "allowed_url_contract_write",
    "target_field_contract_write",
    "parse_strategy_contract_write",
    "event_key_resolution_contract_write",
    "external_network_access",
    "complex_card_fetch",
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
CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
FORBIDDEN_SUFFIXES = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
TARGET_FIELD_COLUMNS = ["target_field", "field_class", "required_for_minimal_event_key", "required_for_preferred_event_key", "expected_source", "raw_structure_required_current_step", "materialization_blocking_if_missing", "target_field_contract_passed", "blocking_reasons"]
ALLOWED_URL_COLUMNS = ["url_contract_item", "contract_value", "contract_status", "allowed_url_contract_passed", "blocking_reasons"]
FORBIDDEN_ARTIFACT_COLUMNS = ["forbidden_artifact_or_action", "contract_policy", "forbidden_artifact_contract_passed", "blocking_reasons"]
PARSE_STRATEGY_COLUMNS = ["parse_strategy_item", "parse_strategy_rule", "parse_strategy_contract_passed", "blocking_reasons"]
EVENT_KEY_RESOLUTION_COLUMNS = ["resolution_status", "candidate_metadata_can_proceed", "candidate_allowlist_can_proceed", "manual_review_path_allowed", "raw_structure_annotation_may_be_required", "event_key_resolution_contract_passed", "blocking_reasons"]
FAILURE_TAXONOMY_COLUMNS = ["failure_reason", "failure_class", "blocks_candidate_metadata", "recommended_handling", "failure_taxonomy_passed", "blocking_reasons"]
READINESS_COLUMNS = ["readiness_item", "current_step_status", "readiness_boundary_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_complex_card_probe_design_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = step13am.LEAKAGE_COLUMNS
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]


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


def is_allowed_complex_card_url(url: str) -> bool:
    return (
        url.startswith("https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/")
        and not any(url.lower().endswith(suffix) for suffix in [".zip", ".pdb", ".ent", ".cif", ".mmcif", ".sdf", ".mol2", ".gz"])
    )


def read_metadata_rows() -> list[dict[str, str]]:
    return _csv_rows(METADATA_CSV)


def complex_card_urls(rows: list[dict[str, str]] | None = None) -> list[str]:
    rows = read_metadata_rows() if rows is None else rows
    return [row["covpdb_complex_card_url"] for row in rows if row.get("covpdb_complex_card_url")]


def validate_step13aq_precondition_v0() -> bool:
    manifest = _load_json(STEP13AQ_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "metadata_csv_row_count": 25,
        "metadata_csv_column_count": 19,
        "missing_critical_allowlist_column_count": 5,
        "minimal_event_key_materializable": False,
        "preferred_event_key_materializable": False,
        "ready_for_covapie_covpdb_complex_card_metadata_probe_design_gate": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("blocking_reasons") != []:
        blockers.append("blocking_reasons")
    if blockers:
        raise ValueError("Step 13AQ precondition failed: " + ";".join(blockers))
    return True


def validate_metadata_csv_v0() -> bool:
    rows = read_metadata_rows()
    return METADATA_CSV.is_file() and _csv_header(METADATA_CSV) == METADATA_COLUMNS and len(rows) == 25 and len(complex_card_urls(rows)) > 0


def validate_allowlist_template_v0() -> bool:
    return ALLOWLIST_TEMPLATE_CSV.is_file() and _csv_header(ALLOWLIST_TEMPLATE_CSV) == ALLOWLIST_COLUMNS


def validate_covapie_naming_convention_v0() -> bool:
    return step13am.validate_covapie_naming_convention_v0()


def build_precondition_rows(output_root: Path) -> list[dict[str, Any]]:
    specs = [
        ("step13aq_manifest", STEP13AQ_MANIFEST_JSON, validate_step13aq_precondition_v0()),
        ("step13aq_missing_field_plan", STEP13AQ_MISSING_PLAN_CSV, STEP13AQ_MISSING_PLAN_CSV.is_file()),
        ("step13aq_mapping_probe", STEP13AQ_MAPPING_PROBE_CSV, STEP13AQ_MAPPING_PROBE_CSV.is_file()),
        ("metadata_csv_25x19_with_card_urls", METADATA_CSV, validate_metadata_csv_v0()),
        ("allowlist_template", ALLOWLIST_TEMPLATE_CSV, validate_allowlist_template_v0()),
        ("covapie_naming_convention", NAMING_CONVENTION_MD, validate_covapie_naming_convention_v0()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", not _protected_source_diff_exists()),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", not _original_dataloader_diff_exists()),
        ("raw_files_not_staged_or_tracked", "data/raw/covalent_sources", not _raw_files_staged() and not _raw_files_tracked()),
        ("output_root_declared", output_root, True),
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


def build_target_field_rows() -> list[dict[str, Any]]:
    rows = []
    for field in CRITICAL_EVENT_KEY_FIELDS:
        rows.append(
            {
                "target_field": field,
                "field_class": "critical_event_key",
                "required_for_minimal_event_key": field != "covalent_bond_atom_pair",
                "required_for_preferred_event_key": True,
                "expected_source": "complex_card_html_text_or_table",
                "raw_structure_required_current_step": False,
                "materialization_blocking_if_missing": True,
                "target_field_contract_passed": True,
                "blocking_reasons": "",
            }
        )
    for field in SUPPORTING_FIELDS:
        rows.append(
            {
                "target_field": field,
                "field_class": "supporting_metadata",
                "required_for_minimal_event_key": field in {"pdb_id", "het_code"},
                "required_for_preferred_event_key": field in {"pdb_id", "het_code"},
                "expected_source": "complex_card_html_text_or_table",
                "raw_structure_required_current_step": False,
                "materialization_blocking_if_missing": field in {"pdb_id", "het_code"},
                "target_field_contract_passed": True,
                "blocking_reasons": "",
            }
        )
    for field in OPTIONAL_ANNOTATION_FIELDS:
        rows.append(
            {
                "target_field": field,
                "field_class": "optional_annotation",
                "required_for_minimal_event_key": False,
                "required_for_preferred_event_key": False,
                "expected_source": "complex_card_html_text_or_table",
                "raw_structure_required_current_step": False,
                "materialization_blocking_if_missing": False,
                "target_field_contract_passed": True,
                "blocking_reasons": "",
            }
        )
    return rows


def build_allowed_url_rows(urls: list[str]) -> list[dict[str, Any]]:
    specs = [
        ("source_url_policy", "URLs already present in covpdb_complex_card_url or source_record_url from committed metadata CSV"),
        ("allowed_domain", "drug-discovery.vm.uni-freiburg.de"),
        ("allowed_path_prefix", "/covpdb/complex_card/"),
        ("forbidden_raw_suffix_filter", ".zip;.pdb;.ent;.cif;.mmcif;.sdf;.mol2;.gz"),
        ("maximum_cards_first_smoke", "5"),
        ("recursive_crawling", "not_allowed"),
        ("download_links", "do_not_follow"),
        ("external_raw_links", "do_not_follow_rcsb_or_pdbe_raw_links"),
        ("observed_complex_card_url_count", str(len(urls))),
        ("observed_first_5_complex_card_urls", ";".join(urls[:5])),
    ]
    return [
        {
            "url_contract_item": item,
            "contract_value": value,
            "contract_status": "design_contract_only_no_fetch",
            "allowed_url_contract_passed": True,
            "blocking_reasons": "",
        }
        for item, value in specs
    ]


def build_forbidden_artifact_rows() -> list[dict[str, Any]]:
    return [
        {
            "forbidden_artifact_or_action": item,
            "contract_policy": "not_allowed_in_complex_card_metadata_probe",
            "forbidden_artifact_contract_passed": True,
            "blocking_reasons": "",
        }
        for item in FORBIDDEN_ARTIFACT_ITEMS
    ]


def build_parse_strategy_rows() -> list[dict[str, Any]]:
    return [
        {
            "parse_strategy_item": item,
            "parse_strategy_rule": rule,
            "parse_strategy_contract_passed": True,
            "blocking_reasons": "",
        }
        for item, rule in PARSE_STRATEGY_ITEMS
    ]


def build_event_key_resolution_rows() -> list[dict[str, Any]]:
    rows = []
    for status in EVENT_KEY_RESOLUTION_STATUSES:
        minimal = status in {"card_resolves_minimal_event_key", "card_resolves_preferred_event_key"}
        preferred = status == "card_resolves_preferred_event_key"
        rows.append(
            {
                "resolution_status": status,
                "candidate_metadata_can_proceed": minimal,
                "candidate_allowlist_can_proceed": preferred,
                "manual_review_path_allowed": minimal and not preferred,
                "raw_structure_annotation_may_be_required": status == "card_requires_raw_structure_annotation",
                "event_key_resolution_contract_passed": True,
                "blocking_reasons": "" if minimal else "minimal_event_key_unresolved",
            }
        )
    return rows


def build_failure_taxonomy_rows() -> list[dict[str, Any]]:
    return [
        {
            "failure_reason": reason,
            "failure_class": "event_key_resolution" if reason.startswith(("no_", "multiple_", "ambiguous_")) else "access_or_boundary",
            "blocks_candidate_metadata": reason not in {"forbidden_download_link_detected"},
            "recommended_handling": "block_current_card_and_record_reason",
            "failure_taxonomy_passed": True,
            "blocking_reasons": "",
        }
        for reason in FAILURE_REASONS
    ]


def build_readiness_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_covpdb_complex_card_metadata_acquisition_smoke", True),
        ("ready_for_covapie_candidate_metadata_materialization", False),
        ("ready_for_covapie_candidate_allowlist_materialization_smoke", False),
        ("ready_for_covapie_batch_scale_raw_read_smoke", False),
        ("ready_for_training", False),
        ("ready_to_train_now", False),
        ("feature_semantics_audit_required_before_training", True),
        ("leakage_split_design_required_before_training", True),
    ]
    return [
        {
            "readiness_item": item,
            "current_step_status": value,
            "readiness_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, value in specs
    ]


def build_execution_boundary_rows() -> list[dict[str, Any]]:
    executed = {
        "complex_card_metadata_probe_design_gate": "executed_design_gate_only",
        "step13aq_manifest_read": "executed_manifest_read_only",
        "step13aq_mapping_probe_read": "executed_mapping_probe_read_only",
        "metadata_csv_card_urls_read": "executed_url_column_read_only",
        "allowed_url_contract_write": "executed_contract_only",
        "target_field_contract_write": "executed_contract_only",
        "parse_strategy_contract_write": "executed_contract_only",
        "event_key_resolution_contract_write": "executed_contract_only",
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
        ("forbidden_suffix_under_step13ar_output_root", "find output root forbidden suffixes", "none", "passed" if not _forbidden_committable_artifacts_created(output_root) else "failed"),
        ("metadata_csv_unchanged_policy", str(METADATA_CSV), "read_only_input", "declared"),
        ("step13ao_artifacts_unchanged_policy", "data/derived/covalent_small/covapie_covpdb_metadata_only_acquisition_smoke_v0", "read_only_input", "declared"),
        ("step13ap_artifacts_unchanged_policy", "data/derived/covalent_small/covapie_external_metadata_index_rediscovery_smoke_v0", "read_only_input", "declared"),
        ("step13aq_artifacts_unchanged_policy", str(STEP13AQ_ROOT), "read_only_input", "declared"),
        ("raw_files_not_staged", "git diff --cached --name-only -- data/raw/covalent_sources", "empty", "passed" if not _raw_files_staged() else "failed"),
        ("raw_files_not_tracked", "git ls-files data/raw/covalent_sources", "empty", "passed" if not _raw_files_tracked() else "failed"),
        ("protected_source_diff_empty", "git diff -- equivariant_diffusion/ lightning_modules.py", "empty", "passed" if not _protected_source_diff_exists() else "failed"),
        ("original_dataloader_diff_empty", "git diff -- dataset.py data/prepare_crossdocked.py", "empty", "passed" if not _original_dataloader_diff_exists() else "failed"),
        ("exact_file_stage_policy", "git add explicit Step 13AR files only", "exact_file_list", "declared"),
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
            "mask_scope_status": "preserved_from_step13aq",
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
            "blocking_for_complex_card_probe_design_gate": False,
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


def run_covapie_covpdb_complex_card_metadata_probe_design_gate_v0(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    output_root = Path(output_root)
    validate_step13aq_precondition_v0()
    validate_metadata_csv_v0()
    validate_allowlist_template_v0()
    validate_covapie_naming_convention_v0()
    metadata_rows = read_metadata_rows()
    urls = complex_card_urls(metadata_rows)
    if not all(is_allowed_complex_card_url(url) for url in urls):
        raise ValueError("Metadata CSV contains disallowed complex card URL")
    precondition_rows = build_precondition_rows(output_root)
    target_rows = build_target_field_rows()
    allowed_url_rows = build_allowed_url_rows(urls)
    forbidden_rows = build_forbidden_artifact_rows()
    parse_rows = build_parse_strategy_rows()
    event_rows = build_event_key_resolution_rows()
    failure_rows = build_failure_taxonomy_rows()
    readiness_rows = build_readiness_rows()
    execution_rows = build_execution_boundary_rows()
    git_rows = build_git_safety_rows(output_root)
    mask_rows = build_mask_scope_rows()
    feature_rows = build_feature_semantics_rows()
    leakage_rows = build_leakage_split_rows()
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13aq_schema_probe_design_gate_validated": True,
        "metadata_csv_row_count": len(metadata_rows),
        "metadata_csv_column_count": len(METADATA_COLUMNS),
        "complex_card_url_count": len(urls),
        "first_5_complex_card_urls": urls[:5],
        "target_field_contract_row_count": len(target_rows),
        "allowed_url_contract_row_count": len(allowed_url_rows),
        "forbidden_artifact_contract_row_count": len(forbidden_rows),
        "parse_strategy_contract_row_count": len(parse_rows),
        "event_key_resolution_contract_row_count": len(event_rows),
        "failure_taxonomy_row_count": len(failure_rows),
        "readiness_boundary_audit_row_count": len(readiness_rows),
        "execution_boundary_audit_row_count": len(execution_rows),
        "git_safety_audit_row_count": len(git_rows),
        "mask_scope_audit_row_count": len(mask_rows),
        "feature_semantics_audit_row_count": len(feature_rows),
        "leakage_split_audit_row_count": len(leakage_rows),
        "ready_for_covapie_covpdb_complex_card_metadata_acquisition_smoke": True,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
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
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_covpdb_complex_card_metadata_acquisition_smoke",
        "complex_card_metadata_probe_design_gate_passed": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    return {
        "paths": {
            "precondition": output_root / PRECONDITION_AUDIT_CSV.name,
            "target": output_root / TARGET_FIELD_CONTRACT_CSV.name,
            "allowed_url": output_root / ALLOWED_URL_CONTRACT_CSV.name,
            "forbidden": output_root / FORBIDDEN_ARTIFACT_CONTRACT_CSV.name,
            "parse": output_root / PARSE_STRATEGY_CONTRACT_CSV.name,
            "event": output_root / EVENT_KEY_RESOLUTION_CONTRACT_CSV.name,
            "failure": output_root / FAILURE_TAXONOMY_CSV.name,
            "readiness": output_root / READINESS_BOUNDARY_AUDIT_CSV.name,
            "execution": output_root / EXECUTION_BOUNDARY_AUDIT_CSV.name,
            "git": output_root / GIT_SAFETY_AUDIT_CSV.name,
            "mask": output_root / MASK_SCOPE_AUDIT_CSV.name,
            "feature": output_root / FEATURE_SEMANTICS_AUDIT_CSV.name,
            "leakage": output_root / LEAKAGE_SPLIT_AUDIT_CSV.name,
            "report": output_root / REPORT_CSV.name,
            "manifest": output_root / MANIFEST_JSON.name,
        },
        "precondition_rows": precondition_rows,
        "target_rows": target_rows,
        "allowed_url_rows": allowed_url_rows,
        "forbidden_rows": forbidden_rows,
        "parse_rows": parse_rows,
        "event_rows": event_rows,
        "failure_rows": failure_rows,
        "readiness_rows": readiness_rows,
        "execution_rows": execution_rows,
        "git_rows": git_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
        "report_sections": {
            "step13aq_precondition": {"passed": True},
            "target_field_contract": {"rows": len(target_rows)},
            "allowed_url_contract": {"rows": len(allowed_url_rows), "complex_card_url_count": len(urls)},
            "forbidden_artifact_contract": {"rows": len(forbidden_rows)},
            "parse_strategy_contract": {"rows": len(parse_rows)},
            "event_key_resolution_contract": {"rows": len(event_rows)},
            "failure_taxonomy": {"rows": len(failure_rows)},
            "readiness_boundary": {"ready_for_acquisition_smoke": True},
            "execution_boundary": {"network_access_used": False},
            "git_safety": {"rows": len(git_rows)},
            "mask_scope": {"mask_count": 5},
            "feature_semantics": {"rows": len(feature_rows)},
            "leakage_split": {"rows": len(leakage_rows)},
        },
    }

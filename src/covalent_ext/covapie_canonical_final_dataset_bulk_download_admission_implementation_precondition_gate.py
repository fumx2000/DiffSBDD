"""Read-only executability precondition audit for the frozen Step14AT contract.

The audit is intentionally not a candidate evaluator. It records whether the
Step14AT dependencies are mapped correctly and, separately, whether their
formats, enums, and explicit caller contexts are sufficiently frozen to write
deterministic admission-rule logic. No raw target, model, checkpoint, or
network resource is opened.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


STAGE = "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
STEP_LABEL = "Step14AU-A"
PROJECT_NAME = "CovaPIE"
PREVIOUS_STAGE = "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
NEXT_STAGE = "covapie_canonical_final_dataset_bulk_download_admission_implementation_v1"
BLOCKED_NEXT_STAGE = "resolve_covapie_bulk_download_admission_implementation_precondition_blockers"
MANIFEST_SCHEMA_VERSION = "covapie_bulk_download_admission_implementation_precondition_gate_v1_manifest_v2"

REPO_ROOT = Path(__file__).resolve().parents[2]
STEP14AT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)

STEP14AT_FILENAMES = (
    "covapie_bulk_download_admission_schema_contract.csv",
    "covapie_bulk_download_admission_rule_registry.csv",
    "covapie_bulk_download_admission_source_boundary_audit.csv",
    "covapie_bulk_download_admission_safety_audit.csv",
    "covapie_bulk_download_admission_issue_inventory.csv",
    "covapie_bulk_download_admission_design_gate_manifest.json",
)
SOURCE_SHA256 = {
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_schema_contract.csv"): "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_rule_registry.csv"): "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_source_boundary_audit.csv"): "2ee9e545469274b9d5464859e370e297e038b3264c3f4b3704b1fb8d6aca03d6",
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_safety_audit.csv"): "388869caf582bdf624d0016cae385dc2268f6cc05f54ecc9bf140608bbd3b208",
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_issue_inventory.csv"): "0f78005a11fbab8d4bbbada49ad4cc1b6803f596c566a27264a36246925d48d3",
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_design_gate_manifest.json"): "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
CANONICAL_FIELDS = (
    ("candidate_record_id", "pre_download"),
    ("pdb_id", "pre_download"),
    ("ligand_comp_id", "pre_download"),
    ("covalent_residue_name", "pre_download"),
    ("covalent_residue_chain_id", "pre_download"),
    ("covalent_residue_index", "pre_download"),
    ("covalent_residue_atom_name", "pre_download"),
    ("covalent_event_evidence_source", "pre_download"),
    ("covalent_bond_atom_pair", "pre_download"),
    ("topology_restoration_disposition", "pre_download"),
    ("duplicate_identity_key", "pre_download"),
    ("raw_target_relative_path", "pre_download"),
    ("leakage_group_id", "pre_final_split"),
    ("download_result_status", "post_download"),
    ("observed_http_status", "post_download"),
    ("observed_content_length_bytes", "post_download"),
    ("observed_sha256", "post_download"),
)
CANONICAL_RULES = (
    ("ADMIT_001", "unique_candidate_identity", "pre_download"),
    ("ADMIT_002", "valid_pdb_id_format", "pre_download"),
    ("ADMIT_003", "ligand_or_het_identity_present", "pre_download"),
    ("ADMIT_004", "covalent_residue_identity_present", "pre_download"),
    ("ADMIT_005", "cys_sg_scope_only_v1", "pre_download"),
    ("ADMIT_006", "explicit_covalent_event_evidence", "pre_download"),
    ("ADMIT_007", "distance_only_inference_forbidden", "pre_download"),
    ("ADMIT_008", "topology_restoration_disposition", "pre_download"),
    ("ADMIT_009", "duplicate_identity_precheck", "pre_download"),
    ("ADMIT_010", "leakage_group_assignment_before_split", "pre_final_split"),
    ("ADMIT_011", "raw_overwrite_forbidden", "pre_download"),
    ("ADMIT_012", "future_download_integrity_fields_required", "post_download"),
    ("ADMIT_013", "download_failure_fail_closed", "post_download"),
    ("ADMIT_014", "current_gate_grants_no_download_permission", "current_step"),
    ("ADMIT_015", "current_gate_grants_no_training_permission", "current_step"),
)

RULE_COLUMNS = (
    "admission_rule_id", "admission_rule_name", "evaluation_phase",
    "candidate_field_dependencies", "batch_context_dependencies",
    "evaluation_context_dependencies", "external_filesystem_required",
    "network_required", "download_execution_result_required",
    "pure_in_memory_interface_possible", "dependency_contract_passed",
    "semantics_complete", "deterministic_evaluation_possible_now",
    "deterministic_evaluation_possible_after_contract_freeze",
    "implementation_disposition", "blocking_reasons",
)
FIELD_COLUMNS = (
    "field_name", "requirement_phase", "source_value_contract", "candidate_record_field",
    "producer_scope", "dependent_rules", "batch_context_required", "evaluation_context_dependencies",
    "allowed_values_defined", "normalization_defined", "exact_validation_defined",
    "implementation_semantics_complete", "semantics_evidence", "blocking_reasons",
    "field_contract_mapping_passed",
)
CONTEXT_COLUMNS = (
    "context_item", "context_scope", "required_by_rules", "provided_by_future_caller",
    "filesystem_access_inside_evaluator", "network_access_inside_evaluator",
    "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
    "implementation_ready", "blocking_reasons",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason",
)
CSV_OUTPUTS = (
    "covapie_bulk_download_admission_rule_executability_matrix.csv",
    "covapie_bulk_download_admission_field_semantics_matrix.csv",
    "covapie_bulk_download_admission_evaluation_context_contract.csv",
    "covapie_bulk_download_admission_implementation_safety_audit.csv",
    "covapie_bulk_download_admission_implementation_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_bulk_download_admission_implementation_precondition_manifest.json"
CANONICAL_SAFETY_ITEMS = (
    "network_access_used_current_step", "raw_directory_traversed_current_step",
    "raw_structure_read_current_step", "artifact_reference_paths_followed_current_step",
    "candidate_records_materialized_current_step", "download_queue_materialized_current_step",
    "raw_files_written_current_step", "torch_imported", "numpy_imported", "rdkit_used",
    "biopython_used", "gemmi_used", "dataloader_instantiated", "checkpoint_loaded",
    "model_forward_called", "loss_compute_called", "training_allowed",
)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_by_git(relative_path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _source_paths() -> tuple[Path, ...]:
    return tuple(STEP14AT_ROOT / name for name in STEP14AT_FILENAMES)


def _read_csv(relative_path: Path) -> list[dict[str, str]]:
    with _repo_path(relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_source() -> dict[str, Any]:
    """Load only the six fixed, tracked Step14AT metadata files."""
    return {
        "schema": _read_csv(STEP14AT_ROOT / STEP14AT_FILENAMES[0]),
        "rules": _read_csv(STEP14AT_ROOT / STEP14AT_FILENAMES[1]),
        "manifest": json.loads(_repo_path(STEP14AT_ROOT / STEP14AT_FILENAMES[-1]).read_text(encoding="utf-8")),
    }


def _row(columns: tuple[str, ...], **values: Any) -> dict[str, str]:
    return {column: str(values.get(column, "")) for column in columns}


def _join(items: tuple[str, ...] | list[str]) -> str:
    return "|".join(items)


def _split(value: str) -> tuple[str, ...]:
    return tuple(item for item in value.split("|") if item)


def _sorted_unique(values: list[str]) -> tuple[str, ...]:
    return tuple(sorted(set(value for value in values if value)))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _context_specs() -> tuple[dict[str, Any], ...]:
    """All future evaluator inputs are explicit and never implicitly read."""
    return (
        dict(item="batch_candidate_record_ids", scope="batch", rules=("ADMIT_001",), exact=True),
        dict(item="batch_duplicate_identity_keys", scope="batch", rules=("ADMIT_009",), exact=True),
        dict(item="candidate_record_id_contract", scope="evaluation_policy", rules=("ADMIT_001",), exact=False, blocker="CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED"),
        dict(item="pdb_id_format_contract", scope="evaluation_policy", rules=("ADMIT_002",), exact=False, blocker="PDB_ID_FORMAT_SEMANTICS_UNRESOLVED"),
        dict(item="ligand_comp_id_contract", scope="evaluation_policy", rules=("ADMIT_003",), exact=False, blocker="LIGAND_COMP_ID_SEMANTICS_UNRESOLVED"),
        dict(item="covalent_residue_identity_contract", scope="evaluation_policy", rules=("ADMIT_004",), exact=False, blocker="COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"),
        dict(item="allowed_covalent_evidence_classes", scope="evaluation_policy", rules=("ADMIT_006", "ADMIT_007"), exact=False, blocker="COVALENT_EVIDENCE_ENUM_UNRESOLVED"),
        dict(item="allowed_topology_restoration_dispositions", scope="evaluation_policy", rules=("ADMIT_008",), exact=False, blocker="TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"),
        dict(item="duplicate_identity_key_contract", scope="evaluation_policy", rules=("ADMIT_009",), exact=False, blocker="DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"),
        dict(item="leakage_group_assignment_provenance_contract", scope="evaluation_policy", rules=("ADMIT_010",), exact=False, blocker="LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"),
        dict(item="existing_raw_target_relative_paths", scope="batch_external_state_snapshot", rules=("ADMIT_011",), exact=True),
        dict(item="raw_target_relative_path_contract", scope="evaluation_policy", rules=("ADMIT_011",), exact=False, blocker="RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"),
        dict(item="allowed_download_result_statuses", scope="evaluation_policy", rules=("ADMIT_012", "ADMIT_013"), exact=False, blocker="DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED"),
        dict(item="successful_http_status_contract", scope="evaluation_policy", rules=("ADMIT_012", "ADMIT_013"), exact=False, blocker="DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"),
        dict(item="content_length_contract", scope="evaluation_policy", rules=("ADMIT_012", "ADMIT_013"), exact=False, blocker="DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"),
        dict(item="sha256_format_contract", scope="evaluation_policy", rules=("ADMIT_012", "ADMIT_013"), exact=False, blocker="DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"),
        dict(item="current_stage_download_authorized", scope="stage", rules=("ADMIT_014",), exact=True),
        dict(item="current_stage_training_authorized", scope="stage", rules=("ADMIT_015",), exact=True),
    )


def _rule_specs() -> dict[str, dict[str, tuple[str, ...]]]:
    return {
        "ADMIT_001": {"fields": ("candidate_record_id",), "batch": ("batch_candidate_record_ids",), "context": ("candidate_record_id_contract",)},
        "ADMIT_002": {"fields": ("pdb_id",), "batch": (), "context": ("pdb_id_format_contract",)},
        "ADMIT_003": {"fields": ("ligand_comp_id",), "batch": (), "context": ("ligand_comp_id_contract",)},
        "ADMIT_004": {"fields": ("covalent_residue_name", "covalent_residue_chain_id", "covalent_residue_index", "covalent_residue_atom_name"), "batch": (), "context": ("covalent_residue_identity_contract",)},
        "ADMIT_005": {"fields": ("covalent_residue_name", "covalent_residue_atom_name"), "batch": (), "context": ()},
        "ADMIT_006": {"fields": ("covalent_event_evidence_source",), "batch": (), "context": ("allowed_covalent_evidence_classes",)},
        "ADMIT_007": {"fields": ("covalent_event_evidence_source",), "batch": (), "context": ("allowed_covalent_evidence_classes",)},
        "ADMIT_008": {"fields": ("topology_restoration_disposition",), "batch": (), "context": ("allowed_topology_restoration_dispositions",)},
        "ADMIT_009": {"fields": ("duplicate_identity_key",), "batch": ("batch_duplicate_identity_keys",), "context": ("duplicate_identity_key_contract",)},
        "ADMIT_010": {"fields": ("leakage_group_id",), "batch": (), "context": ("leakage_group_assignment_provenance_contract",)},
        "ADMIT_011": {"fields": ("raw_target_relative_path",), "batch": (), "context": ("existing_raw_target_relative_paths", "raw_target_relative_path_contract")},
        "ADMIT_012": {"fields": ("download_result_status", "observed_http_status", "observed_content_length_bytes", "observed_sha256"), "batch": (), "context": ("allowed_download_result_statuses", "successful_http_status_contract", "content_length_contract", "sha256_format_contract")},
        "ADMIT_013": {"fields": ("download_result_status", "observed_http_status", "observed_content_length_bytes", "observed_sha256"), "batch": (), "context": ("allowed_download_result_statuses", "successful_http_status_contract", "content_length_contract", "sha256_format_contract")},
        "ADMIT_014": {"fields": (), "batch": (), "context": ("current_stage_download_authorized",)},
        "ADMIT_015": {"fields": (), "batch": (), "context": ("current_stage_training_authorized",)},
    }


def _field_context_dependencies() -> dict[str, tuple[str, ...]]:
    return {
        "candidate_record_id": ("candidate_record_id_contract",),
        "pdb_id": ("pdb_id_format_contract",),
        "ligand_comp_id": ("ligand_comp_id_contract",),
        "covalent_residue_name": ("covalent_residue_identity_contract",),
        "covalent_residue_chain_id": ("covalent_residue_identity_contract",),
        "covalent_residue_index": ("covalent_residue_identity_contract",),
        "covalent_residue_atom_name": (),
        "covalent_event_evidence_source": ("allowed_covalent_evidence_classes",),
        "covalent_bond_atom_pair": (),
        "topology_restoration_disposition": ("allowed_topology_restoration_dispositions",),
        "duplicate_identity_key": ("duplicate_identity_key_contract",),
        "raw_target_relative_path": ("raw_target_relative_path_contract",),
        "leakage_group_id": ("leakage_group_assignment_provenance_contract",),
        "download_result_status": ("allowed_download_result_statuses",),
        "observed_http_status": ("successful_http_status_contract",),
        "observed_content_length_bytes": ("content_length_contract",),
        "observed_sha256": ("sha256_format_contract",),
    }


def _field_direct_blockers() -> dict[str, tuple[str, ...]]:
    return {
        "covalent_residue_atom_name": ("COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",),
        "covalent_bond_atom_pair": ("COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",),
    }


def _source_boundary_rows(source: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in _source_paths():
        absolute = _repo_path(path)
        passed = absolute.is_file() and not absolute.is_symlink() and _tracked_by_git(path) and _sha256(absolute) == SOURCE_SHA256[path.as_posix()]
        rows.append({"item": path.as_posix(), "passed": _bool_text(passed), "blocking_reason": "" if passed else f"source_contract_mismatch:{path.as_posix()}"})
    manifest = source["manifest"]
    checks = (
        ("step14at_stage", manifest.get("stage") == PREVIOUS_STAGE),
        ("step14at_all_checks_passed", manifest.get("all_checks_passed") is True),
        ("step14at_rule_count", manifest.get("admission_rule_count") == 15),
        ("step14at_field_count", manifest.get("admission_schema_field_count") == 17),
        ("step14at_canonical_masks", tuple(tuple(pair) for pair in manifest.get("canonical_mask_pairs", [])) == CANONICAL_MASK_PAIRS),
        ("step14at_bulk_download_not_ready", manifest.get("ready_for_bulk_download_now") is False),
        ("step14at_training_not_ready", manifest.get("ready_for_training") is False and manifest.get("ready_to_train_now") is False),
        ("step14at_feature_semantics_required", manifest.get("feature_semantics_audit_required_before_training") is True),
    )
    rows.extend({"item": item, "passed": _bool_text(passed), "blocking_reason": "" if passed else item} for item, passed in checks)
    return rows


def _validate_source(source: dict[str, Any], boundary_rows: list[dict[str, str]]) -> bool:
    schema_projection = [(row.get("admission_field_name"), row.get("requirement_phase")) for row in source["schema"]]
    rule_projection = [(row.get("admission_rule_id"), row.get("admission_rule_name"), row.get("evaluation_phase")) for row in source["rules"]]
    return all(row["passed"] == "true" for row in boundary_rows) and schema_projection == list(CANONICAL_FIELDS) and rule_projection == list(CANONICAL_RULES)


def _context_rows() -> list[dict[str, str]]:
    return [_row(
        CONTEXT_COLUMNS,
        context_item=spec["item"], context_scope=spec["scope"], required_by_rules=_join(spec["rules"]),
        provided_by_future_caller="true", filesystem_access_inside_evaluator="false",
        network_access_inside_evaluator="false", deterministic_now=_bool_text(bool(spec["exact"])),
        deterministic_after_contract_freeze="true", exact_contract_defined=_bool_text(bool(spec["exact"])),
        implementation_ready=_bool_text(bool(spec["exact"])), blocking_reasons=spec.get("blocker", ""),
    ) for spec in _context_specs()]


def _context_blockers(rows: list[dict[str, str]]) -> dict[str, tuple[str, ...]]:
    return {row["context_item"]: _split(row["blocking_reasons"]) for row in rows}


def _field_blockers_by_name(context_rows: list[dict[str, str]]) -> dict[str, tuple[str, ...]]:
    context_blockers = _context_blockers(context_rows)
    return {
        field: _sorted_unique([
            *_field_direct_blockers().get(field, ()),
            *(blocker for item in contexts for blocker in context_blockers.get(item, (f"MISSING_EVALUATION_CONTEXT:{item}",))),
        ])
        for field, contexts in _field_context_dependencies().items()
    }


def _rule_rows(context_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    context_blockers = _context_blockers(context_rows)
    field_blockers = _field_blockers_by_name(context_rows)
    specs = _rule_specs()
    rows: list[dict[str, str]] = []
    for rule_id, name, phase in CANONICAL_RULES:
        spec = specs[rule_id]
        blockers = _sorted_unique(
            [
                blocker
                for field in spec["fields"]
                for blocker in field_blockers.get(field, (f"MISSING_CANDIDATE_FIELD:{field}",))
            ]
            + [
                blocker
                for item in spec["batch"]
                for blocker in context_blockers.get(item, (f"MISSING_BATCH_CONTEXT:{item}",))
            ]
            + [
                blocker
                for item in spec["context"]
                for blocker in context_blockers.get(item, (f"MISSING_EVALUATION_CONTEXT:{item}",))
            ]
        )
        complete = not blockers
        rows.append(_row(
            RULE_COLUMNS,
            admission_rule_id=rule_id, admission_rule_name=name, evaluation_phase=phase,
            candidate_field_dependencies=_join(spec["fields"]), batch_context_dependencies=_join(spec["batch"]),
            evaluation_context_dependencies=_join(spec["context"]), external_filesystem_required="false",
            network_required="false", download_execution_result_required=_bool_text(phase == "post_download"),
            pure_in_memory_interface_possible="true", dependency_contract_passed="true",
            semantics_complete=_bool_text(complete), deterministic_evaluation_possible_now=_bool_text(complete),
            deterministic_evaluation_possible_after_contract_freeze="true",
            implementation_disposition="rule_logic_ready" if complete else "interface_only_pending_semantics",
            blocking_reasons=_join(blockers),
        ))
    return rows


def _producer_scope(phase: str) -> str:
    if phase == "pre_download":
        return "candidate_metadata_provider"
    if phase == "pre_final_split":
        return "leakage_assignment_stage"
    return "download_execution_result"


def _field_rows(
    schema_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
    rule_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    source_contracts = {row["admission_field_name"]: row["value_contract"] for row in schema_rows}
    field_blockers = _field_blockers_by_name(context_rows)
    field_contexts = _field_context_dependencies()
    rows: list[dict[str, str]] = []
    for field, phase in CANONICAL_FIELDS:
        contexts = field_contexts[field]
        blockers = field_blockers[field]
        allowed_values = field == "covalent_residue_atom_name"
        exact_validation = field == "covalent_residue_atom_name"
        complete = not blockers and allowed_values and exact_validation
        dependent_rules = _sorted_unique([
            row["admission_rule_id"]
            for row in rule_rows
            if field in _split(row["candidate_field_dependencies"])
        ])
        rows.append(_row(
            FIELD_COLUMNS,
            field_name=field, requirement_phase=phase, source_value_contract=source_contracts[field],
            candidate_record_field=_bool_text(phase == "pre_download"), producer_scope=_producer_scope(phase),
            batch_context_required=_bool_text(field in {"candidate_record_id", "duplicate_identity_key"}),
            evaluation_context_dependencies=_join(contexts), allowed_values_defined=_bool_text(allowed_values),
            normalization_defined="false", exact_validation_defined=_bool_text(exact_validation),
            implementation_semantics_complete=_bool_text(complete),
            semantics_evidence="step14at_schema_contract_value_contract_only",
            blocking_reasons=_join(blockers), field_contract_mapping_passed="true",
            dependent_rules=_join(dependent_rules),
        ))
    return rows


def _safety_rows() -> list[dict[str, str]]:
    return [_row(SAFETY_COLUMNS, safety_item=item, required_status="false", observed_status="false", safety_passed="true", blocking_reason="") for item in CANONICAL_SAFETY_ITEMS]


def _validate_dependency_graph(
    rule_rows: list[dict[str, str]],
    field_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
) -> bool:
    """Validate both directions of the frozen field/context-to-rule graph."""
    canonical_fields = {field for field, _ in CANONICAL_FIELDS}
    expected_context_items = [spec["item"] for spec in _context_specs()]
    if len({row.get("context_item") for row in context_rows}) != len(context_rows):
        return False
    if [row.get("context_item") for row in context_rows] != expected_context_items:
        return False
    contexts = {row["context_item"]: row for row in context_rows}
    expected_rules = [rule_id for rule_id, _, _ in CANONICAL_RULES]
    if [row.get("admission_rule_id") for row in rule_rows] != expected_rules:
        return False
    reverse_references = {item: [] for item in expected_context_items}
    specs = _rule_specs()
    for row in rule_rows:
        rule_id = row["admission_rule_id"]
        spec = specs.get(rule_id)
        if spec is None:
            return False
        for column, expected in (
            ("candidate_field_dependencies", spec["fields"]),
            ("batch_context_dependencies", spec["batch"]),
            ("evaluation_context_dependencies", spec["context"]),
        ):
            if row[column] != _join(expected):
                return False
        fields = _split(row["candidate_field_dependencies"])
        batch_contexts = _split(row["batch_context_dependencies"])
        evaluation_contexts = _split(row["evaluation_context_dependencies"])
        if any(field not in canonical_fields for field in fields):
            return False
        if any(item not in contexts or contexts[item]["context_scope"] != "batch" for item in batch_contexts):
            return False
        if any(item not in contexts for item in evaluation_contexts):
            return False
        for item in (*batch_contexts, *evaluation_contexts):
            reverse_references[item].append(rule_id)
    for item, row in contexts.items():
        if row["required_by_rules"] != _join(_sorted_unique(reverse_references[item])):
            return False
        if not reverse_references[item] and row["context_scope"] != "stage":
            return False
    expected_dependents = {
        field: _join(_sorted_unique([
            row["admission_rule_id"]
            for row in rule_rows
            if field in _split(row["candidate_field_dependencies"])
        ]))
        for field in canonical_fields
    }
    return all(row.get("dependent_rules") == expected_dependents[row["field_name"]] for row in field_rows)


def _validate_rule_rows(
    rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
    field_rows: list[dict[str, str]],
) -> bool:
    return (
        len(rows) == len(CANONICAL_RULES)
        and all(tuple(row.keys()) == RULE_COLUMNS for row in rows)
        and rows == _rule_rows(context_rows)
        and _validate_dependency_graph(rows, field_rows, context_rows)
        and all(row["external_filesystem_required"] == "false" and row["network_required"] == "false" for row in rows)
    )


def _validate_field_rows(
    rows: list[dict[str, str]],
    schema_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
    rule_rows: list[dict[str, str]],
) -> bool:
    return (
        len(rows) == len(CANONICAL_FIELDS)
        and all(tuple(row.keys()) == FIELD_COLUMNS for row in rows)
        and rows == _field_rows(schema_rows, context_rows, rule_rows)
        and _validate_dependency_graph(rule_rows, rows, context_rows)
    )


def _validate_context_rows(rows: list[dict[str, str]]) -> bool:
    return len(rows) == len(_context_specs()) and all(tuple(row.keys()) == CONTEXT_COLUMNS for row in rows) and rows == _context_rows()


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return (
        len(rows) == len(CANONICAL_SAFETY_ITEMS)
        and all(tuple(row.keys()) == SAFETY_COLUMNS for row in rows)
        and [row["safety_item"] for row in rows] == list(CANONICAL_SAFETY_ITEMS)
        and len({row["safety_item"] for row in rows}) == len(rows)
        and all(row["required_status"] == "false" for row in rows)
        and all(row["observed_status"] == "false" for row in rows)
        and all(row["safety_passed"] == "true" for row in rows)
        and all(row["blocking_reason"] == "" for row in rows)
    )


def _issue_rows(rule_rows: list[dict[str, str]], field_rows: list[dict[str, str]], context_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    all_issues = _sorted_unique([
        *(blocker for row in rule_rows for blocker in _split(row["blocking_reasons"])),
        *(blocker for row in field_rows for blocker in _split(row["blocking_reasons"])),
        *(blocker for row in context_rows for blocker in _split(row["blocking_reasons"])),
    ])
    context_rules = {
        issue: [
            rule_id
            for row in context_rows
            if issue in _split(row["blocking_reasons"])
            for rule_id in _split(row["required_by_rules"])
        ]
        for issue in all_issues
    }
    return [_row(
        ISSUE_COLUMNS,
        issue_id=issue, issue_type="implementation_semantics_gap",
        affected_fields=_join(_sorted_unique([row["field_name"] for row in field_rows if issue in _split(row["blocking_reasons"])])),
        affected_rules=_join(_sorted_unique(
            [row["admission_rule_id"] for row in rule_rows if issue in _split(row["blocking_reasons"])]
            + [rule_id for row in field_rows if issue in _split(row["blocking_reasons"]) for rule_id in _split(row["dependent_rules"])]
            + context_rules[issue]
        )),
        severity="blocking", status="open", blocking_scope="admission_evaluator_rule_logic", blocking_reason=issue,
    ) for issue in all_issues]


def _build_materialization(
    source: dict[str, Any],
    *,
    rule_rows: list[dict[str, str]] | None = None,
    field_rows: list[dict[str, str]] | None = None,
    context_rows: list[dict[str, str]] | None = None,
    safety_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Audit an injectable metadata contract without evaluating candidates."""
    context_rows = _context_rows() if context_rows is None else context_rows
    rule_rows = _rule_rows(context_rows) if rule_rows is None else rule_rows
    field_rows = _field_rows(source["schema"], context_rows, rule_rows) if field_rows is None else field_rows
    safety_rows = _safety_rows() if safety_rows is None else safety_rows
    source_rows = _source_boundary_rows(source)
    source_passed = _validate_source(source, source_rows)
    dependency_passed = _validate_rule_rows(rule_rows, context_rows, field_rows)
    field_mapping_passed = _validate_field_rows(field_rows, source["schema"], context_rows, rule_rows)
    context_contract_passed = _validate_context_rows(context_rows) and _validate_dependency_graph(rule_rows, field_rows, context_rows)
    safety_passed = _validate_safety_rows(safety_rows)
    rule_semantics_complete = all(row["semantics_complete"] == "true" for row in rule_rows)
    field_semantics_complete = all(row["implementation_semantics_complete"] == "true" for row in field_rows)
    contexts_ready = all(row["implementation_ready"] == "true" for row in context_rows)
    interface_ready = all((source_passed, dependency_passed, field_mapping_passed, context_contract_passed, safety_passed))
    logic_ready = interface_ready and rule_semantics_complete and field_semantics_complete and contexts_ready
    issues = _issue_rows(rule_rows, field_rows, context_rows)
    structural_blockers = [
        *( ["source_boundary_audit_failed"] if not source_passed else []),
        *( ["rule_dependency_contract_failed"] if not dependency_passed else []),
        *( ["field_contract_mapping_failed"] if not field_mapping_passed else []),
        *( ["evaluation_context_contract_failed"] if not context_contract_passed else []),
        *( ["implementation_safety_audit_failed"] if not safety_passed else []),
    ]
    return {
        "source_rows": source_rows, "rule_rows": rule_rows, "field_rows": field_rows,
        "context_rows": context_rows, "safety_rows": safety_rows, "issue_rows": issues,
        "all_source_boundary_checks_passed": source_passed,
        "all_rule_dependency_contract_checks_passed": dependency_passed,
        "all_rule_semantics_complete": rule_semantics_complete,
        "all_field_contract_mapping_checks_passed": field_mapping_passed,
        "all_field_semantics_complete": field_semantics_complete,
        "all_evaluation_context_contract_checks_passed": context_contract_passed,
        "all_evaluation_contexts_ready": contexts_ready,
        "all_safety_checks_passed": safety_passed,
        "precondition_audit_completed": True,
        "ready_for_admission_evaluator_interface_implementation": interface_ready,
        "ready_for_admission_evaluator_rule_logic_implementation": logic_ready,
        "all_checks_passed": logic_ready,
        "blocking_reasons": [*structural_blockers, *[row["issue_id"] for row in issues]],
        "recommended_next_step": NEXT_STAGE if logic_ready else BLOCKED_NEXT_STAGE,
    }


def _write_outputs(output_root: Path, result: dict[str, Any]) -> dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    outputs = (
        (CSV_OUTPUTS[0], RULE_COLUMNS, result["rule_rows"]),
        (CSV_OUTPUTS[1], FIELD_COLUMNS, result["field_rows"]),
        (CSV_OUTPUTS[2], CONTEXT_COLUMNS, result["context_rows"]),
        (CSV_OUTPUTS[3], SAFETY_COLUMNS, result["safety_rows"]),
        (CSV_OUTPUTS[4], ISSUE_COLUMNS, result["issue_rows"]),
    )
    for name, columns, rows in outputs:
        _write_csv(output_root / name, columns, rows)
    return {name: _sha256(output_root / name) for name in CSV_OUTPUTS}


def _manifest_payload(result: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    rule_rows = result["rule_rows"]
    field_rows = result["field_rows"]
    context_rows = result["context_rows"]
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "previous_stage": PREVIOUS_STAGE, "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "source_read_boundary": "only_step14at_6_committed_outputs_metadata_only",
        "source_input_count": len(SOURCE_SHA256), "source_input_sha256": SOURCE_SHA256,
        "artifact_reference_paths_not_recursively_opened": True,
        "rule_count": len(rule_rows), "field_count": len(field_rows),
        "pre_download_field_count": sum(row["requirement_phase"] == "pre_download" for row in field_rows),
        "pre_final_split_field_count": sum(row["requirement_phase"] == "pre_final_split" for row in field_rows),
        "post_download_field_count": sum(row["requirement_phase"] == "post_download" for row in field_rows),
        "pure_in_memory_rule_count": sum(row["pure_in_memory_interface_possible"] == "true" for row in rule_rows),
        "rule_dependency_contract_passed_count": sum(row["dependency_contract_passed"] == "true" for row in rule_rows),
        "semantics_complete_rule_count": sum(row["semantics_complete"] == "true" for row in rule_rows),
        "semantics_incomplete_rule_count": sum(row["semantics_complete"] != "true" for row in rule_rows),
        "semantics_complete_field_count": sum(row["implementation_semantics_complete"] == "true" for row in field_rows),
        "semantics_incomplete_field_count": sum(row["implementation_semantics_complete"] != "true" for row in field_rows),
        "batch_context_rule_count": sum(bool(row["batch_context_dependencies"]) for row in rule_rows),
        "external_context_rule_count": sum(bool(row["evaluation_context_dependencies"]) for row in rule_rows),
        "evaluation_context_item_count": len(context_rows),
        "deterministic_now_context_count": sum(row["deterministic_now"] == "true" for row in context_rows),
        "deterministic_after_contract_freeze_context_count": sum(row["deterministic_after_contract_freeze"] == "true" for row in context_rows),
        "ready_evaluation_context_count": sum(row["implementation_ready"] == "true" for row in context_rows),
        "issue_count": len(result["issue_rows"]),
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": len(CANONICAL_MASK_PAIRS),
        "candidate_records_materialized": False, "download_queue_materialized": False,
        "network_access_used_current_step": False, "raw_structure_read_current_step": False,
        "ready_for_admission_evaluator_interface_implementation": result["ready_for_admission_evaluator_interface_implementation"],
        "ready_for_admission_evaluator_rule_logic_implementation": result["ready_for_admission_evaluator_rule_logic_implementation"],
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "all_source_boundary_checks_passed": result["all_source_boundary_checks_passed"],
        "all_rule_dependency_contract_checks_passed": result["all_rule_dependency_contract_checks_passed"],
        "all_rule_semantics_complete": result["all_rule_semantics_complete"],
        "all_field_contract_mapping_checks_passed": result["all_field_contract_mapping_checks_passed"],
        "all_field_semantics_complete": result["all_field_semantics_complete"],
        "all_evaluation_context_contract_checks_passed": result["all_evaluation_context_contract_checks_passed"],
        "all_evaluation_contexts_ready": result["all_evaluation_contexts_ready"],
        "all_safety_checks_passed": result["all_safety_checks_passed"],
        "precondition_audit_completed": result["precondition_audit_completed"],
        "all_checks_passed": result["all_checks_passed"],
        "blocking_reasons": result["blocking_reasons"], "recommended_next_step": result["recommended_next_step"],
        "non_manifest_output_count": len(CSV_OUTPUTS), "output_file_count": len(CSV_OUTPUTS) + 1,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_sha256": output_sha256,
    }


def run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize deterministic blocker-discovery metadata without side effects elsewhere."""
    result = _build_materialization(_load_source())
    output_sha256 = _write_outputs(output_root, result)
    manifest = _manifest_payload(result, output_sha256)
    (output_root / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest

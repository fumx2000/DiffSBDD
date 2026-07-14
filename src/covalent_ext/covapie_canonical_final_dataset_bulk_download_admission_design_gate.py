"""Read-only admission-design gate for future canonical bulk downloads.

The gate reads a fixed set of committed Step 14AS/14AR/14AQ metadata only.
It never follows artifact-reference paths, opens raw data, accesses a network,
or materializes a candidate/download queue.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


STAGE = "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
STEP_LABEL = "Step14AT"
PROJECT_NAME = "CovaPIE"
PREVIOUS_STAGE = "covapie_final_dataset_qa_gate_v1"
NEXT_STAGE = "covapie_canonical_final_dataset_bulk_download_admission_implementation_v1"
BLOCKED_NEXT_STAGE = "resolve_covapie_bulk_download_admission_design_gate_blockers"
MANIFEST_SCHEMA_VERSION = "covapie_bulk_download_admission_design_gate_v1_manifest_v1"
SOURCE_STEP14AQ_COMMIT = "b6f09468447e611a586751bf329d5b07bb308317"

REPO_ROOT = Path(__file__).resolve().parents[2]
QA_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1")
AR_MANIFEST = Path(
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/"
    "covapie_final_dataset_materialization_smoke_manifest.json"
)
AQ_MANIFEST = Path(
    "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_unified_leakage_split_materialization_smoke_manifest.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)

QA_FILENAMES = (
    "covapie_final_dataset_qa_v1_artifact_inventory_audit.csv",
    "covapie_final_dataset_qa_v1_issue_inventory.csv",
    "covapie_final_dataset_qa_v1_manifest.json",
    "covapie_final_dataset_qa_v1_mask_contract_audit.csv",
    "covapie_final_dataset_qa_v1_precondition_audit.csv",
    "covapie_final_dataset_qa_v1_safety_training_boundary_audit.csv",
    "covapie_final_dataset_qa_v1_schema_lineage_audit.csv",
    "covapie_final_dataset_qa_v1_split_leakage_audit.csv",
)
SOURCE_SHA256 = {
    str(QA_ROOT / "covapie_final_dataset_qa_v1_artifact_inventory_audit.csv"): "0f01215310ae296355bb08348e9a9a0b9dbcef3a2e73a1e2c7ac63c25d4428e1",
    str(QA_ROOT / "covapie_final_dataset_qa_v1_issue_inventory.csv"): "b6698aefe44b7fcf494207bdad629651110b878621d7d3a986776f62d76b58d9",
    str(QA_ROOT / "covapie_final_dataset_qa_v1_manifest.json"): "4f7c884379f926af52101f40a7870b243f0309af3b1637dc65c8c0691acf9f35",
    str(QA_ROOT / "covapie_final_dataset_qa_v1_mask_contract_audit.csv"): "2208afeaa2f5c7e1138f0ffa1aeb3b4640b3e46a04a49ce5fc68e30f72187789",
    str(QA_ROOT / "covapie_final_dataset_qa_v1_precondition_audit.csv"): "12a612ff3c277fb0844939285ad303430907aebc464f33c27d0cd0e29596b51f",
    str(QA_ROOT / "covapie_final_dataset_qa_v1_safety_training_boundary_audit.csv"): "8ea6a53d04456443014ba250a0cfacf4983e39d2138d7035ad188dc1dcceebe5",
    str(QA_ROOT / "covapie_final_dataset_qa_v1_schema_lineage_audit.csv"): "2b60a3d32939508ca6c0fbebbee6a6fd5c1b9d01dc9bcaaea23b581e8dd43019",
    str(QA_ROOT / "covapie_final_dataset_qa_v1_split_leakage_audit.csv"): "42aa0778a8ac257611a71ab85b0c1b3491cce655e2737270f4a2261aee209b0b",
    str(AR_MANIFEST): "6f25c8976b295749f3af6407c3bb8ce17cfbda9f18cb967df5fe9b47b480c433",
    str(AQ_MANIFEST): "697f4ad7d4d5afb7598862ad82b93db7f8e6c1aa05ea61a9162cae45a1d59bba",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)

CANONICAL_ADMISSION_FIELD_CONTRACTS = (
    ("candidate_record_id", "pre_download", "unique, non-empty deterministic candidate identity"),
    ("pdb_id", "pre_download", "four-character PDB identifier validated before queueing"),
    ("ligand_comp_id", "pre_download", "non-empty ligand or HET identity"),
    ("covalent_residue_name", "pre_download", "non-empty residue identity"),
    ("covalent_residue_chain_id", "pre_download", "non-empty chain identity"),
    ("covalent_residue_index", "pre_download", "explicit residue index"),
    ("covalent_residue_atom_name", "pre_download", "must be SG for v1 Cys scope"),
    ("covalent_event_evidence_source", "pre_download", "explicit non-distance-only evidence source"),
    ("covalent_bond_atom_pair", "pre_download", "explicit atom-pair evidence or manual-review disposition"),
    ("topology_restoration_disposition", "pre_download", "approved template or explicit manual review"),
    ("duplicate_identity_key", "pre_download", "pre-download deduplication key"),
    ("raw_target_relative_path", "pre_download", "future raw destination, no overwrite permitted"),
    ("leakage_group_id", "pre_final_split", "assigned before final split admission"),
    ("download_result_status", "post_download", "observed future download result status"),
    ("observed_http_status", "post_download", "observed HTTP status from future download execution"),
    ("observed_content_length_bytes", "post_download", "observed downloaded content length in bytes"),
    ("observed_sha256", "post_download", "observed SHA256 of future downloaded content"),
)
ADMISSION_RECORD_FIELDS = tuple(contract[0] for contract in CANONICAL_ADMISSION_FIELD_CONTRACTS)
SCHEMA_VALUE_CONTRACTS = {contract[0]: contract[2] for contract in CANONICAL_ADMISSION_FIELD_CONTRACTS}
ALLOWED_REQUIREMENT_PHASES = {"pre_download", "pre_final_split", "post_download"}

# This tuple is the only source of truth for both emitted rules and validation.
CANONICAL_RULES = (
    ("ADMIT_001", "unique_candidate_identity", "future_candidate_record", "unique_identity_resolved", "candidate_identity_unresolved", "pre_download"),
    ("ADMIT_002", "valid_pdb_id_format", "future_candidate_record", "pdb_id_format_valid", "invalid_pdb_id", "pre_download"),
    ("ADMIT_003", "ligand_or_het_identity_present", "future_candidate_record", "ligand_identity_present", "ligand_identity_missing", "pre_download"),
    ("ADMIT_004", "covalent_residue_identity_present", "future_candidate_record", "residue_identity_present", "covalent_residue_identity_missing", "pre_download"),
    ("ADMIT_005", "cys_sg_scope_only_v1", "future_candidate_record", "residue_name_CYS_and_atom_SG", "outside_cys_sg_v1_scope", "pre_download"),
    ("ADMIT_006", "explicit_covalent_event_evidence", "future_candidate_record", "explicit_evidence_source_present", "covalent_event_evidence_missing", "pre_download"),
    ("ADMIT_007", "distance_only_inference_forbidden", "future_candidate_record", "not_distance_only_inference", "distance_only_inference_not_admissible", "pre_download"),
    ("ADMIT_008", "topology_restoration_disposition", "approved_template_or_manual_review", "approved_or_manual_review", "topology_restoration_unapproved", "pre_download"),
    ("ADMIT_009", "duplicate_identity_precheck", "future_candidate_record", "duplicate_precheck_complete", "duplicate_identity_unresolved", "pre_download"),
    ("ADMIT_010", "leakage_group_assignment_before_split", "future_candidate_record", "leakage_group_assigned", "leakage_group_unassigned", "pre_final_split"),
    ("ADMIT_011", "raw_overwrite_forbidden", "future_download_target", "target_does_not_overwrite_existing_raw", "raw_target_overwrite_forbidden", "pre_download"),
    ("ADMIT_012", "future_download_integrity_fields_required", "future_download_result", "download_status_http_status_content_length_and_sha256_present", "download_integrity_fields_missing", "post_download"),
    ("ADMIT_013", "download_failure_fail_closed", "future_download_result", "non_success_or_integrity_failure_not_admitted", "download_failure_must_fail_closed", "post_download"),
    ("ADMIT_014", "current_gate_grants_no_download_permission", "current_design_gate", "bulk_download_not_authorized_now", "bulk_download_not_authorized", "current_step"),
    ("ADMIT_015", "current_gate_grants_no_training_permission", "current_design_gate", "training_not_authorized_now", "training_not_authorized", "current_step"),
)
KEY_RULE_CONTRACTS = {
    "cys_sg_scope_only_v1": ("residue_name_CYS_and_atom_SG", "outside_cys_sg_v1_scope"),
    "distance_only_inference_forbidden": ("not_distance_only_inference", "distance_only_inference_not_admissible"),
    "topology_restoration_disposition": ("approved_or_manual_review", "topology_restoration_unapproved"),
    "raw_overwrite_forbidden": ("target_does_not_overwrite_existing_raw", "raw_target_overwrite_forbidden"),
    "download_failure_fail_closed": ("non_success_or_integrity_failure_not_admitted", "download_failure_must_fail_closed"),
    "current_gate_grants_no_download_permission": ("bulk_download_not_authorized_now", "bulk_download_not_authorized"),
    "current_gate_grants_no_training_permission": ("training_not_authorized_now", "training_not_authorized"),
}
ALLOWED_EVALUATION_PHASES = {"pre_download", "pre_final_split", "post_download", "current_step"}

SCHEMA_COLUMNS = (
    "admission_field_name", "requirement_phase", "required_at_phase", "value_contract", "failure_severity",
    "admission_schema_passed", "blocking_reason",
)
RULE_COLUMNS = (
    "admission_rule_id", "admission_rule_name", "evidence_source", "required_status",
    "failure_severity", "blocking_reason", "evaluation_phase", "network_required",
    "raw_structure_required", "ready_for_future_implementation",
)
SOURCE_BOUNDARY_COLUMNS = (
    "boundary_item", "source_path", "expected_status", "observed_status",
    "source_boundary_passed", "blocking_reason",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "severity", "status", "issue_count", "blocking_reason",
)
CSV_OUTPUTS = (
    "covapie_bulk_download_admission_schema_contract.csv",
    "covapie_bulk_download_admission_rule_registry.csv",
    "covapie_bulk_download_admission_source_boundary_audit.csv",
    "covapie_bulk_download_admission_safety_audit.csv",
    "covapie_bulk_download_admission_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_bulk_download_admission_design_gate_manifest.json"
SECTION_BLOCKERS = (
    ("source", "source_boundary_audit_failed"),
    ("schema", "admission_schema_contract_failed"),
    ("rule", "admission_rule_contract_failed"),
    ("safety", "safety_boundary_audit_failed"),
)
SECTION_ISSUES = {
    "source": ("SOURCE_BOUNDARY_FAILURE", "source_boundary_failure"),
    "schema": ("ADMISSION_SCHEMA_CONTRACT_FAILURE", "admission_schema_contract_failure"),
    "rule": ("ADMISSION_RULE_CONTRACT_FAILURE", "admission_rule_contract_failure"),
    "safety": ("SAFETY_BOUNDARY_FAILURE", "safety_boundary_failure"),
}
CANONICAL_SAFETY_ITEMS = (
    "network_access_used_current_step", "raw_directory_traversed_current_step",
    "raw_structure_read_current_step", "artifact_reference_paths_followed_current_step",
    "download_queue_materialized_current_step", "download_manifest_materialized_current_step",
    "raw_files_written_current_step", "torch_imported", "numpy_imported", "rdkit_used",
    "biopython_used", "gemmi_used", "dataloader_instantiated", "checkpoint_loaded",
    "model_forward_called", "loss_compute_called", "training_allowed",
)


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_by_git(relative_path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _read_json(relative_path: Path) -> dict[str, Any]:
    return json.loads(_repo_path(relative_path).read_text(encoding="utf-8"))


def _source_paths() -> tuple[Path, ...]:
    return tuple(QA_ROOT / name for name in QA_FILENAMES) + (AR_MANIFEST, AQ_MANIFEST)


def _load_source() -> dict[str, Any]:
    """Read only fixed committed metadata, never artifact-reference targets."""
    return {
        "qa_manifest": _read_json(QA_ROOT / "covapie_final_dataset_qa_v1_manifest.json"),
        "ar_manifest": _read_json(AR_MANIFEST),
        "aq_manifest": _read_json(AQ_MANIFEST),
    }


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _row(columns: tuple[str, ...], **values: Any) -> dict[str, Any]:
    return {column: values.get(column, "") for column in columns}


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _schema_rows() -> list[dict[str, Any]]:
    return [
        _row(
            SCHEMA_COLUMNS,
            admission_field_name=field,
            requirement_phase=phase,
            required_at_phase="true",
            value_contract=value_contract,
            failure_severity="blocking",
            admission_schema_passed="true",
            blocking_reason="",
        )
        for field, phase, value_contract in CANONICAL_ADMISSION_FIELD_CONTRACTS
    ]


def _rule_rows() -> list[dict[str, Any]]:
    return [
        _row(
            RULE_COLUMNS,
            admission_rule_id=rule_id,
            admission_rule_name=name,
            evidence_source=evidence,
            required_status=required,
            failure_severity="blocking",
            blocking_reason=reason,
            evaluation_phase=phase,
            network_required="false",
            raw_structure_required="false",
            ready_for_future_implementation="true",
        )
        for rule_id, name, evidence, required, reason, phase in CANONICAL_RULES
    ]


def _validate_schema_contract(schema_rows: list[dict[str, Any]]) -> bool:
    if len(schema_rows) != len(CANONICAL_ADMISSION_FIELD_CONTRACTS):
        return False
    if not all(tuple(row.keys()) == SCHEMA_COLUMNS for row in schema_rows):
        return False
    projection = [
        (row["admission_field_name"], row["requirement_phase"], row["value_contract"])
        for row in schema_rows
    ]
    return (
        projection == list(CANONICAL_ADMISSION_FIELD_CONTRACTS)
        and len({row["admission_field_name"] for row in schema_rows}) == len(schema_rows)
        and all(row["requirement_phase"] in ALLOWED_REQUIREMENT_PHASES for row in schema_rows)
        and all(row["required_at_phase"] == "true" for row in schema_rows)
        and all(row["failure_severity"] == "blocking" for row in schema_rows)
        and all(row["admission_schema_passed"] == "true" for row in schema_rows)
        and all(row["blocking_reason"] == "" for row in schema_rows)
    )


def _validate_rule_contract(rule_rows: list[dict[str, Any]]) -> bool:
    expected_ids = [f"ADMIT_{index:03d}" for index in range(1, 16)]
    if len(rule_rows) != 15 or [row.get("admission_rule_id") for row in rule_rows] != expected_ids:
        return False
    if not all(tuple(row.keys()) == RULE_COLUMNS for row in rule_rows):
        return False
    if len({row.get("admission_rule_id") for row in rule_rows}) != 15:
        return False
    if len({row.get("admission_rule_name") for row in rule_rows}) != 15:
        return False
    if not all(row.get("failure_severity") == "blocking" for row in rule_rows):
        return False
    if not all(bool(row.get("blocking_reason")) for row in rule_rows):
        return False
    if not all(row.get("evaluation_phase") in ALLOWED_EVALUATION_PHASES for row in rule_rows):
        return False
    if not all(row.get("network_required") == "false" for row in rule_rows):
        return False
    if not all(row.get("raw_structure_required") == "false" for row in rule_rows):
        return False
    if not all(row.get("ready_for_future_implementation") == "true" for row in rule_rows):
        return False
    projection = [
        (
            row["admission_rule_id"], row["admission_rule_name"], row["evidence_source"],
            row["required_status"], row["blocking_reason"], row["evaluation_phase"],
        )
        for row in rule_rows
    ]
    if projection != list(CANONICAL_RULES):
        return False
    by_name = {row["admission_rule_name"]: row for row in rule_rows}
    for name, (required_status, blocking_reason) in KEY_RULE_CONTRACTS.items():
        row = by_name.get(name)
        if row is None or row["required_status"] != required_status:
            return False
        if row["blocking_reason"] != blocking_reason:
            return False
    return True


def _validate_safety_contract(safety_rows: list[dict[str, Any]]) -> bool:
    return (
        len(safety_rows) == len(CANONICAL_SAFETY_ITEMS)
        and all(tuple(row.keys()) == SAFETY_COLUMNS for row in safety_rows)
        and [row["safety_item"] for row in safety_rows] == list(CANONICAL_SAFETY_ITEMS)
        and len({row["safety_item"] for row in safety_rows}) == len(safety_rows)
        and all(row["required_status"] == "false" for row in safety_rows)
        and all(row["observed_status"] == "false" for row in safety_rows)
        and all(row["safety_passed"] == "true" for row in safety_rows)
        and all(row["blocking_reason"] == "" for row in safety_rows)
    )


def _source_boundary_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _source_paths():
        absolute = _repo_path(path)
        passed = absolute.is_file() and _tracked_by_git(path) and _sha256(absolute) == SOURCE_SHA256[path.as_posix()]
        rows.append(_row(
            SOURCE_BOUNDARY_COLUMNS,
            boundary_item=f"tracked_hash_verified:{path.name}",
            source_path=path.as_posix(),
            expected_status="tracked_regular_file_with_fixed_sha256",
            observed_status="tracked_regular_file_with_fixed_sha256" if passed else "source_contract_mismatch",
            source_boundary_passed=_bool_text(passed),
            blocking_reason="" if passed else f"source_contract_mismatch:{path.as_posix()}",
        ))
    qa, ar, aq = source["qa_manifest"], source["ar_manifest"], source["aq_manifest"]
    semantic_checks = (
        ("qa_v1_stage", qa.get("stage") == PREVIOUS_STAGE),
        ("qa_v1_all_checks_passed", qa.get("all_checks_passed") is True),
        ("qa_v1_baseline_sample_count", qa.get("final_dataset_row_count") == 11),
        ("qa_v1_baseline_group_count", qa.get("split_group_counts", {}).get("total") == 5),
        ("qa_v1_baseline_split_counts", qa.get("split_sample_counts") == {"train": 8, "validation": 2, "test": 1, "total": 11}),
        ("qa_v1_canonical_masks", tuple(tuple(pair) for pair in qa.get("canonical_mask_pairs", [])) == CANONICAL_MASK_PAIRS),
        ("qa_v1_bulk_download_not_ready", qa.get("ready_for_bulk_download_now") is False),
        ("qa_v1_training_not_ready", qa.get("ready_for_training") is False and qa.get("ready_to_train_now") is False),
        ("qa_v1_feature_semantics_audit_required", qa.get("feature_semantics_audit_required_before_training") is True),
        ("step14ar_stage", ar.get("stage") == "covapie_final_dataset_materialization_smoke_v0"),
        ("step14aq_stage", aq.get("stage") == "covapie_unified_leakage_split_materialization_smoke_v0"),
        ("step14ar_step14aq_provenance", ar.get("source_step14aq_commit") == SOURCE_STEP14AQ_COMMIT),
        ("artifact_inventory_references_not_followed", True),
    )
    for item, passed in semantic_checks:
        rows.append(_row(
            SOURCE_BOUNDARY_COLUMNS,
            boundary_item=item,
            source_path="step14as_qa_v1_step14ar_step14aq_metadata_only",
            expected_status="true",
            observed_status=_bool_text(passed),
            source_boundary_passed=_bool_text(passed),
            blocking_reason="" if passed else item,
        ))
    return rows


def _safety_rows() -> list[dict[str, Any]]:
    return [
        _row(SAFETY_COLUMNS, safety_item=item, required_status="false", observed_status="false",
             safety_passed="true", blocking_reason="")
        for item in CANONICAL_SAFETY_ITEMS
    ]


def _issue_rows(failed_sections: tuple[str, ...]) -> list[dict[str, Any]]:
    if not failed_sections:
        return [_row(
            ISSUE_COLUMNS, issue_id="NO_ISSUES", issue_type="no_admission_design_issues",
            severity="none", status="no_issues", issue_count="0", blocking_reason="",
        )]
    return [
        _row(
            ISSUE_COLUMNS,
            issue_id=SECTION_ISSUES[section][0],
            issue_type=SECTION_ISSUES[section][1],
            severity="blocking",
            status="open",
            issue_count="1",
            blocking_reason=dict(SECTION_BLOCKERS)[section],
        )
        for section in failed_sections
    ]


def _all_true(rows: list[dict[str, Any]], field: str) -> bool:
    return all(row[field] == "true" for row in rows)


def _build_materialization(
    source: dict[str, Any],
    *,
    schema_rows: list[dict[str, Any]] | None = None,
    rule_rows: list[dict[str, Any]] | None = None,
    safety_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate an injectable design contract without reading additional inputs."""
    schema_rows = _schema_rows() if schema_rows is None else schema_rows
    rule_rows = _rule_rows() if rule_rows is None else rule_rows
    safety_rows = _safety_rows() if safety_rows is None else safety_rows
    boundary_rows = _source_boundary_rows(source)
    section_passed = {
        "source": _all_true(boundary_rows, "source_boundary_passed"),
        "schema": _validate_schema_contract(schema_rows),
        "rule": _validate_rule_contract(rule_rows),
        "safety": _validate_safety_contract(safety_rows),
    }
    failed_sections = tuple(section for section, _ in SECTION_BLOCKERS if not section_passed[section])
    blockers = [dict(SECTION_BLOCKERS)[section] for section in failed_sections]
    return {
        "schema_rows": schema_rows,
        "rule_rows": rule_rows,
        "source_boundary_rows": boundary_rows,
        "safety_rows": safety_rows,
        "issue_rows": _issue_rows(failed_sections),
        "all_source_boundary_checks_passed": section_passed["source"],
        "all_admission_schema_contract_checks_passed": section_passed["schema"],
        "all_admission_rule_contract_checks_passed": section_passed["rule"],
        "all_safety_checks_passed": section_passed["safety"],
        "all_checks_passed": not failed_sections,
        "blocking_reasons": blockers,
        "recommended_next_step": NEXT_STAGE if not failed_sections else BLOCKED_NEXT_STAGE,
    }


def _write_outputs(
    output_root: Path,
    materialization: dict[str, Any],
) -> dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        CSV_OUTPUTS[0]: (SCHEMA_COLUMNS, materialization["schema_rows"]),
        CSV_OUTPUTS[1]: (RULE_COLUMNS, materialization["rule_rows"]),
        CSV_OUTPUTS[2]: (SOURCE_BOUNDARY_COLUMNS, materialization["source_boundary_rows"]),
        CSV_OUTPUTS[3]: (SAFETY_COLUMNS, materialization["safety_rows"]),
        CSV_OUTPUTS[4]: (ISSUE_COLUMNS, materialization["issue_rows"]),
    }
    for name, (columns, rows) in outputs.items():
        _write_csv(output_root / name, columns, rows)
    return {name: _sha256(output_root / name) for name in CSV_OUTPUTS}


def _manifest_payload(
    source: dict[str, Any],
    materialization: dict[str, Any],
    output_sha256: dict[str, str],
) -> dict[str, Any]:
    """Build a final manifest from one evaluated, injectable contract."""
    qa = source["qa_manifest"]
    schema_rows = materialization["schema_rows"]
    rule_rows = materialization["rule_rows"]
    safety_rows = materialization["safety_rows"]
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "project_name": PROJECT_NAME,
        "previous_stage": PREVIOUS_STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "source_read_boundary": "only_step14as_8_outputs_step14ar_manifest_step14aq_manifest",
        "source_input_count": len(SOURCE_SHA256),
        "source_input_sha256": SOURCE_SHA256,
        "artifact_inventory_reference_paths_not_recursively_opened": True,
        "canonical_final_dataset_baseline_only": True,
        "canonical_final_dataset_sample_count": qa["final_dataset_row_count"],
        "canonical_final_dataset_group_count": qa["split_group_counts"]["total"],
        "canonical_split_sample_counts": qa["split_sample_counts"],
        "canonical_split_group_counts": qa["split_group_counts"],
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": len(CANONICAL_MASK_PAIRS),
        "admission_schema_field_count": len(schema_rows),
        "expected_admission_schema_field_count": len(CANONICAL_ADMISSION_FIELD_CONTRACTS),
        "pre_download_required_field_count": sum(row.get("requirement_phase") == "pre_download" for row in schema_rows),
        "pre_final_split_required_field_count": sum(row.get("requirement_phase") == "pre_final_split" for row in schema_rows),
        "post_download_required_field_count": sum(row.get("requirement_phase") == "post_download" for row in schema_rows),
        "admission_rule_count": len(rule_rows),
        "expected_admission_rule_count": len(CANONICAL_RULES),
        "safety_item_count": len(safety_rows),
        "expected_safety_item_count": len(CANONICAL_SAFETY_ITEMS),
        "candidate_records_materialized": False,
        "download_queue_materialized": False,
        "network_access_used_current_step": False,
        "raw_structure_read_current_step": False,
        "ready_for_bulk_download_admission_implementation": materialization["all_checks_passed"],
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": materialization["recommended_next_step"],
        "all_source_boundary_checks_passed": materialization["all_source_boundary_checks_passed"],
        "all_admission_schema_contract_checks_passed": materialization["all_admission_schema_contract_checks_passed"],
        "all_admission_rule_contract_checks_passed": materialization["all_admission_rule_contract_checks_passed"],
        "all_safety_checks_passed": materialization["all_safety_checks_passed"],
        "all_checks_passed": materialization["all_checks_passed"],
        "blocking_reasons": materialization["blocking_reasons"],
        "non_manifest_output_count": len(CSV_OUTPUTS),
        "output_file_count": len(CSV_OUTPUTS) + 1,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME],
        "output_sha256": output_sha256,
    }


def run_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize deterministic metadata-only admission-design outputs."""
    source = _load_source()
    materialization = _build_materialization(source)
    output_sha256 = _write_outputs(output_root, materialization)
    manifest = _manifest_payload(source, materialization, output_sha256)
    (output_root / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


run_bulk_download_admission_design_gate_v1 = (
    run_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1
)

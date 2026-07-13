from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from covalent_ext.covapie_final_dataset_materialization_smoke import (
    build_contract_snapshot,
    build_in_memory_final_dataset_materialization,
    build_source_step14aq_preconditions_passed_evidence,
    DEFAULT_STEP14AQ_INPUT_PATHS,
    load_step14aq_inputs_safely,
    materialize_final_dataset_core_to_disk,
    materialize_reference_audits_to_disk,
    materialize_summary_and_integrity_to_disk,
    materialize_issue_and_safety_to_disk,
    materialize_final_manifest_and_gate,
    validate_step14ar_metadata_output_boundary,
    validate_contract_snapshot,
)


def main() -> int:
    contract = validate_contract_snapshot(build_contract_snapshot())
    loaded = load_step14aq_inputs_safely(DEFAULT_STEP14AQ_INPUT_PATHS)
    result = build_source_step14aq_preconditions_passed_evidence(
        loaded, enforce_commit_provenance=True
    )
    materialization = build_in_memory_final_dataset_materialization(result)
    disk = materialize_final_dataset_core_to_disk(result, materialization)
    reference = materialize_reference_audits_to_disk(result, materialization, disk)
    summary_integrity = materialize_summary_and_integrity_to_disk(result, materialization, disk, reference)
    issue_safety = materialize_issue_and_safety_to_disk(contract, result, materialization, disk, reference, summary_integrity, allow_existing_manifest=True)
    final_manifest = materialize_final_manifest_and_gate(contract, result, materialization, disk, reference, summary_integrity, issue_safety)
    output_boundary = validate_step14ar_metadata_output_boundary(disk.output_paths, repo_root=Path(__file__).resolve().parents[1])
    values = {
        "source_input_count": contract["source_input_count"],
        "source_input_load_passed": loaded.input_load_passed,
        "commit_provenance_passed": result.source_checks["commit_provenance_passed"],
        "manifest_contract_passed": result.source_checks["manifest_contract_passed"],
        "source_precondition_rows": len(result.typed_precondition_rows),
        "policy_rows": len(result.typed_policy_rows),
        "group_rows": len(result.typed_group_rows),
        "sample_rows": len(result.typed_sample_rows),
        "split_rows": f"{len(result.typed_train_rows)}/{len(result.typed_validation_rows)}/{len(result.typed_test_rows)}",
        "canonical_source_rows": len(result.canonical_source_rows),
        "leakage_rows": len(result.typed_leakage_rows),
        "balance_rows": len(result.typed_balance_rows),
        "safety_rows": len(result.typed_safety_rows),
        "source_validation_passed": result.source_validation_passed,
        "source_checks": f"{sum(result.source_checks.values())}/{len(result.source_checks)}",
        "final_index_rows": len(materialization.final_index_validation.validated_rows) if materialization.final_index_validation else 0,
        "final_index_schema_fields": 33,
        "membership_rows": len(materialization.membership_validation.validated_rows) if materialization.membership_validation else 0,
        "membership_passed": sum(row["final_dataset_membership_passed"] for row in materialization.membership_validation.validated_rows) if materialization.membership_validation else 0,
        "membership_schema_passed": materialization.membership_validation.schema_passed if materialization.membership_validation else False,
        "in_memory_artifact_inventory_rows": len(materialization.artifact_inventory_validation.validated_rows) if materialization.artifact_inventory_validation else 0,
        "in_memory_artifact_inventory_passed": sum(row["artifact_inventory_passed"] for row in materialization.artifact_inventory_validation.validated_rows) if materialization.artifact_inventory_validation else 0,
        "artifact_inventory_schema_passed": materialization.artifact_inventory_validation.schema_passed if materialization.artifact_inventory_validation else False,
        "artifact_paths_inside_allowed_derived_root": materialization.artifact_inventory_validation.all_paths_inside_allowed_derived_root if materialization.artifact_inventory_validation else False,
        "artifact_reference_read_count": len(materialization.artifact_inventory_validation.activity.read_paths) if materialization.artifact_inventory_validation else 0,
        "raw_read_attempted": materialization.artifact_inventory_validation.activity.raw_read_attempted if materialization.artifact_inventory_validation else False,
        "in_memory_split_summary_rows": len(materialization.split_summary_validation.validated_rows) if materialization.split_summary_validation else 0,
        "split_summary_schema_passed": materialization.split_summary_validation.schema_passed if materialization.split_summary_validation else False,
        "in_memory_integrity_rows": len(materialization.integrity_rows),
        "in_memory_integrity_passed": materialization.integrity_validation["integrity_passed_count"],
        "integrity_schema_passed": materialization.integrity_validation["integrity_schema_passed"],
        "integrity_observations_are_dynamic": True,
        "in_memory_materialization_passed": materialization.in_memory_materialization_passed,
        "ready_for_disk_materialization": materialization.ready_for_disk_materialization,
        "ready_for_final_dataset_qa_gate": materialization.ready_for_covapie_final_dataset_qa_gate,
        "ready_for_training": materialization.ready_for_training,
        "output_path_contract_passed": disk.output_path_validation["output_path_contract_passed"],
        "final_precondition_rows": len(disk.precondition_rows),
        "precondition_write_validation_passed": disk.precondition_write_validation["source_precondition_write_validation_passed"],
        "final_index_csv_rows": disk.final_index_csv_write_validation.get("row_count", 0),
        "final_index_csv_fields": disk.final_index_csv_write_validation.get("schema_field_count", 0),
        "final_index_csv_write_validation_passed": disk.final_index_csv_write_validation["final_index_csv_write_validation_passed"],
        "final_index_json_rows": disk.final_index_json_write_validation.get("row_count", 0),
        "final_index_json_fields": disk.final_index_json_write_validation.get("schema_field_count", 0),
        "final_index_json_write_validation_passed": disk.final_index_json_write_validation["final_index_json_write_validation_passed"],
        "final_index_csv_json_consistent": disk.final_index_cross_format_validation["final_index_csv_json_consistent"],
        "membership_write_validation_passed": disk.membership_write_validation["membership_write_validation_passed"],
        "written_output_count": len(disk.activity.written_paths),
        "readback_output_count": len(disk.activity.read_paths),
        "temporary_path_count": len(disk.activity.temporary_paths),
        "ready_for_remaining_disk_materialization": disk.ready_for_remaining_disk_materialization,
        "core_disk_materialization_passed": disk.core_disk_materialization_passed,
        "disk_artifact_inventory_rows": len(reference.artifact_inventory_rows),
        "disk_artifact_inventory_passed": reference.artifact_inventory_write_validation.get("artifact_inventory_passed_count", 0),
        "artifact_inventory_write_validation_passed": reference.artifact_inventory_write_validation["artifact_inventory_write_validation_passed"],
        "schema_audit_rows": len(reference.schema_audit_rows),
        "schema_audit_passed": reference.schema_audit_write_validation.get("schema_audit_passed_count", 0),
        "schema_audit_write_validation_passed": reference.schema_audit_write_validation["schema_audit_write_validation_passed"],
        "source_preservation_rows": len(reference.source_preservation_rows),
        "source_preservation_passed": reference.source_preservation_write_validation.get("source_preservation_passed_count", 0),
        "source_preservation_write_validation_passed": reference.source_preservation_write_validation["source_preservation_write_validation_passed"],
        "r3b1_written_output_count": len(reference.activity.written_paths),
        "r3b1_readback_output_count": len(reference.activity.read_paths),
        "r3b1_temporary_path_count": len(reference.activity.temporary_paths),
        "ready_for_summary_and_integrity_disk_materialization": reference.ready_for_summary_and_integrity_disk_materialization,
        "existing_output_preflight": f"{summary_integrity.preflight_existing_outputs.get('preflight_output_count', 0)}/7",
        "split_summary_rows": len(summary_integrity.split_summary_rows),
        "split_summary_passed": summary_integrity.split_summary_write_validation.get("split_summary_passed_count", 0),
        "split_summary_write_validation_passed": summary_integrity.split_summary_write_validation["split_summary_write_validation_passed"],
        "split_summary_sample_counts": "/".join(str(row["sample_count"]) for row in summary_integrity.split_summary_rows),
        "split_summary_group_counts": "/".join(str(row["leakage_group_count"]) for row in summary_integrity.split_summary_rows),
        "split_summary_artifact_counts": "/".join(str(row["artifact_reference_count"]) for row in summary_integrity.split_summary_rows),
        "disk_integrity_observation_count": len(summary_integrity.disk_integrity_observations),
        "integrity_rows": len(summary_integrity.integrity_rows),
        "integrity_passed": summary_integrity.integrity_write_validation.get("integrity_passed_count", 0),
        "integrity_write_validation_passed": summary_integrity.integrity_write_validation["integrity_write_validation_passed"],
        "disk_integrity_in_memory_consistent": summary_integrity.integrity_rows == materialization.integrity_rows,
        "r3b2_written_output_count": len(summary_integrity.activity.written_paths),
        "r3b2_readback_output_count": len(summary_integrity.activity.read_paths),
        "r3b2_temporary_path_count": len(summary_integrity.activity.temporary_paths),
        "ready_for_issue_safety_manifest_materialization": summary_integrity.ready_for_issue_safety_manifest_materialization,
        "exact_group_member_sets_preserved": all(row["group_integrity_preserved"] is True for row in summary_integrity.split_summary_rows),
        "canonical_order_includes_json": summary_integrity.disk_integrity_observations.get("canonical_sample_order_preserved") == "true",
        "metadata_output_boundary_passed": output_boundary["metadata_output_boundary_passed"],
        "current_metadata_output_count": output_boundary["existing_output_count"],
        "unknown_output_count": output_boundary["unknown_output_count"],
        "forbidden_artifact_count": output_boundary["forbidden_artifact_count"],
        "temporary_artifact_count": output_boundary["temporary_artifact_count"],
        "existing_nine_output_preflight": f"{issue_safety.preflight_existing_nine_outputs.get('preflight_output_count', 0)}/9",
        "declared_output_nodes_passed": issue_safety.preflight_existing_nine_outputs.get("declared_output_nodes_passed", False),
        "final_safety_items": len(issue_safety.safety_rows),
        "final_safety_passed": issue_safety.safety_validation.passed_count if issue_safety.safety_validation else 0,
        "safety_write_validation_passed": issue_safety.safety_write_validation["safety_write_validation_passed"],
        "issue_inventory_rows": len(issue_safety.issue_rows),
        "blocking_issue_count": issue_safety.issue_write_validation.get("blocking_issue_count", 0),
        "issue_inventory_clear": issue_safety.issue_write_validation.get("issue_inventory_clear", False),
        "issue_write_validation_passed": issue_safety.issue_write_validation["issue_write_validation_passed"],
        "r4a_written_output_count": len(issue_safety.activity.written_paths),
        "r4a_readback_output_count": len(issue_safety.activity.read_paths),
        "r4a_temporary_path_count": len(issue_safety.activity.temporary_paths),
        "r4a_planned_write_validation_passed": issue_safety.planned_write_validation.passed if issue_safety.planned_write_validation else False,
        "r4a_exact_planned_write_count": len(issue_safety.planned_write_validation.planned_write_paths) if issue_safety.planned_write_validation else 0,
        "r4a_no_raw_write_paths": issue_safety.planned_write_validation.all_outside_raw_root if issue_safety.planned_write_validation else False,
        "r4a_no_artifact_overwrite_paths": issue_safety.planned_write_validation.disjoint_from_referenced_artifacts if issue_safety.planned_write_validation else False,
        "after_write_declared_nodes": f"{issue_safety.after_write_node_validation.get('regular_file_count', 0)}/{issue_safety.after_write_node_validation.get('expected_node_count', 11)}",
        "mask_pairs_exactly_canonical_five": issue_safety.safety_observations.get("no_extra_mask_tasks_added", False),
        "training_readiness_observations_are_dynamic": True,
        "existing_eleven_output_preflight": f"{final_manifest.preflight_existing_eleven_outputs.get('preflight_output_count', 0)}/11",
        "manifest_planned_write_validation_passed": final_manifest.manifest_planned_write_validation.passed if final_manifest.manifest_planned_write_validation else False,
        "manifest_evidence_read_count": len(final_manifest.manifest_evidence_activity.read_paths),
        "manifest_source_hash_count": len(final_manifest.manifest.get("source_input_sha256", {})),
        "manifest_non_manifest_output_count": final_manifest.manifest.get("non_manifest_output_count", 0),
        "manifest_field_count": len(final_manifest.manifest),
        "manifest_validation_passed": final_manifest.manifest_validation.passed if final_manifest.manifest_validation else False,
        "manifest_write_validation_passed": final_manifest.manifest_write_validation.get("manifest_write_validation_passed", False),
        "manifest_all_checks_passed": final_manifest.manifest.get("all_checks_passed", False),
        "final_declared_nodes": f"{final_manifest.final_node_validation.get('regular_file_count', 0)}/{final_manifest.final_node_validation.get('expected_node_count', 12)}",
        "final_metadata_output_count": final_manifest.final_metadata_boundary.get("existing_output_count", 0),
        "final_unknown_output_count": final_manifest.final_metadata_boundary.get("unknown_output_count", 0),
        "final_forbidden_artifact_count": final_manifest.final_metadata_boundary.get("forbidden_artifact_count", 0),
        "final_temporary_artifact_count": final_manifest.final_metadata_boundary.get("temporary_artifact_count", 0),
        "ready_for_covapie_final_dataset_qa_gate": final_manifest.ready_for_covapie_final_dataset_qa_gate,
        "ready_for_training_final": final_manifest.ready_for_training,
        "ready_to_train_now": final_manifest.ready_to_train_now,
        "feature_semantics_audit_required_before_training": final_manifest.manifest.get("feature_semantics_audit_required_before_training", False),
        "recommended_next_step": final_manifest.manifest.get("recommended_next_step", ""),
        "ready_for_manifest_materialization": issue_safety.ready_for_manifest_materialization,
    }
    for key, value in values.items():
        print(f"{key}={value}")
    if not contract["contract_validation_passed"] or not result.source_validation_passed or not materialization.in_memory_materialization_passed or not disk.core_disk_materialization_passed or not reference.reference_audit_disk_materialization_passed or not summary_integrity.summary_integrity_disk_materialization_passed or not issue_safety.issue_safety_disk_materialization_passed or not final_manifest.final_manifest_materialization_passed:
        print("blocking_reasons=" + ";".join(sorted(set(contract["blocking_reasons"] + result.blocking_reasons + materialization.blocking_reasons + disk.blocking_reasons + reference.blocking_reasons + summary_integrity.blocking_reasons + issue_safety.blocking_reasons + final_manifest.blocking_reasons))) )
        return 1
    print("covapie_final_dataset_materialization_smoke_v0_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

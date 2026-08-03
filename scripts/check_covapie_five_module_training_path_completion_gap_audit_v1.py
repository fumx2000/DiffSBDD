#!/usr/bin/env python3
"""Deterministic static checker for the CovaPIE five-module gap audit V1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from covalent_ext import covapie_five_module_training_path_completion_gap_audit_v1 as audit


ROOT = Path(__file__).resolve().parents[1]


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def main() -> int:
    first = audit.evaluate_covapie_five_module_training_path_completion_gap_audit_v1(repo_root=ROOT)
    second = audit.evaluate_covapie_five_module_training_path_completion_gap_audit_v1(repo_root=ROOT)
    audit._validate_response(first)
    audit._validate_response(second)
    first_bytes = _canonical_bytes(first)
    second_bytes = _canonical_bytes(second)
    if first_bytes != second_bytes:
        raise ValueError(audit._ERROR)

    safe = (
        first["canonical_module_count"] == 5
        and first["canonical_supervision_signal_count"] == 8
        and first["training_ready_module_count"] == 0
        and first["warhead_type_authority_coverage"] == "11/11"
        and first["warhead_type_training_approved"] is False
        and first["warhead_type_consumer_resolved"] is False
        and first["feature_semantics_contract_audit_completed"] is True
        and first["unknown_atom_policy_contract_resolved"] is True
        and first["feature_semantics_runtime_enforcement_integrated"] is False
        and first["final_training_feature_semantics_revalidation_required"] is True
        and first["canonical_mask_tensors_materialized"] is False
        and first["ready_for_training"] is False
        and first["real_training_started"] is False
        and first["parameter_update_performed"] is False
        and first["RL_implementation_started"] is False
    )
    if not safe:
        raise ValueError(audit._ERROR)

    print(f"source_snapshot_commit={first['source_snapshot_commit']}")
    print(f"source_snapshot_subject={first['source_snapshot_subject']}")
    print(f"source_snapshot_tree={first['source_snapshot_tree']}")
    print(f"audit_lifecycle_profile={first['audit_lifecycle_profile']}")
    print(f"audit_commit={first['audit_commit'] or 'none'}")
    print(f"audit_committed={str(first['audit_committed']).lower()}")
    print(f"audit_published={str(first['audit_published']).lower()}")
    print(f"ready_for_audit_commit_review={str(first['ready_for_audit_commit_review']).lower()}")
    print(f"response_exact_field_count={len(first)}")
    print(f"module_count={first['canonical_module_count']}")
    print(f"supervision_signal_count={first['canonical_supervision_signal_count']}")
    print(f"mask_count={first['canonical_mask_count']}")
    for module in first["canonical_module_names"]:
        print(
            "module=" + module
            + ";complete=" + str(first["complete_dimension_count_by_module"][module])
            + ";partial=" + str(first["partial_dimension_count_by_module"][module])
            + ";missing=" + str(first["missing_dimension_count_by_module"][module])
            + ";blocked=" + str(first["blocked_dimension_count_by_module"][module])
            + ";not_applicable=" + str(first["not_applicable_dimension_count_by_module"][module])
            + ";training_ready=" + str(first["module_completion_summary"][module]["training_ready"]).lower()
        )
    print(f"training_ready_module_count={first['training_ready_module_count']}")
    print(f"warhead_type_authority_coverage={first['warhead_type_authority_coverage']}")
    print(f"warhead_type_training_approved={str(first['warhead_type_training_approved']).lower()}")
    print(f"warhead_type_consumer_resolved={str(first['warhead_type_consumer_resolved']).lower()}")
    print(f"feature_semantics_contract_audit_completed={str(first['feature_semantics_contract_audit_completed']).lower()}")
    print(f"unknown_atom_policy_contract_resolved={str(first['unknown_atom_policy_contract_resolved']).lower()}")
    print(f"feature_semantics_known_at_resolution_snapshot={str(first['feature_semantics_known_at_resolution_snapshot']).lower()}")
    print(f"feature_semantics_runtime_enforcement_integrated={str(first['feature_semantics_runtime_enforcement_integrated']).lower()}")
    print(f"final_training_feature_semantics_revalidation_required={str(first['final_training_feature_semantics_revalidation_required']).lower()}")
    print(f"canonical_mask_tensors_materialized={str(first['canonical_mask_tensors_materialized']).lower()}")
    print(f"mainline_blocker_count={len(first['mainline_blockers'])}")
    print(f"prioritized_gap_count={len(first['prioritized_gap_queue'])}")
    print("recommended_next_increment=" + first["recommended_next_increment"]["smallest_verifiable_increment"])
    print(f"recommended_next_increment_module={first['recommended_next_increment']['module']}")
    print(f"exact67_runtime_evidence_available={str(first['exact67_runtime_evidence_available']).lower()}")
    print(f"ready_for_training={str(first['ready_for_training']).lower()}")
    print(f"real_training_started={str(first['real_training_started']).lower()}")
    print(f"parameter_update_performed={str(first['parameter_update_performed']).lower()}")
    print(f"RL_implementation_started={str(first['RL_implementation_started']).lower()}")
    print(f"safety_boundary_verified={str(safe).lower()}")
    print(f"response_sha256={first['response_sha256']}")
    print(f"response_canonical_bytes={len(first_bytes)}")
    print(f"response_canonical_sha256={hashlib.sha256(first_bytes).hexdigest()}")
    print(f"response_double_evaluation_byte_identical={str(first_bytes == second_bytes).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

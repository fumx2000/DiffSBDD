#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_actual_dataloader_design_gate as legacy  # noqa: E402
from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement  # noqa: E402


def _bool(value: bool) -> str:
    return str(value).lower()


def run() -> int:
    policy = legacy.build_retirement_policy()
    policies = retirement.build_all_legacy_stage_retirement_policies()
    validation = retirement.validate_legacy_pipeline_retirement_registry(
        policies
    )
    path_validation = retirement.validate_tracked_successor_manifest_paths(
        policies,
        repo_root=REPO_ROOT,
    )

    summaries = {
        "legacy_stage": policy.stage,
        "legacy_stage_retired": policy.legacy_stage_retired,
        "legacy_stage_executable": policy.legacy_stage_executable,
        "successor_stage_is_none": policy.superseded_by_stage is None,
        "successor_availability": policy.successor_availability,
        "successor_manifest_path_is_none": (
            policy.superseded_by_manifest_path is None
        ),
        "dataloader_interface_redesign_pending": (
            "dataloader_interface_redesign_pending"
            in policy.blocking_reasons
        ),
        "historical_artifacts_read_only": (
            policy.historical_artifacts_read_only
        ),
        "legacy_artifact_regeneration_forbidden": (
            policy.legacy_artifact_regeneration_forbidden
        ),
        "ready_for_training": policy.ready_for_training,
        "ready_to_train_now": policy.ready_to_train_now,
        "feature_semantics_audit_required_before_training": (
            policy.feature_semantics_audit_required_before_training
        ),
        "recommended_next_step": policy.recommended_next_step,
    }
    for key, value in summaries.items():
        print(f"{key}={_bool(value) if isinstance(value, bool) else value}")

    passed = (
        policy
        == retirement.build_legacy_stage_retirement_policy(
            "covapie_actual_dataloader_design_gate_v0"
        )
        and validation.passed is True
        and validation.registry_count_passed is True
        and path_validation["tracked_successor_paths_passed"] is True
        and path_validation["tracked_successor_reference_count"] == 4
        and path_validation["validated_reference_count"] == 4
        and path_validation["unique_manifest_path_count"] == 3
        and path_validation["unique_regular_file_count"] == 3
        and path_validation["shared_manifest_reference_count"] == 1
        and path_validation[
            "shared_manifest_reference_contract_passed"
        ]
        is True
        and policy.legacy_stage_retired is True
        and policy.legacy_stage_executable is False
        and policy.superseded_by_stage is None
        and policy.superseded_by_manifest_path is None
        and policy.successor_availability == "redesign_pending"
        and policy.blocking_reasons
        == (
            "legacy_stage_superseded",
            "dataloader_interface_redesign_pending",
        )
        and policy.historical_artifacts_read_only is True
        and policy.legacy_artifact_regeneration_forbidden is True
        and policy.ready_for_training is False
        and policy.ready_to_train_now is False
        and policy.feature_semantics_audit_required_before_training is True
        and policy.recommended_next_step
        == "covapie_final_dataset_qa_gate_v1"
    )
    print(
        "covapie_actual_dataloader_design_gate_v0_retirement_policy_passed"
        if passed
        else "covapie_actual_dataloader_design_gate_v0_retirement_policy_blocked"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run())

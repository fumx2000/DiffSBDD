#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_final_dataset_qa_gate as legacy  # noqa: E402
from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement  # noqa: E402


EXPECTED_SUCCESSOR_STAGE = "covapie_final_dataset_qa_gate_v1"
EXPECTED_NEXT_STEP = "covapie_final_dataset_qa_gate_v1"


def _bool(value: bool) -> str:
    return str(value).lower()


def run() -> int:
    stage_policy = legacy.build_retirement_policy()
    policies = retirement.build_all_legacy_stage_retirement_policies()
    registry = retirement.validate_legacy_pipeline_retirement_registry(policies)
    tracked_paths = retirement.validate_tracked_successor_manifest_paths(
        policies,
        repo_root=REPO_ROOT,
    )
    canonical_successor_not_materialized = (
        stage_policy.successor_availability == "not_materialized"
        and stage_policy.superseded_by_manifest_path is None
        and "canonical_successor_not_materialized" in stage_policy.blocking_reasons
    )
    values = {
        "legacy_stage": stage_policy.stage,
        "legacy_stage_retired": stage_policy.legacy_stage_retired,
        "legacy_stage_executable": stage_policy.legacy_stage_executable,
        "successor_stage": stage_policy.superseded_by_stage,
        "successor_availability": stage_policy.successor_availability,
        "successor_manifest_path_is_none": (
            stage_policy.superseded_by_manifest_path is None
        ),
        "canonical_successor_not_materialized": (
            canonical_successor_not_materialized
        ),
        "historical_artifacts_read_only": stage_policy.historical_artifacts_read_only,
        "legacy_artifact_regeneration_forbidden": (
            stage_policy.legacy_artifact_regeneration_forbidden
        ),
        "ready_for_training": stage_policy.ready_for_training,
        "ready_to_train_now": stage_policy.ready_to_train_now,
        "feature_semantics_audit_required_before_training": (
            stage_policy.feature_semantics_audit_required_before_training
        ),
        "recommended_next_step": stage_policy.recommended_next_step,
    }
    for key, value in values.items():
        print(f"{key}={_bool(value) if isinstance(value, bool) else value}")
    passed = (
        registry.passed is True
        and tracked_paths["tracked_successor_paths_passed"] is True
        and stage_policy.stage == legacy.LEGACY_STAGE
        and stage_policy.legacy_stage_retired is True
        and stage_policy.legacy_stage_executable is False
        and stage_policy.superseded_by_stage == EXPECTED_SUCCESSOR_STAGE
        and stage_policy.successor_availability == "not_materialized"
        and stage_policy.superseded_by_manifest_path is None
        and canonical_successor_not_materialized is True
        and stage_policy.historical_artifacts_read_only is True
        and stage_policy.legacy_artifact_regeneration_forbidden is True
        and stage_policy.ready_for_training is False
        and stage_policy.ready_to_train_now is False
        and stage_policy.feature_semantics_audit_required_before_training is True
        and stage_policy.recommended_next_step == EXPECTED_NEXT_STEP
        and stage_policy.blocking_reasons
        == ("legacy_stage_superseded", "canonical_successor_not_materialized")
    )
    print(
        "covapie_final_dataset_qa_gate_v0_retirement_policy_passed"
        if passed
        else "covapie_final_dataset_qa_gate_v0_retirement_policy_blocked"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run())

#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement  # noqa: E402
from covalent_ext import covapie_split_leakage_qa_gate as legacy  # noqa: E402


EXPECTED_SUCCESSOR_STAGE = (
    "covapie_unified_leakage_split_materialization_smoke_v0"
)
EXPECTED_SUCCESSOR_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_unified_leakage_split_materialization_smoke_manifest.json"
)
EXPECTED_NEXT_STEP = "covapie_unified_leakage_split_materialization_smoke"
SHARED_STAGES = (
    "covapie_split_leakage_smoke_v0",
    "covapie_split_leakage_qa_gate_v0",
)


def _bool(value: bool) -> str:
    return str(value).lower()


def run() -> int:
    stage_policy = legacy.build_retirement_policy()
    policies = retirement.build_all_legacy_stage_retirement_policies()
    validation = retirement.validate_legacy_pipeline_retirement_registry(policies)
    paths = retirement.validate_tracked_successor_manifest_paths(
        policies,
        repo_root=REPO_ROOT,
    )
    policy_by_stage = {item.stage: item for item in policies}
    shared_contract_passed = (
        retirement.EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES
        == {EXPECTED_SUCCESSOR_MANIFEST: SHARED_STAGES}
        and policy_by_stage[SHARED_STAGES[0]].superseded_by_manifest_path
        == policy_by_stage[SHARED_STAGES[1]].superseded_by_manifest_path
        == EXPECTED_SUCCESSOR_MANIFEST
        and paths["shared_manifest_reference_contract_passed"] is True
    )
    successor_path_passed = (
        paths["tracked_successor_paths_passed"] is True
        and stage_policy.superseded_by_manifest_path == EXPECTED_SUCCESSOR_MANIFEST
    )
    values = {
        "legacy_stage": stage_policy.stage,
        "legacy_stage_retired": stage_policy.legacy_stage_retired,
        "legacy_stage_executable": stage_policy.legacy_stage_executable,
        "successor_stage": stage_policy.superseded_by_stage,
        "successor_availability": stage_policy.successor_availability,
        "successor_manifest_path": stage_policy.superseded_by_manifest_path,
        "successor_manifest_path_validation_passed": successor_path_passed,
        "shared_step14aq_successor_manifest_contract_passed": shared_contract_passed,
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
        validation.passed is True
        and validation.registry_count_passed is True
        and successor_path_passed is True
        and shared_contract_passed is True
        and stage_policy.stage == legacy.LEGACY_STAGE
        and stage_policy.legacy_stage_retired is True
        and stage_policy.legacy_stage_executable is False
        and stage_policy.superseded_by_stage == EXPECTED_SUCCESSOR_STAGE
        and stage_policy.successor_availability == "tracked"
        and stage_policy.superseded_by_manifest_path == EXPECTED_SUCCESSOR_MANIFEST
        and stage_policy.historical_artifacts_read_only is True
        and stage_policy.legacy_artifact_regeneration_forbidden is True
        and stage_policy.ready_for_training is False
        and stage_policy.ready_to_train_now is False
        and stage_policy.feature_semantics_audit_required_before_training is True
        and stage_policy.recommended_next_step == EXPECTED_NEXT_STEP
        and stage_policy.blocking_reasons == ("legacy_stage_superseded",)
    )
    print(
        "covapie_split_leakage_qa_gate_v0_retirement_policy_passed"
        if passed
        else "covapie_split_leakage_qa_gate_v0_retirement_policy_blocked"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run())

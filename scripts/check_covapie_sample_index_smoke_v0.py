#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement  # noqa: E402
from covalent_ext import covapie_sample_index_smoke as legacy  # noqa: E402


EXPECTED_SUCCESSOR_STAGE = "covapie_sample_index_materialization_smoke_v0"
EXPECTED_SUCCESSOR_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_sample_index_materialization_smoke_v0/"
    "covapie_sample_index_materialization_smoke_manifest.json"
)
EXPECTED_NEXT_STEP = "covapie_sample_index_materialization_smoke"


def _bool(value: bool) -> str:
    return str(value).lower()


def run() -> int:
    sample_policy = legacy.build_retirement_policy()
    policies = retirement.build_all_legacy_stage_retirement_policies()
    validation = retirement.validate_legacy_pipeline_retirement_registry(policies)
    path_validation = retirement.validate_tracked_successor_manifest_paths(
        policies,
        repo_root=REPO_ROOT,
    )
    successor_manifest_path_validation_passed = (
        path_validation["tracked_successor_paths_passed"] is True
        and sample_policy.superseded_by_manifest_path
        == EXPECTED_SUCCESSOR_MANIFEST
    )

    values = {
        "legacy_stage": sample_policy.stage,
        "legacy_stage_retired": sample_policy.legacy_stage_retired,
        "legacy_stage_executable": sample_policy.legacy_stage_executable,
        "successor_stage": sample_policy.superseded_by_stage,
        "successor_availability": sample_policy.successor_availability,
        "successor_manifest_path": sample_policy.superseded_by_manifest_path,
        "successor_manifest_path_validation_passed": (
            successor_manifest_path_validation_passed
        ),
        "historical_artifacts_read_only": (
            sample_policy.historical_artifacts_read_only
        ),
        "legacy_artifact_regeneration_forbidden": (
            sample_policy.legacy_artifact_regeneration_forbidden
        ),
        "ready_for_training": sample_policy.ready_for_training,
        "ready_to_train_now": sample_policy.ready_to_train_now,
        "feature_semantics_audit_required_before_training": (
            sample_policy.feature_semantics_audit_required_before_training
        ),
        "recommended_next_step": sample_policy.recommended_next_step,
    }
    for key, value in values.items():
        print(f"{key}={_bool(value) if isinstance(value, bool) else value}")

    passed = (
        validation.passed is True
        and validation.registry_count_passed is True
        and successor_manifest_path_validation_passed is True
        and sample_policy.stage == legacy.LEGACY_STAGE
        and sample_policy.legacy_stage_retired is True
        and sample_policy.legacy_stage_executable is False
        and sample_policy.superseded_by_stage == EXPECTED_SUCCESSOR_STAGE
        and sample_policy.successor_availability == "tracked"
        and sample_policy.superseded_by_manifest_path
        == EXPECTED_SUCCESSOR_MANIFEST
        and sample_policy.historical_artifacts_read_only is True
        and sample_policy.legacy_artifact_regeneration_forbidden is True
        and sample_policy.ready_for_training is False
        and sample_policy.ready_to_train_now is False
        and sample_policy.feature_semantics_audit_required_before_training is True
        and sample_policy.recommended_next_step == EXPECTED_NEXT_STEP
        and sample_policy.blocking_reasons == ("legacy_stage_superseded",)
    )
    print(
        "covapie_sample_index_smoke_v0_retirement_policy_passed"
        if passed
        else "covapie_sample_index_smoke_v0_retirement_policy_blocked"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run())

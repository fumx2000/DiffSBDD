#!/usr/bin/env python
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_legacy_pipeline_retirement_policy as policy  # noqa: E402


def _bool(value: bool) -> str:
    return str(value).lower()


def run() -> int:
    policies = policy.build_all_legacy_stage_retirement_policies()
    validation = policy.validate_legacy_pipeline_retirement_registry(policies)
    path_validation = policy.validate_tracked_successor_manifest_paths(
        policies,
        repo_root=REPO_ROOT,
    )
    availability = Counter(item.successor_availability for item in policies)
    availability_counts = {
        name: availability[name]
        for name, _ in policy.EXPECTED_SUCCESSOR_AVAILABILITY_COUNTS
    }

    summaries = {
        "legacy_retirement_stage_count": len(policies),
        "retirement_registry_validation_passed": validation.passed,
        "tracked_successor_paths_passed": path_validation[
            "tracked_successor_paths_passed"
        ],
        "tracked_successor_reference_count": path_validation[
            "tracked_successor_reference_count"
        ],
        "validated_successor_reference_count": path_validation[
            "validated_reference_count"
        ],
        "unique_successor_manifest_count": path_validation[
            "unique_manifest_path_count"
        ],
        "unique_regular_successor_manifest_count": path_validation[
            "unique_regular_file_count"
        ],
        "shared_manifest_reference_count": path_validation[
            "shared_manifest_reference_count"
        ],
        "shared_manifest_reference_contract_passed": path_validation[
            "shared_manifest_reference_contract_passed"
        ],
        "tracked_count": availability["tracked"],
        "pending_commit_count": availability["pending_commit"],
        "not_materialized_count": availability["not_materialized"],
        "redesign_pending_count": availability["redesign_pending"],
        "all_legacy_stages_retired": all(
            item.legacy_stage_retired for item in policies
        ),
        "all_legacy_stages_executable": all(
            item.legacy_stage_executable for item in policies
        ),
        "all_training_readiness_false": all(
            not item.ready_for_training and not item.ready_to_train_now
            for item in policies
        ),
        "historical_artifacts_read_only": all(
            item.historical_artifacts_read_only for item in policies
        ),
        "legacy_artifact_regeneration_forbidden": all(
            item.legacy_artifact_regeneration_forbidden for item in policies
        ),
        "canonical_final_dataset_qa_stage": (
            policy.CANONICAL_FINAL_DATASET_QA_STAGE
        ),
    }
    for key, value in summaries.items():
        print(f"{key}={_bool(value) if isinstance(value, bool) else value}")

    passed = (
        validation.passed
        and validation.registry_count_passed is True
        and path_validation["tracked_successor_paths_passed"] is True
        and len(policies) == policy.EXPECTED_LEGACY_STAGE_COUNT
        and availability_counts
        == dict(policy.EXPECTED_SUCCESSOR_AVAILABILITY_COUNTS)
        and summaries["all_legacy_stages_retired"] is True
        and summaries["all_legacy_stages_executable"] is False
        and summaries["all_training_readiness_false"] is True
        and summaries["historical_artifacts_read_only"] is True
        and summaries["legacy_artifact_regeneration_forbidden"] is True
    )
    print(
        "covapie_legacy_pipeline_retirement_policy_v0_passed"
        if passed
        else "covapie_legacy_pipeline_retirement_policy_v0_blocked"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run())

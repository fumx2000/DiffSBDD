#!/usr/bin/env python3
"""Check the cumulative1000 high-yield human-review calibration successor."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_high_yield_human_review_authority_calibration_v1 as calibration,
)


SUPPORTED_ACTUAL_PROFILES = frozenset(
    {
        "candidate_precommit_untracked",
        "published_successor",
    }
)


def _validate_actual_repository_profile(profile: object) -> str:
    if type(profile) is not str or profile not in SUPPORTED_ACTUAL_PROFILES:
        raise calibration.CalibrationSafetyError("CHECKER_ACTUAL_PROFILE_INVALID")
    return profile


def _published_successor_simulation() -> dict[str, object]:
    synthetic_head = "f" * 40
    return {
        "branch": "main",
        "HEAD": synthetic_head,
        "HEAD_parent": calibration.BASELINE_HEAD,
        "HEAD_tree": "0" * 40,
        "HEAD_subject": calibration.PUBLICATION_SUBJECT,
        "origin_main": synthetic_head,
        "ahead": 0,
        "behind": 0,
        "status_lines": [],
        "tracked_modifications": [],
        "staged": [],
        "untracked": [],
        "published_diff_statuses": ["A"] * 9,
        "published_diff_modes": ["100644"] * 9,
        "published_diff_paths": sorted(calibration.AUTHORIZED_PATHS),
    }


def run_check(repo_root: Path) -> dict[str, object]:
    started = time.monotonic()
    result = calibration.check_materialized_v1(repo_root)
    actual_profile = _validate_actual_repository_profile(result.get("profile"))
    published = calibration.classify_repository_profile_v1(
        _published_successor_simulation()
    )
    if published != "published_successor":
        raise calibration.CalibrationSafetyError("CHECKER_PUBLISHED_PROFILE_INVALID")
    summary = result["summary"]
    safety = summary["authority_and_execution_safety"]
    reconciliation = summary["reconciliation"]
    shadow = summary["strict_shadow"]
    selection = summary["selection"]
    units = selection["units"]
    lane = {unit["selection_lane"]: unit for unit in units}
    return {
        "elapsed_seconds": time.monotonic() - started,
        "sha256": result["sha256"],
        "summary": summary,
        "reconciliation": reconciliation,
        "shadow": shadow,
        "selection": selection,
        "safety": safety,
        "lane_A": units[0],
        "lane_B": units[1],
        "lane_C": units[2],
        "actual_repository_profile": actual_profile,
        "actual_repository_profile_supported": True,
        "published_profile": published,
    }


def _print_markers(result: dict[str, object]) -> None:
    reconciliation = result["reconciliation"]
    shadow = result["shadow"]
    selection = result["selection"]
    safety = result["safety"]
    lane_a = result["lane_A"]
    lane_b = result["lane_B"]
    lane_c = result["lane_C"]
    print("high_yield_human_review_authority_calibration_built=true")
    for key in (
        "raw_snapshot_review_event_count",
        "raw_snapshot_review_unit_count",
        "current_runtime_positive_excluded_event_count",
        "completed_human_positive_excluded_event_count",
        "completed_human_negative_excluded_event_count",
        "in_progress_excluded_event_count",
        "partial_authority_incomplete_event_count",
        "currently_unreviewed_event_count",
        "currently_unreviewed_unit_count",
    ):
        print(f"{key}={reconciliation[key]}")
    print(
        "calibration_eligible_event_count="
        f"{result['summary']['calibration_eligible_event_count']}"
    )
    print(
        "calibration_eligible_unit_count="
        f"{result['summary']['calibration_eligible_unit_count']}"
    )
    for key in (
        "current_positive_reference_event_count",
        "strict_positive_shadow_event_count",
        "strict_positive_shadow_unit_count",
        "unique_graph_isomorphic_role_transfer_candidate_event_count",
        "ambiguous_graph_automorphism_shadow_event_count",
    ):
        print(f"{key}={shadow[key]}")
    for key in (
        "selected_calibration_unit_count",
        "selected_calibration_total_raw_event_yield",
        "selected_calibration_total_effective_single_decision_event_yield",
    ):
        print(f"{key}={selection[key]}")
    for label, unit in (("A", lane_a), ("B", lane_b), ("C", lane_c)):
        print(f"lane_{label}_selected_unit_id={unit['review_unit_id']}")
        print(f"lane_{label}_effective_event_yield={unit['effective_event_yield']}")
    for key in (
        "human_review_decision_created",
        "new_positive_authority_created",
        "new_negative_authority_created",
        "new_reaction_family_authority_created",
        "new_warhead_rule_authority_created",
        "existing_14_8_14_split_changed",
        "training_performed",
        "Trainer_used",
        "backward_performed",
        "optimizer_created",
        "network_performed",
        "bulk_ranks1001_1500_processed",
        "cumulative1000_rebuild_invoked",
        "cumulative1000_replay_invoked",
        "data_augmentation_performed",
        "feature_semantics_audit_reopened",
    ):
        print(f"{key}={str(safety[key]).lower()}")
    print(f"standalone_checker_runtime_seconds={result['elapsed_seconds']:.6f}")
    actual_profile = result["actual_repository_profile"]
    print(f"actual_repository_profile={actual_profile}")
    print("actual_repository_profile_supported=true")
    print(
        "candidate_precommit_profile_active="
        f"{str(actual_profile == 'candidate_precommit_untracked').lower()}"
    )
    print(
        "published_successor_profile_active="
        f"{str(actual_profile == 'published_successor').lower()}"
    )
    print("published_successor_profile_simulation_passed=true")
    print("ready_for_human_review=true")
    print("ready_for_gpt_review=true")
    print("ready_for_publication=true")
    print(
        "recommended_next_step_exactly="
        "gpt_audit_high_yield_calibration_packet_then_human_review_selected_units"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPOSITORY_ROOT)
    arguments = parser.parse_args()
    result = run_check(arguments.repo_root.resolve())
    _print_markers(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

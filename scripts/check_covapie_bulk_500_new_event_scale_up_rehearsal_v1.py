#!/usr/bin/env python3
"""Fail-closed checker for the 500-new-event scale-up rehearsal plan."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, Mapping
import urllib.request

from covalent_ext import covapie_bulk_500_new_event_scale_up_rehearsal_v1 as rehearsal


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _contains_absolute_path(value: object) -> bool:
    if isinstance(value, str):
        return os.path.isabs(value)
    if isinstance(value, list):
        return any(_contains_absolute_path(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_absolute_path(key) or _contains_absolute_path(item)
            for key, item in value.items()
        )
    return False


def _contains_key(value: object, forbidden: str) -> bool:
    if isinstance(value, Mapping):
        return forbidden in value or any(
            _contains_key(item, forbidden) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_key(item, forbidden) for item in value)
    return False


def _network_blocked_replay(repo_root: Path) -> dict[str, bytes]:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("NETWORK_OR_ACQUISITION_PATH_CALLED_BY_REHEARSAL")

    patches = [
        (urllib.request, "urlopen"),
        (rehearsal.frozen_bulk, "urlopen"),
        (rehearsal.frozen_bulk.BulkCacheV1, "fetch"),
        (rehearsal.frozen_bulk, "discover_covpdb_v1"),
        (rehearsal.frozen_bulk, "discover_covbinder_v1"),
        (rehearsal.frozen_bulk, "discover_rcsb_direct_v1"),
        (rehearsal.frozen_bulk, "discover_rcsb_specialist_seeded_v1"),
        (rehearsal.frozen_bulk, "_acquire_structures_v1"),
        (rehearsal.frozen_bulk, "acquire_ccd_components_v1"),
    ]
    originals = [(owner, name, getattr(owner, name)) for owner, name in patches]
    try:
        for owner, name, _original in originals:
            setattr(owner, name, forbidden)
        return rehearsal.build_artifacts_v1(repo_root=repo_root)
    finally:
        for owner, name, original in originals:
            setattr(owner, name, original)


def check_v1(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    baseline = rehearsal.verify_task_repository_baseline_v1(repo_root)
    worktree_profile = rehearsal.classify_rehearsal_worktree_profile_v1(
        modified_tracked=baseline["modified_tracked"],
        staged=baseline["staged"],
        untracked=baseline["untracked"],
    )
    output_root = repo_root / rehearsal.OUTPUT_ROOT_RELATIVE
    _assert(output_root.is_dir(), "output directory missing")
    _assert(
        {path.name for path in output_root.iterdir() if path.is_file()}
        == set(rehearsal.OUTPUT_FILENAMES),
        "output file set mismatch",
    )
    _assert(
        not any(
            path.is_file() and path.suffix in {".tmp", ".part"}
            for path in output_root.iterdir()
        ),
        "temporary output remains",
    )
    expected = rehearsal.build_artifacts_v1(repo_root=repo_root)
    blocked = _network_blocked_replay(repo_root)
    _assert(expected == blocked, "network-blocked replay mismatch")
    for name in rehearsal.OUTPUT_FILENAMES:
        _assert(
            (output_root / name).read_bytes() == expected[name],
            "deterministic replay mismatch: " + name,
        )

    manifest = json.loads(expected[rehearsal.MANIFEST])
    summary = json.loads(expected[rehearsal.SUMMARY])
    requirements = json.loads(expected[rehearsal.ACQUISITION])
    reader = csv.DictReader(io.StringIO(expected[rehearsal.COHORT].decode("utf-8")))
    _assert(tuple(reader.fieldnames or ()) == rehearsal.EVENT_HEADER, "cohort header")
    rows = list(reader)
    _assert(len(rows) == 500, "cohort row count")
    _assert(
        all(tuple(row) == rehearsal.EVENT_HEADER for row in rows),
        "cohort row schema",
    )

    for artifact in (manifest, summary, requirements):
        _assert(not _contains_absolute_path(artifact), "absolute path persisted")
        for forbidden in (
            "head",
            "current_head",
            "origin_main",
            "ahead",
            "behind",
            "timestamp",
            "execution_timestamp",
            "current_cache_available",
            "current_cache_total_bytes",
            "current_required_pdb_cache_hits",
            "current_required_pdb_cache_misses",
            "current_required_ccd_cache_hits",
            "current_required_ccd_cache_misses",
        ):
            _assert(
                not _contains_key(artifact, forbidden),
                "mutable runtime field persisted: " + forbidden,
            )
    _assert(
        "covapie_bulk_500_scaleup_rehearsal_manifest_v1.json"
        not in manifest["output_sha256_excluding_manifest"],
        "manifest self hash",
    )
    for name, digest in manifest["output_sha256_excluding_manifest"].items():
        _assert(_sha(expected[name]) == digest, "output hash mismatch: " + name)

    ranks = [int(row["scaleup_rank"]) for row in rows]
    event_ids = [row["canonical_event_id"] for row in rows]
    _assert(ranks == list(range(1, 501)), "scaleup rank order")
    _assert(len(set(event_ids)) == 500, "cohort canonical ID uniqueness")
    _assert(
        all(row["tranche"] == rehearsal.HISTORICAL_TRANCHE for row in rows[:250])
        and all(
            row["tranche"] == rehearsal.INCREMENTAL_TRANCHE for row in rows[250:]
        ),
        "tranche boundary",
    )
    _assert(
        all(row["historical_pilot_processed"] == "true" for row in rows[:250])
        and all(row["historical_pilot_processed"] == "false" for row in rows[250:]),
        "historical processed marker",
    )
    _assert(
        all(row["historical_terminal_route"] for row in rows[:250])
        and all(not row["historical_terminal_route"] for row in rows[250:]),
        "historical terminal route boundary",
    )
    _assert(
        all(row["historical_bulk_structure_acquisition_status"] for row in rows[:250])
        and all(
            not row["historical_bulk_structure_acquisition_status"]
            for row in rows[250:]
        ),
        "historical acquisition status boundary",
    )
    _assert(
        all(row["structure_execution_status"] == "NOT_YET_EXECUTED" for row in rows[250:])
        and all(
            row["task_domain_rule_evaluation_status"]
            == rehearsal.INCREMENTAL_RULE_STATUS
            for row in rows[250:]
        )
        and all(
            row["current_123_two_rule_routing_population_overlap"]
            == "NOT_APPLICABLE_NOT_YET_PROCESSED"
            for row in rows[250:]
        ),
        "incremental scientific blank status",
    )
    _assert(
        sum(
            row["current_123_two_rule_routing_population_overlap"] == "true"
            for row in rows[:250]
        )
        == 123,
        "historical current-routing overlap",
    )
    historical_routes = Counter(row["historical_terminal_route"] for row in rows[:250])
    _assert(
        historical_routes
        == Counter(
            {
                "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY": 123,
                "LEAKAGE_EXISTING_GROUP_CONFLICT": 88,
                "STRUCTURAL_EVIDENCE_INCOMPLETE": 32,
                "QUARANTINE_REPRESENTATION_GAP": 7,
            }
        ),
        "historical 250 terminal route counts",
    )

    cohort_summary = summary["cohort"]
    _assert(
        cohort_summary["cumulative_new_event_count"] == 500
        and cohort_summary["historical_pilot_new_event_count"] == 250
        and cohort_summary["incremental_new_event_count"] == 250
        and cohort_summary["remaining_unselected_new_event_count"] == 1860,
        "cohort count reconciliation",
    )
    _assert(
        cohort_summary["historical_250_exact_prefix_of_500"] is True
        and cohort_summary["historical_250_set_equal"] is True
        and cohort_summary["historical_250_order_equal"] is True,
        "historical prefix parity",
    )
    _assert(
        manifest["prefix_parity_proof"]["historical_250_ordered_event_ids_sha256"]
        == manifest["prefix_parity_proof"][
            "derived_500_prefix_ordered_event_ids_sha256"
        ],
        "prefix identity digest",
    )
    _assert(
        manifest["historical_selection_audit"][
            "historical_selected_unique_pdb_count_including_controls"
        ]
        == 175
        and manifest["historical_selection_audit"][
            "historical_unique_pdb_cap_was_nonbinding"
        ]
        is True,
        "historical unique-PDB cap audit",
    )

    expected_acquisition_counts = {
        "cumulative_500_unique_pdb_count": 290,
        "historical_250_unique_pdb_count": 154,
        "incremental_250_unique_pdb_count": 136,
        "incremental_new_unique_pdb_count": 136,
        "cumulative_500_unique_ccd_count": 225,
        "historical_250_unique_ccd_count": 123,
        "incremental_250_unique_ccd_count": 114,
        "incremental_new_ccd_count": 102,
    }
    _assert(
        summary["acquisition_identity_counts"] == expected_acquisition_counts,
        "acquisition identity counts",
    )
    pdb = requirements["pdb_requirements"]
    ccd = requirements["ccd_requirements"]
    _assert(len(pdb["requirements"]) == 290, "PDB requirement row count")
    _assert(len(ccd["requirements"]) == 225, "CCD requirement row count")
    _assert(
        sum(item["event_count"] for item in pdb["requirements"]) == 500
        and sum(item["event_count"] for item in ccd["requirements"]) == 500,
        "acquisition event memberships",
    )
    _assert(
        {
            event_id
            for item in pdb["requirements"]
            for event_id in item["canonical_event_ids"]
        }
        == set(event_ids)
        == {
            event_id
            for item in ccd["requirements"]
            for event_id in item["canonical_event_ids"]
        },
        "acquisition canonical event coverage",
    )
    _assert(
        all(item["ccd_id"] for item in ccd["requirements"])
        and sum(
            item["committed_pilot_resolved_payload"] for item in ccd["requirements"]
        )
        == 123,
        "CCD identity and committed resolution status",
    )
    _assert(
        pdb["known_control_unique_pdb_count"] == 21
        and ccd["known_control_unique_ccd_count"] == 15
        and requirements["population"]["known_existing_control_event_count"] == 27
        and requirements["population"][
            "known_controls_counted_against_new_event_cap"
        ]
        is False,
        "known control separation",
    )
    _assert(
        requirements["execution_not_performed"] is True
        and requirements["network_performed"] is False
        and requirements["downloaded_bytes"] == 0,
        "acquisition execution safety",
    )

    stages = manifest["processing_stage_readiness"]
    _assert(
        [item["stage_name"] for item in stages]
        == list(rehearsal.frozen_bulk.BULK_STAGES),
        "BULK_01 through BULK_15 coverage",
    )
    _assert(
        all(
            item["classification"]
            in {
                "READY_UNCHANGED",
                "READY_WITH_CONFIGURABLE_CAP",
                "NEEDS_MINIMAL_SCALE_FIX",
                "NOT_APPLICABLE_TO_REHEARSAL",
            }
            for item in stages
        ),
        "stage classification vocabulary",
    )
    stage_by_name = {item["stage_name"]: item for item in stages}
    _assert(
        stage_by_name["BULK_05_STRUCTURE_ACQUISITION"]["classification"]
        == "READY_WITH_CONFIGURABLE_CAP"
        and stage_by_name["BULK_05_STRUCTURE_ACQUISITION"][
            "modification_required_before_500_execution"
        ]
        is True
        and stage_by_name["BULK_12_LEAKAGE_AND_SPLIT_PREDICTION"][
            "obvious_o_n_squared_or_high_memory_scale_risk"
        ]
        is True,
        "real cap and scale-risk audit",
    )
    feature_state = manifest["authoritative_resolved_feature_state"]
    _assert(
        all(
            feature_state[field] is True
            for field in (
                "feature_semantics_audit_completed",
                "feature_semantics_known",
                "unknown_atom_feature_policy_resolved",
                "unknown_atom_policy_contract_resolved",
            )
        )
        and feature_state["training_performed_or_authorized_by_rehearsal"]
        is False
        and feature_state["published_resolution_binding"]["sha256"]
        == rehearsal.FEATURE_RESOLUTION_MANIFEST_SHA256,
        "authoritative resolved feature state",
    )
    bulk_09_basis = stage_by_name[
        "BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"
    ]["audit_basis"]
    _assert(
        "already resolved" in bulk_09_basis
        and "remains a separate training prerequisite" not in bulk_09_basis,
        "BULK_09 resolved feature semantics wording",
    )
    execution = summary["execution_configuration_requirements"]
    _assert(
        execution["new_events_selected_if_historical_250_pdb_cap_reused"] == 402
        and execution["historical_250_pdb_cap_is_insufficient_for_500"] is True
        and execution[
            "required_unique_pdb_capacity_for_500_new_plus_27_controls"
        ]
        == 311,
        "configurable-cap execution requirement",
    )

    routing = summary["two_rule_live_routing_baseline"]
    _assert(
        routing["integrated_rule_ids"]
        == [
            "NEG_V1_TS_DUMP_CATALYTIC_ADDUCT_EXACT",
            "NEG_V2_DTT_CRYSTALLIZATION_REDUCING_ADDUCT_EXACT",
        ]
        and routing["candidate_events"] == 123
        and routing["candidate_units"] == 36
        and routing["effective_auto_negative_events"] == 32
        and routing["effective_auto_negative_units"] == 2
        and routing["human_review_required_units"] == 24
        and routing["human_review_required_events"] == 56
        and routing["human_overlay_reviewed_units"] == 10
        and routing["human_overlay_unreviewed_units"] == 26
        and routing["baseline_is_not_prediction_for_incremental_250"] is True,
        "two-rule baseline",
    )

    for field in (
        "network_performed",
        "external_cache_modified",
        "frozen_bulk_pilot_modified",
        "successor_routing_modified",
        "human_overlay_modified",
        "production_authority_created",
        "training_materialization_performed",
        "structural_processing_execution_performed",
    ):
        _assert(summary[field] is False, "summary safety field: " + field)
    _assert(
        summary["ready_for_controlled_500_event_execution"] is True
        and summary["ready_for_gpt_review"] is True
        and not summary["execution_blockers"],
        "readiness",
    )
    _assert(
        summary["recommended_next_step_exactly"]
        == (
            "gpt_audit_500_event_scaleup_rehearsal_then_authorize_controlled_"
            "500_event_bulk_execution_v1"
        ),
        "recommended next step",
    )

    observation = rehearsal.observe_current_cache_v1(
        repo_root=repo_root, acquisition_requirements=requirements
    )
    _assert(observation["cache_modified"] is False, "cache modification marker")
    if observation["current_cache_available"]:
        _assert(
            observation["cache_integrity_failure_count"] == 0,
            "current cache integrity observation",
        )
        _assert(
            observation["current_required_pdb_cache_hits"]
            + observation["current_required_pdb_cache_misses"]
            == 290
            and observation["current_required_ccd_cache_hits"]
            + observation["current_required_ccd_cache_misses"]
            == 225,
            "current cache requirement reconciliation",
        )
        _assert(
            observation["download_size_statistics"]["pdb_structure_payloads"][
                "sample_count"
            ]
            > 0
            and observation["incremental_expected_download_bytes_using_mean"]
            is not None
            and observation["incremental_expected_download_bytes_using_p95"]
            is not None
            and observation["estimate_is_not_guarantee"] is True,
            "download projection",
        )
    return {
        "summary": summary,
        "observation": observation,
        "baseline": baseline,
        "worktree_profile": worktree_profile,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    result = check_v1(arguments.repo_root)
    summary = result["summary"]
    observation = result["observation"]
    baseline = result["baseline"]
    print(
        json.dumps(
            {
                "check": "PASS",
                "historical_250_exact_prefix_of_500": summary["cohort"][
                    "historical_250_exact_prefix_of_500"
                ],
                "cumulative_500_unique_pdb_count": summary[
                    "acquisition_identity_counts"
                ]["cumulative_500_unique_pdb_count"],
                "cumulative_500_unique_ccd_count": summary[
                    "acquisition_identity_counts"
                ]["cumulative_500_unique_ccd_count"],
                "current_cache_observation": observation,
                "network_performed": False,
                "external_cache_modified": False,
                "runtime_head": baseline["runtime_head"],
                "runtime_origin_main": baseline["runtime_origin_main"],
                "worktree_profile": result["worktree_profile"],
                "ready_for_controlled_500_event_execution": summary[
                    "ready_for_controlled_500_event_execution"
                ],
                "ready_for_gpt_review": summary["ready_for_gpt_review"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

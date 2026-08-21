#!/usr/bin/env python3
"""Fail-closed semantic checker for the additive 500-event executor."""

from __future__ import annotations

import json
from pathlib import Path
import urllib.request

from covalent_ext import covapie_bulk_500_event_executor_v1 as executor


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _network_blocked_preflight(repo_root: Path, cache_root: Path) -> dict[str, object]:
    calls: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> bytes:
        calls.append("NETWORK")
        raise AssertionError("NETWORK_CALLED_BY_PREFLIGHT")

    patches = (
        (urllib.request, "urlopen"),
        (executor, "urlopen"),
        (executor, "official_network_backend_v1"),
        (executor.frozen_bulk, "urlopen"),
        (executor.frozen_bulk.BulkCacheV1, "fetch"),
        (executor.frozen_bulk, "discover_covpdb_v1"),
        (executor.frozen_bulk, "discover_covbinder_v1"),
        (executor.frozen_bulk, "discover_rcsb_direct_v1"),
        (executor.frozen_bulk, "discover_rcsb_specialist_seeded_v1"),
        (executor.frozen_bulk, "_acquire_structures_v1"),
        (executor.frozen_bulk, "acquire_ccd_components_v1"),
    )
    originals = [(owner, name, getattr(owner, name)) for owner, name in patches]
    try:
        for owner, name, _original in originals:
            setattr(owner, name, forbidden)
        result = executor.run_v1(
            repo_root=repo_root,
            cache_root=cache_root,
        )
    finally:
        for owner, name, original in originals:
            setattr(owner, name, original)
    _assert(not calls, "network backend reached")
    return result


def check_v1(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    repository = executor.verify_synchronized_descendant_repository_v1(repo_root)
    cache_root = (
        repo_root.parent / executor.DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT
    )
    before = executor.snapshot_cache_tree_v1(cache_root)
    inputs = executor.load_published_executor_inputs_v1(repo_root)
    preflight = _network_blocked_preflight(repo_root, cache_root)
    after = executor.snapshot_cache_tree_v1(cache_root)
    _assert(before == after, "preflight changed external cache")
    _assert(preflight["published_rehearsal_binding_valid"] is True, "bindings")
    _assert(preflight["mode"] == executor.PREFLIGHT_NO_NETWORK, "default mode")
    _assert(preflight["network_authorized"] is False, "network authorization")
    _assert(preflight["network_performed"] is False, "network performed")
    _assert(preflight["cache_modified"] is False, "cache modified")
    _assert(
        preflight["structural_processing_performed"] is False,
        "structural processing performed",
    )
    _assert(
        preflight["current_valid_pdb_cache_hits"]
        + preflight["current_missing_pdb_count"] == 290,
        "dynamic PDB cache reconciliation",
    )
    _assert(
        preflight["current_valid_ccd_cache_hits"]
        + preflight["current_missing_ccd_count"] == 225,
        "dynamic CCD cache reconciliation",
    )
    _assert(
        preflight["current_valid_control_pdb_cache_hits"]
        + preflight["current_missing_control_pdb_count"] == 21,
        "dynamic control PDB cache reconciliation",
    )
    _assert(
        preflight["current_valid_control_ccd_cache_hits"]
        + preflight["current_missing_control_ccd_count"] == 15,
        "dynamic control CCD cache reconciliation",
    )
    _assert(len(inputs["incremental_records"]) == 250, "incremental count")
    _assert(
        executor._ordered_ids_sha256(inputs["incremental_records"])
        == executor.INCREMENTAL_ORDERED_EVENT_IDS_SHA256,
        "incremental ordered identity",
    )
    _assert(
        not (
            {item["canonical_event_id"] for item in inputs["historical_records"]}
            & {item["canonical_event_id"] for item in inputs["incremental_records"]}
        ),
        "historical/incremental overlap",
    )
    _assert(
        not (
            inputs["known_control_event_ids"]
            & {item["canonical_event_id"] for item in inputs["cohort_records"]}
        ),
        "known control mixed into cohort",
    )

    budget = executor.DownloadBudgetV1(total_cap_bytes=3)
    first_limit = budget.request_limit(executor.PDB_SINGLE_PAYLOAD_CAP_BYTES)
    _assert(first_limit == 3, "remaining budget did not bound request")
    budget.record_received_bytes(2)
    budget.record_received_bytes(1)
    _assert(
        budget.network_bytes_received_this_execution == 3,
        "received network bytes not accumulated",
    )
    try:
        budget.request_limit(executor.CCD_SINGLE_PAYLOAD_CAP_BYTES)
    except executor.ExecutorSafetyError as error:
        _assert("EXHAUSTED_BEFORE_REQUEST" in str(error), "wrong budget failure")
    else:
        raise AssertionError("hard total budget inactive")

    canonical_cache = executor.canonical_controlled_cache_root_v1(repo_root)
    canonical_output = executor.controlled_output_namespace_v1(repo_root)
    _assert(
        executor.validate_controlled_state_roots_v1(
            repo_root=repo_root,
            cache_root=canonical_cache,
            output_root=canonical_output,
        ) == (canonical_cache, canonical_output),
        "canonical controlled roots rejected",
    )
    try:
        executor.validate_controlled_state_roots_v1(
            repo_root=repo_root,
            cache_root=repo_root.parent / "covapie-state/arbitrary-cache",
            output_root=canonical_output,
        )
    except executor.ExecutorSafetyError as error:
        _assert("CACHE_ROOT_NOT_CANONICAL" in str(error), "wrong cache root error")
    else:
        raise AssertionError("arbitrary controlled cache root accepted")

    synthetic_publication = {
        "branch": "main",
        "head": "d" * 40,
        "origin_main": "d" * 40,
        "ahead": 0,
        "behind": 0,
        "published_baseline_ancestor_of_head": True,
        "published_baseline_ancestor_of_origin_main": True,
        "modified_tracked": [],
        "staged": [],
        "untracked": [],
        "tracked_executor_paths": sorted(executor.EXECUTOR_IMPLEMENTATION_PATHS),
    }
    executor.validate_controlled_publication_observation_v1(synthetic_publication)
    unpublished = dict(synthetic_publication)
    unpublished["untracked"] = sorted(executor.EXECUTOR_IMPLEMENTATION_PATHS)
    try:
        executor.validate_controlled_publication_observation_v1(unpublished)
    except executor.ExecutorSafetyError as error:
        _assert("UNTRACKED" in str(error), "wrong publication gate error")
    else:
        raise AssertionError("untracked executor accepted for controlled network")

    _assert(
        preflight["leakage_batch_population_count"] == 527
        and preflight["frozen_control_outcomes_in_leakage_context"] == 27,
        "527 leakage population contract",
    )

    ready = all((
        preflight["ready_for_controlled_network_execution"] is True,
        preflight["cache_integrity_failure_count"] == 0,
        before == after,
        budget.hard_stopped,
        preflight["all_received_network_bytes_budget_enforcement_active"] is True,
        preflight["controlled_state_root_separation_active"] is True,
        preflight["implementation_ready_for_publication"] is True,
    ))
    _assert(ready, "executor not ready for GPT review")
    return {
        "schema_version": executor.SCHEMA_VERSION,
        "repository": repository,
        "published_rehearsal_bindings_verified": True,
        "exact_incremental_workset_verified": True,
        "incremental_ordered_event_ids_sha256": (
            executor.INCREMENTAL_ORDERED_EVENT_IDS_SHA256
        ),
        "network_blocked_preflight_passed": True,
        "network_performed": False,
        "cache_modified": False,
        "external_cache_snapshot_unchanged": True,
        "all_received_network_bytes_budget_active": True,
        "dynamic_cache_reconciliation_verified": True,
        "controlled_root_separation_verified": True,
        "leakage_batch_population_count": 527,
        "frozen_control_outcomes_in_leakage_context": 27,
        "synthetic_controlled_publication_gate_verified": True,
        "controlled_network_execution_publication_gate_currently_satisfied": (
            preflight[
                "controlled_network_execution_publication_gate_currently_satisfied"
            ]
        ),
        "implementation_ready_for_publication": preflight[
            "implementation_ready_for_publication"
        ],
        "ready_for_controlled_network_execution": preflight[
            "ready_for_controlled_network_execution"
        ],
        "ready_for_gpt_review": ready,
    }


def main() -> None:
    result = check_v1(Path.cwd())
    if result["ready_for_gpt_review"] is not True:
        raise SystemExit("ready_for_gpt_review=false")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

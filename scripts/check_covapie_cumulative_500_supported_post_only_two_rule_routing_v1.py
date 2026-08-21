#!/usr/bin/env python3
"""Fail-closed checker for cumulative-500 post-only two-rule routing V1."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_cumulative_500_supported_post_only_two_rule_routing_v1 as cumulative,
)


AUTHORIZED_NEW_PATHS = cumulative.AUTHORIZED_PUBLICATION_PATHS
PROTECTED_PATHS = (
    "data/raw/",
    "checkpoints/",
    "equivariant_diffusion/",
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
)
FORBIDDEN_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".tmp",
    ".part",
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _csv(path: Path, header: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _assert(tuple(reader.fieldnames or ()) == tuple(header), path.name + " header")
        rows = list(reader)
    _assert(
        all(tuple(row) == tuple(header) and None not in row.values() for row in rows),
        path.name + " row schema",
    )
    return rows


def _contains_absolute_path(value: object) -> bool:
    if isinstance(value, str):
        return os.path.isabs(value)
    if isinstance(value, list):
        return any(_contains_absolute_path(item) for item in value)
    if isinstance(value, Mapping):
        return any(
            _contains_absolute_path(key) or _contains_absolute_path(item)
            for key, item in value.items()
        )
    return False


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, Mapping):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def check_v1(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_root = repo_root / cumulative.OUTPUT_ROOT_RELATIVE
    _assert(output_root.is_dir(), "output directory missing")
    _assert(
        {path.name for path in output_root.iterdir() if path.is_file()}
        == set(cumulative.OUTPUT_FILENAMES),
        "output file set mismatch",
    )
    _assert(
        not any(path.suffix in {".tmp", ".part"} for path in output_root.iterdir()),
        "temporary output remains",
    )

    repository_profile = cumulative.verify_repository_state_v1(repo_root)
    expected = cumulative.build_artifacts_v1(repo_root=repo_root)
    for name in cumulative.OUTPUT_FILENAMES:
        _assert(
            (output_root / name).read_bytes() == expected[name],
            "deterministic replay mismatch: " + name,
        )

    manifest = json.loads((output_root / cumulative.MANIFEST).read_bytes())
    summary = json.loads((output_root / cumulative.SUMMARY).read_bytes())
    events = _csv(output_root / cumulative.EVENT_INVENTORY, cumulative.EVENT_HEADER)
    units = _csv(
        output_root / cumulative.REVIEW_UNIT_INVENTORY,
        cumulative.REVIEW_UNIT_HEADER,
    )
    for artifact in (manifest, summary):
        _assert(not _contains_absolute_path(artifact), "absolute path persisted")
        for forbidden in (
            "head",
            "origin_main",
            "ahead",
            "behind",
            "timestamp",
            "execution_timestamp",
            "stat_tree_sha256",
        ):
            _assert(
                not _contains_key(artifact, forbidden),
                "runtime state persisted: " + forbidden,
            )
    _assert(manifest["schema_version"] == cumulative.SCHEMA_VERSION, "manifest schema")
    _assert(summary["schema_version"] == cumulative.SCHEMA_VERSION, "summary schema")
    _assert(
        manifest["integrated_exact_rule_ids"]
        == list(cumulative.routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS),
        "exact two-rule registry",
    )
    bindings = cumulative.verify_bound_inputs_v1(repo_root)["predecessor"]
    _assert(
        manifest["published_ts_dump_gate_artifact_bindings"]
        == bindings["published_gate"],
        "published TS gate bindings",
    )
    _assert(
        manifest["published_dtt_gate_artifact_bindings"]
        == bindings["published_dtt_gate"],
        "published DTT gate bindings",
    )
    _assert(
        manifest["current_human_snapshot_binding"]
        == bindings["current_human_snapshot"],
        "current human snapshot binding",
    )
    _assert(
        manifest["canonical_cache_read_only_binding"]["ledger"]["sha256"]
        == cumulative.CACHE_LEDGER_SHA256,
        "cache ledger binding",
    )
    _assert(
        manifest["canonical_cache_read_only_binding"]["missing_ccd_ids"] == ["RU8"],
        "cache missing CCD observation",
    )
    _assert(len(events) == 500, "500 event inventory")
    _assert(
        [int(row["scaleup_rank"]) for row in events] == list(range(1, 501)),
        "rank order",
    )
    _assert(
        len({row["canonical_event_id"] for row in events}) == 500,
        "event identity uniqueness",
    )
    candidate_rows = [
        row for row in events if row["post_only_candidate_eligibility"] == "true"
    ]
    historical_candidates = [
        row
        for row in candidate_rows
        if row["candidate_lane"] == "HISTORICAL_PREDECESSOR_CANDIDATE"
    ]
    new_candidates = [
        row for row in candidate_rows if row["candidate_lane"] == "NEW_INCREMENTAL_CANDIDATE"
    ]
    _assert(len(historical_candidates) == 123, "historical candidate count")
    _assert(len(new_candidates) == 87, "incremental candidate count")
    _assert(
        all(251 <= int(row["scaleup_rank"]) <= 500 for row in new_candidates),
        "incremental rank boundary",
    )
    rank_493 = events[492]
    _assert(
        rank_493["canonical_event_id"]
        == "COVAPIE_CYS_SG_EVENT_V1:3NPL:B:CYS:97-:SG:F:RU8:C49"
        and rank_493["raw_terminal_outcome"] == "STRUCTURAL_EVIDENCE_INCOMPLETE"
        and json.loads(rank_493["raw_terminal_reasons_json"])
        == ["REQUIRED_CCD_PAYLOAD_UNAVAILABLE"]
        and rank_493["post_only_candidate_eligibility"] == "false",
        "rank 493 natural exclusion",
    )

    _assert(
        Counter(row["post_only_partition"] for row in events)
        == {
            cumulative.triage.POST_ONLY_CANDIDATE: 210,
            cumulative.triage.BLOCKED_LEAKAGE: 196,
            cumulative.triage.BLOCKED_REPRESENTATION: 31,
            cumulative.triage.OUTSIDE_STRUCTURAL: 63,
        },
        "cumulative eligibility partition",
    )
    _assert(
        Counter(row["raw_terminal_outcome"] for row in events)
        == {
            "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY": 210,
            "LEAKAGE_EXISTING_GROUP_CONFLICT": 196,
            "STRUCTURAL_EVIDENCE_INCOMPLETE": 61,
            "QUARANTINE_REPRESENTATION_GAP": 31,
            "REJECTED_FEATURE_INCOMPATIBLE": 2,
        },
        "cumulative raw terminal routes",
    )
    _assert(
        all(
            row["ts_dump_rule_status"] == cumulative.routing.gate.NOT_MATCHED
            and row["dtt_rule_status"] == cumulative.routing.gate.NOT_MATCHED
            and row["effective_route"] == cumulative.routing.HUMAN_REVIEW_REQUIRED
            and row["human_decision_propagated_to_new_event"] == "false"
            for row in new_candidates
        ),
        "new exact-rule outcomes",
    )
    historical_effective = Counter(row["effective_route"] for row in historical_candidates)
    _assert(
        historical_effective
        == {
            cumulative.routing.AUTO_NEGATIVE_EXACT_FINAL: 32,
            cumulative.routing.HUMAN_NOT_RELEVANT_FINAL: 30,
            cumulative.routing.HUMAN_RELEVANT_FINAL: 5,
            cumulative.routing.HUMAN_REVIEW_REQUIRED: 56,
        },
        "historical routing parity",
    )
    _assert(len(units) == 57, "cumulative unresolved workload units")
    _assert(
        sum(int(row["event_count"]) for row in units) == 143,
        "cumulative unresolved workload events",
    )
    _assert(
        sum(row["new_events_join_existing_workload_equivalent_unit"] == "true" for row in units)
        == 1,
        "joining workload unit count",
    )
    joining = next(
        row
        for row in units
        if row["new_events_join_existing_workload_equivalent_unit"] == "true"
    )
    _assert(
        joining["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74"
        and int(joining["historical_unresolved_event_count"]) == 5
        and int(joining["new_unresolved_event_count"]) == 4,
        "joining workload membership",
    )
    _assert(
        sum(row["new_genuinely_new_unit"] == "true" for row in units) == 33,
        "genuinely new workload units",
    )

    safety = summary["safety"]
    _assert(all(
        safety[field] is False
        for field in (
            "RU8_retry_performed",
            "attempt_002_created",
            "RU8_special_case_used",
            "historical_two_rule_routing_modified",
            "human_overlay_modified",
            "production_authority_created",
            "canonical_bulk_cache_modified",
            "network_performed",
            "training_materialization_performed",
        )
    ), "summary safety")
    _assert(safety["abandoned_transition_metal_policy_files_removed"] is True, "cleanup")
    _assert(summary["ready_for_gpt_review"] is True, "review readiness")

    _assert(_git(repo_root, "diff", "--name-only") == "", "modified tracked files")
    _assert(_git(repo_root, "diff", "--cached", "--name-only") == "", "staged files")
    _assert(
        repository_profile
        in {
            cumulative.CUMULATIVE_ROUTING_PRECOMMIT_CANDIDATE,
            cumulative.CUMULATIVE_ROUTING_PUBLISHED_CLEAN_DESCENDANT,
        },
        "repository publication profile",
    )
    for protected in PROTECTED_PATHS:
        _assert(
            _git(repo_root, "diff", "--", protected) == ""
            and _git(repo_root, "diff", "--cached", "--", protected) == "",
            "protected source changed: " + protected,
        )
    _assert(
        not any(path.endswith(FORBIDDEN_SUFFIXES) for path in AUTHORIZED_NEW_PATHS),
        "forbidden suffix in file scope",
    )
    return {
        "schema_version": cumulative.SCHEMA_VERSION,
        "historical_post_only_candidate_count": 123,
        "incremental_post_only_candidate_count": 87,
        "cumulative_post_only_candidate_count": 210,
        "new_TS_auto_negative_event_count": 0,
        "new_DTT_auto_negative_event_count": 0,
        "new_unresolved_human_review_event_count": 87,
        "cumulative_unresolved_human_review_event_count": 143,
        "new_unresolved_review_unit_count": 34,
        "cumulative_unresolved_review_unit_count": 57,
        "repository_profile": repository_profile,
        "ready_for_gpt_review": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--materialize", action="store_true")
    arguments = parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    if arguments.materialize:
        cumulative.materialize_v1(repo_root=repo_root)
    print(json.dumps(check_v1(repo_root), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

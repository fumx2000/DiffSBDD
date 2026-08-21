"""Build the cumulative-500 supported-domain post-only two-rule snapshot V1.

This additive successor binds frozen attempt-001 execution evidence.  It does
not rerun structural processing, mutate the canonical cache, propagate human
decisions to new events, or create chemistry/training authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from covalent_ext import covapie_bulk_500_event_executor_v1 as executor
from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk
from covalent_ext import (
    covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1 as routing,
)
from covalent_ext import (
    covapie_bulk_post_only_cys_sg_training_candidate_triage_v1 as triage,
)


SCHEMA_VERSION = "covapie_cumulative_500_supported_post_only_two_rule_routing_v1"
STAGE = SCHEMA_VERSION
SNAPSHOT_SEMANTICS = (
    "FROZEN_ATTEMPT_001_CUMULATIVE_500_SUPPORTED_DOMAIN_POST_ONLY_TWO_RULE_ROUTING"
)
PUBLISHED_CUMULATIVE_ROUTING_BASELINE_ANCESTOR = (
    "b9afb22eaa500b8dbed57e94636872294772645e"
)
CUMULATIVE_ROUTING_PRECOMMIT_CANDIDATE = (
    "CUMULATIVE_ROUTING_PRECOMMIT_CANDIDATE"
)
CUMULATIVE_ROUTING_PUBLISHED_CLEAN_DESCENDANT = (
    "CUMULATIVE_ROUTING_PUBLISHED_CLEAN_DESCENDANT"
)

OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative_500_supported_post_only_two_rule_routing_v1"
)
MANIFEST = "covapie_cumulative_500_two_rule_routing_manifest_v1.json"
EVENT_INVENTORY = "covapie_cumulative_500_event_routing_inventory_v1.csv"
REVIEW_UNIT_INVENTORY = "covapie_cumulative_500_review_unit_inventory_v1.csv"
SUMMARY = "covapie_cumulative_500_two_rule_routing_summary_v1.json"
OUTPUT_FILENAMES = (MANIFEST, EVENT_INVENTORY, REVIEW_UNIT_INVENTORY, SUMMARY)
AUTHORIZED_PUBLICATION_PATHS = frozenset(
    {
        "src/covalent_ext/"
        "covapie_cumulative_500_supported_post_only_two_rule_routing_v1.py",
        "scripts/"
        "check_covapie_cumulative_500_supported_post_only_two_rule_routing_v1.py",
        "tests/"
        "test_covapie_cumulative_500_supported_post_only_two_rule_routing_v1.py",
        *(
            (OUTPUT_ROOT_RELATIVE / name).as_posix()
            for name in OUTPUT_FILENAMES
        ),
    }
)

ATTEMPT_ROOT_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001"
)
ATTEMPT_BINDINGS = {
    "incremental_processing_outcomes_v1.json": {
        "byte_count": 3043911,
        "sha256": "d891a267dc4493cfceda33b70ab4a200d9f806e1bff38c4b6f39b69a1a3548d7",
    },
    "cumulative_processing_view_v1.json": {
        "byte_count": 6469651,
        "sha256": "a27d4bf7977d5a175387af83021270c68f9cf3e8db391113dc6f1ff22f0bfc44",
    },
    "controlled_execution_result_v1.json": {
        "byte_count": 1877,
        "sha256": "381159326fe183c47519acd554acf395f0da067926b93c42fd6962d134e995e9",
    },
}

CACHE_LEDGER_SHA256 = (
    "10057a8fd7e34c5e63a912a44f242926247aef15cffefa942dceb910d3f1cd58"
)
EXPECTED_CACHE_MISSING_CCD_IDS = ("RU8",)

PUBLISHED_REPOSITORY_BINDINGS = {
    "src/covalent_ext/covapie_bulk_500_event_executor_v1.py": {
        "byte_count": 62961,
        "sha256": "8de3f553be8e1ce78077c5920548eff5f7bb73c81632178765489b511ca55d04",
    },
    "src/covalent_ext/covapie_bulk_post_only_cys_sg_training_candidate_triage_v1.py": {
        "byte_count": 89359,
        "sha256": "f87fa78d264e2a68dd4704061632a23f9913caf02e4b8aa4a9dea443ce8c1d97",
    },
    "src/covalent_ext/covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1.py": {
        "byte_count": 69740,
        "sha256": "d0fce4073b7201508091f72e4b016918beaf97d7c236f255f2532871a1ab0673",
    },
    "src/covalent_ext/covapie_post_only_auto_negative_ts_dump_exact_v1.py": {
        "byte_count": 88086,
        "sha256": "90956c833a31a5b5615979dedf3f5205738d27c05efe15168b9c38f71c264bf1",
    },
    "src/covalent_ext/covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1.py": {
        "byte_count": 97154,
        "sha256": "88209a549abf7ab119dc33cd537fcdaad45815ac74f86fdc339e4befa6278c46",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_training_candidate_triage_v1/covapie_bulk_post_only_training_candidate_event_inventory_v1.csv": {
        "byte_count": 1552095,
        "sha256": "a1e48d9efaa9b0f5f1b1d7d5988d9f54c07c22d7249b5a7b43dee31fd6efaa75",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_training_candidate_triage_v1/covapie_bulk_post_only_training_review_unit_inventory_v1.csv": {
        "byte_count": 117421,
        "sha256": "021cf3709c3e6172c592c1fe5cdf7254a87fb345cd23d6d80a5bfb515d8b9713",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_training_candidate_triage_v1/covapie_bulk_post_only_training_human_review_packet_v1.json": {
        "byte_count": 796525,
        "sha256": "39f8afd7b8f62531f9f8704163cc7a444c3b008ff8d4610744d90b4918053194",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_training_candidate_triage_v1/covapie_bulk_post_only_training_candidate_summary_v1.json": {
        "byte_count": 6749,
        "sha256": "1f8deb600137598786b3566c6fd35f0e044e150a306fe75da98f61c59dda07ac",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1/covapie_successor_task_domain_event_routing_inventory_v1.csv": {
        "byte_count": 133425,
        "sha256": "ed89971ff76bad5ff352002891d7822adccb4655797f7ae8c5dfbc1592247fe8",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1/covapie_successor_task_domain_unit_routing_inventory_v1.csv": {
        "byte_count": 19347,
        "sha256": "3512c4a3ff8e871a3120e45c18193462da270d893f9e0b45a97bfefad9dc94e7",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1/covapie_successor_task_domain_routing_manifest_v1.json": {
        "byte_count": 8859,
        "sha256": "84e957456efb107cc8bafa68d2b122d6d9fe6ae070d285bd165c9e6b99796251",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1/covapie_successor_task_domain_routing_summary_v1.json": {
        "byte_count": 3849,
        "sha256": "c0ecca63766529716b02adab7658bd3fa54907a4b53a1fcade56997c116f543e",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_human_review_v1/covapie_post_only_human_review_decisions_v1.json": {
        "byte_count": 91133,
        "sha256": "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441",
    },
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_human_review_v1/covapie_post_only_human_review_progress_v1.json": {
        "byte_count": 621,
        "sha256": "e1e93ff28e823c1f52b306623bbf20c06f2c0c95cca90bb1e61ee4d1b7cea216",
    },
    "data/derived/covalent_small/covapie_post_only_auto_negative_ts_dump_exact_v1/covapie_ts_dump_auto_negative_rule_manifest_v1.json": {
        "byte_count": 20844,
        "sha256": "100b64fff8bbef56f9885a64607d25cff293bd9d98f93f25af71455dcf6bca42",
    },
    "data/derived/covalent_small/covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1/covapie_dtt_auto_negative_rule_manifest_v1.json": {
        "byte_count": 34012,
        "sha256": "9b41905df37beb80f73b3b5e02615439fcbe1f707dd5c1548bb71d0fb4976e45",
    },
    "data/derived/covalent_small/covapie_bulk_500_new_event_scale_up_rehearsal_v1/covapie_bulk_500_scaleup_rehearsal_manifest_v1.json": {
        "byte_count": 16759,
        "sha256": "d8c6d5d4ef181427cb4d1c970de8d03f75ecc976ed18ea9e1ce42f94e3cde4b9",
    },
}

EVENT_HEADER = (
    "scaleup_rank",
    "canonical_event_id",
    "pdb_id",
    "ligand_component_id",
    "ligand_reactive_atom",
    "execution_lane",
    "candidate_lane",
    "raw_terminal_outcome",
    "raw_terminal_reasons_json",
    "feature_compatibility_stage_status",
    "post_only_candidate_eligibility",
    "post_only_partition",
    "eligibility_reason",
    "routing_review_unit_id",
    "workload_review_unit_id",
    "ts_dump_rule_id",
    "ts_dump_rule_status",
    "ts_dump_rule_reason",
    "dtt_rule_id",
    "dtt_rule_status",
    "dtt_rule_reason",
    "selected_effective_rule_id",
    "effective_route",
    "effective_route_reason",
    "human_authority_lane",
    "human_decision_propagated_to_new_event",
)

REVIEW_UNIT_HEADER = (
    "review_unit_id",
    "event_count",
    "historical_unresolved_event_count",
    "new_unresolved_event_count",
    "canonical_event_ids_json",
    "historical_event_ids_json",
    "new_event_ids_json",
    "pdb_ids_json",
    "ligand_component_ids_json",
    "reactive_atom",
    "ccd_component_graph_sha256",
    "reactive_center_radius2_fingerprint",
    "pre_source_graph_fingerprint",
    "pre_reactive_center_fingerprint",
    "pre_status",
    "atom_loss_state",
    "workload_lane",
    "new_events_join_existing_workload_equivalent_unit",
    "new_genuinely_new_unit",
    "grouping_semantics",
    "effective_workload_route",
    "human_decision_propagated",
)

NOT_EVALUATED = "NOT_EVALUATED_OUTSIDE_SUPPORTED_POST_ONLY_CANDIDATE"
UNRESOLVED_ROUTES = frozenset(
    {
        routing.HUMAN_REVIEW_REQUIRED,
        routing.HUMAN_REVIEW_REQUIRED_DEFERRED,
        routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID,
    }
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=list(header), extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(header):
            raise ValueError("CSV_ROW_SCHEMA_OR_ORDER_INVALID")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if type(value) is not dict:
        raise ValueError("JSON_ROOT_NOT_OBJECT:" + path.name)
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _file_binding(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {"byte_count": len(payload), "sha256": _sha(payload)}


def _git_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if completed.returncode not in {0, 1}:
        raise ValueError("REPOSITORY_ANCESTRY_OBSERVATION_FAILED")
    return completed.returncode == 0


def observe_repository_state_v1(repo_root: Path) -> dict[str, object]:
    """Observe publication state without writing it into deterministic data."""

    repo_root = repo_root.resolve()
    head = _git(repo_root, "rev-parse", "HEAD")
    origin = _git(repo_root, "rev-parse", "origin/main")
    divergence = _git(
        repo_root, "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    if len(divergence) != 2:
        raise ValueError("REPOSITORY_AHEAD_BEHIND_OBSERVATION_INVALID")
    try:
        ahead, behind = (int(value) for value in divergence)
    except ValueError as error:
        raise ValueError("REPOSITORY_AHEAD_BEHIND_OBSERVATION_INVALID") from error
    return {
        "branch": _git(repo_root, "branch", "--show-current"),
        "head": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "baseline_ancestor_of_head": _git_is_ancestor(
            repo_root,
            PUBLISHED_CUMULATIVE_ROUTING_BASELINE_ANCESTOR,
            head,
        ),
        "baseline_ancestor_of_origin_main": _git_is_ancestor(
            repo_root,
            PUBLISHED_CUMULATIVE_ROUTING_BASELINE_ANCESTOR,
            origin,
        ),
        "modified_tracked_paths": tuple(
            value
            for value in _git(repo_root, "diff", "--name-only").splitlines()
            if value
        ),
        "staged_paths": tuple(
            value
            for value in _git(
                repo_root, "diff", "--cached", "--name-only"
            ).splitlines()
            if value
        ),
        "untracked_paths": tuple(
            sorted(
                value
                for value in _git(
                    repo_root,
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                ).splitlines()
                if value
            )
        ),
    }


def validate_repository_observation_v1(observation: Mapping[str, object]) -> str:
    """Accept only exact precommit or synchronized published-clean profiles."""

    required_fields = {
        "branch",
        "head",
        "origin_main",
        "ahead",
        "behind",
        "baseline_ancestor_of_head",
        "baseline_ancestor_of_origin_main",
        "modified_tracked_paths",
        "staged_paths",
        "untracked_paths",
    }
    if set(observation) != required_fields:
        raise ValueError("REPOSITORY_OBSERVATION_SCHEMA_INVALID")
    if observation["branch"] != "main":
        raise ValueError("REPOSITORY_BRANCH_MISMATCH")
    head = observation["head"]
    origin = observation["origin_main"]
    if not isinstance(head, str) or not head or not isinstance(origin, str) or not origin:
        raise ValueError("REPOSITORY_HEAD_OR_ORIGIN_INVALID")
    if head != origin:
        raise ValueError("REPOSITORY_HEAD_ORIGIN_MISMATCH")
    if observation["ahead"] != 0 or observation["behind"] != 0:
        raise ValueError("REPOSITORY_AHEAD_BEHIND_MISMATCH")
    if observation["baseline_ancestor_of_head"] is not True:
        raise ValueError("BASELINE_NOT_ANCESTOR_OF_HEAD")
    if observation["baseline_ancestor_of_origin_main"] is not True:
        raise ValueError("BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    modified = observation["modified_tracked_paths"]
    staged = observation["staged_paths"]
    untracked = observation["untracked_paths"]
    if not isinstance(modified, (tuple, list)) or modified:
        raise ValueError("MODIFIED_TRACKED_FILES_PRESENT")
    if not isinstance(staged, (tuple, list)) or staged:
        raise ValueError("STAGED_FILES_PRESENT")
    if not isinstance(untracked, (tuple, list)):
        raise ValueError("UNTRACKED_PATH_OBSERVATION_INVALID")
    untracked_set = set(untracked)
    if len(untracked_set) != len(untracked):
        raise ValueError("UNTRACKED_PATH_OBSERVATION_DUPLICATE")
    if untracked_set == AUTHORIZED_PUBLICATION_PATHS:
        return CUMULATIVE_ROUTING_PRECOMMIT_CANDIDATE
    if not untracked_set:
        return CUMULATIVE_ROUTING_PUBLISHED_CLEAN_DESCENDANT
    raise ValueError("UNTRACKED_PATH_PROFILE_INVALID")


def verify_repository_state_v1(repo_root: Path) -> str:
    """Validate the current publication lifecycle profile."""

    return validate_repository_observation_v1(
        observe_repository_state_v1(repo_root)
    )


def verify_bound_inputs_v1(repo_root: Path) -> dict[str, Any]:
    """Bind every published predecessor and immutable attempt-001 payload."""

    published: dict[str, dict[str, object]] = {}
    for relative, expected in PUBLISHED_REPOSITORY_BINDINGS.items():
        observed = _file_binding(repo_root / relative)
        if observed != expected:
            raise ValueError("PUBLISHED_INPUT_BINDING_MISMATCH:" + relative)
        published[relative] = observed

    attempt_root = repo_root.parent / ATTEMPT_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    attempt: dict[str, dict[str, object]] = {}
    for name, expected in ATTEMPT_BINDINGS.items():
        observed = _file_binding(attempt_root / name)
        if observed != expected:
            raise ValueError("ATTEMPT_001_BINDING_MISMATCH:" + name)
        attempt[(ATTEMPT_ROOT_RELATIVE_TO_REPOSITORY_PARENT / name).as_posix()] = (
            observed
        )
    predecessor = routing.verify_predecessor_bindings_v1(repo_root)
    return {"published": published, "attempt_001": attempt, "predecessor": predecessor}


def verify_canonical_cache_read_only_v1(
    repo_root: Path, published_executor_inputs: Mapping[str, Any]
) -> tuple[dict[str, object], dict[str, Any]]:
    """Validate the canonical cache and return only stable persisted evidence."""

    cache_root = executor.canonical_controlled_cache_root_v1(repo_root)
    before = executor.snapshot_cache_tree_v1(cache_root)
    inspection = executor.inspect_cache_read_only_v1(
        cache_root=cache_root,
        inputs=published_executor_inputs,
        include_payloads=False,
    )
    after = executor.snapshot_cache_tree_v1(cache_root)
    if before != after:
        raise ValueError("CANONICAL_CACHE_MODIFIED_DURING_INSPECTION")
    summary = inspection.summary
    required = {
        "valid_pdb_hits": 290,
        "missing_pdb_count": 0,
        "valid_ccd_hits": 224,
        "missing_ccd_count": 1,
        "missing_ccd_ids": list(EXPECTED_CACHE_MISSING_CCD_IDS),
        "cache_integrity_failure_count": 0,
        "cache_modified": False,
    }
    for field, expected in required.items():
        if summary.get(field) != expected:
            raise ValueError("CANONICAL_CACHE_OBSERVATION_MISMATCH:" + field)
    ledger = cache_root / "cache_manifest_v1.json"
    binding = _file_binding(ledger)
    if binding["sha256"] != CACHE_LEDGER_SHA256:
        raise ValueError("CANONICAL_CACHE_LEDGER_SHA256_MISMATCH")
    stable = {
        "ledger": {
            "path_relative_to_repository_parent": (
                executor.DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT
                / "cache_manifest_v1.json"
            ).as_posix(),
            **binding,
        },
        **required,
        "observation_only": True,
    }
    return stable, before


def supported_post_only_partition_v1(outcome: Mapping[str, Any]) -> str:
    """Reuse the published generic eligibility semantics for any new event."""

    return triage.post_only_partition_v1(outcome, known_event=False)


def _acquisition_rows_from_ledger(
    *, cache_root: Path, candidate_records: Sequence[Mapping[str, Any]]
) -> dict[str, dict[str, object]]:
    ledger = _read_json(cache_root / "cache_manifest_v1.json")
    payloads = ledger.get("payloads")
    if not isinstance(payloads, list):
        raise ValueError("CANONICAL_CACHE_LEDGER_PAYLOADS_INVALID")
    entries = {
        str(item["relative_path"]): item
        for item in payloads
        if isinstance(item, Mapping) and isinstance(item.get("relative_path"), str)
    }
    result: dict[str, dict[str, object]] = {}
    for record in candidate_records:
        pdb_id = str(record["pdb_id"])
        relative = f"rcsb/structures/{pdb_id}.cif.gz"
        entry = entries.get(relative)
        if not isinstance(entry, Mapping):
            raise ValueError("CANDIDATE_PDB_CACHE_ENTRY_MISSING:" + pdb_id)
        result[pdb_id] = {
            "acquisition_status": "SOURCE_VERIFIED",
            "compressed_sha256": entry.get("sha256"),
            "compressed_byte_count": entry.get("byte_count"),
        }
    return result


def _historical_published_state(
    repo_root: Path,
) -> dict[str, Any]:
    triage_root = repo_root / triage.OUTPUT_ROOT_RELATIVE
    successor_root = repo_root / routing.OUTPUT_ROOT_RELATIVE
    candidate_rows = [
        row
        for row in _read_csv(triage_root / triage.EVENT_INVENTORY)
        if row["post_only_partition"] == triage.POST_ONLY_CANDIDATE
    ]
    packet = _read_json(triage_root / triage.REVIEW_PACKET)
    triage_summary = _read_json(triage_root / triage.SUMMARY)
    route_summary = _read_json(successor_root / routing.SUMMARY)
    route_event_rows = _read_csv(successor_root / routing.EVENT_INVENTORY)
    route_unit_rows = _read_csv(successor_root / routing.UNIT_INVENTORY)
    if len(candidate_rows) != 123 or packet.get("review_unit_count") != 36:
        raise ValueError("PUBLISHED_POST_ONLY_123_36_BASELINE_MISMATCH")
    if triage_summary.get("population", {}).get(
        "post_only_v1_review_candidate_count"
    ) != 123:
        raise ValueError("PUBLISHED_TRIAGE_SUMMARY_CANDIDATE_COUNT_MISMATCH")
    required_route = {
        "candidate_events": 123,
        "candidate_units": 36,
        "effective_new_auto_negative_events": 32,
        "effective_new_auto_negative_units": 2,
        "effective_task_domain_resolved_units": 12,
        "effective_task_domain_human_review_required_units": 24,
        "effective_task_domain_human_review_required_events": 56,
        "human_overlay_reviewed_units": 10,
        "human_overlay_unreviewed_units": 26,
    }
    for field, expected in required_route.items():
        if route_summary.get(field) != expected:
            raise ValueError("PUBLISHED_TWO_RULE_BASELINE_MISMATCH:" + field)
    if len(route_event_rows) != 246 or len(route_unit_rows) != 36:
        raise ValueError("PUBLISHED_TWO_RULE_INVENTORY_COUNT_MISMATCH")
    by_event: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in route_event_rows:
        event_id = row["canonical_event_id"]
        rule_id = row["rule_id"]
        if rule_id in by_event[event_id]:
            raise ValueError("PUBLISHED_RULE_EVENT_DUPLICATE")
        by_event[event_id][rule_id] = row
    expected_rules = set(routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS)
    if len(by_event) != 123 or any(set(rows) != expected_rules for rows in by_event.values()):
        raise ValueError("PUBLISHED_RULE_EVENT_COVERAGE_MISMATCH")
    unit_by_id = {row["review_unit_id"]: row for row in route_unit_rows}
    if len(unit_by_id) != 36:
        raise ValueError("PUBLISHED_ROUTING_UNIT_IDENTITY_MISMATCH")
    return {
        "candidate_rows": {row["canonical_event_id"]: row for row in candidate_rows},
        "route_by_event": dict(by_event),
        "unit_by_id": unit_by_id,
        "summary": route_summary,
        "packet": packet,
    }


def _validate_attempt_population(
    *,
    attempt_root: Path,
    executor_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    cumulative = _read_json(attempt_root / "cumulative_processing_view_v1.json")
    incremental = _read_json(attempt_root / "incremental_processing_outcomes_v1.json")
    result = _read_json(attempt_root / "controlled_execution_result_v1.json")
    rows = cumulative.get("events")
    if not isinstance(rows, list) or len(rows) != 500:
        raise ValueError("ATTEMPT_CUMULATIVE_500_POPULATION_INVALID")
    ranks = [item.get("scaleup_rank") for item in rows if isinstance(item, Mapping)]
    if ranks != list(range(1, 501)):
        raise ValueError("ATTEMPT_CUMULATIVE_RANK_ORDER_INVALID")
    cohort_rows = executor_inputs["cohort_rows"]
    if [item["processing_outcome"]["canonical_event_id"] for item in rows] != [
        item["canonical_event_id"] for item in cohort_rows
    ]:
        raise ValueError("ATTEMPT_COHORT_IDENTITY_OR_ORDER_MISMATCH")
    incremental_rows = incremental.get("events")
    if not isinstance(incremental_rows, list) or len(incremental_rows) != 250:
        raise ValueError("ATTEMPT_INCREMENTAL_POPULATION_INVALID")
    if [item["processing_outcome"] for item in rows[250:]] != incremental_rows:
        raise ValueError("ATTEMPT_INCREMENTAL_CUMULATIVE_PARITY_MISMATCH")
    incremental_routes = Counter(item["terminal_outcome"] for item in incremental_rows)
    expected_incremental_routes = {
        "STRUCTURAL_EVIDENCE_INCOMPLETE": 29,
        "REJECTED_FEATURE_INCOMPATIBLE": 2,
        "QUARANTINE_REPRESENTATION_GAP": 24,
        "LEAKAGE_EXISTING_GROUP_CONFLICT": 108,
        "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY": 87,
    }
    if incremental_routes != expected_incremental_routes:
        raise ValueError("ATTEMPT_INCREMENTAL_TERMINAL_ROUTE_RECONCILIATION_MISMATCH")
    if result.get("incremental_terminal_route_counts") != expected_incremental_routes:
        raise ValueError("ATTEMPT_RESULT_TERMINAL_ROUTE_COUNTS_MISMATCH")
    if result.get("execution_complete") is not False or result.get("failures") != {
        "CCD:RU8": (
            "DOWNLOADED_CCD_SCIENTIFIC_VALIDATION_FAILED:CCD_ATOM_ROW_INVALID"
        )
    }:
        raise ValueError("ATTEMPT_RESULT_FAIL_CLOSED_STATE_MISMATCH")
    outcome_by_id = {
        str(item["processing_outcome"]["canonical_event_id"]): item[
            "processing_outcome"
        ]
        for item in rows
    }
    rank_by_id = {
        str(item["processing_outcome"]["canonical_event_id"]): int(
            item["scaleup_rank"]
        )
        for item in rows
    }
    lane_by_id = {
        str(item["processing_outcome"]["canonical_event_id"]): str(item["lane"])
        for item in rows
    }
    return {
        "rows": rows,
        "outcome_by_id": outcome_by_id,
        "rank_by_id": rank_by_id,
        "lane_by_id": lane_by_id,
        "incremental_route_counts": dict(sorted(incremental_routes.items())),
    }


def _build_incremental_rule_state(
    *,
    repo_root: Path,
    candidate_ids: set[str],
    event_by_id: Mapping[str, Mapping[str, Any]],
    outcome_by_id: Mapping[str, Mapping[str, Any]],
    predecessor_bindings: Mapping[str, Any],
    cache_root: Path,
) -> dict[str, Any]:
    candidate_records = [event_by_id[event_id] for event_id in sorted(candidate_ids)]
    coordinate = triage._coordinate_audit_v1(
        candidate_events=candidate_records,
        outcome_by_id=outcome_by_id,
        acquisition=_acquisition_rows_from_ledger(
            cache_root=cache_root, candidate_records=candidate_records
        ),
        cache_root=cache_root,
    )
    rule_events: dict[str, dict[str, object]] = {}
    for event_id in sorted(candidate_ids):
        relevance, _reason = triage.classify_training_domain_relevance_v1(
            event_by_id[event_id]
        )
        rule_events[event_id] = triage._event_inventory_row(
            event=event_by_id[event_id],
            outcome=outcome_by_id[event_id],
            partition=triage.POST_ONLY_CANDIDATE,
            coordinate=coordinate[event_id],
            relevance_status=relevance,
        )
    production = routing.build_current_production_positive_context_v1(
        bindings=predecessor_bindings,
        event_by_id=rule_events,
        outcome_by_id={event_id: outcome_by_id[event_id] for event_id in candidate_ids},
    )
    if production["positive_event_ids"]:
        raise ValueError("NEW_CANDIDATE_CURRENT_PRODUCTION_POSITIVE_UNEXPECTED")
    overlay = predecessor_bindings["current_human"]
    overlay_event_ids = {
        str(event["canonical_event_id"])
        for unit in overlay["units"]
        for event in unit["events"]
    }
    if overlay_event_ids & candidate_ids:
        raise ValueError("NEW_EVENT_ALREADY_COVERED_BY_HUMAN_OVERLAY_UNEXPECTED")
    override = routing.gate.build_runtime_positive_override_context_v1(
        current_human_overlay=overlay,
        current_human_overlay_sha256=predecessor_bindings[
            "current_human_snapshot"
        ]["decisions"]["sha256"],
        outcome_by_id=production["outcome_by_id"],
    )
    contexts = {
        routing.gate.RULE_ID: predecessor_bindings["gate_manifest"][
            "scientific_rule_context"
        ],
        routing.dtt_gate.RULE_ID: predecessor_bindings["dtt_gate_manifest"][
            "scientific_rule_context"
        ],
    }
    evaluations: dict[tuple[str, str], Any] = {}
    for event_id in sorted(candidate_ids):
        results = routing.dispatch_exact_auto_negative_rules_v1(
            event=rule_events[event_id],
            outcome=production["outcome_by_id"][event_id],
            rule_context_by_id=contexts,
            override_context_by_id={rule_id: override for rule_id in contexts},
        )
        if tuple(item.rule_id for item in results) != routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS:
            raise ValueError("INCREMENTAL_RULE_DISPATCH_ORDER_MISMATCH")
        for result in results:
            evaluations[(event_id, result.rule_id)] = result
    units = bulk.build_human_review_units_v1(
        [outcome_by_id[event_id] for event_id in sorted(candidate_ids)], event_by_id
    )
    unit_by_event: dict[str, str] = {}
    routes: dict[str, Any] = {}
    for unit in units:
        unit_id = str(unit["review_unit_id"])
        event_ids = [str(value) for value in unit["canonical_event_ids"]]
        for event_id in event_ids:
            if event_id in unit_by_event:
                raise ValueError("INCREMENTAL_EVENT_IN_MULTIPLE_REVIEW_UNITS")
            unit_by_event[event_id] = unit_id
        event_evaluations = [
            evaluations[(event_id, rule_id)]
            for event_id in event_ids
            for rule_id in routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS
        ]
        blank_human = {
            "review_unit_id": unit_id,
            "workflow_status": "UNREVIEWED",
            "training_domain_relevance_decision": "",
            "events": [{"canonical_event_id": event_id} for event_id in event_ids],
        }
        routes[unit_id] = routing.route_successor_task_domain_review_unit_v1(
            review_unit=unit,
            event_evaluations=event_evaluations,
            human_unit_state=blank_human,
        )
    if set(unit_by_event) != candidate_ids:
        raise ValueError("INCREMENTAL_REVIEW_UNIT_COVERAGE_MISMATCH")
    invalid = sum(
        evaluation.status == routing.gate.INVALID_EVIDENCE
        for evaluation in evaluations.values()
    )
    if invalid or any(
        route.route_status == routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID
        for route in routes.values()
    ):
        raise ValueError("INCREMENTAL_RULE_EVIDENCE_INVALID_FAIL_CLOSED")
    return {
        "rule_events": rule_events,
        "evaluations": evaluations,
        "units": units,
        "unit_by_event": unit_by_event,
        "routes": routes,
        "new_human_resolved_event_count": 0,
    }


def _historical_route_identities(
    historical: Mapping[str, Any], route: str
) -> set[str]:
    return {
        event_id
        for event_id, rule_rows in historical["route_by_event"].items()
        if next(iter(rule_rows.values()))["unit_final_task_domain_route"] == route
    }


def _build_workload_units(
    *,
    unresolved_ids: set[str],
    historical_unresolved_ids: set[str],
    new_unresolved_ids: set[str],
    historical_unresolved_unit_ids: set[str],
    event_by_id: Mapping[str, Mapping[str, Any]],
    outcome_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, object]], dict[str, str], dict[str, int]]:
    units = bulk.build_human_review_units_v1(
        [outcome_by_id[event_id] for event_id in sorted(unresolved_ids)], event_by_id
    )
    rows: list[dict[str, object]] = []
    unit_by_event: dict[str, str] = {}
    joining_unit_count = 0
    genuinely_new_unit_count = 0
    joining_new_event_count = 0
    for unit in units:
        unit_id = str(unit["review_unit_id"])
        event_ids = [str(value) for value in unit["canonical_event_ids"]]
        historical_ids = sorted(set(event_ids) & historical_unresolved_ids)
        new_ids = sorted(set(event_ids) & new_unresolved_ids)
        for event_id in event_ids:
            if event_id in unit_by_event:
                raise ValueError("UNRESOLVED_EVENT_IN_MULTIPLE_WORKLOAD_UNITS")
            unit_by_event[event_id] = unit_id
        joins = bool(new_ids and unit_id in historical_unresolved_unit_ids)
        genuinely_new = bool(new_ids and not joins)
        joining_unit_count += joins
        genuinely_new_unit_count += genuinely_new
        joining_new_event_count += len(new_ids) if joins else 0
        lane = (
            "HISTORICAL_AND_NEW_UNRESOLVED"
            if historical_ids and new_ids
            else "HISTORICAL_UNRESOLVED"
            if historical_ids
            else "NEW_UNRESOLVED"
        )
        raw = {
            "review_unit_id": unit_id,
            "event_count": len(event_ids),
            "historical_unresolved_event_count": len(historical_ids),
            "new_unresolved_event_count": len(new_ids),
            "canonical_event_ids_json": _json_cell(event_ids),
            "historical_event_ids_json": _json_cell(historical_ids),
            "new_event_ids_json": _json_cell(new_ids),
            "pdb_ids_json": _json_cell(unit["PDB_ids"]),
            "ligand_component_ids_json": _json_cell(unit["ligand_component_ids"]),
            "reactive_atom": unit["reactive_atom"],
            "ccd_component_graph_sha256": unit["ccd_component_graph_sha256"] or "",
            "reactive_center_radius2_fingerprint": unit[
                "reactive_center_radius2_fingerprint"
            ]
            or "",
            "pre_source_graph_fingerprint": unit["pre_source_graph_fingerprint"] or "",
            "pre_reactive_center_fingerprint": unit[
                "pre_reactive_center_fingerprint"
            ]
            or "",
            "pre_status": unit["PRE_status"],
            "atom_loss_state": unit["atom_loss_state"],
            "workload_lane": lane,
            "new_events_join_existing_workload_equivalent_unit": str(joins).lower(),
            "new_genuinely_new_unit": str(genuinely_new).lower(),
            "grouping_semantics": "PUBLISHED_COVAPIE_BULK_REVIEW_UNIT_V1_WORKLOAD_ONLY",
            "effective_workload_route": routing.HUMAN_REVIEW_REQUIRED,
            "human_decision_propagated": "false",
        }
        rows.append({field: raw[field] for field in REVIEW_UNIT_HEADER})
    if set(unit_by_event) != unresolved_ids:
        raise ValueError("CUMULATIVE_UNRESOLVED_WORKLOAD_COVERAGE_MISMATCH")
    return rows, unit_by_event, {
        "new_events_joining_existing_workload_equivalent_unit_count": (
            joining_new_event_count
        ),
        "new_units_joining_existing_workload_equivalent_unit_count": (
            joining_unit_count
        ),
        "new_genuinely_new_unit_count": genuinely_new_unit_count,
    }


def _eligibility_reason(outcome: Mapping[str, Any], partition: str) -> str:
    stage = outcome.get("stage_statuses", {}).get(
        "BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"
    )
    if partition == triage.POST_ONLY_CANDIDATE:
        return (
            "PUBLISHED_POST_ONLY_ELIGIBILITY:FEATURE_STAGE_PASSED_AND_"
            "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY"
        )
    return (
        "PUBLISHED_POST_ONLY_INELIGIBILITY:FEATURE_STAGE="
        + str(stage)
        + ";TERMINAL_OUTCOME="
        + str(outcome.get("terminal_outcome"))
    )


def build_artifacts_v1(*, repo_root: Path) -> dict[str, bytes]:
    """Build exactly four deterministic artifacts entirely from bound evidence."""

    repo_root = repo_root.resolve()
    verify_repository_state_v1(repo_root)
    bindings_before = verify_bound_inputs_v1(repo_root)
    executor_inputs = executor.load_published_executor_inputs_v1(repo_root)
    cache_stable, cache_snapshot_before = verify_canonical_cache_read_only_v1(
        repo_root, executor_inputs
    )
    attempt_root = repo_root.parent / ATTEMPT_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    attempt = _validate_attempt_population(
        attempt_root=attempt_root, executor_inputs=executor_inputs
    )
    historical = _historical_published_state(repo_root)

    event_by_id = {
        str(event["canonical_event_id"]): event
        for event in executor_inputs["cohort_records"]
    }
    outcome_by_id = attempt["outcome_by_id"]
    rank_by_id = attempt["rank_by_id"]
    if set(event_by_id) != set(outcome_by_id):
        raise ValueError("CUMULATIVE_CANONICAL_OUTCOME_IDENTITY_MISMATCH")
    partitions = {
        event_id: supported_post_only_partition_v1(outcome_by_id[event_id])
        for event_id in sorted(outcome_by_id)
    }
    candidate_ids = {
        event_id
        for event_id, partition in partitions.items()
        if partition == triage.POST_ONLY_CANDIDATE
    }
    historical_candidate_ids = {
        event_id for event_id in candidate_ids if rank_by_id[event_id] <= 250
    }
    incremental_candidate_ids = candidate_ids - historical_candidate_ids
    published_historical_candidate_ids = set(historical["candidate_rows"])
    if historical_candidate_ids != published_historical_candidate_ids:
        raise ValueError("HISTORICAL_123_CANDIDATE_IDENTITY_PARITY_MISMATCH")
    if len(incremental_candidate_ids) != 87:
        incremental_science = Counter(
            (
                outcome_by_id[event_id].get("stage_statuses", {}).get(
                    "BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"
                ),
                outcome_by_id[event_id].get("terminal_outcome"),
            )
            for event_id in outcome_by_id
            if rank_by_id[event_id] > 250
        )
        raise ValueError(
            "INCREMENTAL_CANDIDATE_COUNT_NOT_87_SCIENTIFIC_DISTRIBUTION:"
            + _json_cell(sorted((list(key), value) for key, value in incremental_science.items()))
        )
    if len(candidate_ids) != 210 or len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("CUMULATIVE_CANDIDATE_210_RECONCILIATION_MISMATCH")

    rank_493_id = next(
        event_id for event_id, rank in rank_by_id.items() if rank == 493
    )
    rank_493_outcome = outcome_by_id[rank_493_id]
    if not (
        rank_493_id == "COVAPIE_CYS_SG_EVENT_V1:3NPL:B:CYS:97-:SG:F:RU8:C49"
        and rank_493_outcome.get("terminal_outcome") == "STRUCTURAL_EVIDENCE_INCOMPLETE"
        and rank_493_outcome.get("terminal_reasons")
        == ["REQUIRED_CCD_PAYLOAD_UNAVAILABLE"]
        and rank_493_id not in candidate_ids
        and partitions[rank_493_id] == triage.OUTSIDE_STRUCTURAL
    ):
        raise ValueError("RANK_493_FAIL_CLOSED_NATURAL_EXCLUSION_MISMATCH")

    incremental = _build_incremental_rule_state(
        repo_root=repo_root,
        candidate_ids=incremental_candidate_ids,
        event_by_id=event_by_id,
        outcome_by_id=outcome_by_id,
        predecessor_bindings=bindings_before["predecessor"],
        cache_root=executor.canonical_controlled_cache_root_v1(repo_root),
    )

    historical_unresolved_ids = set().union(
        *(
            _historical_route_identities(historical, route)
            for route in UNRESOLVED_ROUTES
        )
    )
    new_unresolved_ids = {
        event_id
        for event_id in incremental_candidate_ids
        if incremental["routes"][incremental["unit_by_event"][event_id]].route_status
        in UNRESOLVED_ROUTES
    }
    historical_unresolved_unit_ids = {
        unit_id
        for unit_id, row in historical["unit_by_id"].items()
        if row["final_task_domain_route"] in UNRESOLVED_ROUTES
    }
    workload_rows, workload_by_event, workload_join_metrics = _build_workload_units(
        unresolved_ids=historical_unresolved_ids | new_unresolved_ids,
        historical_unresolved_ids=historical_unresolved_ids,
        new_unresolved_ids=new_unresolved_ids,
        historical_unresolved_unit_ids=historical_unresolved_unit_ids,
        event_by_id=event_by_id,
        outcome_by_id=outcome_by_id,
    )

    event_rows: list[dict[str, object]] = []
    for event_id in sorted(outcome_by_id, key=lambda value: rank_by_id[value]):
        outcome = outcome_by_id[event_id]
        partition = partitions[event_id]
        eligible = partition == triage.POST_ONLY_CANDIDATE
        historical_lane = rank_by_id[event_id] <= 250
        route_unit_id = ""
        selected_rule = ""
        human_lane = "NONE"
        if eligible and historical_lane:
            published_rules = historical["route_by_event"][event_id]
            ts = published_rules[routing.gate.RULE_ID]
            dtt = published_rules[routing.dtt_gate.RULE_ID]
            route_unit_id = ts["review_unit_id"]
            if dtt["review_unit_id"] != route_unit_id:
                raise ValueError("HISTORICAL_RULE_REVIEW_UNIT_DRIFT")
            unit = historical["unit_by_id"][route_unit_id]
            selected_rule = unit["selected_auto_negative_rule_id"]
            effective_route = ts["unit_final_task_domain_route"]
            effective_reason = ts["unit_final_route_reason"]
            if effective_route in {
                routing.HUMAN_NOT_RELEVANT_FINAL,
                routing.HUMAN_RELEVANT_FINAL,
            }:
                human_lane = "PUBLISHED_HISTORICAL_EXACT_EVENT_SCOPE"
            candidate_lane = "HISTORICAL_PREDECESSOR_CANDIDATE"
        elif eligible:
            ts_eval = incremental["evaluations"][(event_id, routing.gate.RULE_ID)]
            dtt_eval = incremental["evaluations"][(event_id, routing.dtt_gate.RULE_ID)]
            route_unit_id = incremental["unit_by_event"][event_id]
            route = incremental["routes"][route_unit_id]
            selected_rule = route.auto_negative_rule_id
            effective_route = route.route_status
            effective_reason = route.route_reason
            ts = {"gate_event_status": ts_eval.status, "gate_event_reason": ts_eval.reason}
            dtt = {
                "gate_event_status": dtt_eval.status,
                "gate_event_reason": dtt_eval.reason,
            }
            human_lane = "NO_NEW_HUMAN_AUTHORITY"
            candidate_lane = "NEW_INCREMENTAL_CANDIDATE"
        else:
            ts = {"gate_event_status": NOT_EVALUATED, "gate_event_reason": NOT_EVALUATED}
            dtt = {"gate_event_status": NOT_EVALUATED, "gate_event_reason": NOT_EVALUATED}
            effective_route = str(outcome["terminal_outcome"])
            effective_reason = "BOUND_STRUCTURAL_EXECUTION_OUTCOME_RETAINED"
            candidate_lane = (
                "HISTORICAL_PREDECESSOR_EXCLUDED"
                if historical_lane
                else "NEW_INCREMENTAL_EXCLUDED"
            )
        raw = {
            "scaleup_rank": rank_by_id[event_id],
            "canonical_event_id": event_id,
            "pdb_id": event_by_id[event_id]["pdb_id"],
            "ligand_component_id": event_by_id[event_id]["ligand_component_id"],
            "ligand_reactive_atom": event_by_id[event_id]["ligand_reactive_atom"],
            "execution_lane": attempt["lane_by_id"][event_id],
            "candidate_lane": candidate_lane,
            "raw_terminal_outcome": outcome["terminal_outcome"],
            "raw_terminal_reasons_json": _json_cell(outcome["terminal_reasons"]),
            "feature_compatibility_stage_status": outcome["stage_statuses"][
                "BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"
            ],
            "post_only_candidate_eligibility": str(eligible).lower(),
            "post_only_partition": partition,
            "eligibility_reason": _eligibility_reason(outcome, partition),
            "routing_review_unit_id": route_unit_id,
            "workload_review_unit_id": workload_by_event.get(event_id, ""),
            "ts_dump_rule_id": routing.gate.RULE_ID,
            "ts_dump_rule_status": ts["gate_event_status"],
            "ts_dump_rule_reason": ts["gate_event_reason"],
            "dtt_rule_id": routing.dtt_gate.RULE_ID,
            "dtt_rule_status": dtt["gate_event_status"],
            "dtt_rule_reason": dtt["gate_event_reason"],
            "selected_effective_rule_id": selected_rule,
            "effective_route": effective_route,
            "effective_route_reason": effective_reason,
            "human_authority_lane": human_lane,
            "human_decision_propagated_to_new_event": "false",
        }
        event_rows.append({field: raw[field] for field in EVENT_HEADER})

    event_payload = _csv_bytes(EVENT_HEADER, event_rows)
    workload_payload = _csv_bytes(REVIEW_UNIT_HEADER, workload_rows)
    partition_by_lane: dict[str, dict[str, int]] = {}
    raw_routes_by_lane: dict[str, dict[str, int]] = {}
    for lane, rank_predicate in (
        ("historical_1_250", lambda value: value <= 250),
        ("incremental_251_500", lambda value: value > 250),
        ("cumulative_1_500", lambda _value: True),
    ):
        ids = [event_id for event_id in outcome_by_id if rank_predicate(rank_by_id[event_id])]
        partition_by_lane[lane] = dict(
            sorted(Counter(partitions[event_id] for event_id in ids).items())
        )
        raw_routes_by_lane[lane] = dict(
            sorted(Counter(outcome_by_id[event_id]["terminal_outcome"] for event_id in ids).items())
        )
    raw_rule_metrics: dict[str, dict[str, int]] = {}
    effective_rule_metrics: dict[str, dict[str, int]] = {}
    for rule_id in routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS:
        rule_evaluations = [
            incremental["evaluations"][(event_id, rule_id)]
            for event_id in incremental_candidate_ids
        ]
        raw_rule_metrics[rule_id] = dict(
            sorted(Counter(item.status for item in rule_evaluations).items())
        )
        selected_routes = [
            route
            for route in incremental["routes"].values()
            if route.route_status == routing.AUTO_NEGATIVE_EXACT_FINAL
            and route.auto_negative_rule_id == rule_id
        ]
        effective_rule_metrics[rule_id] = {
            "events": sum(route.event_count for route in selected_routes),
            "units": len(selected_routes),
        }
    historical_auto_ids = _historical_route_identities(
        historical, routing.AUTO_NEGATIVE_EXACT_FINAL
    )
    historical_human_resolved_ids = _historical_route_identities(
        historical, routing.HUMAN_NOT_RELEVANT_FINAL
    ) | _historical_route_identities(historical, routing.HUMAN_RELEVANT_FINAL)
    new_auto_ids = {
        event_id
        for event_id in incremental_candidate_ids
        if incremental["routes"][incremental["unit_by_event"][event_id]].route_status
        == routing.AUTO_NEGATIVE_EXACT_FINAL
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "snapshot_semantics": SNAPSHOT_SEMANTICS,
        "published_predecessor_bindings": bindings_before["published"],
        "published_executor_baseline_bindings": executor_inputs["bindings"],
        "attempt_001_immutable_execution_bindings": bindings_before["attempt_001"],
        "canonical_cache_read_only_binding": cache_stable,
        "published_ts_dump_gate_artifact_bindings": bindings_before[
            "predecessor"
        ]["published_gate"],
        "published_dtt_gate_artifact_bindings": bindings_before[
            "predecessor"
        ]["published_dtt_gate"],
        "current_human_snapshot_binding": bindings_before["predecessor"][
            "current_human_snapshot"
        ],
        "current_production_exact_positive_authority_binding": bindings_before[
            "predecessor"
        ]["current_production_authority_binding"],
        "published_historical_candidate_contract": {
            "candidate_event_count": 123,
            "review_unit_count": 36,
            "historical_candidate_identity_sha256": _sha(
                _json_bytes(sorted(historical_candidate_ids))
            ),
            "scientific_triage_recomputed": False,
        },
        "integrated_exact_rule_ids": list(routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS),
        "historical_routing_authority": "PUBLISHED_TWO_RULE_SUCCESSOR_IMMUTABLE",
        "incremental_rule_evaluation": (
            "PUBLISHED_EVALUATORS_AND_PUBLISHED_SCIENTIFIC_CONTEXTS_EXACT"
        ),
        "review_unit_grouping": (
            "PUBLISHED_COVAPIE_BULK_REVIEW_UNIT_V1_FOR_WORKLOAD_ONLY"
        ),
        "human_authority_scope": (
            "PUBLISHED_EXACT_HISTORICAL_EVENT_IDENTITIES_ONLY_NO_NEW_PROPAGATION"
        ),
        "output_sha256_excluding_manifest_and_summary": {
            EVENT_INVENTORY: _sha(event_payload),
            REVIEW_UNIT_INVENTORY: _sha(workload_payload),
        },
        "network_performed": False,
        "canonical_bulk_cache_modified": False,
        "attempt_002_created": False,
        "production_authority_created": False,
        "training_materialization_performed": False,
    }
    manifest_payload = _json_bytes(manifest)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "population": {
            "historical_post_only_candidate_count": len(historical_candidate_ids),
            "incremental_post_only_candidate_count": len(incremental_candidate_ids),
            "cumulative_post_only_candidate_count": len(candidate_ids),
            "candidate_identities_unique": len(candidate_ids) == len(set(candidate_ids)),
            "historical_123_identity_set_exact": (
                historical_candidate_ids == published_historical_candidate_ids
            ),
            "partition_counts_by_lane": partition_by_lane,
            "raw_terminal_route_counts_by_lane": raw_routes_by_lane,
            "cumulative_raw_route_reconciliation": sum(
                raw_routes_by_lane["cumulative_1_500"].values()
            )
            == 500,
        },
        "rank_493_fail_closed_evidence": {
            "scaleup_rank": 493,
            "canonical_event_id": rank_493_id,
            "terminal_outcome": rank_493_outcome["terminal_outcome"],
            "terminal_reason": rank_493_outcome["terminal_reasons"][0],
            "post_only_partition": partitions[rank_493_id],
            "post_only_candidate_eligible": False,
            "excluded_by_generic_published_eligibility": True,
            "special_case_used": False,
            "retry_performed": False,
        },
        "historical_two_rule_routing": {
            "candidate_events": 123,
            "candidate_units": 36,
            "effective_auto_negative_events": len(historical_auto_ids),
            "effective_auto_negative_units": 2,
            "human_resolved_events": len(historical_human_resolved_ids),
            "human_resolved_units": 10,
            "unresolved_events": len(historical_unresolved_ids),
            "unresolved_units": len(historical_unresolved_unit_ids),
            "published_routing_modified": False,
            "semantic_identity_parity": True,
        },
        "incremental_two_rule_routing": {
            "candidate_events": len(incremental_candidate_ids),
            "candidate_units": len(incremental["units"]),
            "raw_rule_status_counts": raw_rule_metrics,
            "effective_auto_negative_by_rule": effective_rule_metrics,
            "new_TS_auto_negative_event_count": effective_rule_metrics[
                routing.gate.RULE_ID
            ]["events"],
            "new_DTT_auto_negative_event_count": effective_rule_metrics[
                routing.dtt_gate.RULE_ID
            ]["events"],
            "new_effective_auto_negative_event_count": len(new_auto_ids),
            "new_effective_auto_negative_unit_count": sum(
                route.route_status == routing.AUTO_NEGATIVE_EXACT_FINAL
                for route in incremental["routes"].values()
            ),
            "new_human_resolved_event_count": incremental[
                "new_human_resolved_event_count"
            ],
            "new_unresolved_human_review_event_count": len(new_unresolved_ids),
            "human_decision_propagated": False,
        },
        "cumulative_two_rule_routing": {
            "effective_auto_negative_event_count": len(historical_auto_ids | new_auto_ids),
            "human_resolved_event_count": len(historical_human_resolved_ids),
            "unresolved_human_review_event_count": len(
                historical_unresolved_ids | new_unresolved_ids
            ),
        },
        "human_review_workload": {
            "historical_unresolved_event_count": len(historical_unresolved_ids),
            "historical_unresolved_review_unit_count": len(
                historical_unresolved_unit_ids
            ),
            "new_unresolved_event_count": len(new_unresolved_ids),
            "new_unresolved_review_unit_count": len(
                {
                    workload_by_event[event_id]
                    for event_id in new_unresolved_ids
                }
            ),
            "cumulative_unresolved_event_count": len(
                historical_unresolved_ids | new_unresolved_ids
            ),
            "cumulative_unresolved_review_unit_count": len(workload_rows),
            **workload_join_metrics,
            "grouping_creates_chemistry_authority": False,
            "human_decisions_created": False,
        },
        "safety": {
            "abandoned_transition_metal_policy_files_removed": True,
            "RU8_retry_performed": False,
            "attempt_002_created": False,
            "RU8_special_case_used": False,
            "historical_two_rule_routing_modified": False,
            "human_overlay_modified": False,
            "production_authority_created": False,
            "canonical_bulk_cache_modified": False,
            "network_performed": False,
            "training_materialization_performed": False,
        },
        "output_sha256_excluding_summary": {
            MANIFEST: _sha(manifest_payload),
            EVENT_INVENTORY: _sha(event_payload),
            REVIEW_UNIT_INVENTORY: _sha(workload_payload),
        },
        "ready_for_gpt_review": True,
        "recommended_next_step_exactly": (
            "gpt_audit_cumulative_500_two_rule_routing_then_choose_next_"
            "human_review_batch_or_model_integration_step"
        ),
    }
    summary_payload = _json_bytes(summary)

    if verify_bound_inputs_v1(repo_root)["attempt_001"] != bindings_before["attempt_001"]:
        raise ValueError("ATTEMPT_001_MODIFIED_DURING_BUILD")
    if executor.snapshot_cache_tree_v1(
        executor.canonical_controlled_cache_root_v1(repo_root)
    ) != cache_snapshot_before:
        raise ValueError("CANONICAL_CACHE_MODIFIED_DURING_BUILD")
    verify_repository_state_v1(repo_root)
    return {
        MANIFEST: manifest_payload,
        EVENT_INVENTORY: event_payload,
        REVIEW_UNIT_INVENTORY: workload_payload,
        SUMMARY: summary_payload,
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_v1(
    *, repo_root: Path, output_root: Path | None = None
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target = (
        output_root.resolve()
        if output_root is not None
        else repo_root / OUTPUT_ROOT_RELATIVE
    )
    if target != repo_root / OUTPUT_ROOT_RELATIVE:
        try:
            target.relative_to(Path(tempfile.gettempdir()).resolve())
        except ValueError as error:
            raise ValueError("OUTPUT_ROOT_OUTSIDE_AUTHORIZED_PATH") from error
    artifacts = build_artifacts_v1(repo_root=repo_root)
    for name in OUTPUT_FILENAMES:
        _atomic_write(target / name, artifacts[name])
    return json.loads(artifacts[SUMMARY])


def verify_deterministic_replay_v1(repo_root: Path) -> dict[str, str]:
    repo_root = repo_root.resolve()
    output_root = repo_root / OUTPUT_ROOT_RELATIVE
    observed = {name: (output_root / name).read_bytes() for name in OUTPUT_FILENAMES}
    replay = build_artifacts_v1(repo_root=repo_root)
    result: dict[str, str] = {}
    for name in OUTPUT_FILENAMES:
        if observed[name] != replay[name]:
            raise ValueError("OUTPUT_NOT_BYTE_IDENTICAL_ON_REPLAY:" + name)
        result[name] = _sha(observed[name])
    return result

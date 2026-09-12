#!/usr/bin/env python3
"""Check the read-only FFQ Exact8/current-formal-population binding."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_ffq_exact8_current_formal_population_linkage_binding_v1 as binding,
)


def _axis_summary(rows: object) -> dict[str, dict[str, int]]:
    return {
        row.axis: {
            "logical_pairs": row.logical_pair_count,
            "current_evidence_judged_logical_pairs": (
                row.current_evidence_judged_logical_pair_count
            ),
            "policy_short_circuit_logical_pairs": (
                row.policy_short_circuit_logical_pair_count
            ),
            "unknown_logical_pairs": row.unknown_logical_pair_count,
            "frozen_report_coverage_overlap_pairs": (
                row.frozen_report_coverage_overlap_pair_count
            ),
            "positive": row.positive_pair_count,
            "negative": row.negative_pair_count,
        }
        for row in rows
    }


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("this checker accepts no arguments and never writes")
    inputs = binding.load_covapie_ffq_exact8_current_formal_population_linkage_binding_inputs_v1(
        repo_root=ROOT,
    )
    first = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(inputs)
    binding.validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        first, inputs=inputs,
    )
    second = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(inputs)
    if binding.canonical_json_bytes_v1(first) != binding.canonical_json_bytes_v1(second):
        raise SystemExit("non-deterministic binding result")
    universe_by_id = {
        event.canonical_event_id: event for event in inputs.universe_events
    }
    disposition_event_ids = {
        row.canonical_event_id for row in inputs.training_dispositions
    }
    non_ffq_disposition_event_ids = {
        event_id for event_id in disposition_event_ids
        if universe_by_id[event_id].ligand_component_id != "FFQ"
    }
    if (
        first.current_formal_group_count != 15
        or first.current_formal_identity_count != 48
        or first.old_formal_scope_event_count != 57
        or first.current_formal_event_count != 109
        or first.predictor_universe_event_count != 1027
        or len(first.specified_seed_event_ids) != 8
        or not set(first.specified_seed_event_ids) <= set(first.closure_event_ids)
        or dict(first.permissions) != dict(binding._PERMISSIONS_V1)
        or not set(first.specified_seed_event_ids) <= disposition_event_ids
        or not non_ffq_disposition_event_ids
        or first.formal_population_comparison_complete is not True
        or first.binding_status not in {
            binding.STATUS_COMPLETE_NO_LINKAGE,
            binding.STATUS_COMPLETE_WITH_LINKAGE,
            binding.STATUS_INCOMPLETE,
            binding.STATUS_CROSS_SPLIT_CONFLICT,
        }
    ):
        raise SystemExit("binding contract check failed")

    unknown_patterns = Counter(
        relation.unknown_axes for relation in first.closure_unknown_relations
    )
    summary = {
        "schema_version": first.schema_version,
        "binding_status": first.binding_status,
        "checker_validation_execution": {
            "compute_invocation_count": 3,
            "validator_recomputed_result": True,
            "coverage_counts_describe_one_compute_semantic_result": True,
            "actual_comparator_call_count_reported": False,
        },
        "predictor_universe": {
            "event_count": first.predictor_universe_event_count,
            "lane_counts": dict(first.predictor_lane_counts),
            "event_inventory_sha256": first.predictor_universe_event_inventory_sha256,
        },
        "current_formal_population": {
            "group_count": first.current_formal_group_count,
            "event_count": first.current_formal_event_count,
            "identity_count": first.current_formal_identity_count,
            "groups": [
                {
                    "formal_group_id": group.formal_group_id,
                    "formal_split": group.formal_split,
                    "full_event_count": group.full_event_count,
                    "member_identity_count": group.member_identity_count,
                    "old_scope_event_count": len(group.old57_member_canonical_event_ids),
                    "membership_sources": list(group.membership_sources),
                    "identifier_lineage": list(group.identifier_lineage),
                }
                for group in first.formal_groups
            ],
        },
        "old_scope_to_complete_scope": {
            "old_event_count": first.old_formal_scope_event_count,
            "added_event_count": len(first.formal_population_added_event_ids),
            "added_event_ids": list(first.formal_population_added_event_ids),
        },
        "component_closure": {
            "specified_seed_count": len(first.specified_seed_event_ids),
            "specified_seed_event_ids": list(first.specified_seed_event_ids),
            "actual_closure_count": len(first.closure_event_ids),
            "actual_closure_event_ids": list(first.closure_event_ids),
            "closure_exceeds_exact8": len(first.closure_event_ids) > 8,
            "newly_discovered_event_ids": list(first.newly_discovered_linked_event_ids),
            "verified_positive_edge_count": len(first.verified_component_edges),
            "unknown_boundary_relation_count": len(first.closure_unknown_relations),
            "unknown_boundary_event_count": len({
                row.universe_event_id for row in first.closure_unknown_relations
            }),
            "unknown_axis_patterns": {
                "+".join(key): value for key, value in sorted(unknown_patterns.items())
            },
            "closure_complete_within_frozen_universe": (
                first.closure_complete_within_frozen_universe
            ),
        },
        "universe_axis_coverage": _axis_summary(first.universe_axis_coverage),
        "formal_population_axis_coverage": _axis_summary(
            first.formal_population_axis_coverage
        ),
        "formal_reachability": {
            "formal_population_comparison_complete": (
                first.formal_population_comparison_complete
            ),
            "reachable_formal_group_ids": list(first.reachable_formal_group_ids),
            "reachable_formal_splits": list(first.reachable_formal_splits),
            "cross_split_conflict": first.cross_split_conflict,
        },
        "dispositions": {
            "current_global_census_readback_scope": {
                "scope": "ALL_FROZEN_PREDICTOR_UNIVERSE_EVENT_IDS",
                "loaded_event_count": len(disposition_event_ids),
                "loaded_non_ffq_event_count": len(non_ffq_disposition_event_ids),
                "universe_event_count_without_readback": (
                    len(universe_by_id) - len(disposition_event_ids)
                ),
                "only_specified_seeds_are_required": True,
            },
            "linkage_closure_complete_within_frozen_universe": (
                first.closure_complete_within_frozen_universe
            ),
            "seed_readback_complete": first.seed_disposition_readback_complete,
            "newly_discovered_readback_complete": (
                first.newly_discovered_disposition_readback_complete
            ),
            "closure_readback_complete": first.closure_disposition_readback_complete,
            "specified_seeds": [asdict(row) for row in first.seed_training_dispositions],
            "newly_discovered_events": [
                asdict(row) for row in first.newly_discovered_training_dispositions
            ],
            "newly_discovered_missing_event_ids": list(
                first.newly_discovered_missing_disposition_event_ids
            ),
        },
        "semantic_digests": {
            "source": first.source_semantic_sha256,
            "formal_authority_sources": first.formal_authority_source_binding_sha256,
            "output": first.output_semantic_sha256,
        },
        "permissions": dict(first.permissions),
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

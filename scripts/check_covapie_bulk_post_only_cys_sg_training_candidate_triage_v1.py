#!/usr/bin/env python3
"""Fail-closed checker for the CovaPIE post-only CYS-SG triage lane."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from covalent_ext import (
    covapie_bulk_post_only_cys_sg_training_candidate_triage_v1 as triage,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _csv(path: Path, header: Sequence[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _assert(tuple(reader.fieldnames or ()) == tuple(header), path.name + " header")
        rows = list(reader)
    _assert(
        all(tuple(row) == tuple(header) and all(value is not None for value in row.values()) for row in rows),
        path.name + " row schema",
    )
    return rows


def check_v1(repo_root: Path, cache_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    cache_root = cache_root.resolve()
    output_root = repo_root / triage.OUTPUT_ROOT_RELATIVE
    _assert(output_root.is_dir(), "output directory missing")
    actual_names = {path.name for path in output_root.iterdir() if path.is_file()}
    _assert(actual_names == set(triage.OUTPUT_FILENAMES), "output file set mismatch")

    git_state = triage.verify_base_git_binding_v1(repo_root)
    input_hashes = triage.verify_bound_inputs_v1(repo_root)
    cache_before = triage.task_cache_content_digest_v1(cache_root)
    expected = triage.build_artifacts_v1(repo_root=repo_root, cache_root=cache_root)
    output_hashes: dict[str, str] = {}
    for name in triage.OUTPUT_FILENAMES:
        payload = (output_root / name).read_bytes()
        _assert(payload == expected[name], "deterministic replay mismatch: " + name)
        output_hashes[name] = hashlib.sha256(payload).hexdigest()
    cache_after = triage.task_cache_content_digest_v1(cache_root)
    _assert(cache_after == cache_before, "task cache changed during checker")
    _assert(triage.verify_bound_inputs_v1(repo_root) == input_hashes, "inputs changed")

    events = _csv(output_root / triage.EVENT_INVENTORY, triage.EVENT_HEADER)
    units = _csv(output_root / triage.REVIEW_UNIT_INVENTORY, triage.REVIEW_UNIT_HEADER)
    evidence = _csv(output_root / triage.DOMAIN_EVIDENCE, triage.DOMAIN_EVIDENCE_HEADER)
    summary = json.loads((output_root / triage.SUMMARY).read_text(encoding="utf-8"))
    packet = json.loads((output_root / triage.REVIEW_PACKET).read_text(encoding="utf-8"))

    partitions = Counter(row["post_only_partition"] for row in events)
    _assert(len(events) == 2387, "canonical population is not 2387")
    _assert(partitions[triage.KNOWN_EXISTING] == 27, "known population is not 27")
    _assert(
        len(events) - partitions[triage.KNOWN_EXISTING] == 2360,
        "new population is not 2360",
    )
    _assert(partitions[triage.POST_ONLY_CANDIDATE] == 123, "candidate count is not 123")
    _assert(partitions[triage.BLOCKED_LEAKAGE] == 88, "leakage block count is not 88")
    _assert(
        partitions[triage.BLOCKED_REPRESENTATION] == 7,
        "representation block count is not 7",
    )
    _assert(partitions[triage.OUTSIDE_STRUCTURAL] == 2142, "outside count is not 2142")
    _assert(2387 == 27 + 2360, "canonical arithmetic")
    _assert(2360 == 218 + 2142, "new arithmetic")
    _assert(218 == 123 + 88 + 7, "structural arithmetic")

    candidate_rows = [
        row for row in events if row["post_only_partition"] == triage.POST_ONLY_CANDIDATE
    ]
    candidate_ids = {row["canonical_event_id"] for row in candidate_rows}
    _assert(len(candidate_ids) == 123, "candidate IDs are not unique")
    _assert(
        all(row["population_status"] == "NEW_UNIQUE_CANDIDATE_EVENT" for row in candidate_rows),
        "known event entered candidate lane",
    )
    _assert(
        all(row["terminal_outcome"] == "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY" for row in candidate_rows),
        "leakage or representation block entered candidate lane",
    )
    _assert(
        all(
            row["structural_model_eligible"] == "true"
            and row["feature_compatible"] == "true"
            and row["explicit_cys_sg_event"] == "true"
            and row["usable_post_complex_structural_evidence"] == "true"
            and row[
                "exact_ccd_observed_heavy_atom_identity_coverage"
            ] == "true"
            and row[
                "exact_ccd_observed_heavy_atom_element_agreement"
            ] == "true"
            and row["reactive_ligand_atom_exact_coverage"] == "true"
            and bool(row["observed_heavy_atom_map_sha256"])
            and bool(row["ccd_heavy_atom_map_sha256"])
            for row in candidate_rows
        ),
        "candidate exact atom-wise structural contract",
    )
    _assert(
        {row["pre_status"] for row in candidate_rows}
        == {"PRE_REACTION_UNRESOLVED", "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"},
        "real PRE diagnostic population changed",
    )
    _assert(
        all(row["pre_status_diagnostic_only_for_post_only_triage"] == "true" for row in candidate_rows),
        "PRE status treated as exclusion",
    )
    _assert(
        all(row["training_domain_relevance_human_review_required"] == "true" for row in candidate_rows),
        "candidate human-review requirement missing",
    )

    unit_event_ids: list[str] = []
    for unit in units:
        values = json.loads(unit["canonical_event_ids_json"])
        _assert(int(unit["event_count"]) == len(values), "unit event count")
        unit_event_ids.extend(values)
        _assert(unit["predecessor_review_unit_reused"] == "true", "unit not reused")
        _assert(unit["chemistry_identity_boundary_validated"] == "true", "unit boundary")
        _assert(unit["production_approval_created"] == "false", "unit approval")
        _assert(
            all(unit[field] == "" for field in triage.UNIT_HUMAN_DECISION_FIELDS),
            "CSV unit human decision prefilled",
        )
        _assert(
            "post_geometry_training_usable" not in unit,
            "event geometry decision leaked into unit-level CSV fields",
        )
        _assert(int(unit["events_for_review_count"]) == len(values), "CSV event review count")
        _assert(int(unit["ccd_heavy_atom_inventory_count"]) > 0, "CSV CCD atoms")
        _assert(int(unit["ccd_bond_inventory_count"]) > 0, "CSV CCD bonds")
        _assert(
            int(unit["representative_observed_heavy_atom_coordinate_count"])
            == int(unit["ccd_heavy_atom_inventory_count"]),
            "CSV representative exact atom count",
        )
    _assert(len(units) == 36, "review unit count is not 36")
    _assert(len(unit_event_ids) == len(set(unit_event_ids)), "duplicate event across units")
    _assert(set(unit_event_ids) == candidate_ids, "unit event loss or addition")
    _assert(len(packet["review_units"]) == 36, "packet unit count")
    packet_ids: list[str] = []
    packet_event_ids: list[str] = []
    multi_event_unit_count = 0
    events_inside_multi_event_units = 0
    for unit in packet["review_units"]:
        packet_ids.extend(unit["canonical_event_ids"])
        _assert(
            all(unit[field] == "" for field in triage.UNIT_HUMAN_DECISION_FIELDS),
            "packet unit human decision prefilled",
        )
        _assert(
            "post_geometry_training_usable" not in {
                field for field in triage.UNIT_HUMAN_DECISION_FIELDS
            }
            and "post_geometry_training_usable" not in unit,
            "unit-level post geometry decision present",
        )
        _assert(unit["production_approval_created"] is False, "packet approval")
        machine = unit["machine_chemistry_evidence"]
        ccd_all_atoms = machine["ccd_atom_inventory"]
        ccd_atoms = machine["ccd_heavy_atom_inventory"]
        ccd_bonds = machine["ccd_bond_inventory"]
        observed = machine["representative_observed_ligand_atom_coordinates"]
        _assert(
            ccd_all_atoms and ccd_atoms and ccd_bonds and observed,
            "packet chemistry evidence",
        )
        all_ccd_ids = {atom["atom_id"] for atom in ccd_all_atoms}
        _assert(
            all(
                bond["atom_id_1"] in all_ccd_ids
                and bond["atom_id_2"] in all_ccd_ids
                for bond in ccd_bonds
            ),
            "packet CCD bond endpoint missing from complete atom inventory",
        )
        ccd_by_id = {atom["atom_id"]: atom for atom in ccd_atoms}
        observed_by_id = {atom["atom_id"]: atom for atom in observed}
        _assert(len(ccd_by_id) == len(ccd_atoms), "packet duplicate CCD atom")
        _assert(len(observed_by_id) == len(observed), "packet duplicate observed atom")
        _assert(set(ccd_by_id) == set(observed_by_id), "packet atom ID set mismatch")
        _assert(
            all(
                ccd_by_id[atom_id]["element"] == observed_by_id[atom_id]["element"]
                for atom_id in ccd_by_id
            ),
            "packet atom element mismatch",
        )
        reactive = machine["reactive_atom_evidence"]
        reactive_id = reactive["ligand_reactive_atom"]
        _assert(reactive_id in ccd_by_id, "packet reactive atom missing")
        _assert(
            reactive["reactive_atom_ccd_record"] == ccd_by_id[reactive_id],
            "packet reactive atom record",
        )
        review_events = unit["events_for_review"]
        _assert(
            [event["canonical_event_id"] for event in review_events]
            == unit["canonical_event_ids"],
            "events_for_review unit coverage",
        )
        if len(review_events) > 1:
            multi_event_unit_count += 1
            events_inside_multi_event_units += len(review_events)
        for event in review_events:
            packet_event_ids.append(event["canonical_event_id"])
            _assert(
                all(event[field] == "" for field in triage.EVENT_HUMAN_DECISION_FIELDS),
                "packet event human decision prefilled",
            )
            _assert(
                event["pre_status_role"]
                == "DIAGNOSTIC_NOT_A_POST_ONLY_ELIGIBILITY_HARD_BLOCKER",
                "event PRE role",
            )
    _assert(packet_ids == unit_event_ids, "packet and CSV unit order/content mismatch")
    _assert(len(packet_event_ids) == len(set(packet_event_ids)) == 123, "event review duplicate")
    _assert(set(packet_event_ids) == candidate_ids, "event review coverage")
    _assert(multi_event_unit_count == 25, "multi-event unit count")
    _assert(events_inside_multi_event_units == 112, "events in multi-event units")

    predecessor_clusters = json.loads(
        (
            repo_root / triage.INPUT_ROOT_RELATIVE
            / "bulk_human_review_clusters_v1.json"
        ).read_text(encoding="utf-8")
    )["clusters"]
    packet_unit_by_id = {
        unit["review_unit_id"]: unit for unit in packet["review_units"]
    }
    cluster_events: list[str] = []
    cluster_units: list[str] = []
    for cluster in predecessor_clusters:
        referenced = cluster["review_unit_ids"]
        declared = cluster["canonical_event_ids"]
        _assert(len(referenced) == len(set(referenced)), "cluster duplicate unit")
        _assert(len(declared) == len(set(declared)), "cluster duplicate event")
        exact_union = sorted({
            event_id for unit_id in referenced
            for event_id in packet_unit_by_id[unit_id]["canonical_event_ids"]
        })
        _assert(sorted(declared) == exact_union, "cluster exact unit-event union")
        cluster_events.extend(declared)
        cluster_units.extend(referenced)
    _assert(len(cluster_units) == len(set(cluster_units)) == 36, "cluster unit coverage")
    _assert(len(cluster_events) == len(set(cluster_events)) == 123, "cluster event coverage")
    _assert(set(cluster_events) == candidate_ids, "cluster candidate union")

    evidence_ids = {row["canonical_event_id"] for row in evidence}
    _assert(evidence_ids == candidate_ids, "domain evidence coverage")
    _assert(
        all(
            row["source_annotation_is_production_authority"] == "false"
            and row["evidence_role"] == "SUPPORTING_TRIAGE_EVIDENCE_ONLY"
            for row in evidence
        ),
        "source annotation silently created authority",
    )
    insufficient_ids = {
        row["canonical_event_id"] for row in candidate_rows
        if row["training_domain_relevance_status"] == triage.RELEVANCE_INSUFFICIENT
    }
    _assert(len(insufficient_ids) == 37, "insufficient relevance count")
    _assert(
        all(
            row["training_domain_relevance_human_review_required"] == "true"
            for row in candidate_rows if row["canonical_event_id"] in insufficient_ids
        ),
        "missing evidence did not remain human-review required",
    )

    population = summary["population"]
    _assert(population["production_trainable_new_sample_count"] == 0, "production count")
    _assert(population["authorized_data_population_after"] == 19, "authorized population")
    _assert(all(population[key] is True for key in (
        "canonical_reconciliation", "new_population_reconciliation",
        "structural_population_reconciliation",
    )), "summary reconciliation")
    readiness = summary["post_supervision_readiness"]
    exact_audit = summary["exact_atom_identity_audit"]
    _assert(exact_audit["candidate_count"] == 123, "exact audit candidates")
    _assert(
        exact_audit["exact_ccd_observed_heavy_atom_id_set_coverage_count"] == 123,
        "exact atom ID-set coverage",
    )
    _assert(
        exact_audit["exact_ccd_observed_heavy_atom_element_consistent_count"] == 123,
        "exact element agreement",
    )
    _assert(exact_audit["reactive_ligand_atom_exact_coverage_count"] == 123, "reactive atom exact coverage")
    _assert(exact_audit["failure_count"] == 0 and exact_audit["failure_identities"] == [], "exact audit failures")
    _assert(readiness["exact_reactive_pair_count"] == 123, "reactive pairs")
    _assert(readiness["exact_ccd_observed_heavy_atom_identity_coverage_count"] == 123, "readiness ID coverage")
    _assert(readiness["exact_ccd_observed_heavy_atom_element_agreement_count"] == 123, "readiness elements")
    _assert(readiness["reactive_ligand_atom_exact_coverage_count"] == 123, "readiness reactive atom")
    _assert(readiness["source_derived_post_bond_distance_count"] == 123, "post distances")
    _assert(readiness["full_ligand_coordinate_availability_count"] == 123, "ligand coordinates")
    _assert(readiness["pocket_coordinate_availability_count"] == 123, "pocket coordinates")
    _assert(readiness["ccd_graph_count"] == 123, "CCD graphs")
    _assert(readiness["reactive_center_radius2_topology_count"] == 115, "radius2 topology")
    _assert(readiness["post_geometry_auxiliary_labels_derivable_count"] == 115, "aux labels")
    _assert(summary["cluster_integrity"] == {
        "canonical_event_coverage_count": 123,
        "cluster_union_equals_candidate_ids": True,
        "duplicate_event_across_clusters_count": 0,
        "every_review_unit_exactly_one_cluster": True,
        "exact_cluster_to_review_unit_event_union": True,
        "review_unit_coverage_count": 36,
    }, "cluster integrity summary")
    _assert(summary["pre_policy"] == {
        "accurate_pre_geometry_required_for_v1_training": False,
        "existing_production_chemistry_authority_semantics_changed": False,
        "pre_status_is_post_only_training_hard_blocker": False,
        "pre_status_role": "DIAGNOSTIC_SUPPORTING_INFORMATION_FOR_POST_ONLY_TRIAGE",
    }, "PRE policy")
    _assert(summary["safety"] == {
        "cache_modified": False,
        "chemistry_registry_modified": False,
        "cumulative_registry_modified": False,
        "model_or_training_path_modified": False,
        "network_performed": False,
        "production_approval_created": False,
        "production_materialization_performed": False,
    }, "safety contract")
    _assert(summary["ready_for_gpt_review"] is True, "GPT review readiness")
    _assert(
        summary["recommended_next_step_exactly"]
        == "perform_human_review_of_36_post_only_v1_review_units",
        "next step",
    )
    for name, digest in summary["output_sha256_excluding_summary"].items():
        _assert(output_hashes[name] == digest, "summary output hash: " + name)
    return {
        "git_state": git_state,
        "cache": cache_after,
        "population": population,
        "post_supervision_readiness": readiness,
        "training_domain_relevance": summary["training_domain_relevance"],
        "human_review_workload": summary["human_review_workload"],
        "output_sha256": output_hashes,
        "ready_for_gpt_review": True,
    }


def main() -> None:
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    cache_root = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) > 2
        else repo_root.parent / triage.CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    )
    result = check_v1(repo_root, cache_root)
    print("base_head_binding=true")
    print("input_artifacts_sha_bound=true")
    print("task_cache_unchanged=true")
    print("network_performed=false")
    print("population_reconciliation=true")
    print("exact_ccd_observed_atom_identity_coverage=true")
    print("packet_chemistry_evidence_complete=true")
    print("event_level_geometry_decision_coverage=true")
    print("cluster_exact_union=true")
    print("review_unit_event_coverage=true")
    print("human_decision_fields_blank=true")
    print("production_approval_created=false")
    print("production_materialization_performed=false")
    print("deterministic_replay_byte_identical=true")
    print("ready_for_gpt_review=" + str(result["ready_for_gpt_review"]).lower())


if __name__ == "__main__":
    main()

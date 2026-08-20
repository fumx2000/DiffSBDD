from __future__ import annotations

from copy import deepcopy
import csv
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_post_only_cys_sg_training_candidate_triage_v1 as triage,
)


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / triage.CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
OUTPUT = ROOT / triage.OUTPUT_ROOT_RELATIVE


@pytest.fixture(scope="module")
def real_artifacts() -> dict[str, bytes]:
    original = triage.bulk.urlopen

    def prohibited(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network must not be called")

    triage.bulk.urlopen = prohibited
    try:
        return triage.build_artifacts_v1(repo_root=ROOT, cache_root=CACHE)
    finally:
        triage.bulk.urlopen = original


def _csv(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _observed(*atoms: tuple[str, str]) -> list[dict[str, object]]:
    return [
        {
            "atom_id": atom_id, "element": element,
            "x": float(index), "y": float(index + 1), "z": float(index + 2),
            "selected_altloc": None, "selected_model": "1",
        }
        for index, (atom_id, element) in enumerate(atoms)
    ]


def _ccd(*atoms: tuple[str, str]) -> list[dict[str, object]]:
    return [
        {
            "atom_id": atom_id, "type_symbol": element, "charge": 0,
            "aromatic_flag": "N",
        }
        for atom_id, element in atoms
    ]


def test_real_population_and_readiness_reconcile(real_artifacts: dict[str, bytes]) -> None:
    summary = json.loads(real_artifacts[triage.SUMMARY])
    assert summary["population"] == {
        "authorized_data_population_after": 19,
        "blocked_existing_group_conflict_count": 88,
        "blocked_representation_gap_count": 7,
        "canonical_reconciliation": True,
        "canonical_unique_event_count": 2387,
        "known_existing_event_count": 27,
        "new_population_reconciliation": True,
        "new_unique_candidate_event_count": 2360,
        "outside_structural_eligibility_count": 2142,
        "post_only_v1_review_candidate_count": 123,
        "production_trainable_new_sample_count": 0,
        "structural_population_reconciliation": True,
        "structurally_model_eligible_new_event_count": 218,
    }
    assert summary["post_supervision_readiness"] == {
        "ccd_graph_count": 123,
        "derivable_quantities_are_not_new_loss_definitions": True,
        "exact_ccd_observed_heavy_atom_element_agreement_count": 123,
        "exact_ccd_observed_heavy_atom_identity_coverage_count": 123,
        "exact_reactive_pair_count": 123,
        "full_ligand_coordinate_availability_count": 123,
        "pocket_coordinate_availability_count": 123,
        "post_geometry_auxiliary_labels_derivable_count": 115,
        "reactive_center_radius2_topology_count": 115,
        "reactive_ligand_atom_exact_coverage_count": 123,
        "source_derived_post_bond_distance_count": 123,
    }
    assert summary["exact_atom_identity_audit"] == {
        "candidate_count": 123,
        "count_equality_alone_accepted": False,
        "coverage_contract": (
            "EXACT_CCD_OBSERVED_HEAVY_ATOM_IDENTITY_AND_ELEMENT_COVERAGE"
        ),
        "exact_ccd_observed_heavy_atom_element_consistent_count": 123,
        "exact_ccd_observed_heavy_atom_id_set_coverage_count": 123,
        "failure_count": 0,
        "failure_identities": [],
        "reactive_ligand_atom_exact_coverage_count": 123,
    }


def test_same_count_wrong_atom_id_set_fails_closed() -> None:
    with pytest.raises(
        ValueError, match="EXACT_CCD_OBSERVED_HEAVY_ATOM_ID_SET_MISMATCH"
    ):
        triage.exact_ccd_observed_heavy_atom_coverage_v1(
            observed_atoms=_observed(("A", "C"), ("B", "N"), ("D", "O")),
            ccd_atoms=_ccd(("A", "C"), ("B", "N"), ("C", "O")),
            reactive_atom_id="A",
        )


def test_same_id_element_mismatch_fails_closed() -> None:
    with pytest.raises(
        ValueError, match="EXACT_CCD_OBSERVED_HEAVY_ATOM_ELEMENT_MISMATCH:A:C:N"
    ):
        triage.exact_ccd_observed_heavy_atom_coverage_v1(
            observed_atoms=_observed(("A", "N"), ("B", "O")),
            ccd_atoms=_ccd(("A", "C"), ("B", "O")),
            reactive_atom_id="A",
        )


def test_duplicate_observed_heavy_atom_id_fails_closed() -> None:
    with pytest.raises(ValueError, match="OBSERVED_HEAVY_ATOM_ID_DUPLICATE:B"):
        triage.exact_ccd_observed_heavy_atom_coverage_v1(
            observed_atoms=_observed(("A", "C"), ("B", "N"), ("B", "N")),
            ccd_atoms=_ccd(("A", "C"), ("B", "N")),
            reactive_atom_id="A",
        )


@pytest.mark.parametrize(
    ("observed", "expected_count"),
    [
        (_observed(("A", "C")), 0),
        (_observed(("R", "N"), ("R", "N"), ("A", "C")), 2),
    ],
)
def test_reactive_atom_missing_or_duplicated_fails_closed(
    observed: list[dict[str, object]], expected_count: int,
) -> None:
    with pytest.raises(
        ValueError,
        match=f"REACTIVE_LIGAND_ATOM_OBSERVED_COUNT_INVALID:R:{expected_count}",
    ):
        triage.exact_ccd_observed_heavy_atom_coverage_v1(
            observed_atoms=observed,
            ccd_atoms=_ccd(("R", "N"), ("A", "C")),
            reactive_atom_id="R",
        )


def test_domain_classification_uses_reaction_evidence_not_names() -> None:
    def event(reaction: str | None, warhead: str = "misleading name") -> dict[str, object]:
        return {
            "source_annotations": [{
                "source_dataset": "SOURCE_COVBINDERINPDB",
                "reaction": reaction,
                "warhead": warhead,
            }]
        }

    assert triage.classify_training_domain_relevance_v1(event("inhibitor"))[0] == triage.RELEVANCE_SUPPORTED
    assert triage.classify_training_domain_relevance_v1(event("probe"))[0] == triage.RELEVANCE_SUPPORTED
    assert triage.classify_training_domain_relevance_v1(event("substrate"))[0] == triage.RELEVANCE_NON_TARGET
    assert triage.classify_training_domain_relevance_v1(event("modifier"))[0] == triage.RELEVANCE_REVIEW
    assert triage.classify_training_domain_relevance_v1(event(None))[0] == triage.RELEVANCE_INSUFFICIENT
    assert triage.classify_training_domain_relevance_v1({"source_annotations": []})[0] == triage.RELEVANCE_INSUFFICIENT


def test_pre_status_alone_cannot_change_candidate_partition() -> None:
    base = {
        "stage_statuses": {"BULK_09_MODEL_AND_FEATURE_COMPATIBILITY": "PASSED"},
        "terminal_outcome": "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
    }
    for pre_status in (
        "PRE_REACTION_UNRESOLVED",
        "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "PRE_GRAPH_TRANSFORM_REQUIRED",
    ):
        outcome = {**base, "pre_representability": {"status": pre_status}}
        assert triage.post_only_partition_v1(outcome, known_event=False) == triage.POST_ONLY_CANDIDATE


def test_partition_fails_closed_for_unknown_structurally_eligible_route() -> None:
    with pytest.raises(
        ValueError, match="STRUCTURALLY_ELIGIBLE_NEW_EVENT_PARTITION_UNRESOLVED"
    ):
        triage.post_only_partition_v1(
            {
                "stage_statuses": {"BULK_09_MODEL_AND_FEATURE_COMPATIBILITY": "PASSED"},
                "terminal_outcome": "UNEXPECTED_ROUTE",
            },
            known_event=False,
        )


def test_real_event_inventory_excludes_blocks_and_known_controls(
    real_artifacts: dict[str, bytes],
) -> None:
    rows = _csv(real_artifacts[triage.EVENT_INVENTORY])
    counts = {}
    for partition in {
        triage.KNOWN_EXISTING, triage.POST_ONLY_CANDIDATE,
        triage.BLOCKED_LEAKAGE, triage.BLOCKED_REPRESENTATION,
        triage.OUTSIDE_STRUCTURAL,
    }:
        counts[partition] = sum(row["post_only_partition"] == partition for row in rows)
    assert counts == {
        triage.KNOWN_EXISTING: 27,
        triage.POST_ONLY_CANDIDATE: 123,
        triage.BLOCKED_LEAKAGE: 88,
        triage.BLOCKED_REPRESENTATION: 7,
        triage.OUTSIDE_STRUCTURAL: 2142,
    }
    candidates = [row for row in rows if row["post_only_partition"] == triage.POST_ONLY_CANDIDATE]
    assert all(row["population_status"] == "NEW_UNIQUE_CANDIDATE_EVENT" for row in candidates)
    assert all(
        row["exact_ccd_observed_heavy_atom_identity_coverage"] == "true"
        and row["exact_ccd_observed_heavy_atom_element_agreement"] == "true"
        and row["reactive_ligand_atom_exact_coverage"] == "true"
        for row in candidates
    )
    assert all(row["production_approval_created"] == "false" for row in rows)


def test_review_units_cover_candidates_once_and_human_fields_are_blank(
    real_artifacts: dict[str, bytes],
) -> None:
    events = _csv(real_artifacts[triage.EVENT_INVENTORY])
    candidates = {
        row["canonical_event_id"] for row in events
        if row["post_only_partition"] == triage.POST_ONLY_CANDIDATE
    }
    units = _csv(real_artifacts[triage.REVIEW_UNIT_INVENTORY])
    seen = [event_id for unit in units for event_id in json.loads(unit["canonical_event_ids_json"])]
    assert len(units) == 36
    assert len(seen) == len(set(seen)) == 123
    assert set(seen) == candidates
    assert all(unit["chemistry_identity_boundary_validated"] == "true" for unit in units)
    assert all(
        unit[field] == "" for unit in units
        for field in triage.UNIT_HUMAN_DECISION_FIELDS
    )
    assert "post_geometry_training_usable" not in triage.UNIT_HUMAN_DECISION_FIELDS
    packet = json.loads(real_artifacts[triage.REVIEW_PACKET])
    assert len(packet["review_units"]) == 36
    assert all(
        unit[field] == "" for unit in packet["review_units"]
        for field in triage.UNIT_HUMAN_DECISION_FIELDS
    )


def test_packet_has_complete_chemistry_and_event_level_evidence(
    real_artifacts: dict[str, bytes],
) -> None:
    packet = json.loads(real_artifacts[triage.REVIEW_PACKET])
    event_ids: list[str] = []
    multi_units = []
    for unit in packet["review_units"]:
        machine = unit["machine_chemistry_evidence"]
        ccd_all_atoms = machine["ccd_atom_inventory"]
        ccd_atoms = machine["ccd_heavy_atom_inventory"]
        bonds = machine["ccd_bond_inventory"]
        observed = machine["representative_observed_ligand_atom_coordinates"]
        assert ccd_all_atoms and ccd_atoms and bonds and observed
        all_ccd_ids = {atom["atom_id"] for atom in ccd_all_atoms}
        assert all(
            bond["atom_id_1"] in all_ccd_ids
            and bond["atom_id_2"] in all_ccd_ids
            for bond in bonds
        )
        assert {atom["atom_id"] for atom in ccd_atoms} == {
            atom["atom_id"] for atom in observed
        }
        assert all(
            next(
                item for item in observed if item["atom_id"] == ccd_atom["atom_id"]
            )["element"] == ccd_atom["element"]
            for ccd_atom in ccd_atoms
        )
        reactive = machine["reactive_atom_evidence"]
        assert reactive["ligand_reactive_atom"] == unit["ligand_reactive_atom"]
        assert reactive["reactive_atom_ccd_record"]["atom_id"] == unit["ligand_reactive_atom"]
        review_events = unit["events_for_review"]
        assert len(review_events) == unit["event_count"]
        assert [event["canonical_event_id"] for event in review_events] == unit["canonical_event_ids"]
        for event in review_events:
            event_ids.append(event["canonical_event_id"])
            assert all(event[field] == "" for field in triage.EVENT_HUMAN_DECISION_FIELDS)
            assert event["source_annotation_role"] == "SUPPORTING_TRIAGE_EVIDENCE_ONLY"
        if len(review_events) > 1:
            multi_units.append(unit)
    assert len(event_ids) == len(set(event_ids)) == 123
    assert len(multi_units) == 25
    assert sum(unit["event_count"] for unit in multi_units) == 112


def test_multi_event_geometry_decisions_are_independent(
    real_artifacts: dict[str, bytes],
) -> None:
    packet = json.loads(real_artifacts[triage.REVIEW_PACKET])
    multi = next(
        unit for unit in packet["review_units"]
        if len(unit["events_for_review"]) >= 2
        and len({
            (event["post_distance_angstrom"], event["protein_altloc"], event["ligand_altloc"])
            for event in unit["events_for_review"]
        }) >= 2
    )
    editable = deepcopy(multi)
    first, second = editable["events_for_review"][:2]
    first["post_geometry_training_usable"] = "YES"
    first["event_training_use_decision"] = "INCLUDE"
    assert second["post_geometry_training_usable"] == ""
    assert second["event_training_use_decision"] == ""
    assert "post_geometry_training_usable" not in {
        field for field in triage.UNIT_HUMAN_DECISION_FIELDS
    }


def test_cluster_integrity_exact_union_and_duplicate_fail_closed() -> None:
    units = [
        {"review_unit_id": "U1", "canonical_event_ids": ["E1"]},
        {"review_unit_id": "U2", "canonical_event_ids": ["E2"]},
    ]
    clusters = [
        {"cluster_id": "C1", "review_unit_ids": ["U1"], "canonical_event_ids": ["E1"]},
        {"cluster_id": "C2", "review_unit_ids": ["U2"], "canonical_event_ids": ["E2"]},
    ]
    _mapping, integrity = triage.validate_cluster_integrity_v1(
        units=units, clusters=clusters, candidate_ids={"E1", "E2"}
    )
    assert integrity["exact_cluster_to_review_unit_event_union"] is True
    duplicate = deepcopy(clusters)
    duplicate[0]["canonical_event_ids"] = ["E1", "E1"]
    with pytest.raises(ValueError, match="DUPLICATE_EVENT_WITHIN_CLUSTER:C1"):
        triage.validate_cluster_integrity_v1(
            units=units, clusters=duplicate, candidate_ids={"E1", "E2"}
        )
    mismatch = deepcopy(clusters)
    mismatch[0]["canonical_event_ids"] = ["E2"]
    with pytest.raises(ValueError, match="CLUSTER_TO_REVIEW_UNIT_EVENT_UNION_MISMATCH:C1"):
        triage.validate_cluster_integrity_v1(
            units=units, clusters=mismatch, candidate_ids={"E1", "E2"}
        )


def test_source_annotation_evidence_never_becomes_authority(
    real_artifacts: dict[str, bytes],
) -> None:
    evidence = _csv(real_artifacts[triage.DOMAIN_EVIDENCE])
    assert evidence
    assert all(row["source_annotation_is_production_authority"] == "false" for row in evidence)
    assert all(row["evidence_role"] == "SUPPORTING_TRIAGE_EVIDENCE_ONLY" for row in evidence)
    assert all(row["binding_artifact_sha256"] == triage.INPUT_SHA256["cross_source_canonical_event_manifest_v1.json"] for row in evidence)


def test_real_domain_counts_are_conservative(real_artifacts: dict[str, bytes]) -> None:
    summary = json.loads(real_artifacts[triage.SUMMARY])
    assert summary["training_domain_relevance"] == {
        "all_candidates_still_require_human_decision": True,
        "likely_biochemical_or_non_target_count": 37,
        "machine_supported_relevant_count": 39,
        "molecule_name_or_warhead_label_used_for_machine_classification": False,
        "source_annotations_create_chemistry_authority": False,
        "task_relevance_evidence_insufficient_count": 37,
        "task_relevance_human_review_required_count": 10,
    }


def test_materialized_outputs_match_fresh_build_and_are_byte_identical(
    real_artifacts: dict[str, bytes],
) -> None:
    assert set(real_artifacts) == set(triage.OUTPUT_FILENAMES)
    for name, payload in real_artifacts.items():
        assert (OUTPUT / name).read_bytes() == payload


def test_input_binding_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    changed = dict(triage.INPUT_SHA256)
    changed["bulk_summary_v1.json"] = "0" * 64
    monkeypatch.setattr(triage, "INPUT_SHA256", changed)
    with pytest.raises(ValueError, match="BOUND_INPUT_SHA256_MISMATCH:bulk_summary_v1.json"):
        triage.verify_bound_inputs_v1(ROOT)


def test_csv_writer_rejects_incomplete_schema() -> None:
    with pytest.raises(ValueError, match="CSV_ROW_SCHEMA_MISMATCH"):
        triage._csv_bytes(("a", "b"), [{"a": "x"}])

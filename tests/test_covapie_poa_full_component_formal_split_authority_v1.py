from __future__ import annotations

import copy
from dataclasses import fields, replace
from fractions import Fraction
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from covalent_ext import covapie_poa_full_component_formal_split_authority_v1 as owner


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def source_payloads() -> dict[str, bytes]:
    return {
        path: (REPO_ROOT / path).read_bytes()
        for path in owner._SOURCE_SHA_BY_PATH_V1
    }


@pytest.fixture(scope="module")
def result() -> owner.POAFullComponentFormalSplitAuthorityResultV1:
    return owner.build_covapie_poa_full_component_formal_split_authority_v1(
        repo_root=REPO_ROOT
    )


def _processing_events(source_payloads: dict[str, bytes]) -> list[dict[str, object]]:
    parsed = json.loads(source_payloads[owner._PROCESSING_VIEW_V1])
    return copy.deepcopy(parsed["events"])


def _selected_indices(events: list[dict[str, object]]) -> list[int]:
    return [
        index for index, wrapper in enumerate(events)
        if wrapper["processing_outcome"].get("leakage_key")
        == owner.POA_LEAKAGE_KEY_V1
    ]


def _assert_rejected(callable_object) -> None:
    with pytest.raises(
        owner.POAFullComponentFormalSplitAuthorityError,
        match=owner.COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR,
    ):
        callable_object()


def _sequence_context(source_payloads):
    groups, batch_registry, ndu_registry = owner._reconstruct_frozen_groups_v1(
        source_payloads
    )
    sequence_evidence, group_count, sequence_count = (
        owner._complete_component_sequence_evidence_v1(
            processing_view_payload=source_payloads[owner._PROCESSING_VIEW_V1],
            bulk_processing_payload=source_payloads[owner._BULK_PROCESSING_V1],
            carrier_payload=source_payloads[owner._MISSING_SEQUENCE_EVIDENCE_V1],
            batch_registry=batch_registry,
            ndu_registry=ndu_registry,
        )
    )
    return (
        groups, batch_registry, ndu_registry, sequence_evidence,
        group_count, sequence_count,
    )


def _canonical_payload(value: object) -> bytes:
    return owner._canonical_json_bytes(value)


def test_real_builder_establishes_exact_full_component_authority(result) -> None:
    assert owner.validate_covapie_poa_full_component_formal_split_authority_v1(
        result
    )
    assert len(result.full_member_canonical_event_ids) == 24
    assert result.full_member_pdb_ligand_identities == (
        "4I3U/POA",
        "4I3V/POA",
        "4I3W/G3H",
    )
    assert set(result.exact16_event_ids) < set(
        result.full_member_canonical_event_ids
    )
    assert len(result.exact16_event_ids) == 16
    assert len(result.external_g3h_event_ids) == 8
    assert result.full_component_group_id == (
        "COVAPIE_EXPANSION_LEAKAGE_GROUP_F70DB37A8004AF17"
    )
    assert result.read_only_predicted_split == "train"
    assert result.read_only_prediction_is_authority is False
    assert result.read_only_prediction_copied_as_formal_authority is False
    assert result.formal_group_id == result.full_component_group_id
    assert result.formal_split == "train"
    assert result.formal_split_authoritative is True
    assert result.canonical_event_inventory_sha256 == (
        "71403d2f65a6bbabfe3cca620a0b397a0947648331bc3c4c947dbff93128e049"
    )
    assert result.linking_axes == (
        "LIGAND_GRAPH",
        "PROTEIN_ACCESSION",
        "PROTEIN_EXACT_SEQUENCE",
        "PROTEIN_SEQUENCE_IDENTITY_GE_0.5",
    )


def test_current14_and_additive_after_population_are_exact(result) -> None:
    before = result.before_summary
    after = result.after_summary
    assert (
        before.group_count,
        before.identity_count,
        before.train_group_count,
        before.validation_group_count,
        before.test_group_count,
    ) == (14, 45, 5, 5, 4)
    assert (
        before.train_identity_count,
        before.validation_identity_count,
        before.test_identity_count,
    ) == (23, 5, 17)
    assert (
        after.group_count,
        after.identity_count,
        after.train_group_count,
        after.validation_group_count,
        after.test_group_count,
    ) == (15, 48, 6, 5, 4)
    assert (
        after.train_identity_count,
        after.validation_identity_count,
        after.test_identity_count,
    ) == (26, 5, 17)
    assert result.frozen_inventory_sha256 == (
        "d10efe9c95b85aea4215de68b88df4094d021a06b7b08dd83c116b2c08842a4d"
    )
    assert result.existing_frozen_groups_before == (
        result.existing_frozen_groups_after
    )
    assert result.existing_frozen_splits_changed is False
    assert len({
        identity
        for group in result.existing_frozen_groups_before
        for identity in group.member_identities
    }) == 45


def test_generic_owner_and_independent_one_group_oracle_are_exact(result) -> None:
    oracle = result.independent_oracle
    assert result.generic_owner_oracle_parity is True
    assert oracle.selected_assignment == result.generic_owner_assignment
    assert oracle.candidate_assignment_count == 3
    assert oracle.valid_assignment_count == 3
    assert oracle.selected_split == "train"
    assert oracle.selected_sample_counts == (26, 5, 17)
    assert oracle.selected_group_counts == (6, 5, 4)
    assert oracle.selected_objective == (
        Fraction(98, 5),
        Fraction(49, 5),
        Fraction(9, 1),
    )
    assert oracle.tie_count_before_signature == 1
    assert oracle.lexicographic_tie_break_verified is True
    assert result.input_order_independence_verified is True


def test_every_event_has_split_only_authority_and_no_training_activation(
    result,
) -> None:
    assert len(result.records) == 24
    assert {record.formal_leakage_group_id for record in result.records} == {
        owner.POA_FORMAL_GROUP_ID_V1
    }
    assert {record.formal_split for record in result.records} == {"train"}
    assert all(record.formal_split_authoritative for record in result.records)
    assert not any(record.sample_training_admitted for record in result.records)
    assert not any(
        record.model_training_activation_authorized for record in result.records
    )
    assert result.sample_training_admitted is False
    assert result.model_training_activation_authorized is False
    assert result.ready_for_training is False
    assert result.cross_split_leakage_conflict is False
    assert result.cross_link_conflict_authoritatively_proven is True
    assert result.cross_link_reference_group_count == 14
    assert result.cross_link_reference_count == 64
    assert result.cross_link_comparison_count == 1536
    assert result.sequence_identity_reference_group_count == 5
    assert result.sequence_identity_reference_sequence_count == 15
    assert result.raw_sequence_reference_count == 33
    assert result.sequence_identity_comparison_count == 792
    assert (
        result.protein_sequence_identity_axis_cross_link_coverage_complete is True
    )
    assert result.randomization_used is False
    assert result.random_seed is None
    assert result.manual_split_override is False
    assert {field.name for field in fields(
        owner.POAFullComponentFormalSplitRecordV1
    )} == {
        "canonical_event_id",
        "pdb_ligand_identity",
        "formal_leakage_group_id",
        "formal_split",
        "formal_split_authoritative",
        "sample_training_admitted",
        "model_training_activation_authorized",
    }


def test_source_bindings_are_exact_and_repository_only(result) -> None:
    assert len(result.source_bindings) == len(owner._SOURCE_SPECS_V1)
    for binding, (role, path, sha256) in zip(
        result.source_bindings, owner._SOURCE_SPECS_V1
    ):
        assert binding.artifact_role == role
        assert binding.repository_relative_path == path
        assert binding.sha256 == sha256
        assert binding.byte_count == owner._SOURCE_BYTE_COUNT_BY_PATH_V1[path]
        assert binding.byte_count == (REPO_ROOT / path).stat().st_size
        assert not Path(path).is_absolute()
        assert "covapie-state" not in path


def test_public_validator_rejects_positive_source_binding_byte_count_drift(
    result,
) -> None:
    bindings = list(result.source_bindings)
    bindings[0] = replace(
        bindings[0], byte_count=bindings[0].byte_count + 1,
    )
    drifted = replace(result, source_bindings=tuple(bindings))
    _assert_rejected(
        lambda: owner.validate_covapie_poa_full_component_formal_split_authority_v1(
            drifted
        )
    )


def test_sequence_evidence_carrier_is_exact_portable_and_complete(
    source_payloads,
) -> None:
    carrier = json.loads(source_payloads[owner._MISSING_SEQUENCE_EVIDENCE_V1])
    assert carrier["artifact_role"].endswith("EVIDENCE_CARRIER_ONLY")
    assert carrier["boundary"] == owner._SEQUENCE_EVIDENCE_BOUNDARY_V1
    assert carrier["source_binding"] == owner._EXTERNAL_SEQUENCE_SOURCE_BINDING_V1
    assert carrier["sequence_record_count"] == 6
    assert [
        row["protein_sequence_sha256"] for row in carrier["sequence_records"]
    ] == sorted(owner._MISSING_SEQUENCE_OWNER_BY_SHA_V1)
    assert owner._missing_sequence_evidence_v1(
        source_payloads[owner._MISSING_SEQUENCE_EVIDENCE_V1]
    ).keys() == owner._MISSING_SEQUENCE_OWNER_BY_SHA_V1.keys()

    (
        _groups, _batch, _ndu, sequence_evidence, group_count, sequence_count,
    ) = _sequence_context(source_payloads)
    assert group_count == 5
    assert sequence_count == 15
    assert len(sequence_evidence) == 15
    assert all(sequence_evidence.values())


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("byte_count", 3043910),
        ("sha256", "0" * 64),
        ("path", "wrong/incremental_processing_outcomes_v1.json"),
        ("path_scope", "REPOSITORY"),
    ),
)
def test_carrier_external_source_binding_drift_fails_closed(
    source_payloads, field: str, value: object,
) -> None:
    carrier = json.loads(source_payloads[owner._MISSING_SEQUENCE_EVIDENCE_V1])
    carrier["source_binding"][field] = value
    _assert_rejected(
        lambda: owner._missing_sequence_evidence_v1(_canonical_payload(carrier))
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_record", "seventh_record", "duplicate_record", "wrong_leakage_sha",
        "raw_sequence_hash", "raw_text_checksum", "empty_sequence", "wrong_group",
        "wrong_component",
    ),
)
def test_carrier_record_inventory_or_semantics_drift_fails_closed(
    source_payloads, mutation: str,
) -> None:
    carrier = json.loads(source_payloads[owner._MISSING_SEQUENCE_EVIDENCE_V1])
    records = carrier["sequence_records"]
    if mutation == "missing_record":
        records.pop()
        carrier["sequence_record_count"] = 5
    elif mutation == "seventh_record":
        extra = copy.deepcopy(records[-1])
        extra["protein_sequence_sha256"] = "e" * 64
        records.append(extra)
        carrier["sequence_record_count"] = 7
    elif mutation == "duplicate_record":
        records[-1] = copy.deepcopy(records[0])
    elif mutation == "wrong_leakage_sha":
        records[0]["protein_sequence_sha256"] = "0" * 64
    elif mutation == "raw_sequence_hash":
        sequence = records[0]["protein_sequence"]
        records[0]["protein_sequence"] = sequence[:-1] + (
            "A" if sequence[-1] != "A" else "G"
        )
        records[0]["protein_sequence_text_sha256"] = owner._sha256(
            records[0]["protein_sequence"].encode("utf-8")
        )
    elif mutation == "raw_text_checksum":
        records[0]["protein_sequence_text_sha256"] = "0" * 64
    elif mutation == "empty_sequence":
        records[0]["protein_sequence"] = ""
    elif mutation == "wrong_group":
        records[0]["formal_group_id"] = "COVAPIE_EXPANSION_LEAKAGE_GROUP_WRONG"
    else:
        records[0]["component_name"] = "WRONG"
    _assert_rejected(
        lambda: owner._missing_sequence_evidence_v1(_canonical_payload(carrier))
    )


def test_processing_source_sha_drift_fails_closed(source_payloads) -> None:
    drifted = dict(source_payloads)
    drifted[owner._PROCESSING_VIEW_V1] += b"\n"
    _assert_rejected(lambda: owner._build_from_bound_payloads_v1(drifted))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("leakage_classification", "HISTORICAL_BASELINE_COMPONENT"),
        ("predicted_group_id", "COVAPIE_EXPANSION_LEAKAGE_GROUP_DRIFT"),
    ),
)
def test_wrong_processing_semantics_fail_closed(
    source_payloads, field: str, value: str,
) -> None:
    events = _processing_events(source_payloads)
    index = _selected_indices(events)[0]
    events[index]["processing_outcome"][field] = value
    _assert_rejected(lambda: owner._extract_poa_component_from_events_v1(events))


def test_wrong_leakage_key_fails_closed(source_payloads) -> None:
    events = _processing_events(source_payloads)
    index = _selected_indices(events)[0]
    events[index]["processing_outcome"]["leakage_key"] = "WRONG"
    _assert_rejected(lambda: owner._extract_poa_component_from_events_v1(events))


@pytest.mark.parametrize("new_count", (23, 25))
def test_wrong_event_count_fails_closed(source_payloads, new_count: int) -> None:
    events = _processing_events(source_payloads)
    indices = _selected_indices(events)
    if new_count == 23:
        del events[indices[-1]]
    else:
        events.append(copy.deepcopy(events[indices[-1]]))
    _assert_rejected(lambda: owner._extract_poa_component_from_events_v1(events))


def test_duplicate_event_with_count24_fails_closed(source_payloads) -> None:
    events = _processing_events(source_payloads)
    indices = _selected_indices(events)
    events[indices[-1]] = copy.deepcopy(events[indices[0]])
    _assert_rejected(lambda: owner._extract_poa_component_from_events_v1(events))


def _rewrite_identity(
    outcome: dict[str, object], *, pdb_id: str, ligand_id: str,
) -> None:
    event_id = str(outcome["canonical_event_id"])
    parts = event_id.split(":")
    parts[1] = pdb_id
    parts[7] = ligand_id
    outcome["canonical_event_id"] = ":".join(parts)
    outcome["pdb_id"] = pdb_id
    outcome["ligand_component_id"] = ligand_id


def test_two_identities_and_missing_g3h_fail_closed(source_payloads) -> None:
    events = _processing_events(source_payloads)
    for index in _selected_indices(events):
        outcome = events[index]["processing_outcome"]
        if outcome["pdb_id"] == "4I3W":
            _rewrite_identity(outcome, pdb_id="4I3V", ligand_id="POA")
    _assert_rejected(lambda: owner._extract_poa_component_from_events_v1(events))


def test_four_identities_and_extra_identity_fail_closed(source_payloads) -> None:
    events = _processing_events(source_payloads)
    index = _selected_indices(events)[-1]
    _rewrite_identity(
        events[index]["processing_outcome"], pdb_id="9ZZZ", ligand_id="EXT"
    )
    _assert_rejected(lambda: owner._extract_poa_component_from_events_v1(events))


def test_duplicate_or_extra_result_identity_fails_closed(result) -> None:
    duplicated = replace(
        result,
        full_member_pdb_ligand_identities=(
            "4I3U/POA",
            "4I3U/POA",
            "4I3W/G3H",
        ),
    )
    extra = replace(
        result,
        full_member_pdb_ligand_identities=(
            *result.full_member_pdb_ligand_identities,
            "9ZZZ/EXT",
        ),
    )
    _assert_rejected(
        lambda: owner.validate_covapie_poa_full_component_formal_split_authority_v1(
            duplicated
        )
    )
    _assert_rejected(
        lambda: owner.validate_covapie_poa_full_component_formal_split_authority_v1(
            extra
        )
    )


@pytest.mark.parametrize("identity", ("4I3W/G3H", "4I3V/POA"))
def test_poa_exact16_g3h_or_g1_g2_split_separation_fails_closed(
    result, identity: str,
) -> None:
    records = tuple(
        replace(record, formal_split="validation")
        if record.pdb_ligand_identity == identity else record
        for record in result.records
    )
    drifted = replace(result, records=records)
    _assert_rejected(
        lambda: owner.validate_covapie_poa_full_component_formal_split_authority_v1(
            drifted
        )
    )


def test_existing_frozen_group_move_or_member_removal_fails_closed(result) -> None:
    groups = list(result.existing_frozen_groups_before)
    moved = list(groups)
    moved[0] = replace(moved[0], assigned_split="validation")
    _assert_rejected(lambda: owner._validate_frozen_groups_v1(moved))

    removed = list(groups)
    removed_members = removed[0].member_identities[1:]
    removed[0] = replace(
        removed[0],
        member_identities=removed_members,
        member_count=len(removed_members),
    )
    _assert_rejected(lambda: owner._validate_frozen_groups_v1(removed))


def test_existing_member_duplicate_within_or_across_groups_fails_closed(
    result,
) -> None:
    groups = list(result.existing_frozen_groups_before)
    within = list(groups)
    duplicated_members = tuple(sorted((
        *within[0].member_identities,
        within[0].member_identities[0],
    )))
    within[0] = replace(
        within[0],
        member_identities=duplicated_members,
        member_count=len(duplicated_members),
    )
    _assert_rejected(lambda: owner._validate_frozen_groups_v1(within))

    across = list(groups)
    overlapping_members = tuple(sorted((
        *across[1].member_identities,
        across[0].member_identities[0],
    )))
    across[1] = replace(
        across[1],
        member_identities=overlapping_members,
        member_count=len(overlapping_members),
    )
    _assert_rejected(lambda: owner._validate_frozen_groups_v1(across))


def test_new_identity_collision_with_existing_group_fails_closed(result) -> None:
    candidates = (
        SimpleNamespace(
            candidate_identity=result.existing_frozen_groups_before[0].member_identities[0],
            leakage_key=owner.POA_LEAKAGE_KEY_V1,
        ),
        *owner._poa_candidates_v1()[1:],
    )
    _assert_rejected(lambda: owner._independent_poa_oracle_v1(
        candidates,
        existing_groups=result.existing_frozen_groups_before,
    ))


def test_cross_link_conflict_is_detected_and_build_fails_closed(
    source_payloads, result, monkeypatch,
) -> None:
    component = owner._extract_poa_component_v1(
        source_payloads[owner._PROCESSING_VIEW_V1]
    )
    (
        groups, batch_registry, ndu_registry, sequence_evidence,
        group_count, sequence_count,
    ) = _sequence_context(source_payloads)
    poa_evidence = dict(component.evidence_by_event[0][1])
    poa_sequence = poa_evidence["protein_sequence"]
    replacement = "A" if poa_sequence[-1] != "A" else "G"
    similar_sequence = poa_sequence[:-1] + replacement
    similar_reference = {
        "identity": "SYNTHETIC/SIMILAR",
        "leakage_key": groups[0].leakage_key,
        "group_id": groups[0].final_leakage_group_id,
        "split": groups[0].assigned_split,
        "evidence": {
            "ligand_graph_sha256": "1" * 64,
            "ligand_scaffold_sha256": "2" * 64,
            "protein_accession": "SYNTHETIC_ACCESSION",
            "protein_sequence_sha256": "3" * 64,
            "protein_sequence": similar_sequence,
        },
    }
    assert owner.bulk_owner._leakage_linking_axes_v1(
        poa_evidence, similar_reference["evidence"],
    ) == ["PROTEIN_SEQUENCE_IDENTITY_GE_0.5"]
    conflicts, audit = owner._detect_cross_link_conflicts_v1(
        component,
        groups,
        bulk_processing_payload=source_payloads[owner._BULK_PROCESSING_V1],
        batch_registry=batch_registry,
        ndu_registry=ndu_registry,
        protein_sequence_by_sha=sequence_evidence,
        sequence_reference_group_count=group_count,
        sequence_reference_sequence_count=sequence_count,
        extra_references=(similar_reference,),
    )
    assert conflicts
    assert any(
        item["existing_identity"] == "SYNTHETIC/SIMILAR"
        and item["linking_axes"] == ("PROTEIN_SEQUENCE_IDENTITY_GE_0.5",)
        for item in conflicts
    )
    assert audit.raw_sequence_reference_count == 34
    assert audit.sequence_identity_comparison_count == 816
    monkeypatch.setattr(
        owner,
        "_detect_cross_link_conflicts_v1",
        lambda *_args, **_kwargs: (
            ({"linking_axes": ("PROTEIN_SEQUENCE_IDENTITY_GE_0.5",)},),
            audit,
        ),
    )
    _assert_rejected(lambda: owner._build_from_bound_payloads_v1(source_payloads))


def test_sub_half_sequence_similarity_does_not_create_cross_link(
    source_payloads,
) -> None:
    component = owner._extract_poa_component_v1(
        source_payloads[owner._PROCESSING_VIEW_V1]
    )
    (
        groups, batch_registry, ndu_registry, sequence_evidence,
        group_count, sequence_count,
    ) = _sequence_context(source_payloads)
    poa_evidence = dict(component.evidence_by_event[0][1])
    dissimilar_reference = {
        "identity": "SYNTHETIC/DISSIMILAR",
        "leakage_key": groups[0].leakage_key,
        "group_id": groups[0].final_leakage_group_id,
        "split": groups[0].assigned_split,
        "evidence": {
            "ligand_graph_sha256": "4" * 64,
            "ligand_scaffold_sha256": "5" * 64,
            "protein_accession": "SYNTHETIC_ACCESSION",
            "protein_sequence_sha256": "6" * 64,
            "protein_sequence": "Z" * len(poa_evidence["protein_sequence"]),
        },
    }
    assert owner.bulk_owner._leakage_linking_axes_v1(
        poa_evidence, dissimilar_reference["evidence"],
    ) == []
    conflicts, audit = owner._detect_cross_link_conflicts_v1(
        component,
        groups,
        bulk_processing_payload=source_payloads[owner._BULK_PROCESSING_V1],
        batch_registry=batch_registry,
        ndu_registry=ndu_registry,
        protein_sequence_by_sha=sequence_evidence,
        sequence_reference_group_count=group_count,
        sequence_reference_sequence_count=sequence_count,
        extra_references=(dissimilar_reference,),
    )
    assert not any(
        item["existing_identity"] == "SYNTHETIC/DISSIMILAR"
        for item in conflicts
    )
    assert audit.sequence_identity_comparison_count == 816


def test_identical_sequence_control_reports_exact_and_similarity_axes(
    source_payloads,
) -> None:
    component = owner._extract_poa_component_v1(
        source_payloads[owner._PROCESSING_VIEW_V1]
    )
    evidence = dict(component.evidence_by_event[0][1])
    identical = {
        "ligand_graph_sha256": "7" * 64,
        "ligand_scaffold_sha256": "8" * 64,
        "protein_accession": "SYNTHETIC_ACCESSION",
        "protein_sequence_sha256": evidence["protein_sequence_sha256"],
        "protein_sequence": evidence["protein_sequence"],
    }
    assert owner.bulk_owner._leakage_linking_axes_v1(evidence, identical) == [
        "PROTEIN_EXACT_SEQUENCE",
        "PROTEIN_SEQUENCE_IDENTITY_GE_0.5",
    ]


def test_missing_unknown_or_conflicting_component_sequence_fails_closed(
    source_payloads,
) -> None:
    (
        _groups, batch_registry, ndu_registry, sequence_evidence,
        _group_count, _sequence_count,
    ) = _sequence_context(source_payloads)
    missing = dict(sequence_evidence)
    missing.pop(next(iter(missing)))
    _assert_rejected(lambda: owner._component_axis_references_v1(
        batch_registry,
        reason="SYNTHETIC_MISSING_SEQUENCE",
        protein_sequence_by_sha=missing,
    ))

    unknown_registry = copy.deepcopy(batch_registry)
    row = unknown_registry["components"][1]
    index = next(
        index for index, value in enumerate(row["source_evidence_linking_axis_values"])
        if value.startswith("PROTEIN_EXACT_SEQUENCE:")
    )
    row["source_evidence_linking_axis_values"][index] = (
        "PROTEIN_EXACT_SEQUENCE:" + "f" * 64
    )
    _assert_rejected(lambda: owner._component_registry_sequence_inventory_v1(
        unknown_registry, ndu_registry,
    ))

    conflicting = {"a" * 64: "AAAA"}
    _assert_rejected(lambda: owner._merge_sequence_evidence_v1(
        conflicting, {"a" * 64: "BBBB"}, reason="SYNTHETIC_CONFLICT",
    ))


def test_exact14_of_15_source_coverage_fails_before_cross_link(
    source_payloads,
) -> None:
    processing = json.loads(source_payloads[owner._PROCESSING_VIEW_V1])
    target_sha = (
        "1f8113a43a87f0ca1d568a37b516dcf3ecffd613c04514a77e0032e18c6dee38"
    )
    removed = 0
    for wrapper in processing["events"]:
        outcome = wrapper.get("processing_outcome", {})
        structural = outcome.get("structural_processing", {})
        leakage = structural.get("leakage_evidence", {})
        if leakage.get("protein_sequence_sha256") == target_sha:
            leakage["protein_sequence_sha256"] = ""
            leakage["protein_sequence"] = ""
            removed += 1
    assert removed > 0
    _groups, batch_registry, ndu_registry = owner._reconstruct_frozen_groups_v1(
        source_payloads
    )
    _assert_rejected(lambda: owner._complete_component_sequence_evidence_v1(
        processing_view_payload=_canonical_payload(processing),
        bulk_processing_payload=source_payloads[owner._BULK_PROCESSING_V1],
        carrier_payload=source_payloads[owner._MISSING_SEQUENCE_EVIDENCE_V1],
        batch_registry=batch_registry,
        ndu_registry=ndu_registry,
    ))


def test_formal_assignment_does_not_copy_read_only_token(source_payloads, result) -> None:
    component = owner._extract_poa_component_v1(
        source_payloads[owner._PROCESSING_VIEW_V1]
    )
    counterfactual = replace(component, read_only_split="test")
    generic, oracle, parity = owner._formal_assignment_v1(
        counterfactual, result.existing_frozen_groups_before,
    )
    poa_row = next(row for row in generic if row[0] == owner.POA_LEAKAGE_KEY_V1)
    assert poa_row[2] == "train"
    assert oracle.selected_split == "train"
    assert parity is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("formal_split", "validation"),
        ("formal_group_id", "COVAPIE_EXPANSION_LEAKAGE_GROUP_DRIFT"),
        ("generic_owner_oracle_parity", False),
        ("sequence_identity_reference_group_count", 4),
        ("sequence_identity_reference_sequence_count", 14),
        ("raw_sequence_reference_count", 32),
        ("sequence_identity_comparison_count", 791),
        ("cross_link_conflict_authoritatively_proven", False),
        ("cross_link_reference_group_count", 13),
        ("cross_link_reference_count", 63),
        ("protein_sequence_identity_axis_cross_link_coverage_complete", False),
        ("manual_split_override", True),
        ("randomization_used", True),
        ("random_seed", 7),
        ("sample_training_admitted", True),
        ("model_training_activation_authorized", True),
        ("ready_for_training", True),
    ),
)
def test_result_semantic_drift_fails_closed(result, field: str, value: object) -> None:
    drifted = replace(result, **{field: value})
    _assert_rejected(
        lambda: owner.validate_covapie_poa_full_component_formal_split_authority_v1(
            drifted
        )
    )


def test_generic_owner_oracle_assignment_mismatch_fails_closed(result) -> None:
    rows = list(result.generic_owner_assignment)
    index = next(
        index for index, row in enumerate(rows)
        if row[0] == owner.POA_LEAKAGE_KEY_V1
    )
    rows[index] = (rows[index][0], rows[index][1], "validation")
    drifted = replace(result, generic_owner_assignment=tuple(rows))
    _assert_rejected(
        lambda: owner.validate_covapie_poa_full_component_formal_split_authority_v1(
            drifted
        )
    )

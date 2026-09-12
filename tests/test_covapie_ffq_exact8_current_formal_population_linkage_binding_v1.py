from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_ffq_exact8_current_formal_population_linkage_binding_v1 as binding,
)


@pytest.fixture(scope="session")
def real_inputs() -> binding.BindingInputsV1:
    return binding.load_covapie_ffq_exact8_current_formal_population_linkage_binding_inputs_v1(
        repo_root=REPO_ROOT,
    )


@pytest.fixture(scope="session")
def real_result(
    real_inputs: binding.BindingInputsV1,
) -> binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1:
    return binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        real_inputs
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _event(
    pdb_id: str, ligand: str, *, graph: str, scaffold: str,
    accession: str, sequence: str,
) -> binding.EventEvidenceV1:
    event_id = (
        f"COVAPIE_CYS_SG_EVENT_V1:{pdb_id}:A:CYS:1-:SG:B:{ligand}:C1"
    )
    return binding.EventEvidenceV1(
        canonical_event_id=event_id,
        pdb_id=pdb_id,
        ligand_component_id=ligand,
        source_role="SYNTHETIC_FROZEN_SOURCE",
        source_lane="SYNTHETIC_LANE",
        evidence_complete=bool(graph and accession and sequence),
        ligand_graph_sha256=graph,
        ligand_scaffold_sha256=scaffold,
        protein_accession=accession,
        protein_monomer_sequence_sha256=(
            _digest("MONOMER:" + sequence) if sequence else ""
        ),
        protein_one_letter_sequence=sequence,
        protein_one_letter_sequence_sha256=(
            _digest(sequence) if sequence else ""
        ),
    )


def _group(
    group_id: str, split: str, events: tuple[binding.EventEvidenceV1, ...],
    *, old: bool = False,
) -> binding.FormalGroupV1:
    event_ids = tuple(sorted(item.canonical_event_id for item in events))
    identities = tuple(sorted(
        f"{item.pdb_id}/{item.ligand_component_id}" for item in events
    ))
    return binding.FormalGroupV1(
        formal_group_id=group_id,
        formal_split=split,
        leakage_key="KEY:" + group_id,
        member_identity_count=len(identities),
        full_event_count=len(event_ids),
        member_pdb_ligand_identities=identities,
        full_member_canonical_event_ids=event_ids,
        old57_member_canonical_event_ids=event_ids if old else (),
        membership_sources=("SYNTHETIC_FORMAL_OWNER",),
        identifier_lineage=("SYNTHETIC_CANONICAL_LINEAGE",),
    )


def _inputs(
    events: tuple[binding.EventEvidenceV1, ...],
    groups: tuple[binding.FormalGroupV1, ...],
    seeds: tuple[str, ...], *, empty_graph: str = "",
    extra_dispositions: tuple[binding.TrainingDispositionV1, ...] = (),
) -> binding.BindingInputsV1:
    ordered_seeds = tuple(sorted(seeds))
    old_ids = {
        event_id for group in groups
        for event_id in group.old57_member_canonical_event_ids
    }
    event_by_id = {item.canonical_event_id: item for item in events}
    dispositions = tuple(sorted((
        binding.TrainingDispositionV1(
            canonical_event_id=event_id,
            training_use_disposition="UNRESOLVED",
            human_training_excluded=False,
            formal_split_authoritative=False,
            formal_split="",
        ) for event_id in ordered_seeds
    ), key=lambda item: item.canonical_event_id)) + extra_dispositions
    assert set(ordered_seeds) <= set(event_by_id)
    return binding.BindingInputsV1(
        source_bindings=(),
        formal_authority_source_binding_sha256="a" * 64,
        predictor_lane_counts=(("SYNTHETIC_LANE", len(set(
            event.canonical_event_id for event in events
        ))),),
        universe_events=events,
        formal_groups=groups,
        specified_seed_event_ids=ordered_seeds,
        required_seed_event_ids=ordered_seeds,
        frozen_report_covered_pairs=tuple(sorted(
            (seed, member) for seed in ordered_seeds for member in old_ids
        )),
        verified_empty_scaffold_graph_sha256=empty_graph,
        training_dispositions=dispositions,
        expected_formal_population_inventory_sha256=(
            binding._formal_inventory_sha256(groups)
        ),
    )


def test_real_population_reconstructs_current_15_not_old_formal14(
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    assert real_result.current_formal_group_count == 15
    assert real_result.current_formal_identity_count == 48
    assert real_result.current_formal_event_count == 109
    assert real_result.old_formal_scope_event_count == 57
    poa = next(
        group for group in real_result.formal_groups
        if group.formal_group_id == "COVAPIE_EXPANSION_LEAKAGE_GROUP_F70DB37A8004AF17"
    )
    assert poa.full_event_count == 24
    assert poa.member_identity_count == 3
    assert poa.old57_member_canonical_event_ids == ()


def test_real_ndu_is_full_33_not_truncated_five(
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    ndu = next(
        group for group in real_result.formal_groups
        if group.formal_group_id == "COVAPIE_LEAKAGE_GROUP_000005"
    )
    assert len(ndu.old57_member_canonical_event_ids) == 5
    assert ndu.full_event_count == 33
    assert ndu.member_identity_count == 9
    assert set(ndu.old57_member_canonical_event_ids) < set(
        ndu.full_member_canonical_event_ids
    )


def test_real_closure_exceeds_exact8_and_remains_fail_closed(
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    assert len(real_result.specified_seed_event_ids) == 8
    assert len(real_result.closure_event_ids) == 10
    assert {":3KR6:", ":3LTH:"} == {
        next(marker for marker in (":3KR6:", ":3LTH:") if marker in event_id)
        for event_id in real_result.newly_discovered_linked_event_ids
    }
    assert len(real_result.verified_component_edges) == 45
    assert real_result.closure_complete_within_frozen_universe is False
    assert len(real_result.closure_unknown_relations) == 2300
    assert len({row.universe_event_id for row in real_result.closure_unknown_relations}) == 230
    assert real_result.binding_status == binding.STATUS_INCOMPLETE


def test_real_formal_population_five_axis_coverage_is_complete_and_negative(
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    assert real_result.formal_population_comparison_complete is True
    assert real_result.reachable_formal_group_ids == ()
    assert real_result.reachable_formal_splits == ()
    assert real_result.cross_split_conflict is False
    by_axis = {row.axis: row for row in real_result.formal_population_axis_coverage}
    for axis in binding.AXES_V1:
        row = by_axis[axis]
        assert row.logical_pair_count == 1090
        assert row.positive_pair_count == 0
        assert row.negative_pair_count == 1090
        assert row.unknown_logical_pair_count == 0
        assert row.frozen_report_coverage_overlap_pair_count == 456
        assert (
            row.current_evidence_judged_logical_pair_count
            + row.policy_short_circuit_logical_pair_count
            + row.unknown_logical_pair_count
        ) == row.logical_pair_count
    assert by_axis["LIGAND_SCAFFOLD"].current_evidence_judged_logical_pair_count == 0
    assert by_axis["LIGAND_SCAFFOLD"].policy_short_circuit_logical_pair_count == 1090
    assert (
        by_axis["LIGAND_SCAFFOLD"].policy_short_circuit_logical_pair_count
        + by_axis["LIGAND_SCAFFOLD"].frozen_report_coverage_overlap_pair_count
        > by_axis["LIGAND_SCAFFOLD"].logical_pair_count
    )
    for axis in set(binding.AXES_V1) - {"LIGAND_SCAFFOLD"}:
        assert by_axis[axis].current_evidence_judged_logical_pair_count == 1090


def test_real_universe_is_frozen_1027_and_unknowns_are_not_false(
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    assert real_result.predictor_universe_event_count == 1027
    assert dict(real_result.predictor_lane_counts) == {
        "FROZEN_HISTORICAL_PREDECESSOR": 250,
        "KNOWN_EXISTING_CONTROL_REFERENCE": 27,
        "NEW_INCREMENTAL_EXECUTION": 250,
        "RANKS_0501_1000": 500,
    }
    by_axis = {row.axis: row for row in real_result.universe_axis_coverage}
    assert by_axis["LIGAND_GRAPH"].unknown_logical_pair_count == 1840
    assert by_axis["PROTEIN_ACCESSION"].unknown_logical_pair_count == 1810
    assert by_axis["PROTEIN_EXACT_SEQUENCE"].unknown_logical_pair_count == 1350
    assert by_axis["PROTEIN_SEQUENCE_IDENTITY_GE_0.5"].unknown_logical_pair_count == 1350
    assert by_axis["LIGAND_SCAFFOLD"].frozen_report_coverage_overlap_pair_count == 456
    assert by_axis["LIGAND_SCAFFOLD"].policy_short_circuit_logical_pair_count == 10215


def test_real_source_bindings_dispositions_permissions_and_exact5(
    real_inputs: binding.BindingInputsV1,
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    binding._validate_source_bindings(real_inputs.source_bindings)
    assert len(real_result.source_bindings) == 14
    assert len(real_result.source_semantic_sha256) == 64
    assert len(real_result.output_semantic_sha256) == 64
    assert [row.training_use_disposition for row in real_result.seed_training_dispositions].count("INCLUDE") == 4
    assert [row.training_use_disposition for row in real_result.seed_training_dispositions].count("EXCLUDE_FROM_TRAINING_ONLY") == 4
    assert {row.training_use_disposition for row in real_result.newly_discovered_training_dispositions} == {"UNRESOLVED"}
    assert real_result.newly_discovered_missing_disposition_event_ids == ()
    assert real_result.seed_disposition_readback_complete is True
    assert real_result.newly_discovered_disposition_readback_complete is True
    assert real_result.closure_disposition_readback_complete is True
    assert real_result.permissions == binding._PERMISSIONS_V1
    assert real_result.canonical_exact5 == binding.CANONICAL_EXACT5_V1


def test_real_loader_preserves_applicable_non_ffq_global_census_readback(
    real_inputs: binding.BindingInputsV1,
) -> None:
    census_binding = next(
        row for row in real_inputs.source_bindings
        if row.role == "CURRENT_GLOBAL_DISPOSITION_CENSUS"
    )
    assert "current_global_readiness_census" in census_binding.schema
    with (REPO_ROOT / census_binding.relative_path).open(
        newline="", encoding="utf-8",
    ) as handle:
        census_rows = tuple(csv.DictReader(handle))
    census_by_id = {row["canonical_event_id"]: row for row in census_rows}
    assert len(census_by_id) == len(census_rows)

    universe_by_id = {
        event.canonical_event_id: event for event in real_inputs.universe_events
    }
    loaded_by_id = {
        row.canonical_event_id: row for row in real_inputs.training_dispositions
    }
    expected_readback_ids = set(universe_by_id).intersection(census_by_id)
    assert set(loaded_by_id) == expected_readback_ids
    assert set(universe_by_id) - expected_readback_ids

    non_ffq_readback_ids = sorted(
        event_id for event_id in expected_readback_ids
        if universe_by_id[event_id].ligand_component_id != "FFQ"
    )
    assert non_ffq_readback_ids
    poa_event_id = "COVAPIE_CYS_SG_EVENT_V1:4I3U:A:CYS:291-:SG:I:POA:C2"
    assert poa_event_id in non_ffq_readback_ids
    raw = census_by_id[poa_event_id]
    assert loaded_by_id[poa_event_id] == binding.TrainingDispositionV1(
        canonical_event_id=poa_event_id,
        training_use_disposition=raw["training_use_disposition"],
        human_training_excluded=raw["human_training_excluded"] == "true",
        formal_split_authoritative=raw["formal_split_authoritative"] == "true",
        formal_split=raw["formal_split"],
    )


def test_validator_rejects_old_formal14_that_omits_poa(
    real_inputs: binding.BindingInputsV1,
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    bad = replace(real_result, formal_groups=real_result.formal_groups[:-1])
    with pytest.raises(ValueError, match="RESULT_DOES_NOT_MATCH_RECOMPUTED_BINDING"):
        binding.validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
            bad, inputs=real_inputs,
        )


def test_validator_rejects_full_group_id_with_ndu_members_truncated_to_five(
    real_inputs: binding.BindingInputsV1,
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    groups = list(real_result.formal_groups)
    index = next(i for i, group in enumerate(groups) if group.formal_group_id == "COVAPIE_LEAKAGE_GROUP_000005")
    group = groups[index]
    groups[index] = replace(
        group,
        full_event_count=5,
        full_member_canonical_event_ids=group.old57_member_canonical_event_ids,
    )
    bad = replace(real_result, formal_groups=tuple(groups))
    with pytest.raises(ValueError, match="RESULT_DOES_NOT_MATCH_RECOMPUTED_BINDING"):
        binding.validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
            bad, inputs=real_inputs,
        )


def test_event_count_and_identity_count_are_not_interchangeable(
    real_inputs: binding.BindingInputsV1,
) -> None:
    groups = list(real_inputs.formal_groups)
    index = next(i for i, group in enumerate(groups) if group.full_event_count != group.member_identity_count)
    groups[index] = replace(groups[index], full_event_count=groups[index].member_identity_count)
    bad = replace(real_inputs, formal_groups=tuple(groups))
    with pytest.raises(ValueError, match="FORMAL_GROUP_FIELDS_OR_COUNTS_INVALID"):
        binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(bad)


def test_specified_seeds_missing_one_4r7u_fail_closed(
    real_inputs: binding.BindingInputsV1,
) -> None:
    missing = next(event_id for event_id in real_inputs.specified_seed_event_ids if ":4R7U:" in event_id)
    bad = replace(
        real_inputs,
        specified_seed_event_ids=tuple(
            event_id for event_id in real_inputs.specified_seed_event_ids if event_id != missing
        ),
    )
    with pytest.raises(ValueError, match="SPECIFIED_SEED_INVENTORY_INVALID"):
        binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(bad)


def test_source_hash_and_report_schema_tampering_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    real_inputs: binding.BindingInputsV1,
) -> None:
    first = binding._SOURCE_SPECS_V1[0]
    monkeypatch.setattr(
        binding, "_SOURCE_SPECS_V1",
        (replace(first, sha256="0" * 64), *binding._SOURCE_SPECS_V1[1:]),
    )
    with pytest.raises(ValueError, match="SOURCE_SHA256_MISMATCH"):
        binding._read_bound_payloads_v1(REPO_ROOT)
    sequence_binding = next(
        row for row in real_inputs.source_bindings
        if row.role == "FROZEN_EXACT8_SEQUENCE_AUDIT_REPORT"
    )
    report_path = REPO_ROOT.parent / sequence_binding.relative_path
    report = json.loads(report_path.read_text())
    report["schema_version"] = "tampered"
    with pytest.raises(ValueError, match="SEQUENCE_REPORT_CONTRACT_INVALID"):
        binding._member_sets_from_sequence_report(report)


def test_input_reordering_and_identical_duplicates_are_deterministic() -> None:
    graph_a, graph_b = _digest("ga"), _digest("gb")
    seed = _event("1AAA", "AAA", graph=graph_a, scaffold=_digest("sa"), accession="A", sequence="AAAAAA")
    formal = _event("1BBB", "BBB", graph=graph_b, scaffold=_digest("sb"), accession="B", sequence="RRRRRR")
    group = _group("GROUP_B", "train", (formal,))
    inputs = _inputs((seed, formal), (group,), (seed.canonical_event_id,))
    expected = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(inputs)
    reordered = replace(
        inputs,
        universe_events=(formal, seed, seed),
        formal_groups=tuple(reversed(inputs.formal_groups)),
    )
    observed = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(reordered)
    assert binding.canonical_json_bytes_v1(expected) == binding.canonical_json_bytes_v1(observed)


def test_monomer_digest_cannot_impersonate_one_letter_digest() -> None:
    seed = _event("2AAA", "AAA", graph=_digest("g1"), scaffold=_digest("s1"), accession="A", sequence="AAAAAA")
    formal = _event("2BBB", "BBB", graph=_digest("g2"), scaffold=_digest("s2"), accession="B", sequence="RRRRRR")
    group = _group("GROUP_M", "train", (formal,))
    inputs = _inputs((seed, formal), (group,), (seed.canonical_event_id,))
    bad_seed = replace(
        seed,
        protein_one_letter_sequence_sha256=seed.protein_monomer_sequence_sha256,
    )
    bad = replace(inputs, universe_events=(bad_seed, formal))
    with pytest.raises(ValueError, match="MONOMER_AND_ONE_LETTER_DIGEST_DEFINITIONS_CONFLATED"):
        binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(bad)


def test_verified_empty_scaffold_short_circuit_differs_from_missing_input() -> None:
    graph = _digest("ffq-graph")
    seed = _event("3AAA", "FFQ", graph=graph, scaffold="", accession="A", sequence="AAAAAA")
    formal = _event("3BBB", "BBB", graph=_digest("other"), scaffold="", accession="B", sequence="RRRRRR")
    group = _group("GROUP_S", "train", (formal,))
    short = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        _inputs((seed, formal), (group,), (seed.canonical_event_id,), empty_graph=graph)
    )
    missing = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        _inputs((seed, formal), (group,), (seed.canonical_event_id,), empty_graph="")
    )
    short_axis = next(row for row in short.formal_population_axis_coverage if row.axis == "LIGAND_SCAFFOLD")
    missing_axis = next(row for row in missing.formal_population_axis_coverage if row.axis == "LIGAND_SCAFFOLD")
    assert (short_axis.policy_short_circuit_logical_pair_count, short_axis.unknown_logical_pair_count) == (1, 0)
    assert (missing_axis.policy_short_circuit_logical_pair_count, missing_axis.unknown_logical_pair_count) == (0, 1)


def test_positive_and_unknown_axes_are_both_retained() -> None:
    graph = _digest("shared")
    seed = _event("4AAA", "FFQ", graph=graph, scaffold="", accession="A", sequence="AAAAAA")
    formal = _event("4BBB", "BBB", graph=graph, scaffold="", accession="", sequence="")
    group = _group("GROUP_U", "train", (formal,))
    result = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        _inputs((seed, formal), (group,), (seed.canonical_event_id,), empty_graph=graph)
    )
    edge = next(row for row in result.verified_component_edges if formal.canonical_event_id in {row.left_event_id, row.right_event_id})
    assert "LIGAND_GRAPH" in edge.positive_axes
    assert "PROTEIN_ACCESSION" in edge.unknown_axes
    assert "PROTEIN_EXACT_SEQUENCE" in edge.unknown_axes
    assert "PROTEIN_SEQUENCE_IDENTITY_GE_0.5" in edge.unknown_axes
    assert result.binding_status == binding.STATUS_INCOMPLETE


@pytest.mark.parametrize("middle_has_readback", (False, True))
def test_indirect_nonffq_middle_readback_is_optional_and_preserved(
    middle_has_readback: bool,
) -> None:
    seed = _event("5AAA", "FFQ", graph=_digest("bridge-g"), scaffold=_digest("s1"), accession="A", sequence="AAAAAA")
    middle = _event("5BBB", "BBB", graph=_digest("bridge-g"), scaffold=_digest("s2"), accession="BRIDGE", sequence="RRRRRR")
    formal = _event("5CCC", "CCC", graph=_digest("formal-g"), scaffold=_digest("s3"), accession="BRIDGE", sequence="NNNNNN")
    group = _group("GROUP_INDIRECT", "train", (formal,))
    formal_readback = binding.TrainingDispositionV1(
        canonical_event_id=formal.canonical_event_id,
        training_use_disposition="UNRESOLVED",
        human_training_excluded=False,
        formal_split_authoritative=False,
        formal_split="",
    )
    middle_readback = binding.TrainingDispositionV1(
        canonical_event_id=middle.canonical_event_id,
        training_use_disposition="EXCLUDE_FROM_TRAINING_ONLY",
        human_training_excluded=True,
        formal_split_authoritative=False,
        formal_split="",
    )
    extra_dispositions = (formal_readback,)
    if middle_has_readback:
        extra_dispositions += (middle_readback,)
    result = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        _inputs(
            (seed, middle, formal), (group,), (seed.canonical_event_id,),
            extra_dispositions=extra_dispositions,
        )
    )
    assert result.closure_event_ids == tuple(sorted((
        seed.canonical_event_id, middle.canonical_event_id, formal.canonical_event_id,
    )))
    assert result.reachable_formal_group_ids == ("GROUP_INDIRECT",)
    assert result.binding_status == binding.STATUS_COMPLETE_WITH_LINKAGE
    assert len(result.verified_component_edges) == 2
    discovered_by_id = {
        row.canonical_event_id: row
        for row in result.newly_discovered_training_dispositions
    }
    if middle_has_readback:
        assert discovered_by_id[middle.canonical_event_id] == middle_readback
        assert result.newly_discovered_missing_disposition_event_ids == ()
        assert result.newly_discovered_disposition_readback_complete is True
        assert result.closure_disposition_readback_complete is True
    else:
        assert middle.canonical_event_id not in discovered_by_id
        assert result.newly_discovered_missing_disposition_event_ids == (
            middle.canonical_event_id,
        )
        assert result.newly_discovered_disposition_readback_complete is False
        assert result.closure_disposition_readback_complete is False
    assert dict(result.permissions)["FORMAL_SPLIT_ASSIGNMENT_CREATED"] is False


def test_cross_split_linkage_is_a_distinct_conflict_status() -> None:
    graph = _digest("cross-split")
    seed = _event("6AAA", "AAA", graph=graph, scaffold=_digest("s0"), accession="A", sequence="AAAAAA")
    train = _event("6BBB", "BBB", graph=graph, scaffold=_digest("s1"), accession="B", sequence="RRRRRR")
    valid = _event("6CCC", "CCC", graph=graph, scaffold=_digest("s2"), accession="C", sequence="NNNNNN")
    groups = (
        _group("GROUP_TRAIN", "train", (train,)),
        _group("GROUP_VALID", "validation", (valid,)),
    )
    result = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        _inputs((seed, train, valid), groups, (seed.canonical_event_id,))
    )
    assert result.reachable_formal_splits == ("train", "validation")
    assert result.cross_split_conflict is True
    assert result.binding_status == binding.STATUS_CROSS_SPLIT_CONFLICT


def test_frozen_report_overlap_is_annotation_not_skipped_judgment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = _event("7AAA", "AAA", graph=_digest("g7a"), scaffold=_digest("s7a"), accession="A", sequence="AAAAAA")
    formal = _event("7BBB", "BBB", graph=_digest("g7b"), scaffold=_digest("s7b"), accession="B", sequence="RRRRRR")
    group = _group("GROUP_OLD", "train", (formal,), old=True)
    inputs = _inputs((seed, formal), (group,), (seed.canonical_event_id,))
    original = binding._pair_statuses
    observed_pairs: list[frozenset[str]] = []

    def counted_pair_statuses(*args: object, **kwargs: object) -> object:
        left, right = args[:2]
        observed_pairs.append(frozenset((left.canonical_event_id, right.canonical_event_id)))
        return original(*args, **kwargs)

    monkeypatch.setattr(binding, "_pair_statuses", counted_pair_statuses)
    result = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(inputs)
    assert frozenset((seed.canonical_event_id, formal.canonical_event_id)) in observed_pairs
    for row in result.formal_population_axis_coverage:
        assert row.logical_pair_count == 1
        assert row.current_evidence_judged_logical_pair_count == 1
        assert row.policy_short_circuit_logical_pair_count == 0
        assert row.unknown_logical_pair_count == 0
        assert row.frozen_report_coverage_overlap_pair_count == 1


def test_output_vocabulary_does_not_claim_unimplemented_reuse_or_saved_compute() -> None:
    axis_fields = set(binding.AxisCoverageV1.__dataclass_fields__)
    assert "actual_new_computation_count" not in axis_fields
    assert "verified_existing_result_reuse_count" not in axis_fields
    checker = (
        REPO_ROOT / "scripts/check_covapie_ffq_exact8_current_formal_population_linkage_binding_v1.py"
    ).read_text()
    assert "new_computations" not in checker
    assert "verified_reuse" not in checker
    assert "frozen_report_coverage_overlap_pairs" in checker


def test_disposition_loader_requires_seed_but_allows_optional_nonseed_missing() -> None:
    seed_id = "COVAPIE_CYS_SG_EVENT_V1:8AAA:A:CYS:1-:SG:B:AAA:C1"
    middle_id = "COVAPIE_CYS_SG_EVENT_V1:8BBB:A:CYS:1-:SG:B:BBB:C1"
    payload = (
        "canonical_event_id,training_use_disposition,human_training_excluded,"
        "formal_split_authoritative,formal_split\n"
        f"{seed_id},UNRESOLVED,false,false,\n"
    ).encode("utf-8")
    rows = binding._parse_training_dispositions(
        payload,
        required_event_ids={seed_id},
        readback_scope_event_ids={seed_id, middle_id},
    )
    assert tuple(row.canonical_event_id for row in rows) == (seed_id,)
    with pytest.raises(ValueError, match="CURRENT_CENSUS_REQUIRED_EVENT_MISSING"):
        binding._parse_training_dispositions(
            payload,
            required_event_ids={middle_id},
            readback_scope_event_ids={seed_id, middle_id},
        )


def test_newly_discovered_real_readback_is_preserved_not_defaulted() -> None:
    graph = _digest("readback-link")
    seed = _event("9AAA", "AAA", graph=graph, scaffold=_digest("s9a"), accession="A", sequence="AAAAAA")
    middle = _event("9BBB", "BBB", graph=graph, scaffold=_digest("s9b"), accession="B", sequence="RRRRRR")
    formal = _event("9CCC", "CCC", graph=_digest("g9c"), scaffold=_digest("s9c"), accession="C", sequence="NNNNNN")
    group = _group("GROUP_READBACK", "test", (formal,))
    middle_readback = binding.TrainingDispositionV1(
        canonical_event_id=middle.canonical_event_id,
        training_use_disposition="EXCLUDE_FROM_TRAINING_ONLY",
        human_training_excluded=True,
        formal_split_authoritative=False,
        formal_split="",
    )
    result = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        _inputs(
            (seed, middle, formal), (group,), (seed.canonical_event_id,),
            extra_dispositions=(middle_readback,),
        )
    )
    assert result.newly_discovered_training_dispositions == (middle_readback,)
    assert result.newly_discovered_missing_disposition_event_ids == ()
    assert result.newly_discovered_disposition_readback_complete is True


def test_validator_actually_recomputes_pair_judgments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = _event("0AAA", "AAA", graph=_digest("g0a"), scaffold=_digest("s0a"), accession="A", sequence="AAAAAA")
    formal = _event("0BBB", "BBB", graph=_digest("g0b"), scaffold=_digest("s0b"), accession="B", sequence="RRRRRR")
    group = _group("GROUP_VALIDATE", "train", (formal,))
    inputs = _inputs((seed, formal), (group,), (seed.canonical_event_id,))
    result = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(inputs)
    original = binding._pair_statuses
    call_count = 0

    def counted_pair_statuses(*args: object, **kwargs: object) -> object:
        nonlocal call_count
        call_count += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(binding, "_pair_statuses", counted_pair_statuses)
    assert binding.validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        result, inputs=inputs,
    ) is True
    assert call_count > 0


@pytest.mark.parametrize(
    "mutation",
    ("permissions", "split", "relation", "4r7u_disposition"),
)
def test_permissions_split_relations_and_4r7u_disposition_tampering_fail_closed(
    mutation: str,
    real_inputs: binding.BindingInputsV1,
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    if mutation == "4r7u_disposition":
        rows = list(real_inputs.training_dispositions)
        index = next(i for i, row in enumerate(rows) if ":4R7U:" in row.canonical_event_id)
        rows[index] = replace(
            rows[index], training_use_disposition="INCLUDE", human_training_excluded=False,
        )
        bad_inputs = replace(real_inputs, training_dispositions=tuple(rows))
        with pytest.raises(ValueError, match="SPECIFIED_SEED_TRAINING_DISPOSITION_CHANGED"):
            binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
                bad_inputs
            )
        return
    if mutation == "permissions":
        bad = replace(real_result, permissions=tuple((key, True) for key, _value in real_result.permissions))
    elif mutation == "split":
        groups = list(real_result.formal_groups)
        groups[0] = replace(groups[0], formal_split="train" if groups[0].formal_split != "train" else "test")
        bad = replace(real_result, formal_groups=tuple(groups))
    else:
        assert real_result.verified_component_edges
        edges = list(real_result.verified_component_edges)
        edges[0] = replace(edges[0], positive_axes=("PROTEIN_ACCESSION",))
        bad = replace(real_result, verified_component_edges=tuple(edges))
    with pytest.raises(ValueError, match="RESULT_DOES_NOT_MATCH_RECOMPUTED_BINDING"):
        binding.validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
            bad, inputs=real_inputs,
        )


def test_public_builder_and_validator_are_byte_deterministic(
    real_inputs: binding.BindingInputsV1,
    real_result: binding.FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> None:
    binding.validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        real_result, inputs=real_inputs,
    )
    second = binding.compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        real_inputs
    )
    assert binding.canonical_json_bytes_v1(real_result) == binding.canonical_json_bytes_v1(second)
    public = binding.build_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        repo_root=REPO_ROOT,
    )
    assert binding.canonical_json_bytes_v1(real_result) == binding.canonical_json_bytes_v1(public)
    assert real_result.output_semantic_sha256 == binding._result_output_sha256(real_result)

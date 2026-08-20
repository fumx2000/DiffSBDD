from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from covalent_ext import (
    covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1 as successor,
)
from covalent_ext import (
    covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1 as gate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import (
    check_covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1
    as checker,
)


CACHE_ROOT = REPO_ROOT.parent / gate.CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT


@pytest.fixture(scope="module")
def evidence() -> dict[str, Any]:
    return gate._load_calibration_snapshot_evidence_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def context() -> Any:
    return gate.build_static_rule_context_v1(
        repo_root=REPO_ROOT, cache_root=CACHE_ROOT
    )


@pytest.fixture(scope="module")
def override(evidence: dict[str, Any]) -> Any:
    return gate.build_calibration_snapshot_positive_override_context_v1(
        immutable_calibration_human=evidence["calibration_human"],
        frozen_outcome_by_id=evidence["outcome_by_id"],
    )


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return gate.build_artifacts_v1(repo_root=REPO_ROOT, cache_root=CACHE_ROOT)


def _copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _event_id(
    evidence: dict[str, Any], *, pdb_id: str, component: str, atom: str
) -> str:
    matches = [
        event_id
        for event_id, event in evidence["event_by_id"].items()
        if event["pdb_id"] == pdb_id
        and event["ligand_component_id"] == component
        and event["ligand_reactive_atom"] == atom
    ]
    assert len(matches) == 1
    return matches[0]


def _evaluate(
    evidence: dict[str, Any], context: Any, override: Any, event_id: str
) -> Any:
    return gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=evidence["event_by_id"][event_id],
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=context,
        override_context=override,
    )


def _synthetic_common_repository_state(commit: str) -> dict[str, Any]:
    return {
        "branch": "main",
        "head": commit,
        "origin_main": commit,
        "ahead": 0,
        "behind": 0,
        "calibration_commit": gate.CALIBRATION_COMMIT,
        "calibration_is_ancestor_of_head": True,
        "calibration_is_ancestor_of_origin_main": True,
        "descendant_repository_compatible": True,
    }


def test_current_repository_accepts_successor_base_ancestry() -> None:
    state = gate.verify_repository_binding_v1(REPO_ROOT)
    assert state["head"] == state["origin_main"]
    assert state["ahead"] == state["behind"] == 0
    assert state["base_successor_routing_commit"] == (
        gate.BASE_SUCCESSOR_ROUTING_COMMIT
    )
    assert state["base_successor_routing_subject"] == (
        gate.BASE_SUCCESSOR_ROUTING_SUBJECT
    )
    assert state["base_successor_routing_commit_is_ancestor_of_head"] is True
    assert (
        state["base_successor_routing_commit_is_ancestor_of_origin_main"] is True
    )
    assert state["descendant_repository_compatible"] is True


def test_synthetic_synchronized_descendant_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descendant = "d" * 40
    monkeypatch.setattr(
        gate.common,
        "verify_repository_binding_v1",
        lambda _repo_root: _synthetic_common_repository_state(descendant),
    )
    monkeypatch.setattr(
        gate,
        "_git",
        lambda _repo_root, *_arguments: gate.BASE_SUCCESSOR_ROUTING_SUBJECT,
    )
    monkeypatch.setattr(gate, "_git_is_ancestor", lambda *_arguments: True)
    state = gate.verify_repository_binding_v1(REPO_ROOT)
    assert state["head"] == descendant
    assert state["origin_main"] == descendant
    assert state["head"] != gate.BASE_SUCCESSOR_ROUTING_COMMIT
    assert state["descendant_repository_compatible"] is True


def test_head_origin_mismatch_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_mismatch(_repo_root: Path) -> dict[str, Any]:
        raise ValueError("HEAD_ORIGIN_MAIN_MISMATCH")

    monkeypatch.setattr(gate.common, "verify_repository_binding_v1", reject_mismatch)
    with pytest.raises(ValueError, match="HEAD_ORIGIN_MAIN_MISMATCH"):
        gate.verify_repository_binding_v1(REPO_ROOT)


@pytest.mark.parametrize(
    "rejected_target,error_message",
    (
        ("HEAD", "BASE_SUCCESSOR_ROUTING_COMMIT_NOT_ANCESTOR_OF_HEAD"),
        (
            "refs/remotes/origin/main",
            "BASE_SUCCESSOR_ROUTING_COMMIT_NOT_ANCESTOR_OF_ORIGIN_MAIN",
        ),
    ),
)
def test_successor_base_not_ancestor_is_rejected(
    rejected_target: str,
    error_message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descendant = "e" * 40
    monkeypatch.setattr(
        gate.common,
        "verify_repository_binding_v1",
        lambda _repo_root: _synthetic_common_repository_state(descendant),
    )
    monkeypatch.setattr(
        gate,
        "_git",
        lambda _repo_root, *_arguments: gate.BASE_SUCCESSOR_ROUTING_SUBJECT,
    )
    monkeypatch.setattr(
        gate,
        "_git_is_ancestor",
        lambda _repo_root, _ancestor, target: target != rejected_target,
    )
    with pytest.raises(ValueError, match=error_message):
        gate.verify_repository_binding_v1(REPO_ROOT)


def test_wrong_successor_base_subject_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descendant = "f" * 40
    monkeypatch.setattr(
        gate.common,
        "verify_repository_binding_v1",
        lambda _repo_root: _synthetic_common_repository_state(descendant),
    )
    monkeypatch.setattr(
        gate, "_git", lambda _repo_root, *_arguments: "wrong successor subject"
    )
    monkeypatch.setattr(gate, "_git_is_ancestor", lambda *_arguments: True)
    with pytest.raises(
        ValueError, match="BASE_SUCCESSOR_ROUTING_SUBJECT_BINDING_MISMATCH"
    ):
        gate.verify_repository_binding_v1(REPO_ROOT)


def test_immutable_dtt_human_gold_exact_binding() -> None:
    human = gate.load_immutable_dtt_human_gold_v1(REPO_ROOT)
    unit = next(
        item
        for item in human["units"]
        if item["review_unit_id"] == gate.CALIBRATION_UNIT_ID
    )
    assert unit["workflow_status"] == "COMPLETED"
    assert unit["training_domain_relevance_decision"] == (
        "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
    )
    assert unit["review_rationale"] == gate.CALIBRATION_RATIONALE
    assert unit["reactive_atom_confirmation"] is None
    assert unit["warhead_family_decision"] is None
    assert unit["warhead_atom_ids"] == []
    assert all(
        event[field] == ""
        for event in unit["events"]
        for field in (
            "post_geometry_training_usable",
            "event_training_use_decision",
            "event_exclusion_reason",
        )
    )


def test_immutable_history_is_read_from_git_object_not_guessed() -> None:
    human = gate.load_immutable_dtt_human_gold_v1(REPO_ROOT)
    history = [
        item
        for item in human["decision_history"]
        if item["review_unit_id"] == gate.CALIBRATION_UNIT_ID
    ]
    assert [item["sequence"] for item in history] == [65, 66, 67, 68, 69]
    assert [item["field"] for item in history] == [
        "training_domain_relevance_decision",
        "workflow_status",
        "reviewer_id",
        "reviewed_at_utc",
        "review_rationale",
    ]
    assert all(len(item["entry_sha256"]) == 64 for item in history)


def test_official_dtt_ccd_stereo_binding() -> None:
    dtt = gate._parse_official_ccd(
        repo_root=REPO_ROOT, cache_root=CACHE_ROOT, component_id="DTT"
    )
    assert dtt["source_binding"]["sha256"] == gate.DTT_CCD_SOURCE_SHA256
    assert dtt["inchikey"] == gate.DTT_INCHIKEY
    assert dtt["atom_stereo_config"] == {"C2": "R", "C3": "R"}
    assert dtt["heavy_atom_count"] == 8
    assert dtt["heavy_element_composition"] == {"C": 4, "O": 2, "S": 2}
    assert dtt["all_atom_formal_charges_zero"] is True
    assert dtt["all_heavy_bonds_single"] is True


def test_official_dtu_stereo_counterexample_binding() -> None:
    dtu = gate._parse_official_ccd(
        repo_root=REPO_ROOT, cache_root=CACHE_ROOT, component_id="DTU"
    )
    assert dtu["source_binding"]["sha256"] == gate.DTU_CCD_SOURCE_SHA256
    assert dtu["inchikey"] == gate.DTU_INCHIKEY
    assert dtu["atom_stereo_config"] == {"C2": "S", "C3": "R"}


def test_dtt_endpoint_automorphism_is_derived_from_ccd(context: Any) -> None:
    proof = context["endpoint_automorphism"]
    assert proof["DTT_ENDPOINT_AUTOMORPHISM_PROVEN"] is True
    assert proof["calibration_seed_atom"] == "S4"
    assert set(proof["reactive_sulfur_orbit"]) == {"S1", "S4"}
    assert proof["automorphism_count"] == 8
    mapping = proof["deterministic_endpoint_swap_mapping"]
    assert {
        "S1": mapping["S1"],
        "S4": mapping["S4"],
        "C1": mapping["C1"],
        "C4": mapping["C4"],
        "C2": mapping["C2"],
        "C3": mapping["C3"],
        "O2": mapping["O2"],
        "O3": mapping["O3"],
    } == {
        "S1": "S4",
        "S4": "S1",
        "C1": "C4",
        "C4": "C1",
        "C2": "C3",
        "C3": "C2",
        "O2": "O3",
        "O3": "O2",
    }


def test_dtt_automorphism_freezes_corresponding_hydrogens(context: Any) -> None:
    mapping = context["endpoint_automorphism"][
        "deterministic_endpoint_swap_mapping"
    ]
    assert mapping["HS1"] == "HS2"
    assert mapping["HS2"] == "HS1"
    assert mapping["H2"] == "H3"
    assert mapping["H3"] == "H2"
    assert mapping["HO2"] == "HO3"
    assert mapping["HO3"] == "HO2"
    assert {mapping["H11"], mapping["H12"]} == {"H41", "H42"}


def test_independent_1fvg_reagent_context(context: Any) -> None:
    source = context["independent_1fvg_reagent_context"]
    record = source["normalized_metadata_record"]
    assert source["source_binding"]["compressed_sha256"] == (
        gate.SOURCE_STRUCTURE_SHA256
    )
    assert record["entry_id"] == "1FVG"
    assert record["polymer_entity"]["details"] == "DITHIOTHREITOL COMPLEX"
    assert record["dtt_nonpolymer_entity"]["component_id"] == "DTT"
    assert "dithiothreitol" in record["crystallization"]["details"].lower()
    assert record["protein_reference"]["accession"] == "P54149"
    assert record["protein_reference"]["entity_poly_seq_sha256"] == (
        gate.SOURCE_PROTEIN_SEQUENCE_SHA256
    )
    assert source["pdb_id_is_not_a_sole_predicate"] is True
    assert source["crystallization_word_is_not_a_sole_predicate"] is True


def test_static_rule_builder_source_contains_no_shadow_label(
    evidence: dict[str, Any],
) -> None:
    shadow_event_id = _event_id(
        evidence, pdb_id="1FVG", component="DTT", atom="S1"
    )
    shadow_unit_id = evidence["unit_by_event"][shadow_event_id]
    source = inspect.getsource(gate._build_static_rule_context_v1)
    assert shadow_event_id not in source
    assert shadow_unit_id not in source


def test_context_invariant_after_removing_dtt_s1_from_evaluation_population(
    evidence: dict[str, Any], context: Any
) -> None:
    reduced_population = dict(evidence["event_by_id"])
    shadow_event_id = _event_id(
        evidence, pdb_id="1FVG", component="DTT", atom="S1"
    )
    del reduced_population[shadow_event_id]
    assert len(reduced_population) == 122
    rebuilt = gate.build_static_rule_context_v1(
        repo_root=REPO_ROOT, cache_root=CACHE_ROOT
    )
    assert gate.static_rule_context_bytes_v1(context) == (
        gate.static_rule_context_bytes_v1(rebuilt)
    )


def test_rule_context_is_deeply_immutable(context: Any) -> None:
    with pytest.raises(TypeError):
        context["rule_id"] = "changed"
    with pytest.raises(TypeError):
        context["exact_ligand_identity"]["component_id"] = "DTU"
    assert isinstance(context["required_predicates"], tuple)


def test_dtt_s4_calibration_matches(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    result = _evaluate(evidence, context, override, event_id)
    assert result.status == gate.MATCHED_AUTO_NEGATIVE_EXACT
    assert result.matched_predicates == gate.REQUIRED_PREDICATES


def test_dtt_s1_shadow_matches_without_label_input(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S1")
    result = _evaluate(evidence, context, override, event_id)
    assert result.status == gate.MATCHED_AUTO_NEGATIVE_EXACT
    assert result.reason == "ALL_EXACT_PREDICATES_MATCHED"


def test_total_shadow_match_is_exactly_two(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    results = [
        _evaluate(evidence, context, override, event_id)
        for event_id in evidence["event_by_id"]
    ]
    assert sum(item.status == gate.MATCHED_AUTO_NEGATIVE_EXACT for item in results) == 2
    assert sum(item.status == gate.INVALID_EVIDENCE for item in results) == 0


def test_dtu_does_not_match_and_reports_exact_failures(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1KZI", component="DTU", atom="S4")
    result = _evaluate(evidence, context, override, event_id)
    assert result.status == gate.NOT_MATCHED
    assert "exact_dtt_component_identity" in result.reason
    assert "exact_dtt_component_graph_sha256" in result.reason
    assert "exact_1fvg_source_structure_context" in result.reason


def test_dtt_dtu_nonstereo_graph_shape_but_stereo_boundary() -> None:
    dtt = gate._parse_official_ccd(
        repo_root=REPO_ROOT, cache_root=CACHE_ROOT, component_id="DTT"
    )
    dtu = gate._parse_official_ccd(
        repo_root=REPO_ROOT, cache_root=CACHE_ROOT, component_id="DTU"
    )
    dtt_heavy = {
        tuple(sorted((item["atom_id_1"], item["atom_id_2"])))
        for item in dtt["bond_identity"]
        if not item["atom_id_1"].startswith("H")
        and not item["atom_id_2"].startswith("H")
    }
    dtu_heavy = {
        tuple(sorted((item["atom_id_1"], item["atom_id_2"])))
        for item in dtu["bond_identity"]
        if not item["atom_id_1"].startswith("H")
        and not item["atom_id_2"].startswith("H")
    }
    assert dtt_heavy == dtu_heavy
    assert dtt["inchikey"] != dtu["inchikey"]
    assert dtt["atom_stereo_config"] != dtu["atom_stereo_config"]
    assert gate.DTT_GRAPH_SHA256 != gate.DTU_GRAPH_SHA256


@pytest.mark.parametrize("component", gate.MANDATORY_COMPONENT_COUNTEREXAMPLES)
def test_broader_sulfur_and_named_counterexamples_do_not_match(
    component: str,
    evidence: dict[str, Any],
    context: Any,
    override: Any,
) -> None:
    event_ids = [
        event_id
        for event_id, event in evidence["event_by_id"].items()
        if event["ligand_component_id"] == component
    ]
    assert all(
        _evaluate(evidence, context, override, event_id).status
        != gate.MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in event_ids
    )


def test_human_relevant_counterexamples_do_not_match(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    relevant_ids = [
        event["canonical_event_id"]
        for unit in evidence["calibration_human_unit_by_id"].values()
        if unit["training_domain_relevance_decision"]
        == "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
        for event in unit["events"]
    ]
    assert relevant_ids
    assert all(
        _evaluate(evidence, context, override, event_id).status
        != gate.MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in relevant_ids
    )


@pytest.mark.parametrize(
    "override_field",
    (
        "current_human_relevant_event_ids",
        "current_production_exact_positive_event_ids",
        "explicit_positive_override_event_ids",
    ),
)
def test_each_runtime_positive_override_blocks_otherwise_matching_event(
    override_field: str,
    evidence: dict[str, Any],
    context: Any,
    override: Any,
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    overridden = replace(override, **{override_field: frozenset({event_id})})
    result = _evaluate(evidence, context, overridden, event_id)
    assert result.status == gate.NOT_MATCHED
    assert "no_runtime_positive_override" in result.reason


def test_malformed_override_context_never_matches(
    evidence: dict[str, Any], context: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=evidence["event_by_id"][event_id],
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=context,
        override_context=None,  # type: ignore[arg-type]
    )
    assert result.status == gate.INVALID_EVIDENCE


def test_wrong_dtt_graph_does_not_match(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    event = _copy(evidence["event_by_id"][event_id])
    event["ccd_component_graph_sha256"] = "0" * 64
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=event,
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.NOT_MATCHED
    assert "exact_dtt_component_graph_sha256" in result.reason


def test_wrong_endpoint_outside_derived_orbit_does_not_match(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    event = _copy(evidence["event_by_id"][event_id])
    event["ligand_reactive_atom"] = "O2"
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=event,
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.NOT_MATCHED
    assert "automorphism_derived_dtt_sulfur_endpoint" in result.reason


@pytest.mark.parametrize(
    "field,predicate",
    (
        ("reactive_center_radius1_fingerprint", "exact_radius1_sha256"),
        ("reactive_center_radius2_fingerprint", "exact_radius2_sha256"),
    ),
)
def test_wrong_local_radius_does_not_match(
    field: str,
    predicate: str,
    evidence: dict[str, Any],
    context: Any,
    override: Any,
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    event = _copy(evidence["event_by_id"][event_id])
    event[field] = "f" * 64
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=event,
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.NOT_MATCHED
    assert predicate in result.reason


def test_missing_required_evidence_is_invalid(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    event = _copy(evidence["event_by_id"][event_id])
    del event["ccd_component_graph_sha256"]
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=event,
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.INVALID_EVIDENCE


def test_malformed_required_coordinates_are_invalid(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    event = _copy(evidence["event_by_id"][event_id])
    event["selected_ligand_endpoint_coordinates_json"] = "not-json"
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=event,
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.INVALID_EVIDENCE


def test_source_annotation_conflict_blocks_match(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    event = _copy(evidence["event_by_id"][event_id])
    event["annotation_conflicts_json"] = '[{"conflict":"present"}]'
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=event,
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.NOT_MATCHED
    assert "no_source_annotation_conflict" in result.reason


def test_pdb_id_or_dtt_name_alone_is_not_sufficient(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    unrelated_id = next(
        event_id
        for event_id, event in evidence["event_by_id"].items()
        if event["pdb_id"] != "1FVG" and event["ligand_component_id"] != "DTT"
    )
    event = _copy(evidence["event_by_id"][unrelated_id])
    outcome = _copy(evidence["outcome_by_id"][unrelated_id])
    event["pdb_id"] = "1FVG"
    event["ligand_component_id"] = "DTT"
    outcome["pdb_id"] = "1FVG"
    outcome["ligand_component_id"] = "DTT"
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context=override,
    )
    assert result.status != gate.MATCHED_AUTO_NEGATIVE_EXACT


def test_partial_and_invalid_multi_event_units_fail_closed() -> None:
    match = gate.AutoNegativeEvaluationResult(
        gate.RULE_ID,
        gate.MATCHED_AUTO_NEGATIVE_EXACT,
        "ALL_EXACT_PREDICATES_MATCHED",
        gate.REQUIRED_PREDICATES,
    )
    invalid = gate.AutoNegativeEvaluationResult(
        gate.RULE_ID, gate.INVALID_EVIDENCE, "INVALID_EVIDENCE:test", ()
    )
    result = gate.aggregate_review_unit_shadow_v1(
        review_unit_id="TEST_UNIT", event_results=(match, invalid)
    )
    assert result.shadow_would_auto_negative is False
    assert result.status == gate.UNIT_NOT_SHADOW_AUTO_NEGATIVE
    assert result.matched_event_count == 1
    assert result.invalid_event_count == 1


def test_result_is_immutable(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    result = _evaluate(evidence, context, override, event_id)
    with pytest.raises(FrozenInstanceError):
        result.status = gate.NOT_MATCHED


@pytest.mark.parametrize("exception", (KeyboardInterrupt, SystemExit))
def test_base_exceptions_propagate(
    exception: type[BaseException], evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")

    class ExplodingEvent(dict[str, Any]):
        def get(self, key: str, default: Any = None) -> Any:
            if key == "post_only_partition":
                raise exception()
            return super().get(key, default)

    with pytest.raises(exception):
        gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
            event=ExplodingEvent(evidence["event_by_id"][event_id]),
            outcome=evidence["outcome_by_id"][event_id],
            rule_context=context,
            override_context=override,
        )


def test_deterministic_double_build_byte_identical() -> None:
    first = gate.build_artifacts_v1(repo_root=REPO_ROOT, cache_root=CACHE_ROOT)
    second = gate.build_artifacts_v1(repo_root=REPO_ROOT, cache_root=CACHE_ROOT)
    assert first == second


def test_synthetic_descendant_build_is_byte_identical(
    monkeypatch: pytest.MonkeyPatch, artifacts: dict[str, bytes]
) -> None:
    descendant = "a" * 40
    synthetic_state = {
        **_synthetic_common_repository_state(descendant),
        "base_successor_routing_commit": gate.BASE_SUCCESSOR_ROUTING_COMMIT,
        "base_successor_routing_subject": gate.BASE_SUCCESSOR_ROUTING_SUBJECT,
        "base_successor_routing_commit_is_ancestor_of_head": True,
        "base_successor_routing_commit_is_ancestor_of_origin_main": True,
    }
    monkeypatch.setattr(
        gate, "verify_repository_binding_v1", lambda _repo_root: synthetic_state
    )
    descendant_artifacts = gate.build_artifacts_v1(
        repo_root=REPO_ROOT, cache_root=CACHE_ROOT
    )
    assert descendant_artifacts == artifacts


def test_evolved_current_human_positive_override_and_artifact_invariance(
    evidence: dict[str, Any], context: Any, artifacts: dict[str, bytes]
) -> None:
    immutable_before = gate.load_immutable_dtt_human_gold_v1(REPO_ROOT)
    current = json.loads((REPO_ROOT / gate.HUMAN_DECISIONS_RELATIVE).read_bytes())
    evolved = _copy(current)
    shadow_event_id = _event_id(
        evidence, pdb_id="1FVG", component="DTT", atom="S1"
    )
    shadow_unit_id = evidence["unit_by_event"][shadow_event_id]
    shadow_unit = next(
        unit for unit in evolved["units"] if unit["review_unit_id"] == shadow_unit_id
    )
    shadow_unit["training_domain_relevance_decision"] = (
        "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
    )
    shadow_unit["workflow_status"] = "IN_PROGRESS"
    checker.validate_current_human_overlay_coverage_v1(
        current_human=evolved, evidence=evidence
    )
    evolved_payload = gate._json_bytes(evolved)
    evolved_sha = hashlib.sha256(evolved_payload).hexdigest()
    assert evolved_sha != gate.CALIBRATION_HUMAN_SHA256
    evolved_override = gate.build_runtime_positive_override_context_v1(
        current_human_overlay=evolved,
        current_human_overlay_sha256=evolved_sha,
        outcome_by_id=evidence["outcome_by_id"],
    )
    result = gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
        event=evidence["event_by_id"][shadow_event_id],
        outcome=evidence["outcome_by_id"][shadow_event_id],
        rule_context=context,
        override_context=evolved_override,
    )
    assert result.status == gate.NOT_MATCHED
    assert "no_runtime_positive_override" in result.reason
    assert shadow_event_id in evolved_override.current_human_relevant_event_ids
    rebuilt = gate.build_artifacts_v1(repo_root=REPO_ROOT, cache_root=CACHE_ROOT)
    assert rebuilt == artifacts
    assert gate.load_immutable_dtt_human_gold_v1(REPO_ROOT) == immutable_before


def test_checker_accepts_exact_precommit_and_published_clean_profiles() -> None:
    authorized = tuple(path.as_posix() for path in gate.AUTHORIZED_NEW_PATHS)
    assert checker.classify_worktree_profile_v1(
        modified=(), staged=(), untracked=authorized
    ) == checker.PRECOMMIT_CANDIDATE_PROFILE
    assert checker.classify_worktree_profile_v1(
        modified=(), staged=(), untracked=()
    ) == checker.PUBLISHED_CLEAN_DESCENDANT_PROFILE


@pytest.mark.parametrize(
    "modified,staged,untracked",
    (
        (("tracked.py",), (), ()),
        ((), ("staged.py",), ()),
        ((), (), ("arbitrary.txt",)),
    ),
)
def test_checker_rejects_every_other_worktree_profile(
    modified: tuple[str, ...],
    staged: tuple[str, ...],
    untracked: tuple[str, ...],
) -> None:
    with pytest.raises(AssertionError):
        checker.classify_worktree_profile_v1(
            modified=modified, staged=staged, untracked=untracked
        )


def test_checker_source_does_not_freeze_current_human_to_calibration() -> None:
    source = inspect.getsource(checker.check_v1)
    assert "== gate.CALIBRATION_HUMAN_SHA256" not in source
    assert 'immutable["units"] == current_human["units"]' not in source
    assert "current_human_overlay_sha256" in source


def test_rebuilt_artifacts_match_persisted_bytes(
    artifacts: dict[str, bytes]
) -> None:
    output_root = REPO_ROOT / gate.OUTPUT_ROOT_RELATIVE
    assert artifacts == {
        name: (output_root / name).read_bytes() for name in gate.OUTPUT_FILENAMES
    }


def test_published_successor_dispatcher_contract_accepts_dtt_result(
    evidence: dict[str, Any], context: Any, override: Any
) -> None:
    event_id = _event_id(evidence, pdb_id="1FVG", component="DTT", atom="S4")
    registration = successor.ExactAutoNegativeRuleRegistration(
        rule_id=gate.RULE_ID,
        evaluator=gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact,
    )
    result = successor.dispatch_exact_auto_negative_rules_v1(
        event=evidence["event_by_id"][event_id],
        outcome=evidence["outcome_by_id"][event_id],
        rule_context_by_id={gate.RULE_ID: context},
        override_context_by_id={gate.RULE_ID: override},
        registry=(registration,),
    )
    assert len(result) == 1
    assert result[0].rule_id == gate.RULE_ID
    assert result[0].status == gate.MATCHED_AUTO_NEGATIVE_EXACT


def test_dtt_rule_is_not_integrated_into_live_successor() -> None:
    assert gate.RULE_ID not in successor.INTEGRATED_AUTO_NEGATIVE_RULE_IDS
    source = inspect.getsource(successor)
    assert gate.RULE_ID not in source


def test_distance_is_not_an_identity_predicate() -> None:
    source = inspect.getsource(
        gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact
    )
    assert "post_distance" not in source
    assert "reported_distance" not in source


def test_artifact_summary_and_manifest_are_honest_shadow_only(
    artifacts: dict[str, bytes]
) -> None:
    manifest = json.loads(artifacts[gate.RULE_MANIFEST])
    summary = json.loads(artifacts[gate.SUMMARY])
    assert summary["candidate_event_count"] == 123
    assert summary["historical_review_unit_count"] == 36
    assert summary["observed_shadow_matched_event_count"] == 2
    assert summary["observed_shadow_matched_unit_count"] == 2
    assert summary["human_calibration_matched_event_count"] == 1
    assert summary[
        "calibration_snapshot_unreviewed_shadow_auto_negative_event_count"
    ] == 1
    assert summary["DTU_counterexample_match_count"] == 0
    assert summary["human_relevant_counterexample_match_count"] == 0
    assert summary["invalid_evidence_count"] == 0
    assert summary["DTT_endpoint_automorphism_proven"] is True
    assert summary["cross_CCD_DTU_generalization_authorized"] is False
    assert summary["cross_pdb_DTT_generalization_authorized"] is False
    assert summary["live_integration_ready"] is True
    assert summary["integration_into_live_successor_routing_performed"] is False
    assert summary["ready_for_gpt_review"] is True
    assert manifest["readiness_mode"] == gate.READINESS_MODE
    assert manifest["rule_context_source_contains_shadow_unit_or_event_id"] is False
    serialized = artifacts[gate.RULE_MANIFEST] + artifacts[gate.SUMMARY]
    for forbidden in (
        b'"current_head"',
        b'"origin_main"',
        b'"ahead"',
        b'"behind"',
        b'"current_human_overlay_sha256"',
        b'"current_production_registry_sha256"',
        b'"execution_timestamp"',
    ):
        assert forbidden not in serialized

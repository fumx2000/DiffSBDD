from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from copy import deepcopy
import csv
import inspect
import io
import json
from pathlib import Path

import pytest

from covalent_ext import covapie_post_only_auto_negative_ts_dump_exact_v1 as gate


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / gate.CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
OUTPUT = ROOT / gate.OUTPUT_ROOT_RELATIVE


@pytest.fixture(scope="module")
def real_evidence() -> dict[str, object]:
    evidence = gate._load_bound_evidence_v1(ROOT)
    context = gate._build_static_rule_context_v1(repo_root=ROOT, cache_root=CACHE)
    override = gate.build_runtime_positive_override_context_v1(
        current_human_overlay=evidence["current_human"],
        current_human_overlay_sha256=evidence["current_human_overlay_sha256"],
        outcome_by_id=evidence["outcome_by_id"],
    )
    return {"evidence": evidence, "context": context, "override": override}


@pytest.fixture(scope="module")
def real_artifacts() -> dict[str, bytes]:
    return gate.build_artifacts_v1(repo_root=ROOT, cache_root=CACHE)


def _csv(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _event_inputs(
    real_evidence: dict[str, object], unit_id: str
) -> tuple[
    dict[str, str],
    dict[str, object],
    dict[str, object],
    gate.RuntimePositiveOverrideContext,
]:
    evidence = real_evidence["evidence"]
    unit = evidence["unit_by_id"][unit_id]
    event_id = unit["canonical_event_ids"][0]
    return (
        deepcopy(evidence["event_by_id"][event_id]),
        deepcopy(evidence["outcome_by_id"][event_id]),
        deepcopy(real_evidence["context"]),
        real_evidence["override"],
    )


def _evaluate_all(real_evidence: dict[str, object]) -> dict[str, object]:
    evidence = real_evidence["evidence"]
    context = real_evidence["context"]
    override = real_evidence["override"]
    return {
        event_id: gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
            event=event,
            outcome=evidence["outcome_by_id"][event_id],
            rule_context=context,
            override_context=override,
        )
        for event_id, event in evidence["event_by_id"].items()
    }


def test_immutable_human_gold_is_exactly_bound() -> None:
    human = gate.load_immutable_human_gold_v1(ROOT)
    unit = next(
        item
        for item in human["units"]
        if item["review_unit_id"] == gate.CALIBRATION_UNIT_ID
    )
    assert unit["workflow_status"] == "COMPLETED"
    assert unit["training_domain_relevance_decision"] == (
        "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
    )
    assert unit["reactive_atom_confirmation"] is None
    assert unit["warhead_family_decision"] is None
    assert unit["warhead_atom_ids"] == []
    assert unit["roles"] == {
        "linker_atom_ids": [],
        "scaffold_atom_ids": [],
        "warhead_atom_ids": [],
    }
    assert unit["review_rationale"] == gate.CALIBRATION_RATIONALE
    assert len(unit["events"]) == 16
    assert all(
        event["post_geometry_training_usable"] == ""
        and event["event_training_use_decision"] == ""
        and event["event_exclusion_reason"] == ""
        for event in unit["events"]
    )


def test_independent_structured_target_family_provenance(
    real_evidence: dict[str, object],
) -> None:
    context = real_evidence["context"]
    assert context["target_family_context_provenance"] == (
        gate.TARGET_FAMILY_CONTEXT_PROVENANCE
    )
    assert context["target_family_context_was_derived_from_shadow_matches"] is False
    assert context["shadow_label_leakage_prohibited"] is True
    assert context["rule_context_is_independent_of_shadow_evaluation_population"] is True
    assert context["target_family_generalization_authorized"] is True
    assert context["rule_identity_excludes_pdb_id"] is True
    assert context["rule_identity_excludes_chain_id"] is True
    assert context["source_verified_structure_count"] == 175
    assert context["structured_ec_matched_structure_count"] == 20
    assert context["authorized_target_family_key_count"] == 15
    assert context["target_family_context_input_sha256"][
        gate.UPSTREAM_ACQUISITION_RELATIVE.as_posix()
    ] == gate.INPUT_SHA256[gate.UPSTREAM_ACQUISITION_RELATIVE]
    assert all(
        item["structured_target_family_id"] == "EC:2.1.1.45"
        and item["protein_reactive_atom"] == "SG"
        and item["provenance_records"]
        and all(
            record["structured_family_field"] == "_entity.pdbx_ec"
            and record["structured_family_value"] == "2.1.1.45"
            for record in item["provenance_records"]
        )
        for item in context["authorized_target_family_registry"]
    )


def test_rule_context_contains_no_sibling_or_shadow_label_dependency(
    real_evidence: dict[str, object],
) -> None:
    context = real_evidence["context"]
    serialized = json.dumps(context, sort_keys=True)
    evidence = real_evidence["evidence"]
    sibling_ids = evidence["unit_by_id"][gate.SIBLING_UNIT_ID]["canonical_event_ids"]
    assert gate.SIBLING_UNIT_ID not in serialized
    assert all(event_id not in serialized for event_id in sibling_ids)
    assert "shadow_expected_counts" not in serialized
    assert "expected_matched" not in serialized
    builder_source = inspect.getsource(gate._build_static_rule_context_v1)
    assert "SIBLING_UNIT_ID" not in builder_source
    assert "_load_bound_evidence_v1" not in builder_source
    assert set(inspect.signature(gate._build_static_rule_context_v1).parameters) == {
        "repo_root",
        "cache_root",
    }
    artifact_builder_source = inspect.getsource(gate.build_artifacts_v1)
    assert "_load_bound_evidence_v1" not in artifact_builder_source
    assert "_load_calibration_snapshot_evidence_v1" in artifact_builder_source


def test_context_is_invariant_to_sibling_removal_from_evaluation_population(
    real_evidence: dict[str, object],
) -> None:
    context_before = json.dumps(real_evidence["context"], sort_keys=True)
    reduced = deepcopy(real_evidence["evidence"])
    sibling_ids = set(
        reduced["unit_by_id"][gate.SIBLING_UNIT_ID]["canonical_event_ids"]
    )
    for field in ("event_by_id", "outcome_by_id", "unit_by_event"):
        reduced[field] = {
            key: value for key, value in reduced[field].items() if key not in sibling_ids
        }
    reduced["unit_by_id"].pop(gate.SIBLING_UNIT_ID)
    assert not sibling_ids & set(reduced["event_by_id"])
    assert json.dumps(real_evidence["context"], sort_keys=True) == context_before


def test_leave_one_unit_out_generalizes_to_all_sibling_events(
    real_evidence: dict[str, object],
) -> None:
    evidence = real_evidence["evidence"]
    results = _evaluate_all(real_evidence)
    counts = Counter(result.status for result in results.values())
    assert counts == Counter(
        {gate.MATCHED_AUTO_NEGATIVE_EXACT: 47, gate.NOT_MATCHED: 76}
    )
    assert counts[gate.INVALID_EVIDENCE] == 0
    sibling_ids = evidence["unit_by_id"][gate.SIBLING_UNIT_ID]["canonical_event_ids"]
    assert len(sibling_ids) == 31
    assert all(
        results[event_id].status == gate.MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in sibling_ids
    )
    by_unit: dict[str, list[object]] = defaultdict(list)
    for event_id, result in results.items():
        by_unit[evidence["unit_by_event"][event_id]].append(result)
    aggregate = {
        unit_id: gate.aggregate_review_unit_shadow_v1(
            review_unit_id=unit_id, event_results=unit_results
        )
        for unit_id, unit_results in by_unit.items()
    }
    assert {
        unit_id for unit_id, result in aggregate.items() if result.shadow_would_auto_negative
    } == {gate.CALIBRATION_UNIT_ID, gate.SIBLING_UNIT_ID}


def test_synthetic_new_pdb_and_chain_with_authorized_family_key_matches(
    real_evidence: dict[str, object],
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    synthetic_id = "COVAPIE_SYNTHETIC_EVENT_V1:9ZZZ:Z:CYS:187:SG:UMP:C6"
    event["canonical_event_id"] = synthetic_id
    event["pdb_id"] = "9ZZZ"
    event["target_residue_identity"] = "Z:CYS:187"
    event["target_cys_chain_residue"] = "Z:187"
    outcome["canonical_event_id"] = synthetic_id
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.MATCHED_AUTO_NEGATIVE_EXACT


def test_unknown_target_accession_and_sequence_never_match(
    real_evidence: dict[str, object],
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    leakage = outcome["structural_processing"]["leakage_evidence"]
    leakage["protein_accession"] = "Q99999"
    leakage["protein_sequence_sha256"] = "3" * 64
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.NOT_MATCHED
    assert "exact_ts_family_accession_sequence_key" in gate._reason_failed_predicates(
        result.reason
    )


def test_ufp_counterexamples_remain_outside_exact_dump_chemistry(
    real_evidence: dict[str, object],
) -> None:
    evidence = real_evidence["evidence"]
    results = _evaluate_all(real_evidence)
    required = {"exact_ccd_component_graph_sha256", "exact_radius2_sha256"}
    for unit_id in gate.UFP_COUNTEREXAMPLE_UNITS:
        for event_id in evidence["unit_by_id"][unit_id]["canonical_event_ids"]:
            result = results[event_id]
            assert result.status == gate.NOT_MATCHED
            assert required <= gate._reason_failed_predicates(result.reason)
            assert "exact_ts_family_accession_sequence_key" in result.matched_predicates


def test_human_positive_and_pyr_boundaries_have_zero_match(
    real_evidence: dict[str, object],
) -> None:
    evidence = real_evidence["evidence"]
    results = _evaluate_all(real_evidence)
    positive_ids = [
        event_id
        for unit_id in gate.HUMAN_RELEVANT_COUNTEREXAMPLE_UNITS
        for event_id in evidence["unit_by_id"][unit_id]["canonical_event_ids"]
    ]
    pyr_ids = evidence["unit_by_id"][gate.PYR_COUNTEREXAMPLE_UNIT][
        "canonical_event_ids"
    ]
    assert not any(
        results[event_id].status == gate.MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in positive_ids + pyr_ids
    )
    assert all(
        "no_runtime_positive_override"
        in gate._reason_failed_predicates(results[event_id].reason)
        for event_id in positive_ids
    )


def test_missing_target_family_provenance_is_invalid(
    real_evidence: dict[str, object],
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    context.pop("target_family_context_provenance")
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.INVALID_EVIDENCE


def test_future_current_human_positive_override_beats_otherwise_exact_match(
    real_evidence: dict[str, object],
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    event_id = event["canonical_event_id"]
    future_override = gate.RuntimePositiveOverrideContext(
        schema_version=gate.RUNTIME_OVERRIDE_SCHEMA_VERSION,
        current_human_relevant_event_ids=frozenset(
            {*override.current_human_relevant_event_ids, event_id}
        ),
        current_production_exact_positive_event_ids=(
            override.current_production_exact_positive_event_ids
        ),
        explicit_positive_override_event_ids=override.explicit_positive_override_event_ids,
        current_human_overlay_sha256="a" * 64,
    )
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context=future_override,
    )
    assert result.status == gate.NOT_MATCHED
    assert "no_runtime_positive_override" in gate._reason_failed_predicates(
        result.reason
    )


def test_current_overlay_may_evolve_without_changing_calibration_gold(
    real_evidence: dict[str, object],
    real_artifacts: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = real_evidence["evidence"]
    changed = deepcopy(evidence["current_human"])
    calibration = next(
        unit
        for unit in changed["units"]
        if unit["review_unit_id"] == gate.CALIBRATION_UNIT_ID
    )
    calibration["training_domain_relevance_decision"] = (
        "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
    )
    current_units = gate.validate_current_human_overlay_v1(changed)
    assert current_units[gate.CALIBRATION_UNIT_ID][
        "training_domain_relevance_decision"
    ] == "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
    override = gate.build_runtime_positive_override_context_v1(
        current_human_overlay=changed,
        current_human_overlay_sha256="b" * 64,
        outcome_by_id=evidence["outcome_by_id"],
    )
    calibration_ids = {event["canonical_event_id"] for event in calibration["events"]}
    assert calibration_ids <= override.current_human_relevant_event_ids
    event_id = sorted(calibration_ids)[0]
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=evidence["event_by_id"][event_id],
        outcome=evidence["outcome_by_id"][event_id],
        rule_context=real_evidence["context"],
        override_context=override,
    )
    assert result.status == gate.NOT_MATCHED
    assert "no_runtime_positive_override" in gate._reason_failed_predicates(
        result.reason
    )
    immutable = gate.load_immutable_human_gold_v1(ROOT)
    immutable_calibration = next(
        unit
        for unit in immutable["units"]
        if unit["review_unit_id"] == gate.CALIBRATION_UNIT_ID
    )
    assert immutable_calibration["training_domain_relevance_decision"] == (
        "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
    )

    def dynamic_loader_must_not_be_used(_repo_root: Path):
        raise AssertionError("persisted artifact build read dynamic current state")

    monkeypatch.setattr(gate, "_load_bound_evidence_v1", dynamic_loader_must_not_be_used)
    assert gate.build_artifacts_v1(repo_root=ROOT, cache_root=CACHE) == real_artifacts


def test_current_overlay_accepts_official_deferred_relevance_without_positive_override(
    real_evidence: dict[str, object],
) -> None:
    evidence = real_evidence["evidence"]
    changed = deepcopy(evidence["current_human"])
    unit = next(
        item
        for item in changed["units"]
        if item["review_unit_id"] == gate.SIBLING_UNIT_ID
    )
    unit["workflow_status"] = "DEFERRED"
    unit["training_domain_relevance_decision"] = (
        "DEFERRED_INSUFFICIENT_EVIDENCE"
    )
    current_units = gate.validate_current_human_overlay_v1(changed)
    assert current_units[gate.SIBLING_UNIT_ID][
        "training_domain_relevance_decision"
    ] == "DEFERRED_INSUFFICIENT_EVIDENCE"
    override = gate.build_runtime_positive_override_context_v1(
        current_human_overlay=changed,
        current_human_overlay_sha256="d" * 64,
        outcome_by_id=evidence["outcome_by_id"],
    )
    deferred_event_ids = {
        event["canonical_event_id"] for event in unit["events"]
    }
    assert deferred_event_ids.isdisjoint(
        override.current_human_relevant_event_ids
    )


def test_malformed_override_context_never_matches(
    real_evidence: dict[str, object],
) -> None:
    event, outcome, context, _override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context={},  # type: ignore[arg-type]
    )
    assert result.status == gate.INVALID_EVIDENCE


@pytest.mark.parametrize(
    ("field", "replacement", "failed_predicate"),
    [
        ("ccd_component_graph_sha256", "0" * 64, "exact_ccd_component_graph_sha256"),
        ("ligand_reactive_atom", "C5", "exact_ligand_reactive_atom"),
        ("reactive_center_radius1_fingerprint", "1" * 64, "exact_radius1_sha256"),
        ("reactive_center_radius2_fingerprint", "2" * 64, "exact_radius2_sha256"),
    ],
)
def test_exact_chemistry_mutations_fail_closed_not_matched(
    real_evidence: dict[str, object],
    field: str,
    replacement: str,
    failed_predicate: str,
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    event[field] = replacement
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.NOT_MATCHED
    assert failed_predicate in gate._reason_failed_predicates(result.reason)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("ccd_component_graph_sha256", None),
        ("ccd_component_graph_sha256", 7),
        ("ccd_component_graph_sha256", "not-a-sha"),
        ("feature_compatible", 1),
    ],
)
def test_missing_wrong_builtin_and_malformed_evidence_are_invalid(
    real_evidence: dict[str, object], field: str, replacement: object
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    if replacement is None:
        event.pop(field)
    else:
        event[field] = replacement
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.INVALID_EVIDENCE


def test_substrate_and_protein_name_alone_are_not_dispositive(
    real_evidence: dict[str, object],
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, "COVAPIE_BULK_REVIEW_UNIT_CF6D3ADC970757BA"
    )
    assert any(
        annotation.get("reaction") == "substrate"
        for annotation in json.loads(event["source_annotations_json"])
    )
    event["protein_name"] = "thymidylate synthase"
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event,
        outcome=outcome,
        rule_context=context,
        override_context=override,
    )
    assert result.status == gate.NOT_MATCHED


def test_conflict_existing_authority_and_production_approval_never_match(
    real_evidence: dict[str, object],
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    event["annotation_conflicts_json"] = '["reaction"]'
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event, outcome=outcome, rule_context=context, override_context=override
    )
    assert result.status == gate.NOT_MATCHED
    assert "no_source_annotation_conflict" in gate._reason_failed_predicates(result.reason)

    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    outcome["existing_exact_authority_match"] = True
    evidence = real_evidence["evidence"]
    outcome_by_id = deepcopy(evidence["outcome_by_id"])
    outcome_by_id[event["canonical_event_id"]] = outcome
    override = gate.build_runtime_positive_override_context_v1(
        current_human_overlay=evidence["current_human"],
        current_human_overlay_sha256=evidence["current_human_overlay_sha256"],
        outcome_by_id=outcome_by_id,
    )
    assert (
        event["canonical_event_id"]
        in override.current_production_exact_positive_event_ids
    )
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event, outcome=outcome, rule_context=context, override_context=override
    )
    assert result.status == gate.NOT_MATCHED
    assert "no_existing_exact_positive_authority" in gate._reason_failed_predicates(
        result.reason
    )
    assert "no_runtime_positive_override" in gate._reason_failed_predicates(
        result.reason
    )

    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    event["production_approval_created"] = "true"
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event, outcome=outcome, rule_context=context, override_context=override
    )
    assert result.status == gate.NOT_MATCHED
    assert "no_production_approval" in gate._reason_failed_predicates(result.reason)


def test_partial_or_invalid_multi_event_unit_never_auto_negatives() -> None:
    matched = gate.AutoNegativeEvaluationResult(
        gate.RULE_ID,
        gate.MATCHED_AUTO_NEGATIVE_EXACT,
        "ALL_EXACT_PREDICATES_MATCHED",
        gate.REQUIRED_PREDICATES,
    )
    not_matched = gate.AutoNegativeEvaluationResult(
        gate.RULE_ID,
        gate.NOT_MATCHED,
        "PREDICATE_MISMATCH:exact_radius2_sha256",
        (),
    )
    invalid = gate.AutoNegativeEvaluationResult(
        gate.RULE_ID,
        gate.INVALID_EVIDENCE,
        "INVALID_EVIDENCE:exact_radius2_sha256[MISSING]",
        (),
    )
    partial = gate.aggregate_review_unit_shadow_v1(
        review_unit_id="SYNTHETIC_UNIT", event_results=[matched, not_matched]
    )
    assert partial.shadow_would_auto_negative is False
    assert partial.matched_event_count == 1
    with_invalid = gate.aggregate_review_unit_shadow_v1(
        review_unit_id="SYNTHETIC_UNIT", event_results=[matched, invalid]
    )
    assert with_invalid.shadow_would_auto_negative is False
    assert with_invalid.invalid_event_count == 1


def test_result_and_override_context_objects_are_frozen(
    real_evidence: dict[str, object],
) -> None:
    event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )
    result = gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=event, outcome=outcome, rule_context=context, override_context=override
    )
    with pytest.raises(Exception):
        result.status = gate.NOT_MATCHED  # type: ignore[misc]
    with pytest.raises(Exception):
        override.current_human_overlay_sha256 = "0" * 64  # type: ignore[misc]


def test_keyboard_interrupt_and_system_exit_propagate(
    real_evidence: dict[str, object],
) -> None:
    _event, outcome, context, override = _event_inputs(
        real_evidence, gate.CALIBRATION_UNIT_ID
    )

    class InterruptingMapping(Mapping[str, object]):
        def __getitem__(self, key: str) -> object:
            raise KeyboardInterrupt

        def __iter__(self):
            return iter(())

        def __len__(self) -> int:
            return 0

        def get(self, key: str, default: object = None) -> object:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
            event=InterruptingMapping(),
            outcome=outcome,
            rule_context=context,
            override_context=override,
        )

    class ExitingMapping(InterruptingMapping):
        def get(self, key: str, default: object = None) -> object:
            raise SystemExit(2)

    with pytest.raises(SystemExit):
        gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
            event=ExitingMapping(),
            outcome=outcome,
            rule_context=context,
            override_context=override,
        )


def _fake_git_state(*, head: str, origin: str):
    def fake(_repo_root: Path, *arguments: str) -> str:
        mapping = {
            ("branch", "--show-current"): "main",
            ("rev-parse", "HEAD"): head,
            ("rev-parse", "refs/remotes/origin/main"): origin,
            (
                "show",
                "-s",
                "--format=%s",
                gate.CALIBRATION_COMMIT,
            ): gate.CALIBRATION_SUBJECT,
            (
                "rev-list",
                "--left-right",
                "--count",
                "HEAD...refs/remotes/origin/main",
            ): "0 0",
        }
        return mapping[arguments]

    return fake


def test_repository_binding_accepts_exact_calibration_and_descendant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert gate.verify_repository_binding_v1(ROOT)[
        "descendant_repository_compatible"
    ] is True
    descendant = "d" * 40
    monkeypatch.setattr(
        gate, "_git", _fake_git_state(head=descendant, origin=descendant)
    )
    monkeypatch.setattr(gate, "_git_is_ancestor", lambda *_args: True)
    observed = gate.verify_repository_binding_v1(ROOT)
    assert observed["head"] == descendant
    assert observed["origin_main"] == descendant


def test_repository_binding_rejects_unsynchronized_or_non_descendant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate, "_git", _fake_git_state(head="a" * 40, origin="b" * 40)
    )
    monkeypatch.setattr(gate, "_git_is_ancestor", lambda *_args: True)
    with pytest.raises(ValueError, match="HEAD_ORIGIN_MAIN_MISMATCH"):
        gate.verify_repository_binding_v1(ROOT)

    descendant = "d" * 40
    monkeypatch.setattr(
        gate, "_git", _fake_git_state(head=descendant, origin=descendant)
    )
    monkeypatch.setattr(gate, "_git_is_ancestor", lambda *_args: False)
    with pytest.raises(ValueError, match="CALIBRATION_COMMIT_NOT_ANCESTOR_OF_HEAD"):
        gate.verify_repository_binding_v1(ROOT)


def test_artifact_bytes_are_identical_at_calibration_and_descendant_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descendant_state = gate.verify_repository_binding_v1(ROOT)
    assert descendant_state["head"] != gate.CALIBRATION_COMMIT
    assert descendant_state["head"] == descendant_state["origin_main"]
    assert descendant_state["calibration_is_ancestor_of_head"] is True
    descendant_artifacts = gate.build_artifacts_v1(repo_root=ROOT, cache_root=CACHE)

    validation_calls = 0

    def calibration_equivalent_validation(_repo_root: Path) -> dict[str, object]:
        nonlocal validation_calls
        validation_calls += 1
        return {
            "branch": "main",
            "head": gate.CALIBRATION_COMMIT,
            "origin_main": gate.CALIBRATION_COMMIT,
            "ahead": 0,
            "behind": 0,
            "calibration_commit": gate.CALIBRATION_COMMIT,
            "calibration_subject": gate.CALIBRATION_SUBJECT,
            "calibration_is_ancestor_of_head": True,
            "calibration_is_ancestor_of_origin_main": True,
            "descendant_repository_compatible": True,
        }

    monkeypatch.setattr(
        gate, "verify_repository_binding_v1", calibration_equivalent_validation
    )
    calibration_artifacts = gate.build_artifacts_v1(
        repo_root=ROOT, cache_root=CACHE
    )
    assert validation_calls == 1
    assert calibration_artifacts == descendant_artifacts
    assert set(calibration_artifacts) == set(gate.OUTPUT_FILENAMES)


def test_summary_and_manifest_report_observed_generalization(
    real_artifacts: dict[str, bytes],
) -> None:
    summary = json.loads(real_artifacts[gate.SUMMARY])
    manifest = json.loads(real_artifacts[gate.RULE_MANIFEST])
    assert summary["readiness_mode"] == gate.GENERALIZATION_MODE
    assert summary["generalization_without_sibling_label_leakage"] is True
    assert summary["target_family_generalization_authorized"] is True
    assert summary["live_integration_ready"] is True
    assert summary["observed_shadow_matched_event_count"] == 47
    assert summary["observed_shadow_matched_unit_count"] == 2
    assert summary["invalid_evidence_count"] == 0
    assert summary["UFP_counterexample_match_count"] == 0
    assert summary["calibration_snapshot_human_relevant_match_count"] == 0
    assert summary["PYR_boundary_match_count"] == 0
    assert summary["artifact_semantics"] == gate.ARTIFACT_SEMANTICS
    assert summary["runtime_state_embedded_in_deterministic_artifacts"] is False
    assert (
        summary["current_human_overlay_embedded_in_deterministic_artifacts"]
        is False
    )
    assert summary["runtime_positive_override_evaluated_separately"] is True
    assert summary["future_human_positive_override_supported"] is True
    assert "base_git_binding" not in summary
    assert "current_human_overlay_sha256" not in summary
    assert summary["calibration_snapshot_unreviewed_unit_workload"] == 26
    assert (
        summary["calibration_snapshot_unreviewed_shadow_auto_negative_event_count"]
        == 31
    )
    assert (
        summary["calibration_snapshot_unreviewed_shadow_auto_negative_unit_count"]
        == 1
    )
    assert (
        summary[
            "calibration_snapshot_projected_remaining_unreviewed_unit_workload"
        ]
        == 25
    )
    assert manifest["artifact_semantics"] == gate.ARTIFACT_SEMANTICS
    assert manifest["runtime_state_embedded_in_deterministic_artifacts"] is False
    assert (
        manifest["current_human_overlay_embedded_in_deterministic_artifacts"]
        is False
    )
    assert manifest["runtime_positive_override_evaluated_separately"] is True
    assert "shadow_runtime_context_observation" not in manifest
    assert manifest["observed_shadow_counts"]["matched_event_count"] == 47
    assert manifest["leave_one_unit_out_generalization"][
        "rule_context_constructed_without_reporting_unit_or_event_ids"
    ] is True
    assert manifest["scientific_rule_context"]["context_semantics"].endswith(
        "NO_STANDALONE_CATALYTIC_PREDICATE_CLAIM"
    )


def test_inventory_is_one_row_per_candidate_and_writes_no_decision(
    real_artifacts: dict[str, bytes],
) -> None:
    rows = _csv(real_artifacts[gate.SHADOW_INVENTORY])
    assert len(rows) == 123
    assert len({row["canonical_event_id"] for row in rows}) == 123
    assert Counter(row["evaluation_status"] for row in rows) == Counter(
        {gate.MATCHED_AUTO_NEGATIVE_EXACT: 47, gate.NOT_MATCHED: 76}
    )
    sibling = [row for row in rows if row["review_unit_id"] == gate.SIBLING_UNIT_ID]
    assert len(sibling) == 31
    assert all(
        row["calibration_snapshot_human_review_state"] == "UNREVIEWED"
        for row in sibling
    )
    assert all(row["shadow_would_auto_negative"] == "true" for row in sibling)


def test_deterministic_double_build_is_byte_identical(
    real_artifacts: dict[str, bytes],
) -> None:
    replay = gate.build_artifacts_v1(repo_root=ROOT, cache_root=CACHE)
    assert replay == real_artifacts
    assert all((OUTPUT / name).read_bytes() == payload for name, payload in replay.items())

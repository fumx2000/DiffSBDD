from __future__ import annotations

import importlib.util
import inspect
import os
import subprocess
import sys
from dataclasses import fields, replace
from functools import lru_cache
from pathlib import Path

import pytest

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle
from covalent_ext import (
    covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_audit_gate_v1
    as audit,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts"
    / (
        "check_covapie_covalent_bond_atom_pair_current_semantics_and_"
        "downstream_consumers_audit_gate_v1.py"
    )
)
NESTED_LIFECYCLE_ENV = "COVAPIE_ATOM_PAIR_AUDIT_NESTED_LIFECYCLE"


@lru_cache(maxsize=1)
def _checker():
    name = "covapie_atom_pair_current_semantics_audit_checker"
    spec = importlib.util.spec_from_file_location(name, CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _decision(**overrides):
    evidence = {
        "current_source_lineage_verified": True,
        "current_representation_inventory_complete": True,
        "current_consumer_inventory_complete": True,
        "current_semantics_internally_consistent": True,
        "explicit_bond_authority_verified": True,
        "distance_only_inference_used": False,
        "current_pair_is_metadata_string": True,
        "current_pair_is_tensor_index_pair": False,
        "current_dataloader_consumer_present": False,
        "current_model_forward_consumer_present": False,
        "current_loss_consumer_present": False,
        "current_training_target_tensor_present": False,
        "unresolved_semantics_inventory_complete": True,
    }
    evidence.update(overrides)
    return audit.audit_covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_v1(
        **evidence
    )


@lru_cache(maxsize=1)
def _actual_components():
    checker = _checker()
    lineage = checker.build_executable_lineage_evidence()
    representation = checker.build_current_representation_rows()
    consumers = checker.build_downstream_consumer_rows()
    unresolved = checker.build_unresolved_semantics_rows()
    return checker, lineage, representation, consumers, unresolved


def _derived(*, lineage=None, representation=None):
    checker, actual_lineage, actual_representation, consumers, unresolved = (
        _actual_components()
    )
    return checker.derive_audit_evidence(
        lineage_evidence=actual_lineage if lineage is None else lineage,
        representation=(
            actual_representation
            if representation is None
            else representation
        ),
        consumers=consumers,
        unresolved=unresolved,
    )


def _layer_from_producer(checker, producer, layer_name):
    return checker.AtomPairLayerProjection(
        layer_name=layer_name,
        source_record_id=producer.producer_record_id,
        event_identity=producer.event_identity,
        pdb_id=producer.pdb_id,
        ligand_identity=producer.ligand_identity,
        residue_identity=producer.residue_identity,
        residue_atom_name=producer.residue_atom_name,
        ligand_atom_name=producer.ligand_atom_name,
        covalent_bond_atom_pair=producer.covalent_bond_atom_pair,
        conn_id=producer.conn_id,
        conn_type_id=producer.conn_type_id,
        explicit_bond_authority=producer.explicit_bond_authority,
    )


def _validate_single_layer(layer_name, layer_rows, expected_ids):
    checker, lineage, _, _, _ = _actual_components()
    return checker.validate_producer_projection_chain(
        lineage.producer_projections,
        {layer_name: tuple(layer_rows)},
        {layer_name: len(expected_ids)},
        {layer_name: frozenset(expected_ids)},
    )


def test_public_audit_api_and_frozen_decision() -> None:
    decision = _decision()
    assert audit.__all__ == (
        "CovalentBondAtomPairCurrentSemanticsAuditDecision",
        "audit_covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_v1",
        "serialize_covalent_bond_atom_pair_current_semantics_audit_decision",
    )
    assert tuple(item.name for item in fields(type(decision))) == (
        "schema_version",
        "outcome",
        "current_source_lineage_verified",
        "current_representation_inventory_complete",
        "current_consumer_inventory_complete",
        "current_semantics_internally_consistent",
        "explicit_bond_authority_verified",
        "distance_only_inference_used",
        "current_pair_is_metadata_string",
        "current_pair_is_tensor_index_pair",
        "current_dataloader_consumer_present",
        "current_model_forward_consumer_present",
        "current_loss_consumer_present",
        "current_training_target_tensor_present",
        "unresolved_semantics_inventory_complete",
        "atom_pair_issue_resolved",
        "ready_for_encoding_contract_design",
        "feature_semantics_audit_completed",
        "ready_for_training",
        "recommended_next_step",
    )
    assert type(decision).__dataclass_params__.frozen is True
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in inspect.signature(
            audit.audit_covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_v1
        ).parameters.values()
    )


@pytest.mark.parametrize(
    "overrides",
    (
        {"current_source_lineage_verified": False},
        {"current_representation_inventory_complete": False},
        {"current_consumer_inventory_complete": False},
        {"current_semantics_internally_consistent": False},
        {"explicit_bond_authority_verified": False},
        {"distance_only_inference_used": True},
        {"current_pair_is_tensor_index_pair": True},
        {"current_model_forward_consumer_present": True},
        {"current_loss_consumer_present": True},
        {"current_training_target_tensor_present": True},
        {"unresolved_semantics_inventory_complete": False},
    ),
)
def test_incomplete_or_contradictory_evidence_fails_closed(overrides) -> None:
    decision = _decision(**overrides)
    assert decision.outcome == "invalid"
    assert decision.atom_pair_issue_resolved is False
    assert decision.ready_for_encoding_contract_design is False
    assert decision.feature_semantics_audit_completed is False
    assert decision.ready_for_training is False


def test_source_lineage_is_complete_and_points_to_committed_selectors() -> None:
    checker = _checker()
    evidence = checker.build_executable_lineage_evidence()
    rows = evidence.lineage_rows
    assert len(rows) == 15
    assert [row["lineage_order"] for row in rows] == [
        str(index) for index in range(1, 16)
    ]
    assert sum(row["current_source_of_truth"] == "true" for row in rows) == 1
    assert all(
        row["source_path"]
        and row["source_symbol_or_selector"]
        and row["selector_kind"]
        and row["selector_expression"]
        and row["expected_record_count"]
        and row["observed_record_count"]
        and row["predecessor_projection"]
        and row["observed_projection"]
        and row["predecessor_successor_projection_verified"] == "true"
        and row["selector_verified"] == "true"
        and row["source_sha256"]
        and row["committed_in_base"] == "true"
        and row["verified"] == "true"
        for row in rows
    )
    assert evidence.original_producer_record_count == 3
    assert evidence.expansion_producer_record_count == 8
    assert len(evidence.producer_projections) == 11
    assert evidence.original_sample_index_record_count == 3
    assert evidence.expansion_sample_index_record_count == 8
    assert evidence.unified_sample_index_record_count == 11
    assert evidence.split_union_record_count == 11
    assert evidence.final_dataset_record_count == 11
    assert evidence.producer_validation.producer_projection_verified is True


def test_actual_current_records_are_traceable_and_dynamic() -> None:
    rows = _checker().build_current_representation_rows()
    assert len(rows) == 11
    assert len({row["sample_or_event_id"] for row in rows}) == 11
    assert {row["stored_covalent_bond_atom_pair"] for row in rows} == {
        "SG--CAG",
        "SG--C2",
        "SG--CM",
        "SG--C22",
        "SG--C17",
        "SG--C21",
        "SG--C6",
    }
    assert all(row["event_pair_cardinality"] == "1" for row in rows)


def test_stored_pair_matches_separate_atom_fields_for_every_record() -> None:
    rows = _checker().build_current_representation_rows()
    assert all(row["stored_matches_reconstructed"] == "true" for row in rows)
    assert all(
        row["stored_covalent_bond_atom_pair"]
        == row["pair_reconstructed_from_separate_fields"]
        for row in rows
    )
    assert all(row["verified"] == "true" for row in rows)


def test_explicit_bond_authority_is_not_distance_inference() -> None:
    rows = _checker().build_current_representation_rows()
    assert all(
        row["explicit_bond_evidence_type"].startswith(
            "validated_struct_conn:"
        )
        for row in rows
    )
    lineage = _checker().build_source_lineage_rows()
    assert all(row["distance_only_inference_used"] == "false" for row in lineage)
    assert all(
        row["conn_id_if_available"] and row["conn_type_id_if_available"] == "covale"
        for row in rows
    )


def test_consumer_roles_are_closed_and_all_matches_are_classified() -> None:
    checker = _checker()
    rows = checker.build_downstream_consumer_rows()
    assert rows
    assert checker._consumer_inventory_complete(rows) is True
    assert {row["consumer_role"] for row in rows} <= checker.CONSUMER_ROLES
    assert all(
        row["consumer_path"]
        and row["consumer_symbol_or_selector"]
        and row["matched_term"]
        and row["source_sha256"]
        and row["verified"] == "true"
        for row in rows
    )


def test_test_report_and_schema_references_are_not_model_consumers() -> None:
    rows = _checker().build_downstream_consumer_rows()
    for row in rows:
        if row["consumer_path"].startswith(
            ("tests/", "docs/", "data/derived/")
        ):
            assert row["consumer_role"] not in {
                "dataloader_consumer",
                "model_forward_consumer",
                "loss_consumer",
                "training_target_consumer",
            }
            assert row["uses_in_forward"] == "false"
            assert row["uses_in_loss"] == "false"


def test_no_current_dataloader_forward_loss_or_training_target_consumer() -> None:
    checker = _checker()
    checker._negative_model_consumer_check()
    rows = checker.build_downstream_consumer_rows()
    assert not any(row["uses_in_collate"] == "true" for row in rows)
    assert not any(row["uses_in_forward"] == "true" for row in rows)
    assert not any(row["uses_in_loss"] == "true" for row in rows)
    assert not any(row["uses_as_training_target"] == "true" for row in rows)
    decision = _decision()
    assert decision.current_dataloader_consumer_present is False
    assert decision.current_model_forward_consumer_present is False
    assert decision.current_loss_consumer_present is False
    assert decision.current_training_target_tensor_present is False


def test_distinct_pair_status_path_count_event_and_distance_concepts() -> None:
    rows = _checker().build_downstream_consumer_rows()
    matched = {row["matched_term"] for row in rows}
    assert {
        "covalent_bond_atom_pair",
        "residue_atom_name",
        "ligand_atom_name",
        "covalent_residue_atom_name",
        "ligand_covalent_atom_name",
        "ligand_residue_atom_pair_label_status",
        "ligand_residue_atom_pair_table_path",
        "ligand_residue_atom_pair_count",
        "covalent_event_table_path",
        "post_covalent_bond_distance_angstrom",
    } <= matched


def test_unresolved_semantics_inventory_is_exact24_and_defers_design() -> None:
    rows = _checker().build_unresolved_semantics_rows()
    assert len(rows) == 24
    assert all(row["currently_formally_defined"] == "false" for row in rows)
    assert all(row["decision_made_current_audit"] == "false" for row in rows)
    assert all(row["deferred_to_next_contract"] == "true" for row in rows)
    assert all(row["verified"] == "true" for row in rows)


def test_issue_inventory_stays_open_and_byte_identical() -> None:
    checker = _checker()
    payload, rows = checker._issue_payload_and_rows()
    assert payload == checker._git_show(checker.PREDECESSOR_ISSUE_PATH)
    assert len(rows) == 30
    assert (
        __import__("hashlib").sha256(payload).hexdigest()
        == checker.PREDECESSOR_ISSUE_SHA256
    )
    decision = _decision()
    assert decision.atom_pair_issue_resolved is False


def test_encoding_design_readiness_is_separate_from_training_readiness() -> None:
    decision = _decision()
    assert decision.outcome == "audited"
    assert decision.ready_for_encoding_contract_design is True
    assert decision.atom_pair_issue_resolved is False
    assert decision.feature_semantics_audit_completed is False
    assert decision.ready_for_training is False
    assert decision.recommended_next_step == audit.RECOMMENDED_NEXT_STEP


def test_tamper_missing_lineage_selector_row_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    rows = [dict(row) for row in lineage.lineage_rows]
    rows[0]["observed_record_count"] = "2"
    rows[0]["selector_verified"] = "false"
    rows[0]["verified"] = "false"
    tampered = replace(
        lineage,
        lineage_rows=tuple(rows),
        lineage_selectors_executed=False,
        lineage_transition_projections_verified=False,
    )
    evidence = _derived(lineage=tampered)
    assert evidence.current_source_lineage_verified is False
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_original_producer_count_not_three_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    removed = False
    producers = []
    for item in lineage.producer_projections:
        if item.producer_branch == "original" and not removed:
            removed = True
            continue
        producers.append(item)
    tampered = replace(
        lineage,
        producer_projections=tuple(producers),
        original_producer_record_count=2,
    )
    evidence = _derived(lineage=tampered)
    assert evidence.producer_projection_verified is False
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_expansion_producer_count_not_eight_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    removed = False
    producers = []
    for item in lineage.producer_projections:
        if item.producer_branch == "expansion" and not removed:
            removed = True
            continue
        producers.append(item)
    tampered = replace(
        lineage,
        producer_projections=tuple(producers),
        expansion_producer_record_count=7,
    )
    evidence = _derived(lineage=tampered)
    assert evidence.producer_projection_verified is False
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_sample_index_pair_vs_producer_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    original = tuple(
        item
        for item in lineage.producer_projections
        if item.producer_branch == "original"
    )
    layers = [
        _layer_from_producer(checker, item, "original_sample_index")
        for item in original
    ]
    layers[0] = replace(
        layers[0], covalent_bond_atom_pair="SG--TAMPERED"
    )
    validation = _validate_single_layer(
        "original_sample_index",
        layers,
        {item.event_identity for item in original},
    )
    evidence = _derived(
        lineage=replace(lineage, producer_validation=validation)
    )
    assert evidence.producer_conflict_present is True
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_unified_projection_missing_event_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    layers = [
        _layer_from_producer(checker, item, "unified_sample_index")
        for item in lineage.producer_projections
    ][:-1]
    validation = checker.validate_producer_projection_chain(
        lineage.producer_projections,
        {"unified_sample_index": tuple(layers)},
        {"unified_sample_index": 11},
        {
            "unified_sample_index": frozenset(
                item.event_identity for item in lineage.producer_projections
            )
        },
    )
    evidence = _derived(
        lineage=replace(
            lineage,
            producer_validation=validation,
            unified_sample_index_record_count=10,
        )
    )
    assert validation.producer_projection_verified is False
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_split_overlap_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    unified = checker._base_csv(checker.UNIFIED_SAMPLE_INDEX_PATH)
    splits = {
        name: [dict(row) for row in checker._base_csv(path)]
        for name, path in zip(
            ("train", "validation", "test"), checker.SPLIT_PATHS, strict=True
        )
    }
    splits["validation"].append(dict(splits["train"][0]))
    split_ok, _ = checker.validate_split_partitions(splits, unified)
    assert split_ok is False
    evidence = _derived(
        lineage=replace(lineage, split_partition_verified=False)
    )
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_split_union_not_eleven_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    unified = checker._base_csv(checker.UNIFIED_SAMPLE_INDEX_PATH)
    splits = {
        name: [dict(row) for row in checker._base_csv(path)]
        for name, path in zip(
            ("train", "validation", "test"), checker.SPLIT_PATHS, strict=True
        )
    }
    splits["train"].pop()
    split_ok, union = checker.validate_split_partitions(splits, unified)
    assert split_ok is False
    assert len(union) == 10
    evidence = _derived(
        lineage=replace(
            lineage,
            split_partition_verified=False,
            split_union_record_count=10,
        )
    )
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_final_pair_vs_producer_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    layers = [
        _layer_from_producer(checker, item, "final_dataset")
        for item in lineage.producer_projections
    ]
    layers[-1] = replace(
        layers[-1], covalent_bond_atom_pair="SG--FINAL_TAMPER"
    )
    validation = _validate_single_layer(
        "final_dataset",
        layers,
        {item.event_identity for item in lineage.producer_projections},
    )
    evidence = _derived(
        lineage=replace(lineage, producer_validation=validation)
    )
    assert evidence.producer_conflict_present is True
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_explicit_bond_authority_loss_makes_audit_invalid() -> None:
    checker, lineage, _, _, _ = _actual_components()
    layers = [
        _layer_from_producer(checker, item, "final_dataset")
        for item in lineage.producer_projections
    ]
    layers[0] = replace(layers[0], explicit_bond_authority=False)
    validation = _validate_single_layer(
        "final_dataset",
        layers,
        {item.event_identity for item in lineage.producer_projections},
    )
    evidence = _derived(
        lineage=replace(lineage, producer_validation=validation)
    )
    assert evidence.explicit_bond_authority_verified is False
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_duplicate_producer_key_different_pair_is_producer_conflict() -> None:
    checker, lineage, _, _, _ = _actual_components()
    duplicate = replace(
        lineage.producer_projections[0],
        producer_record_id="TAMPERED_DUPLICATE",
        ligand_atom_name="DIFFERENT",
        covalent_bond_atom_pair="SG--DIFFERENT",
    )
    producers = (*lineage.producer_projections, duplicate)
    validation = checker.validate_producer_projection_chain(
        producers, {}, {}
    )
    evidence = _derived(
        lineage=replace(
            lineage,
            producer_projections=producers,
            producer_validation=validation,
        )
    )
    assert validation.producer_conflict_present is True
    assert evidence.record_conflict_present is False
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_tamper_same_final_event_multiple_pairs_is_record_conflict() -> None:
    checker, _, representation, _, _ = _actual_components()
    duplicate = dict(representation[0])
    duplicate["stored_covalent_bond_atom_pair"] = "SG--OTHER"
    duplicate["pair_reconstructed_from_separate_fields"] = "SG--OTHER"
    tampered = (*representation, duplicate)
    evidence = _derived(representation=tampered)
    assert evidence.record_conflict_present is True
    assert evidence.producer_conflict_present is False
    assert checker._audit_decision(evidence).outcome == "invalid"


def test_record_and_producer_conflicts_do_not_substitute_for_each_other() -> None:
    checker, lineage, representation, _, _ = _actual_components()
    record_duplicate = dict(representation[0])
    record_duplicate["stored_covalent_bond_atom_pair"] = "SG--RECORD"
    record_duplicate["pair_reconstructed_from_separate_fields"] = "SG--RECORD"
    record_evidence = _derived(
        representation=(*representation, record_duplicate)
    )
    producer_duplicate = replace(
        lineage.producer_projections[0],
        producer_record_id="TAMPERED_PRODUCER",
        ligand_atom_name="PRODUCER",
        covalent_bond_atom_pair="SG--PRODUCER",
    )
    validation = checker.validate_producer_projection_chain(
        (*lineage.producer_projections, producer_duplicate), {}, {}
    )
    producer_evidence = _derived(
        lineage=replace(lineage, producer_validation=validation)
    )
    assert (
        record_evidence.record_conflict_present,
        record_evidence.producer_conflict_present,
    ) == (True, False)
    assert (
        producer_evidence.record_conflict_present,
        producer_evidence.producer_conflict_present,
    ) == (False, True)


def test_checker_decision_bool_values_are_derived_from_evidence() -> None:
    checker, _, _, _, _ = _actual_components()
    evidence = _derived()
    assert checker._audit_decision(evidence).outcome == "audited"
    tampered = replace(
        evidence,
        current_consumer_inventory_complete=False,
        current_semantics_internally_consistent=False,
    )
    decision = checker._audit_decision(tampered)
    assert decision.outcome == "invalid"
    assert decision.current_consumer_inventory_complete is False
    assert decision.current_semantics_internally_consistent is False
    source = inspect.getsource(checker._audit_decision)
    assert "current_source_lineage_verified=True" not in source
    assert "current_semantics_internally_consistent=True" not in source


def test_all_evidence_and_decision_bytes_are_deterministic() -> None:
    checker = _checker()
    first = checker.build_evidence_payloads()
    second = checker.build_evidence_payloads()
    third = checker.build_evidence_payloads()
    assert first == second == third
    derived = _derived()
    decisions = tuple(checker._audit_decision(derived) for _ in range(3))
    assert decisions[0] == decisions[1] == decisions[2]
    assert (
        audit.serialize_covalent_bond_atom_pair_current_semantics_audit_decision(
            decisions[0]
        )
        == audit.serialize_covalent_bond_atom_pair_current_semantics_audit_decision(
            decisions[1]
        )
        == audit.serialize_covalent_bond_atom_pair_current_semantics_audit_decision(
            decisions[2]
        )
    )


def test_shared_lifecycle_three_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert _checker()._audit_decision(_derived()).outcome == "audited"
        return
    checker = _checker()
    real_capture = lifecycle._capture_state
    states: list[str] = []
    targeted_outputs: list[bytes] = []
    checker_outputs: list[bytes] = []

    def capture_with_validation(repository, **kwargs):
        state = real_capture(repository, **kwargs)
        if state.lifecycle in (
            "pre_commit",
            "formal_main_post_commit_unpushed",
            "formal_main_post_push",
        ):
            environment = os.environ.copy()
            environment[NESTED_LIFECYCLE_ENV] = "1"
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = "src"
            targeted = subprocess.run(
                (
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    checker.EXACT10[1].as_posix(),
                ),
                cwd=repository,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert targeted.returncode == 0, targeted.stdout + targeted.stderr
            assert targeted.stderr == b""
            checked = subprocess.run(
                (sys.executable, "-B", checker.EXACT10[2].as_posix()),
                cwd=repository,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert checked.returncode == 0, checked.stdout + checked.stderr
            assert checked.stderr == b""
            states.append(state.lifecycle)
            targeted_outputs.append(targeted.stdout)
            checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture_with_validation)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=checker.BASE_COMMIT,
        formal_commit_subject=checker.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert states == [
        "pre_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    ]
    assert len(targeted_outputs) == 3
    assert all(b"38 passed" in output for output in targeted_outputs)
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == checker.BASE_COMMIT
    assert report.candidate_subject == checker.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True

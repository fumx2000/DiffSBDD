from __future__ import annotations

import csv
import importlib.util
import inspect
import io
import json
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields, replace
from functools import lru_cache
from pathlib import Path
from typing import get_type_hints

import pytest

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle
from covalent_ext import (
    covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1 as gate,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts"
    / "check_covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1.py"
)
NESTED_LIFECYCLE_ENV = "COVAPIE_ATOM_PAIR_ENCODING_NESTED_LIFECYCLE"


@lru_cache(maxsize=1)
def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_atom_pair_encoding_contract_checker",
        CHECKER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _payloads():
    return gate.build_covapie_covalent_bond_atom_pair_encoding_contract_artifacts_v1(
        ROOT
    )


def _rows(name: str) -> tuple[dict[str, str], ...]:
    return tuple(
        csv.DictReader(
            io.StringIO(_payloads()[name].decode("utf-8"), newline="")
        )
    )


@lru_cache(maxsize=1)
def _evidence():
    return gate.derive_covapie_model_input_index_space_compatibility_evidence_v1(
        ROOT
    )


def _contract(**overrides):
    values = {
        "current_semantics_audit_precondition_verified": True,
        "model_input_index_space_compatibility_evidence": _evidence(),
    }
    values.update(overrides)
    return gate.design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
        **values
    )


def _locator(**overrides):
    values = {
        "locator_schema_version": gate.LOCATOR_SCHEMA_VERSION,
        "entity_role": "target_residue_atom",
        "event_id": "EVENT_1",
        "pdb_id": "1ABC",
        "model_id": "",
        "auth_asym_id": "A",
        "auth_seq_id": "10",
        "insertion_code": "",
        "label_asym_id": "",
        "label_seq_id": "",
        "comp_id": "CYS",
        "atom_name": "SG",
        "altloc": "",
    }
    values.update(overrides)
    return gate.CovalentAtomLocatorContractDesign(**values)


def _canonical_record(
    *,
    residue_overrides=None,
    ligand_overrides=None,
    **overrides,
):
    residue_values = {} if residue_overrides is None else residue_overrides
    ligand_values = (
        {
            "entity_role": "ligand_atom",
            "comp_id": "LIG",
            "atom_name": "C1",
            "auth_asym_id": "",
            "auth_seq_id": "",
        }
        if ligand_overrides is None
        else {
            "entity_role": "ligand_atom",
            "comp_id": "LIG",
            "atom_name": "C1",
            "auth_asym_id": "",
            "auth_seq_id": "",
            **ligand_overrides,
        }
    )
    values = {
        "pair_record_schema_version": gate.PAIR_RECORD_SCHEMA_VERSION,
        "residue_atom_locator": _locator(**residue_values),
        "ligand_atom_locator": _locator(**ligand_values),
        "explicit_bond_authority_class": "validated_struct_conn",
        "explicit_bond_provenance_id": "struct_conn:covale1",
    }
    values.update(overrides)
    return gate.CovalentBondAtomPairCanonicalRecordDesign(**values)


def test_public_api_and_frozen_dataclasses() -> None:
    assert gate.__all__ == (
        "CovalentAtomLocatorContractDesign",
        "CovalentBondAtomPairCanonicalRecordDesign",
        "CovalentBondAtomPairEncodingContractDesign",
        "CovalentBondAtomPairPolicyDecision",
        "ModelInputIndexSpaceCompatibilityEvidence",
        "derive_covapie_model_input_index_space_compatibility_evidence_v1",
        "design_covapie_covalent_bond_atom_pair_encoding_contract_v1",
        "evaluate_covapie_covalent_bond_atom_pair_policy_case_v1",
        "project_covapie_legacy_atom_name_pair_v1",
        "serialize_covapie_covalent_bond_atom_pair_encoding_contract_design_v1",
        "validate_covapie_covalent_atom_locator_contract_design_v1",
        "validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1",
    )
    assert gate.CovalentAtomLocatorContractDesign.__dataclass_params__.frozen
    assert (
        gate.CovalentBondAtomPairCanonicalRecordDesign
        .__dataclass_params__.frozen
    )
    assert (
        gate.CovalentBondAtomPairEncodingContractDesign.__dataclass_params__.frozen
    )
    assert gate.CovalentBondAtomPairPolicyDecision.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        _locator().atom_name = "CB"


def test_exact_locator_fields_types_and_missing_sentinel() -> None:
    assert tuple(
        item.name for item in fields(gate.CovalentAtomLocatorContractDesign)
    ) == _checker().LOCATOR_FIELDS
    assert all(
        value is str
        for value in get_type_hints(
            gate.CovalentAtomLocatorContractDesign
        ).values()
    )
    assert gate.validate_covapie_covalent_atom_locator_contract_design_v1(
        _locator()
    )
    assert gate.validate_covapie_covalent_atom_locator_contract_design_v1(
        _locator(model_id="", insertion_code="", altloc="")
    )
    assert not gate.validate_covapie_covalent_atom_locator_contract_design_v1(
        replace(_locator(), model_id=None)  # type: ignore[arg-type]
    )


@pytest.mark.parametrize(
    "field_name",
    ("event_id", "pdb_id", "comp_id", "atom_name"),
)
def test_required_locator_strings_fail_closed(field_name: str) -> None:
    assert not gate.validate_covapie_covalent_atom_locator_contract_design_v1(
        _locator(**{field_name: ""})
    )


def test_locator_role_vocabulary_is_exact_and_role_labeled() -> None:
    assert gate.ROLE_VOCABULARY == (
        "target_residue_atom",
        "ligand_atom",
    )
    assert gate.validate_covapie_covalent_atom_locator_contract_design_v1(
        _locator(entity_role="ligand_atom", comp_id="LIG", atom_name="C1")
    )
    assert not gate.validate_covapie_covalent_atom_locator_contract_design_v1(
        _locator(entity_role="protein_atom")
    )


def test_canonical_pair_record_exact_fields_types_and_frozen() -> None:
    record_type = gate.CovalentBondAtomPairCanonicalRecordDesign
    assert tuple(item.name for item in fields(record_type)) == (
        "pair_record_schema_version",
        "residue_atom_locator",
        "ligand_atom_locator",
        "explicit_bond_authority_class",
        "explicit_bond_provenance_id",
    )
    assert tuple(get_type_hints(record_type).values()) == (
        str,
        gate.CovalentAtomLocatorContractDesign,
        gate.CovalentAtomLocatorContractDesign,
        str,
        str,
    )
    assert record_type.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        _canonical_record().explicit_bond_provenance_id = "changed"


def test_valid_canonical_record_and_legacy_projection() -> None:
    record = _canonical_record()
    assert (
        gate.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
            record
        )
    )
    assert gate.project_covapie_legacy_atom_name_pair_v1(record) == "SG--C1"


@pytest.mark.parametrize(
    ("record", "reason"),
    (
        (
            _canonical_record(
                residue_overrides={"entity_role": "ligand_atom"}
            ),
            "residue role",
        ),
        (
            _canonical_record(
                ligand_overrides={"entity_role": "target_residue_atom"}
            ),
            "ligand role",
        ),
        (
            _canonical_record(ligand_overrides={"event_id": "EVENT_2"}),
            "event identity",
        ),
        (
            _canonical_record(ligand_overrides={"pdb_id": "2XYZ"}),
            "PDB identity",
        ),
        (
            _canonical_record(ligand_overrides={"model_id": "2"}),
            "model identity",
        ),
        (
            _canonical_record(explicit_bond_authority_class="distance"),
            "authority",
        ),
        (
            _canonical_record(explicit_bond_provenance_id=""),
            "provenance",
        ),
        (
            _canonical_record(
                residue_overrides={"locator_schema_version": "wrong"}
            ),
            "residue locator",
        ),
        (
            _canonical_record(
                ligand_overrides={"atom_name": ""}
            ),
            "ligand locator",
        ),
        (
            _canonical_record(pair_record_schema_version="wrong"),
            "record schema",
        ),
    ),
)
def test_invalid_canonical_record_cases_fail_closed(record, reason) -> None:
    assert reason
    assert not (
        gate.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
            record
        )
    )
    with pytest.raises(ValueError, match="invalid canonical atom-pair record"):
        gate.project_covapie_legacy_atom_name_pair_v1(record)


def test_canonical_record_requires_exact_record_and_nested_locator_types() -> None:
    class RecordSubclass(gate.CovalentBondAtomPairCanonicalRecordDesign):
        pass

    subclass = RecordSubclass(**_canonical_record().__dict__)
    assert not (
        gate.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
            subclass
        )
    )
    wrong_nested = replace(
        _canonical_record(),
        residue_atom_locator=object(),  # type: ignore[arg-type]
    )
    assert not (
        gate.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
            wrong_nested
        )
    )


def test_structured_record_is_canonical_and_legacy_is_not() -> None:
    contract = _contract()
    assert contract.outcome == "frozen"
    assert contract.canonical_encoding_kind == "structured_role_labeled_record"
    assert contract.pair_role_semantics == (
        "residue_atom_locator_and_ligand_atom_locator_are_role_labeled"
    )
    assert contract.legacy_string_role == (
        "legacy_display_and_backward_compatibility_projection"
    )
    manifest = json.loads(_payloads()[gate.MANIFEST_FILE])
    assert manifest["legacy_string_is_canonical_identity"] is False
    assert manifest["legacy_string_is_display_only"] is True
    assert manifest["legacy_value_may_be_used_as_sole_locator"] is False
    assert manifest["legacy_value_may_be_used_as_tensor_target"] is False


def test_explicit_authority_vocabulary_and_distance_only_fail_closed() -> None:
    contract = _contract()
    assert contract.explicit_bond_authority_required is True
    assert contract.accepted_explicit_bond_authority_classes == (
        "validated_struct_conn",
        "explicit_curated_covalent_annotation",
    )
    assert contract.distance_only_inference_forbidden is True
    decision = (
        gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
            "distance_only_candidate"
        )
    )
    assert decision.outcome == "invalid"
    assert decision.reason == "distance_only_inference_forbidden"
    assert decision.fails_closed is True


def test_exactly_one_cardinality_and_duplicate_policy() -> None:
    contract = _contract()
    assert contract.positive_pair_cardinality_policy == (
        "exactly_one_positive_explicit_pair_per_sample"
    )
    assert contract.mapping_cardinality_policy == (
        "exactly_one_residue_atom_row_and_exactly_one_ligand_atom_row"
    )
    valid = gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
        "valid_explicit_single_pair"
    )
    duplicate = gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
        "exact_duplicate_evidence"
    )
    assert valid.outcome == "valid" and valid.mapping_allowed
    assert duplicate.outcome == "valid_deduplicated"
    assert duplicate.pair_retained and duplicate.mapping_allowed


@pytest.mark.parametrize(
    "case_id",
    (
        "zero_pair",
        "multiple_distinct_pairs",
        "conflicting_duplicate",
    ),
)
def test_zero_multi_and_conflicting_pairs_fail_closed(case_id: str) -> None:
    decision = gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
        case_id
    )
    assert decision.outcome == "invalid"
    assert decision.pair_retained is False
    assert decision.mapping_allowed is False
    assert decision.fails_closed is True


@pytest.mark.parametrize(
    "case_id",
    (
        "missing_residue_locator",
        "missing_ligand_locator",
        "ambiguous_residue_mapping",
        "ambiguous_ligand_mapping",
        "altloc_ambiguity",
        "model_ambiguity",
        "insertion_code_ambiguity",
    ),
)
def test_missing_or_ambiguous_locator_mapping_fails_closed(
    case_id: str,
) -> None:
    decision = gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
        case_id
    )
    assert decision.outcome == "invalid"
    assert decision.fails_closed is True
    assert decision.mapping_allowed is False


@pytest.mark.parametrize(
    "case_id",
    (
        "unsupported_explicit_authority",
        "missing_explicit_authority_provenance",
        "residue_role_mismatch",
        "ligand_role_mismatch",
        "event_identity_mismatch",
        "pdb_identity_mismatch",
        "model_identity_mismatch",
    ),
)
def test_canonical_record_policy_cases_fail_closed(case_id: str) -> None:
    decision = gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
        case_id
    )
    assert decision.outcome == "invalid"
    assert decision.pair_retained is False
    assert decision.mapping_allowed is False
    assert decision.fails_closed is True


def test_future_mapping_index_spaces_are_zero_based_derived_views() -> None:
    contract = _contract()
    assert contract.residue_model_index_space == "pocket_atom_table_row_index"
    assert contract.ligand_model_index_space == "ligand_atom_table_row_index"
    assert contract.model_index_base == 0
    manifest = json.loads(_payloads()[gate.MANIFEST_FILE])
    assert manifest["semantic_locator_is_authority"] is True
    assert manifest["row_index_is_derived_view"] is True
    assert manifest["full_protein_mapping_role"] == (
        "trace_or_qa_only_not_v1_model_target"
    )
    assert (
        gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
            "non_zero_based_requested_index"
        ).outcome
        == "invalid"
    )


def test_index_space_compatibility_is_derived_from_committed_evidence() -> None:
    evidence = _evidence()
    assert evidence.final_dataset_pocket_atom_table_reference_present is True
    assert evidence.final_dataset_ligand_atom_table_reference_present is True
    assert evidence.current_pair_tensor_index_contract_present is False
    assert evidence.conflicting_existing_index_space_contract_present is False
    assert evidence.pair_tensorization_currently_blocked is True
    assert (
        evidence.row_order_validation_deferred_to_contract_validation is True
    )
    assert evidence.compatible is True
    assert evidence.evidence_paths == tuple(
        path.as_posix() for path in gate.INDEX_SPACE_EVIDENCE_SHA256
    )
    for relative, expected in gate.INDEX_SPACE_EVIDENCE_SHA256.items():
        assert subprocess.run(
            (
                "git",
                "cat-file",
                "-e",
                f"{gate.BASE_COMMIT}:{relative.as_posix()}",
            ),
            cwd=ROOT,
            check=False,
        ).returncode == 0
        assert gate._sha256((ROOT / relative).read_bytes()) == expected


@pytest.mark.parametrize(
    "evidence",
    (
        replace(
            _evidence(),
            conflicting_existing_index_space_contract_present=True,
        ),
        replace(
            _evidence(),
            current_pair_tensor_index_contract_present=True,
        ),
        replace(
            _evidence(),
            pair_tensorization_currently_blocked=False,
        ),
        replace(
            _evidence(),
            row_order_validation_deferred_to_contract_validation=False,
        ),
    ),
)
def test_incompatible_index_space_evidence_makes_design_invalid(
    evidence,
) -> None:
    contract = _contract(
        model_input_index_space_compatibility_evidence=evidence
    )
    assert contract.outcome == "invalid"
    assert contract.ready_for_contract_validation is False
    assert contract.ready_for_tensorization is False
    assert contract.ready_for_training is False


def test_artifact_builder_has_no_literal_index_compatibility_success() -> None:
    source = inspect.getsource(
        gate.build_covapie_covalent_bond_atom_pair_encoding_contract_artifacts_v1
    )
    assert "model_input_index_spaces_compatible=True" not in source
    assert "compatible=True" not in source
    assert (
        "derive_covapie_model_input_index_space_compatibility_evidence_v1"
        in source
    )
    assert (
        "model_input_index_space_compatibility_evidence="
        in source
    )


def test_five_mask_pair_identity_is_invariant_including_b3() -> None:
    assert gate.CANONICAL_MASKS == (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )
    manifest = json.loads(_payloads()[gate.MANIFEST_FILE])
    assert manifest["canonical_mask_pair_identity_invariant"] is True
    assert manifest["b3_warhead_retention_changes_pair_identity"] is False
    assert manifest["b3_pair_auxiliary_loss_activation_defined"] is False


def test_tensor_loss_model_and_training_boundaries_remain_closed() -> None:
    contract = _contract()
    assert contract.pair_tensor_materialized is False
    assert contract.pair_tensor_shape_defined is False
    assert contract.pair_loss_mask_defined is False
    manifest = json.loads(_payloads()[gate.MANIFEST_FILE])
    for key in (
        "pair_head_implemented",
        "pair_contrastive_loss_implemented",
        "model_changed",
        "dataloader_changed",
        "forward_changed",
        "loss_changed",
        "training_used",
        "raw_read",
        "provider_used",
        "download_used",
    ):
        assert manifest[key] is False


def test_seven_legacy_values_are_name_level_compatible_only() -> None:
    rows = _rows(gate.LEGACY_FILE)
    records = gate._canonical_records_from_current_representation(
        (ROOT / gate.PREDECESSOR_REPRESENTATION).read_bytes()
    )
    assert len(records) == 7
    assert tuple(row["legacy_value"] for row in rows) == gate.LEGACY_VALUES
    for row, record in zip(rows, records):
        assert (
            gate.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
                record
            )
        )
        assert (
            gate.project_covapie_legacy_atom_name_pair_v1(record)
            == row["legacy_value"]
        )
        assert row["reconstructed_legacy_value"] == row["legacy_value"]
        assert row["matches_current_observation"] == "true"
        assert row["canonical_identity_source"] == (
            "structured_role_labeled_record"
        )
        assert row["legacy_is_display_only"] == "true"
        assert row["current_cys_sg_compatible"] == "true"


def test_issue_inventory_stays_open_and_byte_identical() -> None:
    issue_payload = _payloads()[gate.ISSUE_FILE]
    predecessor = (ROOT / gate.PREDECESSOR_ISSUES).read_bytes()
    assert issue_payload == predecessor
    assert gate._sha256(issue_payload) == (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    )
    issues = _rows(gate.ISSUE_FILE)
    assert tuple(
        row["issue_id"]
        for row in issues
        if row["successor_effective_status"] == "open"
    ) == (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    )
    manifest = json.loads(_payloads()[gate.MANIFEST_FILE])
    assert manifest["issue_status_changed"] is False
    assert (
        manifest["resolved_issue_count"],
        manifest["new_issue_count"],
        manifest["deleted_issue_count"],
    ) == (0, 0, 0)


def test_validation_readiness_is_separate_from_tensor_and_training() -> None:
    contract = _contract()
    assert contract.ready_for_contract_validation is True
    assert contract.ready_for_tensorization is False
    assert contract.atom_pair_issue_resolved is False
    assert contract.ready_for_training is False
    manifest = json.loads(_payloads()[gate.MANIFEST_FILE])
    assert manifest["canonical_pair_record_schema_frozen"] is True
    assert manifest["canonical_pair_record_validator_available"] is True
    assert (
        manifest[
            "model_input_index_space_compatibility_derived_from_committed_evidence"
        ]
        is True
    )
    assert (
        manifest["model_input_index_space_compatibility_verified"] is True
    )
    assert manifest["encoding_contract_validation_completed"] is False
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["feature_semantics_known"] is False
    assert manifest["unknown_atom_feature_policy_resolved"] is False


@pytest.mark.parametrize(
    "overrides",
    (
        {"current_semantics_audit_precondition_verified": False},
        {
            "model_input_index_space_compatibility_evidence": replace(
                _evidence(), compatible=False
            )
        },
    ),
)
def test_design_precondition_failure_is_invalid(overrides) -> None:
    contract = _contract(**overrides)
    assert contract.outcome == "invalid"
    assert contract.ready_for_contract_validation is False
    assert contract.ready_for_tensorization is False
    assert contract.ready_for_training is False


def test_exact_bool_inputs_and_unknown_policy_case_fail_closed() -> None:
    with pytest.raises(TypeError):
        gate.design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
            current_semantics_audit_precondition_verified=1,  # type: ignore[arg-type]
            model_input_index_space_compatibility_evidence=_evidence(),
        )
    with pytest.raises(TypeError):
        gate.design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
            current_semantics_audit_precondition_verified=True,
            model_input_index_space_compatibility_evidence=True,  # type: ignore[arg-type]
        )
    unknown = gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
        "not_in_v1"
    )
    assert unknown.outcome == "invalid"
    assert unknown.reason == "unknown_policy_case"
    assert unknown.fails_closed is True


def test_contract_decision_serialization_and_all_evidence_are_deterministic() -> None:
    evidence = tuple(
        gate.derive_covapie_model_input_index_space_compatibility_evidence_v1(
            ROOT
        )
        for _ in range(3)
    )
    assert evidence[0] == evidence[1] == evidence[2]
    record_sets = tuple(
        gate._canonical_records_from_current_representation(
            (ROOT / gate.PREDECESSOR_REPRESENTATION).read_bytes()
        )
        for _ in range(3)
    )
    assert record_sets[0] == record_sets[1] == record_sets[2]
    projections = tuple(
        tuple(
            gate.project_covapie_legacy_atom_name_pair_v1(record)
            for record in records
        )
        for records in record_sets
    )
    assert projections[0] == projections[1] == projections[2]
    decisions = tuple(_contract() for _ in range(3))
    assert decisions[0] == decisions[1] == decisions[2]
    serialized = tuple(
        gate.serialize_covapie_covalent_bond_atom_pair_encoding_contract_design_v1(
            decision
        )
        for decision in decisions
    )
    assert serialized[0] == serialized[1] == serialized[2]
    builds = tuple(
        gate.build_covapie_covalent_bond_atom_pair_encoding_contract_artifacts_v1(
            ROOT
        )
        for _ in range(3)
    )
    assert builds[0] == builds[1] == builds[2]
    assert all(
        builds[0][name] == (ROOT / gate.OUTPUT_ROOT / name).read_bytes()
        for name in gate.OUTPUT_FILES
    )


def test_predecessor_sha_and_readiness_are_verified_independently() -> None:
    checker = _checker()
    checker._verify_base_and_predecessors()
    manifest = json.loads((ROOT / gate.PREDECESSOR_MANIFEST).read_bytes())
    assert manifest["outcome"] == "audited"
    assert manifest["ready_for_encoding_contract_design"] is True
    assert manifest["ready_for_training"] is False


def test_checker_validates_direct_evidence_and_required_stdout() -> None:
    result = subprocess.run(
        (sys.executable, "-B", CHECKER_PATH.as_posix()),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == b""
    required = (
        b"encoding_contract_frozen=true",
        b"structured_canonical_encoding_frozen=true",
        b"distance_only_inference_forbidden=true",
        b"positive_pair_cardinality_policy=exactly_one_positive_explicit_pair_per_sample",
        b"model_index_base=0",
        b"pair_tensor_materialized=false",
        b"encoding_contract_validation_completed=false",
        b"atom_pair_issue_resolved=false",
        b"ready_for_contract_validation=true",
        b"ready_for_tensorization=false",
        b"feature_semantics_audit_completed=false",
        b"ready_for_training=false",
    )
    assert all(item in result.stdout for item in required)


def test_import_is_quiet_and_has_no_output_side_effects(tmp_path: Path) -> None:
    result = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext.covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1",
        ),
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(ROOT / "src"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
    assert tuple(tmp_path.iterdir()) == ()


def test_shared_lifecycle_three_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert _contract().outcome == "frozen"
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
                    checker.TEST.as_posix(),
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
                (sys.executable, "-B", checker.CHECKER.as_posix()),
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
    pass_counts = tuple(
        next(
            token
            for token in output.split()
            if token.isdigit()
            and f"{token.decode()} passed".encode() in output
        )
        for output in targeted_outputs
    )
    assert len(set(pass_counts)) == 1
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == checker.BASE_COMMIT
    assert report.candidate_subject == checker.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True

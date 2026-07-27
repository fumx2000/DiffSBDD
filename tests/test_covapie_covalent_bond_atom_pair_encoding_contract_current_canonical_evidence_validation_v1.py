from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import subprocess
import sys
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, fields, replace
from functools import lru_cache
from pathlib import Path

import pytest

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle
from covalent_ext import (
    covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1
    as gate,
)
from covalent_ext import (
    covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1 as contract,
)

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / (
    "check_covapie_covalent_bond_atom_pair_encoding_contract_"
    "current_canonical_evidence_validation_v1.py"
)
NESTED_LIFECYCLE_ENV = "COVAPIE_ATOM_PAIR_VALIDATION_NESTED_LIFECYCLE"


@lru_cache(maxsize=1)
def _result():
    return gate.derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(
        ROOT
    )


@lru_cache(maxsize=1)
def _artifacts():
    return gate.build_covapie_covalent_bond_atom_pair_encoding_contract_validation_artifacts_v1(
        ROOT
    )


@lru_cache(maxsize=1)
def _checker():
    spec = importlib.util.spec_from_file_location("atom_pair_validation_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _base_rows(path: str | Path) -> list[dict[str, str]]:
    payload = _base_payload(path)
    return list(csv.DictReader(io.StringIO(payload.decode(), newline="")))


def _base_payload(path: str | Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{gate.BASE_COMMIT}:{Path(path).as_posix()}"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _sample_and_record(index: int = 0):
    sample = _base_rows(gate.FINAL_DATASET_INDEX)[index]
    event = _base_rows(sample["covalent_event_table_path"])[0]
    return sample, event, gate._record(event)


def _bundle_values(index: int = 0) -> dict[str, object]:
    sample = _base_rows(gate.FINAL_DATASET_INDEX)[index]
    pocket_payload = _base_payload(sample["pocket_atom_table_path"])
    ligand_payload = _base_payload(sample["ligand_atom_table_path"])
    return {
        "contract_precondition_verified": True,
        "sample_row": sample,
        "event_rows": _base_rows(sample["covalent_event_table_path"]),
        "pair_rows": _base_rows(sample["ligand_residue_atom_pair_table_path"]),
        "pocket_table_payload": pocket_payload,
        "pocket_table_rows": _base_rows(sample["pocket_atom_table_path"]),
        "ligand_table_payload": ligand_payload,
        "ligand_table_rows": _base_rows(sample["ligand_atom_table_path"]),
        "expected_pocket_table_sha256": gate._sha(pocket_payload),
        "expected_ligand_table_sha256": gate._sha(ligand_payload),
        "model_index_base": 0,
    }


def _bundle(**overrides):
    values = _bundle_values()
    values.update(overrides)
    return gate.validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1(
        **values
    )


def test_public_validation_api_and_frozen_decision() -> None:
    assert gate.__all__ == (
        "CovalentBondAtomPairEncodingContractValidationDecision",
        "CovalentBondAtomPairSampleEvidenceValidationObservation",
        "build_covapie_covalent_bond_atom_pair_encoding_contract_validation_artifacts_v1",
        "derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1",
        "serialize_covapie_covalent_bond_atom_pair_encoding_contract_validation_decision_v1",
        "validate_covapie_atom_table_locator_exact_one_v1",
        "validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1",
    )
    assert gate.CovalentBondAtomPairEncodingContractValidationDecision.__dataclass_params__.frozen
    assert gate.CovalentBondAtomPairSampleEvidenceValidationObservation.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        _result()["decision"].outcome = "invalid"
    assert tuple(item.name for item in fields(gate.CovalentBondAtomPairEncodingContractValidationDecision)) == (
        "schema_version", "outcome", "contract_precondition_verified",
        "current_canonical_record_count", "canonical_record_valid_count",
        "exact_one_residue_mapping_count", "exact_one_ligand_mapping_count",
        "pair_table_atom_site_crosscheck_count",
        "pair_table_coordinate_crosscheck_count", "legacy_projection_match_count",
        "explicit_bond_authority_preserved_count", "model_index_base",
        "row_order_validation_completed", "encoding_contract_validation_completed",
        "atom_pair_issue_resolved", "provider_issue_resolved",
        "atom_pair_ready_for_downstream_contracts", "ready_for_tensorization",
        "feature_semantics_audit_completed", "ready_for_training",
        "recommended_next_step",
    )


def test_mapping_helper_rejects_wrong_types_and_invalid_locator_schema() -> None:
    sample, _, record = _sample_and_record()
    table = _base_rows(sample["pocket_atom_table_path"])
    invalid = replace(
        record.residue_atom_locator, locator_schema_version="invalid"
    )
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        object(), table  # type: ignore[arg-type]
    ) == (0, None)
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        invalid, table
    ) == (0, None)
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, tuple(table)  # type: ignore[arg-type]
    ) == (0, None)
    malformed = deepcopy(table)
    malformed[0]["atom_site_id"] = 1  # type: ignore[assignment]
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, malformed
    ) == (0, None)
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, table,
        expected_het_id=1,  # type: ignore[arg-type]
    ) == (0, None)
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, table, model_index_base=True
    ) == (0, None)


def test_nonempty_optional_locator_column_unavailable_fails_closed() -> None:
    sample, _, record = _sample_and_record()
    pocket = _base_rows(sample["pocket_atom_table_path"])
    ligand = _base_rows(sample["ligand_atom_table_path"])
    cases = (
        (replace(record.residue_atom_locator, model_id="1"), pocket),
        (replace(record.residue_atom_locator, altloc="A"), pocket),
        (replace(record.residue_atom_locator, insertion_code="A"), pocket),
        (replace(record.ligand_atom_locator, insertion_code="A"), ligand),
    )
    for locator, table in cases:
        assert gate.validate_covapie_atom_table_locator_exact_one_v1(
            locator, table, expected_het_id=sample["expected_het_id"]
        ) == (0, None)


def test_unified_sample_bundle_normal_path_passes() -> None:
    observation = _bundle()
    assert observation.outcome == "validated"
    assert observation.record_retained is True
    assert observation.mapping_retained is True
    assert observation.residue_row_index_0based == 88
    assert observation.ligand_row_index_0based == 3
    assert observation.atom_site_crosscheck_valid is True
    assert observation.coordinate_crosscheck_valid is True
    assert observation.source_binding_valid is True


@pytest.mark.parametrize(
    "tamper",
    (
        "legacy",
        "zero_pair",
        "multiple_pair",
        "residue_site",
        "ligand_site",
        "coordinate",
        "row_count",
        "missing_target",
    ),
)
def test_unified_bundle_tampers_fail_closed(tamper: str) -> None:
    values = _bundle_values()
    if tamper == "legacy":
        sample = deepcopy(values["sample_row"])
        sample["covalent_bond_atom_pair"] = "SG--TAMPER"
        values["sample_row"] = sample
    elif tamper == "zero_pair":
        values["pair_rows"] = []
    elif tamper == "multiple_pair":
        values["pair_rows"] = [
            deepcopy(values["pair_rows"][0]),
            deepcopy(values["pair_rows"][0]),
        ]
    elif tamper in {"residue_site", "ligand_site", "coordinate"}:
        pair = deepcopy(values["pair_rows"][0])
        key = {
            "residue_site": "residue_atom_site_id",
            "ligand_site": "ligand_atom_site_id",
            "coordinate": "residue_x",
        }[tamper]
        pair[key] = "TAMPER" if tamper != "coordinate" else "999999"
        values["pair_rows"] = [pair]
    elif tamper == "row_count":
        sample = deepcopy(values["sample_row"])
        sample["pocket_atom_count"] = str(int(sample["pocket_atom_count"]) + 1)
        values["sample_row"] = sample
    elif tamper == "missing_target":
        values["pocket_table_payload"] = gate._csv_bytes(
            tuple(values["pocket_table_rows"][0]), []
        )
        values["pocket_table_rows"] = []
    observation = (
        gate.validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1(
            **values
        )
    )
    assert observation.outcome == "invalid"
    assert observation.record_retained is False
    assert observation.mapping_retained is False


def test_contract_predecessor_verification_is_base_bound() -> None:
    assert _result()["decision"].contract_precondition_verified is True
    for path, expected in gate.FROZEN_SHA256.items():
        payload = subprocess.check_output(
            ("git", "show", f"{gate.BASE_COMMIT}:{path.as_posix()}"), cwd=ROOT
        )
        assert gate._sha(payload) == expected
    tampered = {
        path: subprocess.check_output(
            ("git", "show", f"{gate.BASE_COMMIT}:{path.as_posix()}"), cwd=ROOT
        )
        for path in gate.FROZEN_SHA256
    }
    tampered[gate.CONTRACT_SOURCE] += b"tamper"
    assert gate._precondition(tampered) is False


def test_exactly_11_structured_records_come_from_event_fields() -> None:
    records = _result()["records"]
    index = _base_rows(gate.FINAL_DATASET_INDEX)
    assert len(records) == len(index) == 11
    for sample, record in zip(index, records):
        event = _base_rows(sample["covalent_event_table_path"])[0]
        assert record.residue_atom_locator.event_id == event["sample_preparation_input_id"]
        assert record.residue_atom_locator.auth_seq_id == event["residue_auth_seq_id"]
        assert record.ligand_atom_locator.auth_seq_id == event["ligand_auth_seq_id"]
        assert record.explicit_bond_provenance_id == f"{event['sample_preparation_input_id']}:{event['conn_id']}"


def test_all_canonical_records_validate_and_authority_is_explicit() -> None:
    rows = _result()["canonical_rows"]
    assert len(rows) == 11
    assert all(
        contract.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(record)
        for record in _result()["records"]
    )
    assert {row["explicit_bond_authority_class"] for row in rows} == {"validated_struct_conn"}
    assert all(row["canonical_record_valid"] and row["explicit_authority_preserved"] for row in rows)


def test_seven_legacy_projections_remain_compatible() -> None:
    rows = _result()["canonical_rows"]
    assert {row["legacy_projection"] for row in rows} == set(contract.LEGACY_VALUES)
    assert all(row["legacy_projection_matches"] for row in rows)


def test_exact_one_residue_mappings_and_zero_based_ranges() -> None:
    rows = [row for row in _result()["mapping_rows"] if row["entity_role"] == "target_residue_atom"]
    assert len(rows) == 11
    assert all(row["candidate_match_count"] == 1 and row["verified"] for row in rows)
    assert all(0 <= row["matched_row_index_0based"] < row["target_table_data_row_count"] for row in rows)


def test_exact_one_ligand_mappings_and_zero_based_ranges() -> None:
    rows = [row for row in _result()["mapping_rows"] if row["entity_role"] == "ligand_atom"]
    assert len(rows) == 11
    assert all(row["candidate_match_count"] == 1 and row["verified"] for row in rows)
    assert all(0 <= row["matched_row_index_0based"] < row["target_table_data_row_count"] for row in rows)


def test_row_counts_atom_sites_coordinates_and_distance_boundary() -> None:
    rows = _result()["mapping_rows"]
    assert len(rows) == 22
    assert all(row["source_row_order_sha_bound"] for row in rows)
    assert all(row["atom_site_id_matches"] for row in rows)
    assert all(row["coordinate_crosscheck_passed"] for row in rows)
    assert all(row["distance_used_for_mapping_selection"] is False for row in rows)


def test_missing_and_duplicate_residue_mapping_fail_closed() -> None:
    sample, _, record = _sample_and_record()
    table = _base_rows(sample["pocket_atom_table_path"])
    count, index = gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, table[0:1], expected_het_id=sample["expected_het_id"]
    )
    assert (count, index) == (0, None)
    matched = [
        row for row in table
        if row["atom_name"] == record.residue_atom_locator.atom_name
        and row["auth_seq_id"] == record.residue_atom_locator.auth_seq_id
    ][0]
    duplicated = deepcopy(table) + [deepcopy(matched)]
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, duplicated, expected_het_id=sample["expected_het_id"]
    )[1] is None


def test_missing_and_duplicate_ligand_mapping_fail_closed() -> None:
    sample, _, record = _sample_and_record()
    table = _base_rows(sample["ligand_atom_table_path"])
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.ligand_atom_locator, table[0:1], expected_het_id=sample["expected_het_id"]
    ) == (0, None)
    matched = [row for row in table if row["is_covalent_ligand_atom"] == "True"][0]
    duplicated = deepcopy(table) + [deepcopy(matched)]
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.ligand_atom_locator, duplicated, expected_het_id=sample["expected_het_id"]
    )[1] is None


@pytest.mark.parametrize(
    "mutator",
    (
        lambda r: replace(r, pair_record_schema_version="invalid"),
        lambda r: replace(r, explicit_bond_authority_class="distance"),
        lambda r: replace(r, explicit_bond_provenance_id=""),
        lambda r: replace(r, residue_atom_locator=replace(r.residue_atom_locator, event_id="other")),
        lambda r: replace(r, ligand_atom_locator=replace(r.ligand_atom_locator, pdb_id="other")),
        lambda r: replace(r, residue_atom_locator=replace(r.residue_atom_locator, entity_role="ligand_atom")),
    ),
)
def test_schema_event_pdb_role_authority_and_provenance_mismatches_fail_closed(mutator) -> None:
    record = mutator(_sample_and_record()[2])
    assert not contract.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(record)


def test_model_altloc_ambiguity_and_nonzero_index_base_fail_closed() -> None:
    sample, _, record = _sample_and_record()
    table = _base_rows(sample["ligand_atom_table_path"])
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.ligand_atom_locator, table, expected_het_id=sample["expected_het_id"], model_index_base=1
    ) == (0, None)
    matched = [row for row in table if row["is_covalent_ligand_atom"] == "True"][0]
    for field_name, column, value in (("model_id", "model_num", "1"), ("altloc", "altloc", "A")):
        locator = replace(record.ligand_atom_locator, **{field_name: value})
        ambiguous = deepcopy(table)
        original = next(
            row for row in ambiguous if row["atom_site_id"] == matched["atom_site_id"]
        )
        original[column] = value
        ambiguous.append(deepcopy(original))
        count, index = gate.validate_covapie_atom_table_locator_exact_one_v1(
            locator, ambiguous, expected_het_id=sample["expected_het_id"]
        )
        assert index is None
        assert count != 1


def test_row_order_drift_is_rejected_by_original_sha_binding() -> None:
    values = _bundle_values()
    original_rows = values["pocket_table_rows"]
    drifted = list(reversed(deepcopy(original_rows)))
    values["pocket_table_rows"] = drifted
    values["pocket_table_payload"] = gate._csv_bytes(
        tuple(original_rows[0]), drifted
    )
    observation = (
        gate.validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1(
            **values
        )
    )
    assert observation.outcome == "invalid"
    assert observation.source_binding_valid is False
    assert observation.record_retained is False
    assert observation.mapping_retained is False


def test_failure_matrix_is_complete_and_fail_closed() -> None:
    rows = _result()["failure_rows"]
    assert tuple(row["failure_case"] for row in rows) == gate.FAILURE_CASES
    assert len(rows) == 27
    assert all(
        row["expected_outcome"] == row["observed_outcome"] == "invalid"
        and row["fails_closed"] and not row["record_retained"]
        and not row["mapping_retained"] and not row["issue_resolved"]
        and row["verified"]
        for row in rows
    )


def test_failure_matrix_is_required_for_issue_resolution() -> None:
    assert _result()["all_failure_cases_verified"] is True
    assert gate._overall_validation_success(
        precondition=True,
        all_canonical=True,
        all_mappings=True,
        row_order_ok=True,
        all_failure_cases_verified=True,
    ) is True
    assert gate._overall_validation_success(
        precondition=True,
        all_canonical=True,
        all_mappings=True,
        row_order_ok=True,
        all_failure_cases_verified=False,
    ) is False
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    assert manifest["failure_matrix_executable"] is True
    assert manifest["failure_matrix_all_cases_verified"] is True
    assert manifest["failure_matrix_required_for_issue_resolution"] is True


def test_false_failure_observation_keeps_atom_pair_issue_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def one_unverified(**_kwargs):
        return {
            name: index != 0 for index, name in enumerate(gate.FAILURE_CASES)
        }

    monkeypatch.setattr(gate, "_failure_observations", one_unverified)
    result = (
        gate.derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(
            ROOT
        )
    )
    assert result["all_failure_cases_verified"] is False
    assert result["decision"].outcome == "invalid"
    assert result["decision"].atom_pair_issue_resolved is False
    atom_pair = next(
        row for row in result["issue_rows"]
        if row["issue_id"] == "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED"
    )
    assert atom_pair["successor_effective_status"] == "open"


def test_sample_level_bilateral_crosscheck_counts_and_exact_indices() -> None:
    decision = _result()["decision"]
    assert decision.pair_table_atom_site_crosscheck_count == 11
    assert decision.pair_table_coordinate_crosscheck_count == 11
    expected = (
        (88, 3), (25, 3), (19, 3), (39, 3), (37, 27), (50, 21),
        (48, 16), (53, 20), (52, 21), (53, 18), (84, 5),
    )
    observations = _result()["sample_observations"]
    assert tuple(
        (
            observation.residue_row_index_0based,
            observation.ligand_row_index_0based,
        )
        for observation in observations
    ) == expected
    assert all(
        observation.residue_atom_site_matches
        and observation.ligand_atom_site_matches
        and observation.residue_coordinate_matches
        and observation.ligand_coordinate_matches
        for observation in observations
    )


def test_atom_pair_issue_only_transition_and_provider_remains_open() -> None:
    predecessor = _base_rows(gate.PREDECESSOR_ISSUES)
    successor = _result()["issue_rows"]
    assert len(predecessor) == len(successor) == 30
    changed = []
    for old, new in zip(predecessor, successor):
        assert old["issue_id"] == new["issue_id"]
        differences = {key for key in old if old[key] != new[key]}
        if differences:
            changed.append((old["issue_id"], differences))
    assert changed == [(
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        {
            "successor_effective_status", "successor_transition_stage",
            "successor_transition_action", "successor_transition_evidence",
        },
    )]
    assert [row["issue_id"] for row in successor if row["successor_effective_status"] == "open"] == [
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
    ]


def test_tensor_model_training_and_feature_semantics_remain_closed() -> None:
    decision = _result()["decision"]
    assert decision.atom_pair_issue_resolved is True
    assert decision.provider_issue_resolved is False
    assert decision.ready_for_tensorization is False
    assert decision.feature_semantics_audit_completed is False
    assert decision.ready_for_training is False
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    assert manifest["pair_tensor_materialized"] is False
    assert manifest["pair_head_implemented"] is False
    assert manifest["pair_contrastive_loss_implemented"] is False
    assert manifest["raw_read"] is False and manifest["training_used"] is False


def test_source_inventory_is_complete_base_bound_and_never_lists_raw() -> None:
    rows = _result()["source_rows"]
    assert len(rows) == 49
    assert all(row["committed_in_base"] and row["verified"] for row in rows)
    assert sum(row["source_role"] == "event_table" for row in rows) == 11
    assert sum(row["source_role"] == "pair_table" for row in rows) == 11
    assert sum(row["source_role"] == "pocket_table" for row in rows) == 11
    assert sum(row["source_role"] == "ligand_table" for row in rows) == 11
    assert all(not row["source_path"].startswith("data/raw/") for row in rows)
    assert all(row["read_count"] == 3 for row in rows if row["source_role"] in {"pocket_table", "ligand_table"})


def test_deterministic_decision_records_mappings_and_all_evidence_bytes() -> None:
    first = gate.derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(ROOT)
    second = gate.derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(ROOT)
    third = gate.derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(ROOT)
    assert first == second == third
    assert gate.serialize_covapie_covalent_bond_atom_pair_encoding_contract_validation_decision_v1(first["decision"]) == gate.serialize_covapie_covalent_bond_atom_pair_encoding_contract_validation_decision_v1(second["decision"])
    assert _artifacts() == gate.build_covapie_covalent_bond_atom_pair_encoding_contract_validation_artifacts_v1(ROOT)


def test_materialized_artifacts_match_builder_and_manifest_evidence_hashes() -> None:
    for name, payload in _artifacts().items():
        assert (ROOT / gate.OUTPUT_ROOT / name).read_bytes() == payload
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    for name, expected in manifest["evidence_sha256"].items():
        assert gate._sha(_artifacts()[name]) == expected
    assert manifest["canonical_masks"] == [
        {"semantic_name": name, "display_alias": alias}
        for name, alias in gate.CANONICAL_MASKS
    ]


def test_checker_independently_reconstructs_and_reports() -> None:
    first = subprocess.run(
        (sys.executable, "-B", CHECKER_PATH.as_posix()), cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    second = subprocess.run(
        (sys.executable, "-B", CHECKER_PATH.as_posix()), cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert b"validation_outcome=validated" in first.stdout
    assert b"ready_for_training=false" in first.stdout


def test_shared_lifecycle_three_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert _result()["decision"].outcome == "validated"
        return
    checker = _checker()
    real_capture = lifecycle._capture_state
    states: list[str] = []
    checker_outputs: list[bytes] = []

    def capture(repository, **kwargs):
        state = real_capture(repository, **kwargs)
        if state.lifecycle in (
            "pre_commit", "formal_main_post_commit_unpushed", "formal_main_post_push"
        ):
            environment = {
                **os.environ,
                NESTED_LIFECYCLE_ENV: "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": "src",
            }
            targeted = subprocess.run(
                (sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", checker.EXACT10[1].as_posix()),
                cwd=repository, env=environment, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            assert targeted.returncode == 0, targeted.stdout + targeted.stderr
            assert targeted.stderr == b""
            checked = subprocess.run(
                (sys.executable, "-B", checker.EXACT10[2].as_posix()),
                cwd=repository, env=environment, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            assert checked.returncode == 0, checked.stdout + checked.stderr
            assert checked.stderr == b""
            states.append(state.lifecycle)
            checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT, tmp_path, base_commit=gate.BASE_COMMIT,
        formal_commit_subject=gate.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert states == [
        "pre_commit", "formal_main_post_commit_unpushed", "formal_main_post_push"
    ]
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == gate.BASE_COMMIT
    assert report.candidate_subject == gate.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True

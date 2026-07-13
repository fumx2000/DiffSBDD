from __future__ import annotations

import copy
import csv
import hashlib
import ast
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from covalent_ext import covapie_final_dataset_materialization_smoke as contract


def snapshot():
    return contract.build_contract_snapshot()


def result(data=None):
    return contract.validate_contract_snapshot(snapshot() if data is None else data)


def test_valid_snapshot_passes():
    assert result()["contract_validation_passed"] is True


def test_source_inputs_exactly_twelve():
    assert result()["source_input_count"] == 12


def test_source_logical_names_are_unique():
    data = snapshot(); data["source_input_contract"][1]["logical_name"] = data["source_input_contract"][0]["logical_name"]
    assert "source_logical_name_duplicate" in result(data)["blocking_reasons"]


def test_source_paths_are_unique():
    data = snapshot(); data["source_input_contract"][1]["relative_path"] = data["source_input_contract"][0]["relative_path"]
    assert "source_relative_path_duplicate" in result(data)["blocking_reasons"]


def test_source_counts_are_frozen():
    data = snapshot(); data["source_input_contract"][0]["expected_row_count"] = 2
    assert "source_row_count_contract_mismatch" in result(data)["blocking_reasons"]


def test_outputs_exactly_twelve():
    assert result()["output_artifact_count"] == 12


def test_output_filenames_are_unique():
    data = snapshot(); data["output_artifact_contract"][1]["filename"] = data["output_artifact_contract"][0]["filename"]
    assert "output_filename_duplicate" in result(data)["blocking_reasons"]


def test_canonical_index_has_exactly_33_fields():
    assert result()["canonical_schema_field_count"] == 33


def test_canonical_index_forbids_split_group_and_row_fields():
    data = snapshot(); data["sample_index_fields"].append("assigned_split")
    assert "canonical_index_extra_split_or_group_field" in result(data)["blocking_reasons"]


def test_membership_schema_is_frozen():
    assert result()["membership_field_count"] == len(contract.FINAL_DATASET_MEMBERSHIP_FIELDS)


def test_artifact_path_fields_exactly_six():
    assert result()["artifact_path_field_count"] == 6


def test_artifact_inventory_expected_rows_is_66():
    assert result()["artifact_reference_row_count"] == 66


def test_masks_exactly_five_include_b3():
    data = snapshot(); assert result(data)["canonical_mask_count"] == 5
    data["canonical_masks"] = [mask for mask in data["canonical_masks"] if mask != ("scaffold_only", "B3")]
    assert "canonical_mask_b3_missing" in result(data)["blocking_reasons"]


def test_training_readiness_boundary_is_false():
    data = snapshot(); assert data["training_boundary"]["ready_for_training"] is False
    data["training_boundary"]["ready_for_training"] = True
    assert "training_boundary_contract_mismatch" in result(data)["blocking_reasons"]


def test_missing_pass_evidence_fails():
    data = snapshot(); data["pass_field_evidence_contract"].pop()
    assert "pass_field_evidence_coverage_mismatch" in result(data)["blocking_reasons"]


def test_hardcoded_pass_field_is_forbidden():
    data = snapshot(); data["pass_field_evidence_contract"][0]["may_be_hardcoded"] = True
    assert result(data)["no_pass_field_hardcoding_allowed"] is False


def test_thirteenth_output_fails():
    data = snapshot(); data["output_artifact_contract"].append(copy.deepcopy(data["output_artifact_contract"][0]))
    assert "output_artifact_count_mismatch" in result(data)["blocking_reasons"]


def test_missing_source_input_fails():
    data = snapshot(); data["source_input_contract"].pop()
    assert "source_input_count_mismatch" in result(data)["blocking_reasons"]


def test_membership_field_order_tamper_fails():
    data = snapshot(); data["membership_fields"][0], data["membership_fields"][1] = data["membership_fields"][1], data["membership_fields"][0]
    assert "membership_schema_mismatch" in result(data)["blocking_reasons"]


def test_raw_structure_output_is_forbidden():
    data = snapshot(); data["output_artifact_contract"][0]["contains_raw_structure"] = True
    assert "output_raw_structure_forbidden" in result(data)["blocking_reasons"]


def test_feature_semantics_known_for_training_is_forbidden():
    data = snapshot(); data["training_boundary"]["feature_semantics_known_for_training"] = True
    assert "training_boundary_contract_mismatch" in result(data)["blocking_reasons"]


def test_required_tamper_test_is_mandatory():
    data = snapshot(); data["pass_field_evidence_contract"][0]["required_tamper_test"] = ""
    assert any(item.startswith("pass_field_evidence_missing") for item in result(data)["blocking_reasons"])


def test_r0_snapshot_and_validator_are_repeatable_without_source_loading():
    first = contract.validate_contract_snapshot(contract.build_contract_snapshot())
    second = contract.validate_contract_snapshot(contract.build_contract_snapshot())
    assert first == second and first["contract_validation_passed"] is True


def _bundle(tmp_path):
    values = {}
    for attribute, (_, source) in zip(
        contract.DEFAULT_STEP14AQ_INPUT_PATHS.__dataclass_fields__,
        contract.logical_input_items(contract.DEFAULT_STEP14AQ_INPUT_PATHS),
    ):
        destination = tmp_path / attribute / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(contract._absolute(source), destination)
        values[attribute] = destination
    return contract.Step14AQInputPaths(**values)


def _validate(paths, provenance=False):
    loaded = contract.load_step14aq_inputs_safely(paths)
    return loaded, contract.build_source_step14aq_preconditions_passed_evidence(
        loaded, enforce_commit_provenance=provenance
    )


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def test_r1_default_source_bundle_loads():
    assert contract.load_step14aq_inputs_safely(contract.DEFAULT_STEP14AQ_INPUT_PATHS).input_load_passed


def test_r1_default_commit_provenance_passes():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert validation.source_checks["commit_provenance_passed"] is True


def test_r1_valid_source_validation_passes():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert validation.source_validation_passed is True


def test_r1_manifest_contract_passes():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert validation.source_checks["manifest_contract_passed"] is True


def test_r1_preconditions_45_of_45():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert len(validation.typed_precondition_rows) == 45 and validation.source_checks["precondition_audit_passed"]


def test_r1_policy_29_of_29():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert len(validation.typed_policy_rows) == 29 and validation.source_checks["policy_audit_passed"]


def test_r1_group_5_of_5():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert len(validation.typed_group_rows) == 5 and validation.source_checks["group_assignment_passed"]


def test_r1_sample_11_of_11():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert len(validation.typed_sample_rows) == 11 and validation.source_checks["sample_assignment_passed"]


def test_r1_split_rows_8_2_1():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert [len(validation.typed_train_rows), len(validation.typed_validation_rows), len(validation.typed_test_rows)] == [8, 2, 1]


def test_r1_canonical_source_rows_are_assignment_ordered():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert [row["sample_index_row_id"] for row in validation.canonical_source_rows] == [row["sample_index_row_id"] for row in validation.typed_sample_rows]


def test_r1_leakage_55_of_55():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert len(validation.typed_leakage_rows) == 55 and validation.source_checks["leakage_audit_passed"]


def test_r1_balance_4_of_4():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert len(validation.typed_balance_rows) == 4 and validation.source_checks["balance_audit_passed"]


def test_r1_issue_sentinel_passes():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert validation.source_checks["issue_sentinel_passed"]


def test_r1_safety_33_of_33():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert len(validation.typed_safety_rows) == 33 and validation.source_checks["source_safety_audit_passed"]


def test_r1_missing_manifest_blocks_safely(tmp_path):
    paths = _bundle(tmp_path); paths.manifest.unlink(); loaded, validation = _validate(paths)
    assert not loaded.input_load_passed and "source_file_missing:step14aq_manifest" in validation.blocking_reasons


def test_r1_malformed_manifest_blocks_safely(tmp_path):
    paths = _bundle(tmp_path); paths.manifest.write_text("{")
    _, validation = _validate(paths)
    assert "source_json_unreadable:step14aq_manifest" in validation.blocking_reasons


def test_r1_manifest_readiness_false_blocks(tmp_path):
    paths = _bundle(tmp_path); data = json.loads(paths.manifest.read_text()); data["ready_for_covapie_final_dataset_materialization_smoke"] = False; paths.manifest.write_text(json.dumps(data))
    _, validation = _validate(paths)
    assert "source_manifest_readiness_mismatch" in validation.blocking_reasons


def test_r1_manifest_training_true_blocks(tmp_path):
    paths = _bundle(tmp_path); data = json.loads(paths.manifest.read_text()); data["ready_for_training"] = True; paths.manifest.write_text(json.dumps(data))
    _, validation = _validate(paths)
    assert "source_manifest_readiness_mismatch" in validation.blocking_reasons


def test_r1_precondition_duplicate_item_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.precondition_audit); rows[1]["precondition_item"] = rows[0]["precondition_item"]; _write_csv(paths.precondition_audit, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_precondition_duplicate_item") for item in validation.blocking_reasons)


def test_r1_policy_observed_value_tamper_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.policy_audit); rows[0]["observed_value"] = "tampered"; _write_csv(paths.policy_audit, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_policy_observed_value_mismatch") for item in validation.blocking_reasons)


def test_r1_group_duplicate_id_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.group_split_assignment); rows[1]["final_leakage_group_id"] = rows[0]["final_leakage_group_id"]; _write_csv(paths.group_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert "source_group_duplicate_or_missing" in validation.blocking_reasons


def test_r1_group_member_count_mismatch_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.group_split_assignment); rows[0]["member_count"] = "99"; _write_csv(paths.group_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_group_member_contract_mismatch") for item in validation.blocking_reasons)


def test_r1_sample_assigned_split_mismatch_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.sample_split_assignment); rows[0]["assigned_split"] = "test"; _write_csv(paths.sample_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_sample_assigned_split_mismatch") for item in validation.blocking_reasons)


def test_r1_sample_group_mismatch_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.sample_split_assignment); rows[0]["final_leakage_group_id"] = "COVAPIE_LEAKAGE_GROUP_000005"; _write_csv(paths.sample_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_sample_group_membership_mismatch") for item in validation.blocking_reasons)


def test_r1_train_index_missing_row_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.train_sample_index); rows.pop(); _write_csv(paths.train_sample_index, fields, rows)
    _, validation = _validate(paths)
    assert "source_split_index_count_mismatch:train" in validation.blocking_reasons


def test_r1_duplicate_sample_across_splits_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, train = _read_csv(paths.train_sample_index); _, validation_rows = _read_csv(paths.validation_sample_index); validation_rows[0] = dict(train[0]); _write_csv(paths.validation_sample_index, fields, validation_rows)
    _, validation = _validate(paths)
    assert "source_split_indexes_union_mismatch" in validation.blocking_reasons


def test_r1_split_canonical_schema_tamper_blocks(tmp_path):
    paths = _bundle(tmp_path); _, rows = _read_csv(paths.train_sample_index); _write_csv(paths.train_sample_index, list(contract.SAMPLE_INDEX_FIELDS[:-1]), rows)
    _, validation = _validate(paths)
    assert "source_split_index_schema_mismatch" in validation.blocking_reasons


def test_r1_leakage_missing_pair_with_55_rows_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.cross_split_leakage_audit); rows[-1] = dict(rows[0]); _write_csv(paths.cross_split_leakage_audit, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_leakage_pair_mismatch") for item in validation.blocking_reasons)


def test_r1_leakage_cross_split_signal_tamper_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.cross_split_leakage_audit); row = next(item for item in rows if item["cross_split_pair"] == "True"); row["direct_must_link_edge"] = "True"; _write_csv(paths.cross_split_leakage_audit, fields, rows)
    _, validation = _validate(paths)
    assert "source_leakage_recomputed_count_mismatch" in validation.blocking_reasons


def test_r1_balance_sample_count_tamper_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.split_balance_audit); rows[0]["actual_sample_count"] = "99"; _write_csv(paths.split_balance_audit, fields, rows)
    _, validation = _validate(paths)
    assert "source_balance_count_mismatch:train" in validation.blocking_reasons


def test_r1_wrong_issue_sentinel_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.issue_inventory); rows[0]["issue_id"] = "WRONG"; _write_csv(paths.issue_inventory, fields, rows)
    _, validation = _validate(paths)
    assert "source_issue_sentinel_mismatch" in validation.blocking_reasons


def test_r1_duplicate_safety_item_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.safety_audit); rows[-1]["safety_item"] = rows[0]["safety_item"]; _write_csv(paths.safety_audit, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_safety_duplicate_item") for item in validation.blocking_reasons)


def test_r1_invalid_boolean_string_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.precondition_audit); rows[0]["precondition_passed"] = "yes"; _write_csv(paths.precondition_audit, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_precondition_type_invalid") for item in validation.blocking_reasons)


def test_r1_source_failure_creates_no_step14ar_outputs(tmp_path):
    paths = _bundle(tmp_path); paths.manifest.unlink(); _, validation = _validate(paths)
    assert validation.source_validation_passed is False
    assert not (tmp_path / "data" / "derived" / contract.STAGE).exists()


def test_r1_final_sample_assignment_reorder_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.sample_split_assignment); rows[0], rows[1] = rows[1], rows[0]; _write_csv(paths.sample_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert "source_sample_identity_order_mismatch" in validation.blocking_reasons


def test_r1_final_unknown_sample_id_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.sample_split_assignment); rows[0]["sample_index_row_id"] = "CYS_SG_SAMPLE_INDEX_999999"; _write_csv(paths.sample_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert "source_sample_identity_order_mismatch" in validation.blocking_reasons


def test_r1_final_canonical_source_rows_exact_expected_order():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=True)
    assert [row["sample_index_row_id"] for row in validation.canonical_source_rows] == list(contract.EXPECTED_SAMPLE_INDEX_ROW_IDS)


def test_r1_final_split_integer_one_point_zero_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.train_sample_index); rows[0]["protein_atom_count"] = "1.0"; _write_csv(paths.train_sample_index, fields, rows)
    _, validation = _validate(paths)
    assert "source_split_index_type_invalid:train:1:protein_atom_count" in validation.blocking_reasons


def test_r1_final_split_boolean_yes_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.train_sample_index); rows[0]["eligible_for_final_dataset_design"] = "yes"; _write_csv(paths.train_sample_index, fields, rows)
    _, validation = _validate(paths)
    assert "source_split_index_type_invalid:train:1:eligible_for_final_dataset_design" in validation.blocking_reasons


def test_r1_final_split_nan_bond_distance_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.train_sample_index); rows[0]["bond_distance_angstrom"] = "NaN"; _write_csv(paths.train_sample_index, fields, rows)
    _, validation = _validate(paths)
    assert "source_split_index_type_invalid:train:1:bond_distance_angstrom" in validation.blocking_reasons


def test_r1_final_safety_required_and_observed_tamper_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.safety_audit); rows[0]["required_status"] = "True"; rows[0]["observed_status"] = "True"; _write_csv(paths.safety_audit, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_safety_required_status_mismatch") for item in validation.blocking_reasons)


def test_r1_final_group_split_policy_tamper_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.group_split_assignment); rows[0]["split_policy"] = "tampered"; _write_csv(paths.group_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_group_policy_mismatch") for item in validation.blocking_reasons)


def test_r1_final_sample_leakage_boundary_false_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.sample_split_assignment); rows[0]["leakage_split_design_required_before_training"] = "False"; _write_csv(paths.sample_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_sample_training_boundary_mismatch") for item in validation.blocking_reasons)


def test_r1_final_sample_source_stage_invalid_blocks(tmp_path):
    paths = _bundle(tmp_path); fields, rows = _read_csv(paths.sample_split_assignment); rows[0]["source_index_stage"] = "invalid"; _write_csv(paths.sample_split_assignment, fields, rows)
    _, validation = _validate(paths)
    assert any(item.startswith("source_sample_source_stage_invalid") for item in validation.blocking_reasons)


def _r2_source():
    _, validation = _validate(contract.DEFAULT_STEP14AQ_INPUT_PATHS, provenance=False)
    assert validation.source_validation_passed
    return validation


def _r2_parts():
    source = _r2_source()
    index = contract.build_final_dataset_index_schema_passed_evidence(contract.build_candidate_final_dataset_index_rows(source), source)
    membership = contract.build_membership_checks_passed_evidence(contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source), index.validated_rows, source)
    inventory = contract.build_artifact_inventory_checks_passed_evidence(contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows), index.validated_rows, membership.validated_rows)
    summary = contract.build_split_summary_checks_passed_evidence(contract.build_candidate_split_summary_rows(index.validated_rows, membership.validated_rows, inventory.validated_rows), index.validated_rows, membership.validated_rows, inventory.validated_rows)
    return source, index, membership, inventory, summary


def test_r2_valid_final_index_has_11_rows():
    _, index, *_ = _r2_parts()
    assert index.passed and len(index.validated_rows) == 11


def test_r2_final_index_schema_is_exactly_33_fields():
    _, index, *_ = _r2_parts()
    assert all(list(row) == list(contract.SAMPLE_INDEX_FIELDS) for row in index.validated_rows)


def test_r2_final_index_canonical_order_is_preserved():
    _, index, *_ = _r2_parts()
    assert [row["sample_index_row_id"] for row in index.validated_rows] == list(contract.EXPECTED_SAMPLE_INDEX_ROW_IDS)


def test_r2_final_index_duplicate_sample_blocks():
    source = _r2_source(); rows = contract.build_candidate_final_dataset_index_rows(source); rows[1]["sample_index_row_id"] = rows[0]["sample_index_row_id"]
    assert any(item.startswith("final_index_duplicate_sample") for item in contract.build_final_dataset_index_schema_passed_evidence(rows, source).blocking_reasons)


def test_r2_final_index_source_value_tamper_blocks():
    source = _r2_source(); rows = contract.build_candidate_final_dataset_index_rows(source); rows[0]["pdb_id"] = "XXXX"
    assert any(item.startswith("final_index_source_value_mismatch") for item in contract.build_final_dataset_index_schema_passed_evidence(rows, source).blocking_reasons)


def test_r2_final_index_empty_artifact_field_blocks():
    source = _r2_source(); rows = contract.build_candidate_final_dataset_index_rows(source); rows[0]["protein_atom_table_path"] = ""
    assert any(item.startswith("final_index_artifact_reference_missing") for item in contract.build_final_dataset_index_schema_passed_evidence(rows, source).blocking_reasons)


def test_r2_final_index_extra_split_field_blocks():
    source = _r2_source(); rows = contract.build_candidate_final_dataset_index_rows(source); rows[0]["assigned_split"] = "train"
    assert any(item.startswith("final_index_schema_mismatch") for item in contract.build_final_dataset_index_schema_passed_evidence(rows, source).blocking_reasons)


def test_r2_valid_membership_is_11_of_11():
    _, _, membership, *_ = _r2_parts()
    assert membership.passed and sum(row["final_dataset_membership_passed"] for row in membership.validated_rows) == 11


def test_r2_membership_ids_and_order_are_exact():
    _, _, membership, *_ = _r2_parts()
    assert [row["final_dataset_membership_id"] for row in membership.validated_rows] == [f"COVAPIE_FINAL_DATASET_MEMBERSHIP_{index:06d}" for index in range(1, 12)]


def test_r2_membership_wrong_split_blocks():
    source, index, _, *_ = _r2_parts(); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source); rows[0]["assigned_split"] = "test"
    assert any(item.startswith("membership_split_mismatch") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_membership_wrong_split_rank_blocks():
    source, index, _, *_ = _r2_parts(); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source); rows[0]["assigned_split_rank"] = 2
    assert any(item.startswith("membership_split_rank_mismatch") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_membership_wrong_group_blocks():
    source, index, _, *_ = _r2_parts(); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source); rows[0]["final_leakage_group_id"] = "COVAPIE_LEAKAGE_GROUP_000005"
    assert any(item.startswith("membership_group_mismatch") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_membership_wrong_member_count_blocks():
    source, index, _, *_ = _r2_parts(); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source); rows[0]["final_leakage_group_member_count"] = 99
    assert any(item.startswith("membership_group_count_mismatch") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_membership_wrong_source_logical_name_blocks():
    source, index, _, *_ = _r2_parts(); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source); rows[0]["source_split_sample_index_logical_name"] = "wrong"
    assert any(item.startswith("membership_source_logical_name_mismatch") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_membership_duplicate_source_sample_blocks():
    source, index, _, *_ = _r2_parts(); source.typed_sample_rows.append(copy.deepcopy(source.typed_sample_rows[0])); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source)
    assert any(item.startswith("membership_source_sample_duplicate") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_membership_missing_group_source_blocks():
    source, index, _, *_ = _r2_parts(); source.typed_group_rows = source.typed_group_rows[1:]; rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source)
    assert any(item.startswith("membership_source_group_missing") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_membership_training_boundary_tamper_blocks():
    source, index, _, *_ = _r2_parts(); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source); rows[0]["ready_for_training_current_step"] = True
    assert any(item.startswith("membership_training_boundary_mismatch") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_membership_eligible_qa_is_derived_from_passed():
    _, _, membership, *_ = _r2_parts()
    assert all(row["eligible_for_final_dataset_qa_gate_current_step"] == row["final_dataset_membership_passed"] for row in membership.validated_rows)


def test_r2_valid_artifact_inventory_is_66_of_66():
    _, _, _, inventory, _ = _r2_parts()
    assert inventory.passed and len(inventory.validated_rows) == 66 and sum(row["artifact_inventory_passed"] for row in inventory.validated_rows) == 66


def test_r2_artifact_inventory_ids_and_order_are_exact():
    _, _, _, inventory, _ = _r2_parts()
    assert [row["artifact_inventory_id"] for row in inventory.validated_rows] == [f"COVAPIE_FINAL_ARTIFACT_{index:06d}" for index in range(1, 67)]


def test_r2_artifact_wrong_role_blocks():
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_role"] = "wrong"
    assert any(item.startswith("artifact_inventory_role_mismatch") for item in contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows).blocking_reasons)


def test_r2_artifact_wrong_source_field_blocks():
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["source_field_name"] = "wrong"
    assert any(item.startswith("artifact_inventory_role_mismatch") for item in contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows).blocking_reasons)


def test_r2_artifact_source_reference_mismatch_blocks():
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "data/derived/not-real.csv"
    assert any(item.startswith("artifact_inventory_reference_mismatch") for item in contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows).blocking_reasons)


def test_r2_artifact_absolute_path_blocks_without_read():
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "/tmp/nope"
    result = contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows)
    assert any(item.startswith("artifact_inventory_absolute_path") for item in result.blocking_reasons)
    assert "/tmp/nope" not in result.activity.read_paths


def test_r2_artifact_parent_traversal_blocks_without_read():
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "../nope"
    result = contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows)
    assert any(item.startswith("artifact_inventory_parent_traversal") for item in result.blocking_reasons)
    assert all(not path.endswith("/nope") for path in result.activity.read_paths)


def test_r2_artifact_raw_reference_blocks_without_raw_read():
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "data/raw/covalent_sources/nope"
    result = contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows)
    assert any(item.startswith("artifact_inventory_raw_reference") for item in result.blocking_reasons) and result.activity.raw_read_attempted is False


def test_r2_artifact_outside_repo_blocks_without_read(tmp_path):
    outside = tmp_path.parent / "outside.txt"; outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "data" / "derived" / "covalent_small" / "outside-link"; link.parent.mkdir(parents=True); link.symlink_to(outside)
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "data/derived/covalent_small/outside-link"
    result = contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows, repo_root=tmp_path)
    assert any(item.startswith("artifact_inventory_outside_repo") for item in result.blocking_reasons)
    assert str(outside) not in result.activity.read_paths


def test_r2_contract_updates_precondition_and_integrity_counts():
    output_specs = {name: row_count for name, _, _, row_count, _, _ in contract.OUTPUT_SPECS}
    assert output_specs["precondition_audit"] == 23
    assert output_specs["integrity_audit"] == 24


def test_r2_artifact_missing_file_blocks():
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "data/derived/covalent_small/nope.csv"
    assert any(item.startswith("artifact_inventory_missing_file") for item in contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows).blocking_reasons)


def test_r2_artifact_directory_path_blocks():
    source, index, membership, _, _ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "data/derived/covalent_small"
    assert any(item.startswith("artifact_inventory_not_regular_file") for item in contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows).blocking_reasons)


def test_r2_artifact_hash_and_size_are_real():
    _, _, _, inventory, _ = _r2_parts()
    assert all(row["artifact_size_bytes"] > 0 and len(row["artifact_sha256"]) == 64 for row in inventory.validated_rows)


def test_r2_artifact_activity_only_records_successful_reads():
    _, _, _, inventory, _ = _r2_parts()
    assert len(inventory.activity.read_paths) == 66 and inventory.activity.raw_read_attempted is False


def test_r2_valid_split_summary_is_4_of_4():
    _, _, _, _, summary = _r2_parts()
    assert summary.passed and len(summary.validated_rows) == 4 and all(row["split_summary_passed"] for row in summary.validated_rows)


def test_r2_split_summary_sample_count_tamper_blocks():
    _, index, membership, inventory, _ = _r2_parts(); rows = contract.build_candidate_split_summary_rows(index.validated_rows, membership.validated_rows, inventory.validated_rows); rows[0]["sample_count"] = 99
    assert any(item.startswith("split_summary_sample_count_mismatch") for item in contract.build_split_summary_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows, inventory.validated_rows).blocking_reasons)


def test_r2_split_summary_group_count_tamper_blocks():
    _, index, membership, inventory, _ = _r2_parts(); rows = contract.build_candidate_split_summary_rows(index.validated_rows, membership.validated_rows, inventory.validated_rows); rows[0]["leakage_group_count"] = 99
    assert any(item.startswith("split_summary_group_count_mismatch") for item in contract.build_split_summary_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows, inventory.validated_rows).blocking_reasons)


def test_r2_split_summary_artifact_count_tamper_blocks():
    _, index, membership, inventory, _ = _r2_parts(); rows = contract.build_candidate_split_summary_rows(index.validated_rows, membership.validated_rows, inventory.validated_rows); rows[0]["artifact_reference_count"] = 99
    assert any(item.startswith("split_summary_artifact_count_mismatch") for item in contract.build_split_summary_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows, inventory.validated_rows).blocking_reasons)


def test_r2_split_summary_statistical_claim_blocks():
    _, index, membership, inventory, _ = _r2_parts(); rows = contract.build_candidate_split_summary_rows(index.validated_rows, membership.validated_rows, inventory.validated_rows); rows[0]["statistical_representativeness_claimed"] = True
    assert any(item.startswith("split_summary_statistical_claim_mismatch") for item in contract.build_split_summary_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows, inventory.validated_rows).blocking_reasons)


def test_r2_valid_integrity_is_24_of_24():
    source, index, membership, inventory, summary = _r2_parts(); rows = contract.build_integrity_checks_passed_evidence(contract.build_integrity_observations(source, index, membership, inventory, summary)); validation = contract.validate_integrity_checks_passed(rows)
    assert validation["integrity_checks_passed"] and validation["integrity_row_count"] == 24 and validation["integrity_passed_count"] == 24


def test_r2_integrity_observed_count_tamper_blocks():
    source, index, membership, inventory, summary = _r2_parts(); observations = contract.build_integrity_observations(source, index, membership, inventory, summary); observations["membership_row_count"] = "10"; rows = contract.build_integrity_checks_passed_evidence(observations)
    assert not contract.validate_integrity_checks_passed(rows)["integrity_checks_passed"]


def test_r2_integrity_artifact_hash_observation_tamper_blocks():
    source, index, membership, inventory, summary = _r2_parts(); observations = contract.build_integrity_observations(source, index, membership, inventory, summary); observations["artifact_hashes_all_present"] = "false"; rows = contract.build_integrity_checks_passed_evidence(observations)
    assert not contract.validate_integrity_checks_passed(rows)["integrity_checks_passed"]


def test_r2_integrity_extra_item_blocks():
    source, index, membership, inventory, summary = _r2_parts(); rows = contract.build_integrity_checks_passed_evidence(contract.build_integrity_observations(source, index, membership, inventory, summary)); rows.append(copy.deepcopy(rows[0]))
    assert not contract.validate_integrity_checks_passed(rows)["integrity_checks_passed"]


def test_r2_valid_in_memory_materialization_passes():
    result = contract.build_in_memory_final_dataset_materialization(_r2_source())
    assert result.in_memory_materialization_passed


def test_r2_failed_source_does_not_read_artifacts(tmp_path):
    paths = _bundle(tmp_path); paths.manifest.unlink(); _, source = _validate(paths); result = contract.build_in_memory_final_dataset_materialization(source)
    assert not result.in_memory_materialization_passed and result.artifact_inventory_validation is None


def test_r2_materialization_does_not_create_or_modify_step14ar_outputs():
    root = Path("data/derived/covalent_small") / contract.STAGE
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir()} if root.exists() else None
    contract.build_in_memory_final_dataset_materialization(_r2_source())
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir()} if root.exists() else None
    assert after == before


def test_r2_disk_readiness_true_but_qa_and_training_false():
    result = contract.build_in_memory_final_dataset_materialization(_r2_source())
    assert result.ready_for_disk_materialization is True and result.ready_for_covapie_final_dataset_qa_gate is False and result.ready_for_training is False and result.ready_to_train_now is False


def test_r2_final_missing_source_group_makes_group_consistency_false():
    source, index, _, *_ = _r2_parts(); sample = source.typed_sample_rows[0]; source.typed_group_rows = [row for row in source.typed_group_rows if row["final_leakage_group_id"] != sample["final_leakage_group_id"]]
    result = contract.build_membership_checks_passed_evidence(contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source), index.validated_rows, source)
    row = next(row for row in result.validated_rows if row["sample_index_row_id"] == sample["sample_index_row_id"])
    assert row["source_group_split_assignment_row_found"] is False and row["group_membership_consistent"] is False


def test_r2_final_duplicate_source_group_makes_group_consistency_false():
    source, index, _, *_ = _r2_parts(); source.typed_group_rows.append(copy.deepcopy(source.typed_group_rows[0]))
    result = contract.build_membership_checks_passed_evidence(contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source), index.validated_rows, source)
    row = next(row for row in result.validated_rows if row["sample_index_row_id"] == source.typed_sample_rows[0]["sample_index_row_id"])
    assert row["source_group_split_assignment_row_found"] is False and row["group_membership_consistent"] is False


def test_r2_final_missing_final_index_makes_both_consistency_flags_false():
    source, index, _, *_ = _r2_parts(); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source)
    result = contract.build_membership_checks_passed_evidence(rows, index.validated_rows[1:], source)
    row = result.validated_rows[0]
    assert row["final_dataset_index_row_found"] is False and row["split_membership_consistent"] is False and row["group_membership_consistent"] is False


def test_r2_final_membership_candidate_extra_field_blocks():
    source, index, _, *_ = _r2_parts(); rows = contract.build_candidate_final_dataset_membership_rows(index.validated_rows, source); rows[0]["extra"] = True
    assert any(item.startswith("membership_schema_mismatch") for item in contract.build_membership_checks_passed_evidence(rows, index.validated_rows, source).blocking_reasons)


def test_r2_final_valid_membership_rows_match_frozen_schema():
    _, _, membership, *_ = _r2_parts()
    assert membership.schema_passed and all(list(row) == list(contract.FINAL_DATASET_MEMBERSHIP_FIELDS) for row in membership.validated_rows)


def test_r2_final_artifact_directory_has_exists_not_regular_and_no_read():
    _, index, membership, *_ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "data/derived/covalent_small"
    result = contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows)
    row = result.validated_rows[0]
    assert row["artifact_path_exists"] is True and row["artifact_is_regular_file"] is False and row["artifact_size_bytes"] == 0 and row["artifact_sha256"] == "" and str((contract.REPO / "data/derived/covalent_small").resolve()) not in result.activity.read_paths


def test_r2_final_artifact_missing_file_has_exists_and_regular_false():
    _, index, membership, *_ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["artifact_path"] = "data/derived/covalent_small/nope.csv"
    row = contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows).validated_rows[0]
    assert row["artifact_path_exists"] is False and row["artifact_is_regular_file"] is False


def test_r2_final_artifact_candidate_extra_field_blocks():
    _, index, membership, *_ = _r2_parts(); rows = contract.build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows); rows[0]["extra"] = True
    assert any(item.startswith("artifact_inventory_schema_mismatch") for item in contract.build_artifact_inventory_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows).blocking_reasons)


def test_r2_final_valid_artifact_rows_match_frozen_schema():
    _, _, _, inventory, _ = _r2_parts()
    assert inventory.schema_passed and all(list(row) == list(contract.FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS) for row in inventory.validated_rows)


def test_r2_final_split_summary_candidate_extra_field_blocks():
    _, index, membership, inventory, _ = _r2_parts(); rows = contract.build_candidate_split_summary_rows(index.validated_rows, membership.validated_rows, inventory.validated_rows); rows[0]["extra"] = True
    assert any(item.startswith("split_summary_schema_mismatch") for item in contract.build_split_summary_checks_passed_evidence(rows, index.validated_rows, membership.validated_rows, inventory.validated_rows).blocking_reasons)


def test_r2_final_valid_split_summary_rows_match_frozen_schema():
    _, _, _, _, summary = _r2_parts()
    assert summary.schema_passed and all(list(row) == list(contract.FINAL_DATASET_SPLIT_SUMMARY_FIELDS) for row in summary.validated_rows)


def test_r2_final_integrity_schema_count_uses_actual_index_rows():
    source, index, membership, inventory, summary = _r2_parts(); index.validated_rows[0]["extra"] = True
    assert contract.build_integrity_observations(source, index, membership, inventory, summary)["final_dataset_index_schema_field_count"] == "inconsistent"


def test_r2_final_integrity_roles_per_sample_uses_actual_inventory():
    source, index, membership, inventory, summary = _r2_parts(); inventory.validated_rows.pop()
    assert contract.build_integrity_observations(source, index, membership, inventory, summary)["artifact_roles_per_sample"] == "inconsistent"


def test_r2_final_integrity_statistical_claim_uses_summary_rows():
    source, index, membership, inventory, summary = _r2_parts(); summary.validated_rows[0]["statistical_representativeness_claimed"] = True
    assert contract.build_integrity_observations(source, index, membership, inventory, summary)["statistical_representativeness_claimed"] == "true"


def test_r2_final_integrity_policy_uses_source_manifest():
    source, index, membership, inventory, summary = _r2_parts(); source.manifest["production_split_policy_finalized"] = True
    assert contract.build_integrity_observations(source, index, membership, inventory, summary)["production_split_policy_finalized"] == "true"


def test_r2_final_integrity_joint_expected_observed_tamper_blocks():
    source, index, membership, inventory, summary = _r2_parts(); rows = contract.build_integrity_checks_passed_evidence(contract.build_integrity_observations(source, index, membership, inventory, summary)); rows[0]["expected_value"] = "bad"; rows[0]["observed_value"] = "bad"; rows[0]["integrity_check_passed"] = True
    assert any(item.startswith("final_integrity_expected_value_mismatch") for item in contract.validate_integrity_checks_passed(rows)["blocking_reasons"])


def test_r2_final_integrity_pass_flag_mismatch_blocks():
    source, index, membership, inventory, summary = _r2_parts(); rows = contract.build_integrity_checks_passed_evidence(contract.build_integrity_observations(source, index, membership, inventory, summary)); rows[0]["integrity_check_passed"] = False
    assert any(item.startswith("final_integrity_pass_flag_mismatch") for item in contract.validate_integrity_checks_passed(rows)["blocking_reasons"])


def test_r2_final_valid_integrity_rows_match_frozen_schema():
    source, index, membership, inventory, summary = _r2_parts(); rows = contract.build_integrity_checks_passed_evidence(contract.build_integrity_observations(source, index, membership, inventory, summary)); validation = contract.validate_integrity_checks_passed(rows)
    assert validation["integrity_schema_passed"] and all(list(row) == list(contract.FINAL_DATASET_INTEGRITY_AUDIT_FIELDS) for row in rows)


def test_r2_final_membership_schema_failure_blocks_disk_readiness(monkeypatch):
    original = contract.build_candidate_final_dataset_membership_rows
    def invalid_rows(index_rows, source_validation):
        rows = original(index_rows, source_validation); rows[0]["extra"] = True; return rows
    monkeypatch.setattr(contract, "build_candidate_final_dataset_membership_rows", invalid_rows)
    result = contract.build_in_memory_final_dataset_materialization(_r2_source())
    assert result.membership_validation is not None and result.membership_validation.schema_passed is False and result.ready_for_disk_materialization is False


def _single_artifact_validation(repo_root, artifact_path):
    index = {"sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000001", **{field: "" for field in contract.ARTIFACT_PATH_FIELDS}}
    index["protein_atom_table_path"] = artifact_path
    membership = {"sample_index_row_id": index["sample_index_row_id"], "assigned_split": "train", "final_leakage_group_id": "COVAPIE_LEAKAGE_GROUP_000001"}
    row = contract.build_candidate_artifact_inventory_rows([index], [membership])[0]
    return contract.build_artifact_inventory_checks_passed_evidence([row], [index], [membership], repo_root=repo_root)


def test_r2_security_repo_inside_but_not_derived_is_not_read(tmp_path):
    target = tmp_path / "docs" / "probe.txt"; target.parent.mkdir(); target.write_text("probe", encoding="utf-8")
    result = _single_artifact_validation(tmp_path, "docs/probe.txt"); row = result.validated_rows[0]
    assert any(item.startswith("artifact_inventory_not_derived") for item in result.blocking_reasons)
    assert row["artifact_path_exists"] is False and row["artifact_is_regular_file"] is False and row["artifact_sha256"] == "" and str(target.resolve()) not in result.activity.read_paths


def test_r2_security_derived_symlink_to_repo_non_derived_is_not_read(tmp_path):
    target = tmp_path / "docs" / "target.txt"; target.parent.mkdir(); target.write_text("target", encoding="utf-8")
    link = tmp_path / "data" / "derived" / "covalent_small" / "escape.csv"; link.parent.mkdir(parents=True); link.symlink_to(target)
    result = _single_artifact_validation(tmp_path, "data/derived/covalent_small/escape.csv"); row = result.validated_rows[0]
    assert any(item.startswith("artifact_inventory_not_derived") for item in result.blocking_reasons)
    assert row["artifact_path_exists"] is False and row["artifact_is_regular_file"] is False and row["artifact_sha256"] == "" and str(target.resolve()) not in result.activity.read_paths


def test_r2_security_allowed_derived_regular_file_is_read(tmp_path):
    target = tmp_path / "data" / "derived" / "covalent_small" / "probe.csv"; target.parent.mkdir(parents=True); target.write_text("header\nvalue\n", encoding="utf-8")
    result = _single_artifact_validation(tmp_path, "data/derived/covalent_small/probe.csv"); row = result.validated_rows[0]
    assert row["artifact_path_exists"] is True and row["artifact_is_regular_file"] is True and row["artifact_size_bytes"] > 0 and len(row["artifact_sha256"]) == 64 and str(target.resolve()) in result.activity.read_paths


def test_r2_security_complete_inventory_remains_authorized_and_ready():
    _, _, _, inventory, _ = _r2_parts(); materialization = contract.build_in_memory_final_dataset_materialization(_r2_source())
    assert inventory.passed and len(inventory.activity.read_paths) == 66 and inventory.all_paths_inside_allowed_derived_root is True and inventory.activity.raw_read_attempted is False and materialization.in_memory_materialization_passed and materialization.ready_for_disk_materialization


def _r3_paths(tmp_path):
    return contract.Step14AROutputPaths(**{name: tmp_path / contract.FINAL_ROOT / filename for name, filename, *_ in contract.OUTPUT_SPECS})


def _r3_result(tmp_path):
    source = _r2_source(); memory = contract.build_in_memory_final_dataset_materialization(source); paths = _r3_paths(tmp_path)
    return source, memory, paths, contract.materialize_final_dataset_core_to_disk(source, memory, output_paths=paths, repo_root=tmp_path)


def test_r3a_output_path_contract_passes(tmp_path):
    assert contract.validate_step14ar_output_paths(_r3_paths(tmp_path), repo_root=tmp_path)["output_path_contract_passed"]


def test_r3a_normal_materialization_writes_only_four_files(tmp_path):
    _, _, paths, result = _r3_result(tmp_path)
    assert result.core_disk_materialization_passed and {path.name for path in (tmp_path / contract.FINAL_ROOT).iterdir()} == {paths.precondition_audit.name, paths.final_dataset_index_csv.name, paths.final_dataset_index_json.name, paths.membership.name}


def test_r3a_preconditions_are_23_of_23(tmp_path):
    _, _, _, result = _r3_result(tmp_path)
    assert len(result.precondition_rows) == 23 and result.precondition_write_validation["source_precondition_passed_count"] == 23


def test_r3a_final_index_csv_is_11_by_33(tmp_path):
    _, _, _, result = _r3_result(tmp_path)
    assert result.final_index_csv_write_validation["row_count"] == 11 and result.final_index_csv_write_validation["schema_field_count"] == 33


def test_r3a_final_index_json_is_11_by_33(tmp_path):
    _, _, _, result = _r3_result(tmp_path)
    assert result.final_index_json_write_validation["row_count"] == 11 and result.final_index_json_write_validation["schema_field_count"] == 33


def test_r3a_cross_format_typed_rows_are_identical(tmp_path):
    _, _, _, result = _r3_result(tmp_path)
    assert result.final_index_cross_format_validation["final_index_csv_json_consistent"] is True


def test_r3a_membership_is_11_of_11(tmp_path):
    _, _, _, result = _r3_result(tmp_path)
    assert result.membership_write_validation["membership_row_count"] == 11 and result.membership_write_validation["membership_passed_count"] == 11


def test_r3a_activity_records_exactly_four_writes_and_reads(tmp_path):
    _, _, _, result = _r3_result(tmp_path)
    assert len(result.activity.written_paths) == 4 and len(result.activity.read_paths) == 4


def test_r3a_leaves_no_temporary_paths(tmp_path):
    _, _, _, result = _r3_result(tmp_path)
    assert not result.activity.temporary_paths and not list((tmp_path / contract.FINAL_ROOT).glob("*.tmp"))


def test_r3a_disk_readiness_true_and_qa_training_false(tmp_path):
    _, _, _, result = _r3_result(tmp_path)
    assert result.ready_for_remaining_disk_materialization and result.ready_for_covapie_final_dataset_qa_gate is False and result.ready_for_training is False and result.ready_to_train_now is False


def test_r3a_csv_deleted_row_is_detected(tmp_path):
    _, memory, paths, result = _r3_result(tmp_path); fields, rows = _read_csv(paths.final_dataset_index_csv); _write_csv(paths.final_dataset_index_csv, fields, rows[:-1])
    assert not contract.validate_written_final_dataset_index_csv(memory.final_index_validation.validated_rows, paths.final_dataset_index_csv, contract.DiskWriteActivity())["final_index_csv_write_validation_passed"]


def test_r3a_csv_wrong_header_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); paths.final_dataset_index_csv.write_text("wrong\nvalue\n", encoding="utf-8")
    assert "final_index_csv_schema_mismatch" in contract.validate_written_final_dataset_index_csv(memory.final_index_validation.validated_rows, paths.final_dataset_index_csv, contract.DiskWriteActivity())["blocking_reasons"]


def test_r3a_csv_field_tamper_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); fields, rows = _read_csv(paths.final_dataset_index_csv); rows[0]["pdb_id"] = "XXXX"; _write_csv(paths.final_dataset_index_csv, fields, rows)
    assert any(item.startswith("final_index_csv_content_mismatch") for item in contract.validate_written_final_dataset_index_csv(memory.final_index_validation.validated_rows, paths.final_dataset_index_csv, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3a_csv_boolean_yes_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); fields, rows = _read_csv(paths.final_dataset_index_csv); rows[0]["eligible_for_final_dataset_design"] = "yes"; _write_csv(paths.final_dataset_index_csv, fields, rows)
    assert any(item.startswith("final_index_csv_type_invalid") for item in contract.validate_written_final_dataset_index_csv(memory.final_index_validation.validated_rows, paths.final_dataset_index_csv, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3a_json_root_dict_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); paths.final_dataset_index_json.write_text("{}\n", encoding="utf-8")
    assert "final_index_json_root_invalid" in contract.validate_written_final_dataset_index_json(memory.final_index_validation.validated_rows, paths.final_dataset_index_json, contract.DiskWriteActivity())["blocking_reasons"]


def test_r3a_json_deleted_row_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); rows = json.loads(paths.final_dataset_index_json.read_text()); rows.pop(); paths.final_dataset_index_json.write_text(json.dumps(rows), encoding="utf-8")
    assert "final_index_json_row_count_mismatch" in contract.validate_written_final_dataset_index_json(memory.final_index_validation.validated_rows, paths.final_dataset_index_json, contract.DiskWriteActivity())["blocking_reasons"]


def test_r3a_json_extra_key_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); rows = json.loads(paths.final_dataset_index_json.read_text()); rows[0]["extra"] = True; paths.final_dataset_index_json.write_text(json.dumps(rows), encoding="utf-8")
    assert any(item.startswith("final_index_json_schema_mismatch") for item in contract.validate_written_final_dataset_index_json(memory.final_index_validation.validated_rows, paths.final_dataset_index_json, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3a_json_value_tamper_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); rows = json.loads(paths.final_dataset_index_json.read_text()); rows[0]["pdb_id"] = "XXXX"; paths.final_dataset_index_json.write_text(json.dumps(rows), encoding="utf-8")
    assert any(item.startswith("final_index_json_content_mismatch") for item in contract.validate_written_final_dataset_index_json(memory.final_index_validation.validated_rows, paths.final_dataset_index_json, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3a_cross_format_mismatch_is_detected(tmp_path):
    _, _, _, result = _r3_result(tmp_path); altered = dict(result.final_index_json_write_validation); altered["typed_rows"] = []
    assert contract.validate_final_dataset_index_cross_format(result.final_index_csv_write_validation, altered)["final_index_csv_json_consistent"] is False


def test_r3a_membership_deleted_row_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); fields, rows = _read_csv(paths.membership); _write_csv(paths.membership, fields, rows[:-1])
    assert not contract.validate_written_membership_checks_passed(memory.membership_validation.validated_rows, paths.membership, contract.DiskWriteActivity())["membership_write_validation_passed"]


def test_r3a_membership_id_tamper_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); fields, rows = _read_csv(paths.membership); rows[0]["final_dataset_membership_id"] = "wrong"; _write_csv(paths.membership, fields, rows)
    assert "membership_csv_order_mismatch" in contract.validate_written_membership_checks_passed(memory.membership_validation.validated_rows, paths.membership, contract.DiskWriteActivity())["blocking_reasons"]


def test_r3a_membership_pass_flag_tamper_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); fields, rows = _read_csv(paths.membership); rows[0]["final_dataset_membership_passed"] = "False"; _write_csv(paths.membership, fields, rows)
    assert any(item.startswith("membership_csv_pass_mismatch") for item in contract.validate_written_membership_checks_passed(memory.membership_validation.validated_rows, paths.membership, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3a_membership_training_boundary_tamper_is_detected(tmp_path):
    _, memory, paths, _ = _r3_result(tmp_path); fields, rows = _read_csv(paths.membership); rows[0]["ready_for_training_current_step"] = "True"; _write_csv(paths.membership, fields, rows)
    assert any(item.startswith("membership_csv_training_boundary_mismatch") for item in contract.validate_written_membership_checks_passed(memory.membership_validation.validated_rows, paths.membership, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3a_precondition_observed_pass_joint_tamper_is_detected(tmp_path):
    source, _, paths, result = _r3_result(tmp_path); fields, rows = _read_csv(paths.precondition_audit); rows[0]["observed_status"] = "False"; rows[0]["precondition_passed"] = "False"; rows[0]["blocking_reasons"] = "source_check_failed:" + rows[0]["precondition_item"]; _write_csv(paths.precondition_audit, fields, rows)
    assert not contract.validate_written_source_step14aq_preconditions_passed(result.precondition_rows, paths.precondition_audit, contract.DiskWriteActivity())["source_precondition_write_validation_passed"]


def test_r3a_output_path_outside_final_root_blocks_without_directory(tmp_path):
    paths = _r3_paths(tmp_path); bad = contract.Step14AROutputPaths(**{name: (tmp_path / "other" / "bad.csv" if name == "membership" else getattr(paths, name)) for name in paths.__dataclass_fields__})
    source = _r2_source(); memory = contract.build_in_memory_final_dataset_materialization(source); result = contract.materialize_final_dataset_core_to_disk(source, memory, output_paths=bad, repo_root=tmp_path)
    assert not result.passed and not (tmp_path / contract.FINAL_ROOT).exists()


def test_r3a_output_root_symlink_escape_blocks_without_write(tmp_path):
    target = tmp_path / "escape"; target.mkdir(); root = tmp_path / "data" / "derived" / "covalent_small"; root.mkdir(parents=True); (root / contract.STAGE).symlink_to(target, target_is_directory=True)
    source = _r2_source(); memory = contract.build_in_memory_final_dataset_materialization(source); result = contract.materialize_final_dataset_core_to_disk(source, memory, output_paths=_r3_paths(tmp_path), repo_root=tmp_path)
    assert any(item.startswith("output_path_symlink_escape") for item in result.blocking_reasons) and not list(target.iterdir())


def test_r3a_source_failure_writes_four_blocked_outputs(tmp_path):
    source, memory, paths, _ = _r3_result(tmp_path); source.passed = False; source.blocking_reasons = ["failed"]
    result = contract.materialize_final_dataset_core_to_disk(source, memory, output_paths=paths, repo_root=tmp_path); header, rows = _read_csv(paths.precondition_audit)
    assert not result.passed and len(result.activity.written_paths) == 4 and header == list(contract.FINAL_DATASET_PRECONDITION_FIELDS) and rows == [] and json.loads(paths.final_dataset_index_json.read_text()) == []


def test_r3a_in_memory_failure_writes_four_blocked_outputs_without_tmp(tmp_path):
    source, memory, paths, _ = _r3_result(tmp_path); memory.passed = False; memory.blocking_reasons = ["failed"]
    result = contract.materialize_final_dataset_core_to_disk(source, memory, output_paths=paths, repo_root=tmp_path)
    assert not result.passed and len(result.activity.written_paths) == 4 and not result.activity.temporary_paths and not list((tmp_path / contract.FINAL_ROOT).glob("*.tmp"))


def test_r3a_second_run_is_deterministic(tmp_path):
    _, _, paths, first = _r3_result(tmp_path); before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (paths.precondition_audit, paths.final_dataset_index_csv, paths.final_dataset_index_json, paths.membership)}
    source = _r2_source(); memory = contract.build_in_memory_final_dataset_materialization(source); second = contract.materialize_final_dataset_core_to_disk(source, memory, output_paths=paths, repo_root=tmp_path); after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (paths.precondition_audit, paths.final_dataset_index_csv, paths.final_dataset_index_json, paths.membership)}
    assert first.passed and second.passed and before == after


def _r3b_result(tmp_path):
    source, memory, paths, core = _r3_result(tmp_path)
    return source, memory, paths, core, contract.materialize_reference_audits_to_disk(source, memory, core, output_paths=paths, repo_root=tmp_path)


def _core_hashes(paths):
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (paths.precondition_audit, paths.final_dataset_index_csv, paths.final_dataset_index_json, paths.membership)}


def test_r3b1_writes_only_three_new_outputs(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path)
    assert result.passed and {path.name for path in (tmp_path / contract.FINAL_ROOT).iterdir()} == {getattr(paths, name).name for name in (*contract.CORE_OUTPUT_LOGICAL_NAMES, *contract.R3B1_OUTPUT_LOGICAL_NAMES)}


def test_r3b1_keeps_core_hashes_unchanged(tmp_path):
    source, memory, paths, core = _r3_result(tmp_path); before = _core_hashes(paths); contract.materialize_reference_audits_to_disk(source, memory, core, output_paths=paths, repo_root=tmp_path)
    assert _core_hashes(paths) == before


def test_r3b1_artifact_inventory_is_66_of_66(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert result.artifact_inventory_write_validation["artifact_inventory_row_count"] == 66 and result.artifact_inventory_write_validation["artifact_inventory_passed_count"] == 66


def test_r3b1_artifact_inventory_schema_is_exact(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert all(list(row) == list(contract.FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS) for row in result.artifact_inventory_write_validation["typed_rows"])


def test_r3b1_artifact_inventory_ids_and_order_are_exact(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert [row["artifact_inventory_id"] for row in result.artifact_inventory_write_validation["typed_rows"]] == [f"COVAPIE_FINAL_ARTIFACT_{n:06d}" for n in range(1, 67)]


def test_r3b1_schema_audit_is_33_of_33(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert result.schema_audit_write_validation["schema_audit_row_count"] == 33 and result.schema_audit_write_validation["schema_audit_passed_count"] == 33


def test_r3b1_type_mapping_covers_all_33_fields_in_order():
    assert tuple(contract.SAMPLE_INDEX_EXPECTED_TYPE_BY_FIELD) == tuple(contract.SAMPLE_INDEX_FIELDS) and len(contract.SAMPLE_INDEX_EXPECTED_TYPE_BY_FIELD) == 33


def test_r3b1_schema_audit_field_order_is_exact(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert [row["sample_index_field"] for row in result.schema_audit_write_validation["typed_rows"]] == list(contract.SAMPLE_INDEX_FIELDS)


def test_r3b1_source_preservation_is_11_of_11(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert result.source_preservation_write_validation["source_preservation_row_count"] == 11 and result.source_preservation_write_validation["source_preservation_passed_count"] == 11


def test_r3b1_source_preservation_order_is_canonical(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert [row["sample_index_row_id"] for row in result.source_preservation_write_validation["typed_rows"]] == list(contract.EXPECTED_SAMPLE_INDEX_ROW_IDS)


def test_r3b1_activity_is_three_writes_three_reads_no_temp(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert len(result.activity.written_paths) == 3 and len(result.activity.read_paths) == 3 and not result.activity.temporary_paths


def test_r3b1_readiness_true_and_qa_training_false(tmp_path):
    _, _, _, _, result = _r3b_result(tmp_path)
    assert result.ready_for_summary_and_integrity_disk_materialization and result.ready_for_covapie_final_dataset_qa_gate is False and result.ready_for_training is False and result.ready_to_train_now is False


def test_r3b1_inventory_deleted_row_is_detected(tmp_path):
    _, memory, paths, _, _ = _r3b_result(tmp_path); fields, rows = _read_csv(paths.artifact_inventory); _write_csv(paths.artifact_inventory, fields, rows[:-1])
    assert not contract.validate_written_artifact_inventory_checks_passed(memory.artifact_inventory_validation.validated_rows, paths.artifact_inventory, contract.DiskWriteActivity())["artifact_inventory_write_validation_passed"]


def test_r3b1_inventory_wrong_header_is_detected(tmp_path):
    _, memory, paths, _, _ = _r3b_result(tmp_path); paths.artifact_inventory.write_text("wrong\nvalue\n", encoding="utf-8")
    assert "artifact_inventory_csv_schema_mismatch" in contract.validate_written_artifact_inventory_checks_passed(memory.artifact_inventory_validation.validated_rows, paths.artifact_inventory, contract.DiskWriteActivity())["blocking_reasons"]


def test_r3b1_inventory_hash_tamper_is_detected(tmp_path):
    _, memory, paths, _, _ = _r3b_result(tmp_path); fields, rows = _read_csv(paths.artifact_inventory); rows[0]["artifact_sha256"] = "bad"; _write_csv(paths.artifact_inventory, fields, rows)
    assert any(item.startswith("artifact_inventory_csv_hash_invalid") for item in contract.validate_written_artifact_inventory_checks_passed(memory.artifact_inventory_validation.validated_rows, paths.artifact_inventory, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3b1_inventory_size_tamper_is_detected(tmp_path):
    _, memory, paths, _, _ = _r3b_result(tmp_path); fields, rows = _read_csv(paths.artifact_inventory); rows[0]["artifact_size_bytes"] = "0"; _write_csv(paths.artifact_inventory, fields, rows)
    assert any(item.startswith("artifact_inventory_csv_path_contract_mismatch") for item in contract.validate_written_artifact_inventory_checks_passed(memory.artifact_inventory_validation.validated_rows, paths.artifact_inventory, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3b1_inventory_pass_tamper_is_detected(tmp_path):
    _, memory, paths, _, _ = _r3b_result(tmp_path); fields, rows = _read_csv(paths.artifact_inventory); rows[0]["artifact_inventory_passed"] = "False"; _write_csv(paths.artifact_inventory, fields, rows)
    assert any(item.startswith("artifact_inventory_csv_pass_mismatch") for item in contract.validate_written_artifact_inventory_checks_passed(memory.artifact_inventory_validation.validated_rows, paths.artifact_inventory, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3b1_inventory_duplicate_sample_field_is_detected(tmp_path):
    _, memory, paths, _, _ = _r3b_result(tmp_path); fields, rows = _read_csv(paths.artifact_inventory); rows[1]["source_field_name"] = rows[0]["source_field_name"]; _write_csv(paths.artifact_inventory, fields, rows)
    assert any(item.startswith("artifact_inventory_csv_duplicate_sample_field") for item in contract.validate_written_artifact_inventory_checks_passed(memory.artifact_inventory_validation.validated_rows, paths.artifact_inventory, contract.DiskWriteActivity())["blocking_reasons"])


def test_r3b1_schema_audit_deleted_row_is_detected(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path); fields, rows = _read_csv(paths.schema_validation_audit); _write_csv(paths.schema_validation_audit, fields, rows[:-1])
    assert not contract.validate_written_final_dataset_index_schema_passed(result.schema_audit_rows, paths.schema_validation_audit, contract.DiskWriteActivity())["schema_audit_write_validation_passed"]


def test_r3b1_schema_expected_type_tamper_is_detected(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path); fields, rows = _read_csv(paths.schema_validation_audit); rows[0]["expected_data_type"] = "bad"; _write_csv(paths.schema_validation_audit, fields, rows)
    assert not contract.validate_written_final_dataset_index_schema_passed(result.schema_audit_rows, paths.schema_validation_audit, contract.DiskWriteActivity())["schema_audit_write_validation_passed"]


def test_r3b1_schema_field_order_tamper_is_detected(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path); fields, rows = _read_csv(paths.schema_validation_audit); rows[1]["sample_index_field"] = rows[0]["sample_index_field"]; _write_csv(paths.schema_validation_audit, fields, rows)
    assert "schema_audit_csv_order_mismatch" in contract.validate_written_final_dataset_index_schema_passed(result.schema_audit_rows, paths.schema_validation_audit, contract.DiskWriteActivity())["blocking_reasons"]


def test_r3b1_schema_observed_pass_tamper_is_detected(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path); fields, rows = _read_csv(paths.schema_validation_audit); rows[0]["csv_column_present"] = "False"; rows[0]["schema_validation_passed"] = "False"; _write_csv(paths.schema_validation_audit, fields, rows)
    assert not contract.validate_written_final_dataset_index_schema_passed(result.schema_audit_rows, paths.schema_validation_audit, contract.DiskWriteActivity())["schema_audit_write_validation_passed"]


def test_r3b1_source_preservation_deleted_row_is_detected(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path); fields, rows = _read_csv(paths.source_preservation_audit); _write_csv(paths.source_preservation_audit, fields, rows[:-1])
    assert not contract.validate_written_source_preservation_checks_passed(result.source_preservation_rows, paths.source_preservation_audit, contract.DiskWriteActivity())["source_preservation_write_validation_passed"]


def test_r3b1_source_preservation_split_tamper_is_detected(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path); fields, rows = _read_csv(paths.source_preservation_audit); rows[0]["assigned_split"] = "test"; _write_csv(paths.source_preservation_audit, fields, rows)
    assert not contract.validate_written_source_preservation_checks_passed(result.source_preservation_rows, paths.source_preservation_audit, contract.DiskWriteActivity())["source_preservation_write_validation_passed"]


def test_r3b1_source_preservation_field_flag_tamper_is_detected(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path); fields, rows = _read_csv(paths.source_preservation_audit); rows[0]["all_33_fields_preserved"] = "False"; _write_csv(paths.source_preservation_audit, fields, rows)
    assert not contract.validate_written_source_preservation_checks_passed(result.source_preservation_rows, paths.source_preservation_audit, contract.DiskWriteActivity())["source_preservation_write_validation_passed"]


def test_r3b1_source_preservation_artifact_flag_tamper_is_detected(tmp_path):
    _, _, paths, _, result = _r3b_result(tmp_path); fields, rows = _read_csv(paths.source_preservation_audit); rows[0]["six_artifact_references_preserved"] = "False"; _write_csv(paths.source_preservation_audit, fields, rows)
    assert not contract.validate_written_source_preservation_checks_passed(result.source_preservation_rows, paths.source_preservation_audit, contract.DiskWriteActivity())["source_preservation_write_validation_passed"]


def test_r3b1_core_failure_writes_three_blocked_outputs(tmp_path):
    source, memory, paths, core = _r3_result(tmp_path); core.passed = False; result = contract.materialize_reference_audits_to_disk(source, memory, core, output_paths=paths, repo_root=tmp_path)
    assert not result.passed and len(result.activity.written_paths) == 3 and _read_csv(paths.artifact_inventory)[1] == []


def test_r3b1_path_failure_writes_no_new_outputs(tmp_path):
    source, memory, paths, core = _r3_result(tmp_path); bad = contract.Step14AROutputPaths(**{name: (tmp_path / "outside" / "x.csv" if name == "artifact_inventory" else getattr(paths, name)) for name in paths.__dataclass_fields__}); result = contract.materialize_reference_audits_to_disk(source, memory, core, output_paths=bad, repo_root=tmp_path)
    assert not result.passed and not (tmp_path / "outside").exists()


def test_r3b1_second_run_is_deterministic_for_all_seven_outputs(tmp_path):
    source, memory, paths, core, first = _r3b_result(tmp_path); before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (tmp_path / contract.FINAL_ROOT).iterdir()}; second = contract.materialize_reference_audits_to_disk(source, memory, core, output_paths=paths, repo_root=tmp_path); after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (tmp_path / contract.FINAL_ROOT).iterdir()}
    assert first.passed and second.passed and before == after


def test_r3b1_check_script_uses_distinct_source_and_final_precondition_keys():
    text = (Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py")).read_text(encoding="utf-8")
    assert '"source_precondition_rows"' in text and '"final_precondition_rows"' in text and '"precondition_rows"' not in text


def _preservation_result(source, memory, core, reference):
    candidates = contract.build_candidate_source_preservation_rows(source, memory, core, reference.artifact_inventory_write_validation)
    return contract.build_source_preservation_checks_passed_evidence(candidates, source, memory, core, reference.artifact_inventory_write_validation)


def test_r3b1_closure_normal_preservation_evidence_is_all_true(tmp_path):
    source, memory, _, core, reference = _r3b_result(tmp_path); result = _preservation_result(source, memory, core, reference)
    bools = contract.SOURCE_PRESERVATION_BOOL_FIELDS
    assert result.passed and all(row[field] is True for row in result.validated_rows for field in bools)


def test_r3b1_closure_missing_membership_does_not_break_field_evidence(tmp_path):
    source, memory, _, core, reference = _r3b_result(tmp_path); core = copy.deepcopy(core); core.membership_write_validation["typed_rows"].pop(0); result = _preservation_result(source, memory, core, reference); row = result.validated_rows[0]
    assert row["all_33_fields_preserved"] is True and row["split_membership_preserved"] is False and row["group_membership_preserved"] is False and row["source_preservation_passed"] is False


def test_r3b1_closure_csv_field_tamper_only_breaks_field_evidence(tmp_path):
    source, memory, _, core, reference = _r3b_result(tmp_path); core = copy.deepcopy(core); core.final_index_csv_write_validation["typed_rows"][0]["pdb_id"] = "XXXX"; result = _preservation_result(source, memory, core, reference); row = result.validated_rows[0]
    assert row["all_33_fields_preserved"] is False and row["split_membership_preserved"] is True and row["group_membership_preserved"] is True


def test_r3b1_closure_reference_flag_failure_keeps_path_evidence_true(tmp_path):
    source, memory, _, core, reference = _r3b_result(tmp_path); reference = copy.deepcopy(reference); reference.artifact_inventory_write_validation["typed_rows"][0]["artifact_reference_preserved"] = False; reference.artifact_inventory_write_validation["typed_rows"][0]["artifact_inventory_passed"] = False; result = _preservation_result(source, memory, core, reference); row = result.validated_rows[0]
    assert row["six_artifact_references_preserved"] is False and row["artifact_paths_exist"] is True and row["source_preservation_passed"] is False


def test_r3b1_closure_hash_failure_keeps_reference_evidence_true(tmp_path):
    source, memory, _, core, reference = _r3b_result(tmp_path); reference = copy.deepcopy(reference); reference.artifact_inventory_write_validation["typed_rows"][0]["artifact_sha256"] = ""; result = _preservation_result(source, memory, core, reference); row = result.validated_rows[0]
    assert row["six_artifact_references_preserved"] is True and row["artifact_paths_exist"] is False and row["source_preservation_passed"] is False


def test_r3b1_closure_missing_artifact_row_breaks_both_artifact_evidence(tmp_path):
    source, memory, _, core, reference = _r3b_result(tmp_path); reference = copy.deepcopy(reference); reference.artifact_inventory_write_validation["typed_rows"].pop(0); result = _preservation_result(source, memory, core, reference); row = result.validated_rows[0]
    assert row["six_artifact_references_preserved"] is False and row["artifact_paths_exist"] is False and any(item.startswith("source_preservation_artifact_count_mismatch") for item in result.blocking_reasons)


def test_r3b1_closure_assignment_split_mismatch_breaks_only_split_evidence(tmp_path):
    source, memory, _, core, reference = _r3b_result(tmp_path); source = copy.deepcopy(source); source.typed_sample_rows[0]["assigned_split"] = "test"; result = _preservation_result(source, memory, core, reference)
    assert result.validated_rows[0]["split_membership_preserved"] is False


def test_r3b1_closure_check_values_has_no_duplicate_literal_keys():
    tree = ast.parse(Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py").read_text(encoding="utf-8")); dictionaries = [node for node in ast.walk(tree) if isinstance(node, ast.Dict)]
    values = max(dictionaries, key=lambda node: sum(isinstance(key, ast.Constant) and isinstance(key.value, str) for key in node.keys if key is not None)); keys = [key.value for key in values.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)]
    assert len(keys) == len(set(keys))


def test_r3b1_closure_check_reports_distinct_inventory_sources(tmp_path):
    source, memory, _, core, reference = _r3b_result(tmp_path)
    assert len(memory.artifact_inventory_validation.validated_rows) == 66 and reference.artifact_inventory_write_validation["artifact_inventory_row_count"] == 66 and reference.artifact_inventory_write_validation["artifact_inventory_passed_count"] == 66


def test_r3b1_closure_disk_preservation_output_stays_11_of_11(tmp_path):
    _, _, _, _, reference = _r3b_result(tmp_path)
    assert reference.source_preservation_write_validation["source_preservation_row_count"] == 11 and reference.source_preservation_write_validation["source_preservation_passed_count"] == 11


def _r3b2_result(tmp_path):
    source, memory, paths, core, reference = _r3b_result(tmp_path)
    return source, memory, paths, core, reference, contract.materialize_summary_and_integrity_to_disk(source, memory, core, reference, output_paths=paths, repo_root=tmp_path)


def test_r3b2_01_only_two_outputs_added(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert r.passed and len(r.activity.written_paths) == 2
def test_r3b2_02_preflight_reads_seven(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert r.preflight_existing_outputs["preflight_existing_outputs_passed"] and r.preflight_existing_outputs["preflight_output_count"] == 7
def test_r3b2_03_summary_four_rows(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert len(r.split_summary_rows) == 4
def test_r3b2_04_summary_ids_order(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert [x["split_summary_id"] for x in r.split_summary_rows] == [f"COVAPIE_FINAL_SPLIT_SUMMARY_{n:06d}" for n in range(1,5)]
def test_r3b2_05_summary_sample_counts(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert [x["sample_count"] for x in r.split_summary_rows] == [8,2,1,11]
def test_r3b2_06_summary_group_counts(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert [x["leakage_group_count"] for x in r.split_summary_rows] == [2,2,1,5]
def test_r3b2_07_summary_artifact_counts(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert [x["artifact_reference_count"] for x in r.split_summary_rows] == [48,12,6,66]
def test_r3b2_08_summary_schema_counts(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert {x["canonical_schema_field_count"] for x in r.split_summary_rows} == {33}
def test_r3b2_09_summary_matches_memory(tmp_path):
    _, memory, _, _, _, r = _r3b2_result(tmp_path); assert r.split_summary_rows == memory.split_summary_validation.validated_rows
def test_r3b2_10_integrity_24_of_24(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert len(r.integrity_rows) == 24 and r.integrity_write_validation["integrity_passed_count"] == 24
def test_r3b2_11_integrity_matches_memory(tmp_path):
    _, memory, _, _, _, r = _r3b2_result(tmp_path); assert r.integrity_rows == memory.integrity_rows
def test_r3b2_12_activity_counts(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert len(r.activity.written_paths) == len(r.activity.read_paths) == 2 and not r.activity.temporary_paths
def test_r3b2_13_readiness(tmp_path):
    *_, r = _r3b2_result(tmp_path); assert r.ready_for_issue_safety_manifest_materialization and not r.ready_for_training
def test_r3b2_14_summary_delete_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.split_summary); _write_csv(p.split_summary,f,rows[:-1]); assert not contract.validate_written_split_summary_checks_passed(r.split_summary_rows,p.split_summary,contract.DiskWriteActivity())["split_summary_write_validation_passed"]
def test_r3b2_15_summary_header_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); p.split_summary.write_text("bad\n",encoding="utf-8"); assert "split_summary_csv_schema_mismatch" in contract.validate_written_split_summary_checks_passed(r.split_summary_rows,p.split_summary,contract.DiskWriteActivity())["blocking_reasons"]
def test_r3b2_16_summary_count_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.split_summary); rows[0]["sample_count"]="9"; _write_csv(p.split_summary,f,rows); assert not contract.validate_written_split_summary_checks_passed(r.split_summary_rows,p.split_summary,contract.DiskWriteActivity())["split_summary_write_validation_passed"]
def test_r3b2_17_summary_group_flag_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.split_summary); rows[0]["group_integrity_preserved"]="False"; _write_csv(p.split_summary,f,rows); assert not contract.validate_written_split_summary_checks_passed(r.split_summary_rows,p.split_summary,contract.DiskWriteActivity())["split_summary_write_validation_passed"]
def test_r3b2_18_summary_claim_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.split_summary); rows[0]["statistical_representativeness_claimed"]="True"; _write_csv(p.split_summary,f,rows); assert not contract.validate_written_split_summary_checks_passed(r.split_summary_rows,p.split_summary,contract.DiskWriteActivity())["split_summary_write_validation_passed"]
def test_r3b2_19_integrity_delete_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.integrity_audit); _write_csv(p.integrity_audit,f,rows[:-1]); assert not contract.validate_written_integrity_checks_passed(r.integrity_rows,p.integrity_audit,contract.DiskWriteActivity())["integrity_write_validation_passed"]
def test_r3b2_20_integrity_duplicate_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.integrity_audit); rows[1]["integrity_audit_item"]=rows[0]["integrity_audit_item"]; _write_csv(p.integrity_audit,f,rows); assert not contract.validate_written_integrity_checks_passed(r.integrity_rows,p.integrity_audit,contract.DiskWriteActivity())["integrity_write_validation_passed"]
def test_r3b2_21_integrity_joint_tamper_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.integrity_audit); rows[0]["expected_value"]=rows[0]["observed_value"]="bad"; _write_csv(p.integrity_audit,f,rows); assert not contract.validate_written_integrity_checks_passed(r.integrity_rows,p.integrity_audit,contract.DiskWriteActivity())["integrity_write_validation_passed"]
def test_r3b2_22_integrity_pass_tamper_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.integrity_audit); rows[0]["integrity_check_passed"]="False"; _write_csv(p.integrity_audit,f,rows); assert not contract.validate_written_integrity_checks_passed(r.integrity_rows,p.integrity_audit,contract.DiskWriteActivity())["integrity_write_validation_passed"]
def test_r3b2_23_integrity_reason_tamper_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.integrity_audit); rows[0]["blocking_reasons"]="bad"; _write_csv(p.integrity_audit,f,rows); assert not contract.validate_written_integrity_checks_passed(r.integrity_rows,p.integrity_audit,contract.DiskWriteActivity())["integrity_write_validation_passed"]
def test_r3b2_24_reference_failure_blocked(tmp_path):
    s,m,p,c,ref=_r3b_result(tmp_path); ref.passed=False; r=contract.materialize_summary_and_integrity_to_disk(s,m,c,ref,output_paths=p,repo_root=tmp_path); assert not r.passed and len(r.activity.written_paths)==2
def test_r3b2_25_preflight_tamper_blocked(tmp_path):
    s,m,p,c,ref=_r3b_result(tmp_path); p.artifact_inventory.write_text("bad\n",encoding="utf-8"); r=contract.materialize_summary_and_integrity_to_disk(s,m,c,ref,output_paths=p,repo_root=tmp_path); assert not r.passed
def test_r3b2_26_path_failure_no_write(tmp_path):
    s,m,p,c,ref=_r3b_result(tmp_path); bad=contract.Step14AROutputPaths(**{n:(tmp_path/"bad"/"x.csv" if n=="split_summary" else getattr(p,n)) for n in p.__dataclass_fields__}); r=contract.materialize_summary_and_integrity_to_disk(s,m,c,ref,output_paths=bad,repo_root=tmp_path); assert not r.passed and not (tmp_path/"bad").exists()
def test_r3b2_27_remaining_outputs_absent(tmp_path):
    *_,r=_r3b2_result(tmp_path); assert r.passed
def test_r3b2_28_deterministic(tmp_path):
    s,m,p,c,ref,r=_r3b2_result(tmp_path); before={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in (tmp_path/contract.FINAL_ROOT).iterdir()}; r2=contract.materialize_summary_and_integrity_to_disk(s,m,c,ref,output_paths=p,repo_root=tmp_path); after={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in (tmp_path/contract.FINAL_ROOT).iterdir()}; assert r2.passed and before==after
def test_r3b2_29_split_source_flags_true(tmp_path):
    *_,r=_r3b2_result(tmp_path); assert all(x["source_rows_preserved"] is True for x in r.split_summary_rows)
def test_r3b2_30_group_flags_true(tmp_path):
    *_,r=_r3b2_result(tmp_path); assert all(x["group_integrity_preserved"] is True for x in r.split_summary_rows)


def test_r3b2_closure_group_member_set_mismatch_is_detected(tmp_path):
    s,m,p,c,ref,r=_r3b2_result(tmp_path); pre=contract.preflight_existing_seven_outputs(s,m,c,ref); members=pre["core"]["membership"]["typed_rows"]; left=next(i for i,row in enumerate(members) if row["assigned_split"]=="train"); right=next(i for i,row in enumerate(members) if row["assigned_split"]=="train" and row["final_leakage_group_id"]!=members[left]["final_leakage_group_id"]); members[left]["final_leakage_group_id"]=members[right]["final_leakage_group_id"]; rows=contract.build_candidate_disk_split_summary_rows(s,c,ref,pre); out=contract.build_disk_split_summary_checks_passed_evidence(rows,s,m,c,ref,pre); assert not out.validated_rows[0]["group_integrity_preserved"] and any("group_member_set_mismatch" in x for x in out.blocking_reasons)
def test_r3b2_closure_json_order_is_explicit(tmp_path):
    s,m,p,c,ref,r=_r3b2_result(tmp_path); rows=json.loads(p.final_dataset_index_json.read_text()); rows[0],rows[1]=rows[1],rows[0]; p.final_dataset_index_json.write_text(json.dumps(rows),encoding="utf-8"); b=contract.validate_step14ar_metadata_output_boundary(p,repo_root=tmp_path); o=contract.build_disk_integrity_observations(s,m,c,ref,r.split_summary_validation,repo_root=tmp_path,output_boundary_validation=b); assert o["canonical_sample_order_preserved"]=="false"
def test_r3b2_closure_unknown_output_is_detected(tmp_path):
    *_,p,c,ref,r=_r3b2_result(tmp_path); (tmp_path/contract.FINAL_ROOT/"unexpected.txt").write_text("x"); assert not contract.validate_step14ar_metadata_output_boundary(p,repo_root=tmp_path)["metadata_output_boundary_passed"]
def test_r3b2_closure_forbidden_output_breaks_training_boundary(tmp_path):
    s,m,p,c,ref,r=_r3b2_result(tmp_path); (tmp_path/contract.FINAL_ROOT/"probe.pt").write_text("x"); b=contract.validate_step14ar_metadata_output_boundary(p,repo_root=tmp_path); o=contract.build_disk_integrity_observations(s,m,c,ref,r.split_summary_validation,repo_root=tmp_path,output_boundary_validation=b); assert not b["metadata_output_boundary_passed"] and o["training_boundary_preserved"]=="false"
def test_r3b2_closure_temporary_output_is_detected(tmp_path):
    *_,p,c,ref,r=_r3b2_result(tmp_path); (tmp_path/contract.FINAL_ROOT/"leftover.tmp").write_text("x"); b=contract.validate_step14ar_metadata_output_boundary(p,repo_root=tmp_path); assert b["temporary_artifact_count"]==1
def test_r3b2_closure_remaining_outputs_are_absent(tmp_path):
    *_,p,c,ref,r=_r3b2_result(tmp_path); root=tmp_path/contract.FINAL_ROOT; assert {x.name for x in root.iterdir()}=={f for _,f,*_ in contract.OUTPUT_SPECS[:9]} and not (root/contract.OUTPUT_SPECS[9][1]).exists()
def test_r3b2_closure_summary_group_count_tamper_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.split_summary); rows[0]["leakage_group_count"]="9"; _write_csv(p.split_summary,f,rows); assert not contract.validate_written_split_summary_checks_passed(r.split_summary_rows,p.split_summary,contract.DiskWriteActivity())["split_summary_write_validation_passed"]
def test_r3b2_closure_summary_artifact_count_tamper_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.split_summary); rows[0]["artifact_reference_count"]="9"; _write_csv(p.split_summary,f,rows); assert not contract.validate_written_split_summary_checks_passed(r.split_summary_rows,p.split_summary,contract.DiskWriteActivity())["split_summary_write_validation_passed"]
def test_r3b2_closure_summary_source_flag_tamper_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.split_summary); rows[0]["source_rows_preserved"]="False"; _write_csv(p.split_summary,f,rows); assert not contract.validate_written_split_summary_checks_passed(r.split_summary_rows,p.split_summary,contract.DiskWriteActivity())["split_summary_write_validation_passed"]
def test_r3b2_closure_integrity_observed_tamper_detected(tmp_path):
    _,_,p,_,_,r=_r3b2_result(tmp_path); f,rows=_read_csv(p.integrity_audit); rows[0]["observed_value"]="bad"; _write_csv(p.integrity_audit,f,rows); assert not contract.validate_written_integrity_checks_passed(r.integrity_rows,p.integrity_audit,contract.DiskWriteActivity())["integrity_write_validation_passed"]


def _r4a_result(tmp_path):
    source, memory, paths, core, reference, summary = _r3b2_result(tmp_path)
    snapshot = contract.validate_contract_snapshot(contract.build_contract_snapshot())
    return source, memory, paths, core, reference, summary, contract.materialize_issue_and_safety_to_disk(snapshot, source, memory, core, reference, summary, output_paths=paths, repo_root=tmp_path)


def test_r4a_01_safety_contract_is_exactly_55():
    assert len(contract.FINAL_SAFETY_EXPECTED) == 55 and len({item for item, _ in contract.FINAL_SAFETY_EXPECTED}) == 55
def test_r4a_02_safety_output_contract_is_55_and_issue_is_1():
    counts={name:normal for name,_,_,normal,_,_ in contract.OUTPUT_SPECS}; assert counts["safety_audit"]==55 and counts["issue_inventory"]==1
def test_r4a_03_normal_safety_is_55_of_55(tmp_path):
    *_,r=_r4a_result(tmp_path); assert len(r.safety_rows)==55 and r.safety_validation.passed_count==55
def test_r4a_04_normal_issue_is_unique_sentinel(tmp_path):
    *_,r=_r4a_result(tmp_path); assert r.issue_rows==[contract.ISSUE_SENTINEL] and r.issue_validation["issue_inventory_clear"]
def test_r4a_05_secure_preflight_is_9_of_9(tmp_path):
    *_,r=_r4a_result(tmp_path); assert r.preflight_existing_nine_outputs["preflight_existing_nine_outputs_passed"] and r.preflight_existing_nine_outputs["preflight_output_count"]==9
def test_r4a_06_declared_nodes_are_regular_not_symlink(tmp_path):
    *_,r=_r4a_result(tmp_path); n=r.preflight_existing_nine_outputs["node_validation"]; assert n["regular_file_count"]==9 and n["symlink_count"]==n["missing_count"]==0
def test_r4a_07_only_two_outputs_added(tmp_path):
    *_,r=_r4a_result(tmp_path); assert len(r.activity.written_paths)==2 and r.metadata_output_boundary_after_write["existing_output_count"]==11
def test_r4a_08_activity_two_reads_no_temp(tmp_path):
    *_,r=_r4a_result(tmp_path); assert len(r.activity.read_paths)==2 and not r.activity.temporary_paths
def test_r4a_09_manifest_absent(tmp_path):
    _,_,p,_,_,_,r=_r4a_result(tmp_path); assert r.passed and not p.manifest.exists()
def test_r4a_10_readiness_manifest_only(tmp_path):
    *_,r=_r4a_result(tmp_path); assert r.ready_for_manifest_materialization and not r.ready_for_training and not r.ready_for_covapie_final_dataset_qa_gate
def test_r4a_11_safety_delete_detected(tmp_path):
    *_,r=_r4a_result(tmp_path); rows=copy.deepcopy(r.safety_rows); rows.pop(); assert not contract.build_safety_checks_passed_evidence(rows).passed
def test_r4a_12_safety_duplicate_detected(tmp_path):
    *_,r=_r4a_result(tmp_path); rows=copy.deepcopy(r.safety_rows); rows[1]["safety_item"]=rows[0]["safety_item"]; assert not contract.build_safety_checks_passed_evidence(rows).passed
def test_r4a_13_safety_required_observed_joint_tamper_detected(tmp_path):
    *_,r=_r4a_result(tmp_path); rows=copy.deepcopy(r.safety_rows); rows[0]["required_status"]=rows[0]["observed_status"]=False; assert not contract.build_safety_checks_passed_evidence(rows).passed
def test_r4a_14_safety_pass_flag_tamper_detected(tmp_path):
    *_,r=_r4a_result(tmp_path); rows=copy.deepcopy(r.safety_rows); rows[0]["safety_passed"]=False; assert not contract.build_safety_checks_passed_evidence(rows).passed
def test_r4a_15_safety_reason_tamper_detected(tmp_path):
    *_,r=_r4a_result(tmp_path); rows=copy.deepcopy(r.safety_rows); rows[0]["blocking_reasons"]="bad"; assert not contract.build_safety_checks_passed_evidence(rows).passed
def test_r4a_16_feature_semantics_true_is_blocked(tmp_path):
    s,m,p,c,ref,si,r=_r4a_result(tmp_path); obs=dict(r.safety_observations); obs["feature_semantics_known_for_training"]=True; assert not contract.build_safety_checks_passed_evidence(contract.build_final_safety_rows(obs)).passed
def test_r4a_17_ready_for_training_true_is_blocked(tmp_path):
    *_,r=_r4a_result(tmp_path); obs=dict(r.safety_observations); obs["ready_for_training"]=True; assert not contract.build_safety_checks_passed_evidence(contract.build_final_safety_rows(obs)).passed
def test_r4a_18_statistical_claim_true_is_blocked(tmp_path):
    *_,r=_r4a_result(tmp_path); obs=dict(r.safety_observations); obs["statistical_representativeness_claimed"]=True; assert not contract.build_safety_checks_passed_evidence(contract.build_final_safety_rows(obs)).passed
def test_r4a_19_issue_sentinel_tamper_detected():
    rows=[dict(contract.ISSUE_SENTINEL)]; rows[0]["issue_id"]="bad"; assert not contract.validate_issue_inventory_clear(rows,[])["issue_inventory_validation_passed"]
def test_r4a_20_duplicate_blocker_generates_one_issue():
    assert len(contract.build_final_issue_inventory_rows(["bad:x","bad:x"]))==1
def test_r4a_21_blocked_issue_count_is_dynamic():
    rows=contract.build_final_issue_inventory_rows(["b","a"]); assert contract.validate_issue_inventory_clear(rows,["b","a"])["blocking_issue_count"]==2
def test_r4a_22_symlink_existing_output_is_blocked_without_read(tmp_path):
    s,m,p,c,ref,si=_r3b2_result(tmp_path); target=tmp_path/"target"; target.write_text("secret"); p.artifact_inventory.unlink(); p.artifact_inventory.symlink_to(target); pre=contract.preflight_existing_nine_outputs(s,m,c,ref,si,repo_root=tmp_path); assert not pre["preflight_existing_nine_outputs_passed"] and str(target.resolve()) not in pre["read_paths"]
def test_r4a_23_directory_existing_output_is_blocked(tmp_path):
    s,m,p,c,ref,si=_r3b2_result(tmp_path); p.artifact_inventory.unlink(); p.artifact_inventory.mkdir(); pre=contract.preflight_existing_nine_outputs(s,m,c,ref,si,repo_root=tmp_path); assert not pre["preflight_existing_nine_outputs_passed"]
def test_r4a_24_missing_existing_output_is_blocked(tmp_path):
    s,m,p,c,ref,si=_r3b2_result(tmp_path); p.integrity_audit.unlink(); assert not contract.preflight_existing_nine_outputs(s,m,c,ref,si,repo_root=tmp_path)["preflight_existing_nine_outputs_passed"]
def test_r4a_25_unknown_output_produces_failed_safety_and_issues(tmp_path):
    s,m,p,c,ref,si=_r3b2_result(tmp_path); (tmp_path/contract.FINAL_ROOT/"unexpected.txt").write_text("x"); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_issue_and_safety_to_disk(cv,s,m,c,ref,si,output_paths=p,repo_root=tmp_path); assert not r.passed and not r.issue_validation["issue_inventory_clear"]
def test_r4a_26_pt_output_blocks_safety(tmp_path):
    s,m,p,c,ref,si=_r3b2_result(tmp_path); (tmp_path/contract.FINAL_ROOT/"probe.pt").write_text("x"); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_issue_and_safety_to_disk(cv,s,m,c,ref,si,output_paths=p,repo_root=tmp_path); assert r.safety_observations["no_forbidden_artifacts"] is False
def test_r4a_27_tmp_output_blocks_safety(tmp_path):
    s,m,p,c,ref,si=_r3b2_result(tmp_path); (tmp_path/contract.FINAL_ROOT/"leftover.tmp").write_text("x"); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_issue_and_safety_to_disk(cv,s,m,c,ref,si,output_paths=p,repo_root=tmp_path); assert r.safety_observations["no_temporary_artifacts"] is False
def test_r4a_28_written_safety_delete_detected(tmp_path):
    _,_,p,_,_,_,r=_r4a_result(tmp_path); f,rows=_read_csv(p.safety_audit); _write_csv(p.safety_audit,f,rows[:-1]); assert not contract.validate_written_safety_checks_passed(r.safety_rows,p.safety_audit,contract.DiskWriteActivity())["safety_write_validation_passed"]
def test_r4a_29_written_safety_joint_tamper_detected(tmp_path):
    _,_,p,_,_,_,r=_r4a_result(tmp_path); f,rows=_read_csv(p.safety_audit); rows[0]["required_status"]=rows[0]["observed_status"]="False"; _write_csv(p.safety_audit,f,rows); assert not contract.validate_written_safety_checks_passed(r.safety_rows,p.safety_audit,contract.DiskWriteActivity())["safety_write_validation_passed"]
def test_r4a_30_written_issue_tamper_detected(tmp_path):
    _,_,p,_,_,_,r=_r4a_result(tmp_path); f,rows=_read_csv(p.issue_inventory); rows[0]["issue_id"]="bad"; _write_csv(p.issue_inventory,f,rows); assert not contract.validate_written_issue_inventory_clear(r.issue_rows,[],p.issue_inventory,contract.DiskWriteActivity())["issue_write_validation_passed"]
def test_r4a_31_path_contract_failure_writes_nothing(tmp_path):
    s,m,p,c,ref,si=_r3b2_result(tmp_path); bad=contract.Step14AROutputPaths(**{n:(tmp_path/"bad"/"x.csv" if n=="safety_audit" else getattr(p,n)) for n in p.__dataclass_fields__}); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_issue_and_safety_to_disk(cv,s,m,c,ref,si,output_paths=bad,repo_root=tmp_path); assert not r.passed and not (tmp_path/"bad").exists()
def test_r4a_32_second_run_is_deterministic(tmp_path):
    s,m,p,c,ref,si,r=_r4a_result(tmp_path); root=tmp_path/contract.FINAL_ROOT; before={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir()}; cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); second=contract.materialize_issue_and_safety_to_disk(cv,s,m,c,ref,si,output_paths=p,repo_root=tmp_path); after={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir()}; assert second.passed and before==after


def _rebuild_r4a_observations(source, memory, core, reference, summary, result, *, repo_root):
    snapshot = contract.validate_contract_snapshot(contract.build_contract_snapshot())
    return contract.build_final_safety_observations(
        snapshot, source, memory, core, reference, summary,
        result.preflight_existing_nine_outputs,
        result.metadata_output_boundary_before_write,
        result.planned_write_validation,
        repo_root=repo_root,
    )


def test_r4a_truthfulness_01_repo_inside_non_derived_path_is_independent(tmp_path):
    boundary = contract._artifact_disk_path_contract([{"artifact_path": "docs/example.csv"}], tmp_path)
    assert boundary.all_relative_and_traversal_free and boundary.all_inside_repo
    assert not boundary.all_inside_allowed_derived_root and boundary.all_outside_raw_root


def test_r4a_truthfulness_02_repo_outside_path_fails_repo_and_derived(tmp_path):
    boundary = contract._artifact_disk_path_contract([{"artifact_path": str(tmp_path.parent / "outside.csv")}], tmp_path)
    assert not boundary.all_relative_and_traversal_free
    assert not boundary.all_inside_repo and not boundary.all_inside_allowed_derived_root


def test_r4a_truthfulness_03_normal_planned_writes_are_exact(tmp_path):
    *_, result = _r4a_result(tmp_path)
    planned = result.planned_write_validation
    assert planned.passed and planned.exact_r4a_output_set and len(planned.planned_write_paths) == 2


def test_r4a_truthfulness_04_raw_planned_issue_path_is_blocked(tmp_path):
    *_, paths, _, _, _, result = _r4a_result(tmp_path)
    bad = contract.Step14AROutputPaths(**{
        name: (tmp_path / "data/raw/issue.csv" if name == "issue_inventory" else getattr(paths, name))
        for name in paths.__dataclass_fields__
    })
    inventory = result.preflight_existing_nine_outputs["seven"]["inventory"]["typed_rows"]
    planned = contract.validate_r4a_planned_writes(bad, inventory, repo_root=tmp_path)
    assert not planned.passed and not planned.all_outside_raw_root
    assert any(item.startswith("r4a_planned_raw_write:") for item in planned.blocking_reasons)


def test_r4a_truthfulness_05_artifact_overwrite_planned_path_is_blocked(tmp_path):
    *_, paths, _, _, _, result = _r4a_result(tmp_path)
    inventory = copy.deepcopy(result.preflight_existing_nine_outputs["seven"]["inventory"]["typed_rows"])
    inventory[0]["artifact_path"] = str(paths.issue_inventory.relative_to(tmp_path))
    planned = contract.validate_r4a_planned_writes(paths, inventory, repo_root=tmp_path)
    assert not planned.passed and not planned.disjoint_from_referenced_artifacts
    assert any(item.startswith("r4a_planned_artifact_overwrite:") for item in planned.blocking_reasons)


def test_r4a_truthfulness_06_raw_preflight_read_makes_no_raw_reads_false(tmp_path):
    source, memory, _, core, reference, summary, result = _r4a_result(tmp_path)
    result.preflight_existing_nine_outputs["read_paths"].pop()
    result.preflight_existing_nine_outputs["read_paths"].add(str(tmp_path / "data/raw/probe.csv"))
    observations = _rebuild_r4a_observations(source, memory, core, reference, summary, result, repo_root=tmp_path)
    assert observations["no_raw_reads"] is False


def test_r4a_truthfulness_07_dynamic_ready_for_training_is_detected(tmp_path):
    source, memory, _, core, reference, summary, result = _r4a_result(tmp_path)
    memory.ready_for_training = True
    observations = _rebuild_r4a_observations(source, memory, core, reference, summary, result, repo_root=tmp_path)
    assert observations["ready_for_training"] is True
    assert not contract.build_safety_checks_passed_evidence(contract.build_final_safety_rows(observations)).passed


def test_r4a_truthfulness_08_dynamic_ready_to_train_now_is_detected(tmp_path):
    source, memory, _, core, reference, summary, result = _r4a_result(tmp_path)
    core.ready_to_train_now = True
    observations = _rebuild_r4a_observations(source, memory, core, reference, summary, result, repo_root=tmp_path)
    assert observations["ready_to_train_now"] is True
    assert not contract.build_safety_checks_passed_evidence(contract.build_final_safety_rows(observations)).passed


def test_r4a_truthfulness_09_swapped_aliases_fail_exact_mask_pairs(tmp_path, monkeypatch):
    source, memory, _, core, reference, summary, result = _r4a_result(tmp_path)
    aliases = list(contract.CANONICAL_MASK_TASK_ALIASES); aliases[0], aliases[1] = aliases[1], aliases[0]
    monkeypatch.setattr(contract, "CANONICAL_MASK_TASK_ALIASES", aliases)
    observations = _rebuild_r4a_observations(source, memory, core, reference, summary, result, repo_root=tmp_path)
    assert observations["canonical_mask_count_is_five"] is True
    assert observations["no_extra_mask_tasks_added"] is False


def test_r4a_truthfulness_10_missing_scaffold_b3_pair_is_detected(tmp_path, monkeypatch):
    source, memory, _, core, reference, summary, result = _r4a_result(tmp_path)
    aliases = list(contract.CANONICAL_MASK_TASK_ALIASES); aliases[3] = "C"
    monkeypatch.setattr(contract, "CANONICAL_MASK_TASK_ALIASES", aliases)
    observations = _rebuild_r4a_observations(source, memory, core, reference, summary, result, repo_root=tmp_path)
    assert observations["scaffold_only_b3_present"] is False


def test_r4a_truthfulness_11_normal_mask_pairs_are_exact():
    actual = tuple(zip(contract.CANONICAL_MASK_TASK_NAMES, contract.CANONICAL_MASK_TASK_ALIASES))
    assert actual == contract.EXPECTED_CANONICAL_MASK_PAIRS


def test_r4a_truthfulness_12_after_write_nodes_are_eleven_regular(tmp_path):
    *_, result = _r4a_result(tmp_path); nodes = result.after_write_node_validation
    assert nodes["declared_output_nodes_passed"] and nodes["regular_file_count"] == nodes["expected_node_count"] == 11
    assert nodes["symlink_count"] == nodes["missing_count"] == 0


def test_r4a_truthfulness_13_check_values_has_no_duplicate_literal_keys():
    tree = ast.parse(Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py").read_text(encoding="utf-8"))
    dictionaries = [node for node in ast.walk(tree) if isinstance(node, ast.Dict)]
    values = max(dictionaries, key=lambda node: sum(isinstance(key, ast.Constant) and isinstance(key.value, str) for key in node.keys if key is not None))
    keys = [key.value for key in values.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)]
    assert len(keys) == len(set(keys))


def test_r4a_truthfulness_14_check_has_no_misleading_r3b2_final_count():
    text = Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py").read_text(encoding="utf-8")
    assert "r3b2_final_root_output_count" not in text


def test_r4a_truthfulness_15_normal_safety_and_issue_sentinel_unchanged(tmp_path):
    *_, result = _r4a_result(tmp_path)
    assert len(result.safety_rows) == result.safety_validation.passed_count == 55
    assert result.issue_rows == [contract.ISSUE_SENTINEL]


def _r4b_result(tmp_path):
    source, memory, paths, core, reference, summary, r4a = _r4a_result(tmp_path)
    snapshot = contract.validate_contract_snapshot(contract.build_contract_snapshot())
    r4b = contract.materialize_final_manifest_and_gate(snapshot, source, memory, core, reference, summary, r4a, output_paths=paths, repo_root=tmp_path)
    return source, memory, paths, core, reference, summary, r4a, r4b


def _r4b_evidence(source, memory, core, reference, summary, r4a, r4b):
    return contract._manifest_actual_evidence(source, memory, core, reference, summary, r4a, r4b.preflight_existing_eleven_outputs, r4b.manifest_planned_write_validation, r4b.manifest["non_manifest_outputs"])


def _tampered_manifest_case(tmp_path):
    source, memory, paths, core, reference, summary, r4a, r4b = _r4b_result(tmp_path)
    evidence = _r4b_evidence(source, memory, core, reference, summary, r4a, r4b)
    return copy.deepcopy(r4b.manifest), evidence


def test_r4b_01_manifest_fields_are_exact():
    assert len(contract.FINAL_MANIFEST_FIELDS) == len(set(contract.FINAL_MANIFEST_FIELDS)) == 54


def test_r4b_02_manifest_root_is_dict(tmp_path):
    *_, r = _r4b_result(tmp_path); assert isinstance(r.manifest, dict)


def test_r4b_03_manifest_top_level_order_is_frozen(tmp_path):
    *_, r = _r4b_result(tmp_path); assert tuple(r.manifest) == contract.FINAL_MANIFEST_FIELDS


def test_r4b_04_source_hash_count_is_twelve(tmp_path):
    *_, r = _r4b_result(tmp_path); assert len(r.manifest["source_input_sha256"]) == 12


def test_r4b_05_source_hash_key_order_is_frozen(tmp_path):
    *_, r = _r4b_result(tmp_path); assert tuple(r.manifest["source_input_sha256"]) == contract.SOURCE_LOGICAL_NAMES


def test_r4b_06_non_manifest_outputs_are_eleven(tmp_path):
    *_, r = _r4b_result(tmp_path); assert r.manifest["non_manifest_output_count"] == len(r.manifest["non_manifest_outputs"]) == 11


def test_r4b_07_non_manifest_output_order_is_frozen(tmp_path):
    *_, r = _r4b_result(tmp_path); assert [row["logical_name"] for row in r.manifest["non_manifest_outputs"]] == [row[0] for row in contract.OUTPUT_SPECS[:11]]


def test_r4b_08_output_hashes_match_real_bytes(tmp_path):
    *_, paths, _, _, _, _, r = _r4b_result(tmp_path)
    assert all(row["sha256"] == hashlib.sha256(Path(getattr(paths, row["logical_name"])).read_bytes()).hexdigest() for row in r.manifest["non_manifest_outputs"])


def test_r4b_09_output_row_counts_are_exact(tmp_path):
    *_, r = _r4b_result(tmp_path); assert [row["row_count"] for row in r.manifest["non_manifest_outputs"]] == [23,11,11,11,66,33,11,4,24,1,55]


def test_r4b_10_manifest_has_no_self_hash(tmp_path):
    *_, r = _r4b_result(tmp_path); text=json.dumps(r.manifest); assert "manifest_sha256" not in text and all(row["logical_name"] != "manifest" for row in r.manifest["non_manifest_outputs"])


def test_r4b_11_split_counts_are_exact(tmp_path):
    *_, r = _r4b_result(tmp_path); assert r.manifest["split_sample_counts"] == contract.EXPECTED_SPLIT_SAMPLE_COUNTS and r.manifest["split_group_counts"] == contract.EXPECTED_SPLIT_GROUP_COUNTS and r.manifest["split_artifact_counts"] == contract.EXPECTED_SPLIT_ARTIFACT_COUNTS


def test_r4b_12_canonical_masks_are_exact(tmp_path):
    *_, r = _r4b_result(tmp_path); assert r.manifest["canonical_mask_pairs"] == [list(pair) for pair in contract.EXPECTED_CANONICAL_MASK_PAIRS]


def test_r4b_13_all_pass_fields_are_true(tmp_path):
    *_, r = _r4b_result(tmp_path); assert all(r.manifest[field] is True for field in contract.FINAL_MANIFEST_PASS_FIELDS)


def test_r4b_14_all_checks_passed(tmp_path):
    *_, r = _r4b_result(tmp_path); assert r.manifest["all_checks_passed"] is True and r.passed


def test_r4b_15_qa_readiness_is_true(tmp_path):
    *_, r = _r4b_result(tmp_path); assert r.ready_for_covapie_final_dataset_qa_gate and r.manifest["ready_for_covapie_final_dataset_qa_gate"]


def test_r4b_16_training_readiness_is_false(tmp_path):
    *_, r = _r4b_result(tmp_path); assert not r.ready_for_training and not r.ready_to_train_now and not r.manifest["ready_for_training"]


def test_r4b_17_feature_audit_remains_required(tmp_path):
    *_, r = _r4b_result(tmp_path); assert r.manifest["feature_semantics_audit_required_before_training"] is True


def test_r4b_18_recommended_next_step_is_qa(tmp_path):
    *_, r = _r4b_result(tmp_path); assert r.manifest["recommended_next_step"] == "covapie_final_dataset_qa_gate_v0"


def test_r4b_19_manifest_write_and_read_are_one(tmp_path):
    *_, r = _r4b_result(tmp_path); assert len(r.activity.written_paths) == len(r.activity.read_paths) == 1


def test_r4b_20_evidence_reads_are_eleven(tmp_path):
    *_, r = _r4b_result(tmp_path); assert len(r.manifest_evidence_activity.read_paths) == 11 and not r.manifest_evidence_activity.raw_read_attempted


def test_r4b_21_final_nodes_are_twelve_regular(tmp_path):
    *_, r = _r4b_result(tmp_path); n=r.final_node_validation; assert n["regular_file_count"] == n["expected_node_count"] == 12 and n["symlink_count"] == n["missing_count"] == 0


def test_r4b_22_final_output_count_is_twelve(tmp_path):
    *_, r = _r4b_result(tmp_path); assert r.final_metadata_boundary["existing_output_count"] == 12 and r.final_metadata_boundary["unknown_output_count"] == 0


def test_r4b_23_first_eleven_hashes_are_preserved(tmp_path):
    *_, r = _r4b_result(tmp_path); expected={row["logical_name"]:row["sha256"] for row in r.manifest["non_manifest_outputs"]}; assert all(r.final_output_sha256[name] == value for name,value in expected.items())


def test_r4b_24_list_root_is_detected(tmp_path):
    _, evidence = _tampered_manifest_case(tmp_path); assert "final_manifest_root_invalid" in contract.validate_final_manifest([], evidence, repo_root=tmp_path).blocking_reasons


def test_r4b_25_missing_top_level_key_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest.pop("stage"); assert "final_manifest_schema_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_26_extra_top_level_key_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["extra"]=1; assert "final_manifest_schema_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_27_source_hash_tamper_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["source_input_sha256"][contract.SOURCE_LOGICAL_NAMES[0]]="0"*64; assert "final_manifest_source_hash_contract_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_28_output_hash_tamper_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["non_manifest_outputs"][0]["sha256"]="0"*64; assert any(x.startswith("final_manifest_output_hash_mismatch:") for x in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons)


def test_r4b_29_output_order_tamper_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["non_manifest_outputs"][0],manifest["non_manifest_outputs"][1]=manifest["non_manifest_outputs"][1],manifest["non_manifest_outputs"][0]; assert "final_manifest_output_order_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_30_output_path_tamper_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["non_manifest_outputs"][0]["relative_path"]="bad.csv"; assert any(x.startswith("final_manifest_output_path_mismatch:") for x in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons)


def test_r4b_31_output_row_count_tamper_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["non_manifest_outputs"][0]["row_count"]=99; assert any(x.startswith("final_manifest_output_row_count_mismatch:") for x in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons)


def test_r4b_32_mask_pair_tamper_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["canonical_mask_pairs"][3][1]="C"; assert "final_manifest_mask_contract_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_33_false_subcheck_with_all_checks_true_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest[contract.FINAL_MANIFEST_PASS_FIELDS[0]]=False; assert any(x.startswith("final_manifest_pass_field_mismatch:") for x in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons)


def test_r4b_34_all_checks_false_with_qa_true_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["all_checks_passed"]=False; assert "final_manifest_all_checks_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons and "final_manifest_qa_readiness_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_35_ready_for_training_true_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["ready_for_training"]=True; assert "final_manifest_training_boundary_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_36_feature_audit_false_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["feature_semantics_audit_required_before_training"]=False; assert "final_manifest_training_boundary_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_37_blocker_with_all_checks_true_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["blocking_reasons"]=["bad"]; assert "final_manifest_blocking_reason_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_38_recommended_next_step_tamper_is_detected(tmp_path):
    manifest,evidence=_tampered_manifest_case(tmp_path); manifest["recommended_next_step"]="training"; assert "final_manifest_recommended_next_step_mismatch" in contract.validate_final_manifest(manifest,evidence,repo_root=tmp_path).blocking_reasons


def test_r4b_39_missing_safety_writes_only_blocked_manifest(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); p.safety_audit.unlink(); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a,output_paths=p,repo_root=tmp_path); assert not r.passed and r.manifest["all_checks_passed"] is False


def test_r4b_40_tampered_issue_writes_only_blocked_manifest(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); p.issue_inventory.write_text("bad\n",encoding="utf-8"); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a,output_paths=p,repo_root=tmp_path); assert not r.passed and r.manifest["ready_for_covapie_final_dataset_qa_gate"] is False


def test_r4b_41_raw_manifest_path_is_blocked(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); bad=contract.Step14AROutputPaths(**{name:(tmp_path/"data/raw/manifest.json" if name=="manifest" else getattr(p,name)) for name in p.__dataclass_fields__}); inventory=r4a.preflight_existing_nine_outputs["seven"]["inventory"]["typed_rows"]; planned=contract.validate_manifest_planned_write(bad,inventory,repo_root=tmp_path); assert not planned.passed and not planned.outside_raw_root


def test_r4b_42_existing_manifest_symlink_is_blocked_without_reading_target(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); target=tmp_path/"secret"; target.write_text("secret"); p.manifest.symlink_to(target); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a,output_paths=p,repo_root=tmp_path); assert not r.passed and not r.activity.read_paths and target.read_text()=="secret"


def test_r4b_43_existing_manifest_directory_is_blocked(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); p.manifest.mkdir(); inventory=r4a.preflight_existing_nine_outputs["seven"]["inventory"]["typed_rows"]; planned=contract.validate_manifest_planned_write(p,inventory,repo_root=tmp_path); assert not planned.passed and not planned.safe_existing_node


def test_r4b_44_existing_regular_manifest_is_deterministically_overwritten(tmp_path):
    s,m,p,c,ref,si,r4a,first=_r4b_result(tmp_path); before=p.manifest.read_bytes(); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r4a2=contract.materialize_issue_and_safety_to_disk(cv,s,m,c,ref,si,output_paths=p,repo_root=tmp_path,allow_existing_manifest=True); second=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a2,output_paths=p,repo_root=tmp_path); assert second.passed and p.manifest.read_bytes()==before


def test_r4b_45_path_contract_failure_writes_no_manifest(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); bad=contract.Step14AROutputPaths(**{name:(tmp_path/"outside/manifest.json" if name=="manifest" else getattr(p,name)) for name in p.__dataclass_fields__}); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a,output_paths=bad,repo_root=tmp_path); assert not r.passed and not bad.manifest.exists()


def test_r4b_46_r4a_failure_writes_blocked_manifest(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); r4a.passed=False; r4a.blocking_reasons=["forced_r4a_failure"]; cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a,output_paths=p,repo_root=tmp_path); assert not r.passed and p.manifest.exists() and r.manifest["blocking_reasons"]


def test_r4b_47_blocked_manifest_qa_and_training_are_false(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); r4a.passed=False; r4a.blocking_reasons=["blocked"]; cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a,output_paths=p,repo_root=tmp_path); assert not r.manifest["ready_for_covapie_final_dataset_qa_gate"] and not r.manifest["ready_for_training"] and not r.manifest["ready_to_train_now"]


def test_r4b_48_blocked_manifest_is_deterministic(tmp_path):
    s,m,p,c,ref,si,r4a=_r4a_result(tmp_path); r4a.passed=False; r4a.blocking_reasons=["blocked"]; cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a,output_paths=p,repo_root=tmp_path); before=p.manifest.read_bytes(); contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a,output_paths=p,repo_root=tmp_path); assert p.manifest.read_bytes()==before


def test_r4b_49_second_complete_pipeline_run_passes(tmp_path):
    s,m,p,c,ref,si,r4a,first=_r4b_result(tmp_path); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r4a_second=contract.materialize_issue_and_safety_to_disk(cv,s,m,c,ref,si,output_paths=p,repo_root=tmp_path,allow_existing_manifest=True); second=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a_second,output_paths=p,repo_root=tmp_path); assert first.passed and r4a_second.passed and second.passed


def test_r4b_50_two_runs_have_identical_twelve_hashes(tmp_path):
    s,m,p,c,ref,si,r4a,first=_r4b_result(tmp_path); cv=contract.validate_contract_snapshot(contract.build_contract_snapshot()); r4a_second=contract.materialize_issue_and_safety_to_disk(cv,s,m,c,ref,si,output_paths=p,repo_root=tmp_path,allow_existing_manifest=True); second=contract.materialize_final_manifest_and_gate(cv,s,m,c,ref,si,r4a_second,output_paths=p,repo_root=tmp_path); assert first.final_output_sha256==second.final_output_sha256 and len(second.final_output_sha256)==12

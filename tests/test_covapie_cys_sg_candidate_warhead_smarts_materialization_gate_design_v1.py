from __future__ import annotations

import csv
import copy
import dataclasses
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import rdkit

from covalent_ext import (
    covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1
    as gate,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle_harness


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / gate.OUTPUT_ROOT


def csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def output_payloads() -> dict[str, bytes]:
    return {name: (OUTPUT_ROOT / name).read_bytes() for name in gate.OUTPUT_FILES}


def leaving_group_inputs(
    class_id: str,
) -> tuple[
    dict[str, str],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    frozen = gate.load_frozen_sources(REPO_ROOT)
    classes = csv_rows(frozen[gate.CLASS_VOCABULARY])
    assignments = csv_rows(frozen[gate.ASSIGNMENT_AUTHORITY])
    rules = csv_rows(frozen[gate.RULE_REGISTRY])
    atoms = csv_rows(frozen[gate.PARENT_ATOM_AUTHORITY])
    bonds = csv_rows(frozen[gate.PARENT_BOND_AUTHORITY])
    mappings = csv_rows(frozen[gate.ATOM_MAPPING_AUTHORITY])
    cls = next(row for row in classes if row["warhead_type_candidate_class_id"] == class_id)
    rule = next(row for row in rules if row["warhead_rule_id"] == cls["warhead_rule_id"])
    support = [
        row
        for row in assignments
        if row["warhead_type_candidate_class_id"] == class_id
    ]
    return rule, support, atoms, bonds, mappings


def proposal_record() -> tuple[dict[str, object], list[str]]:
    parent_ids = ["A", "B", "C", "F1"]
    values: dict[str, object] = {
        "proposal_version": "proposal_v1",
        "sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000001",
        "pdb_id": "6BV6",
        "ligand_comp_id": "JUG",
        "warhead_type_candidate_class_index_0based": 3,
        "warhead_type_candidate_class_id": "CLASS",
        "reaction_family_id": "FAMILY",
        "warhead_rule_id": "RULE",
        "component_parent_graph_sha256": "a" * 64,
        "ligand_reactive_parent_atom_id": "A",
        "local_reaction_center_atom_ids": ["A", "B"],
        "local_reaction_center_bond_ids": ["A|B|single"],
        "proposed_pre_reaction_warhead_atom_ids": ["A", "B", "F1"],
        "proposed_warhead_attachment_atom_id": "B",
        "proposed_nonwarhead_boundary_atom_id": "C",
        "proposed_attachment_boundary_bond_order": "single",
        "required_leaving_group_atom_ids": ["F1"],
        "proposal_method": "candidate_method_v1",
        "proposal_status": "auto_exact_candidate",
        "ambiguity_reasons": [],
        "source_assignment_record_sha256": "b" * 64,
        "proposal_record_sha256": "",
    }
    record = {field: values[field] for field in gate.PROPOSAL_FIELDS}
    record["proposal_record_sha256"] = gate.proposal_record_sha256(record)
    return record, parent_ids


def test_formal_runtime_and_base_identity() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"
    identity = subprocess.run(
        [
            "git",
            "show",
            "-s",
            "--format=%H%n%P%n%T%n%s",
            gate.BASE_COMMIT,
        ],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode().splitlines()
    assert identity == [
        gate.BASE_COMMIT,
        gate.BASE_PARENT,
        gate.BASE_TREE,
        gate.BASE_SUBJECT,
    ]
    assert gate.validate_execution_boundary_v1(REPO_ROOT) in {
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    }


def test_exact15_source_inventory_and_sha() -> None:
    frozen = gate.load_frozen_sources(REPO_ROOT)
    assert tuple(frozen) == gate.SOURCE_PATHS
    assert len(frozen) == 15
    for path, payload in frozen.items():
        assert hashlib.sha256(payload).hexdigest() == gate.FROZEN_BASE_SHA256[path]
    rows = csv_rows((OUTPUT_ROOT / gate.SOURCE_FILE).read_bytes())
    assert len(rows) == 15
    assert [row["source_path"] for row in rows] == [
        path.as_posix() for path in gate.SOURCE_PATHS
    ]
    assert all(row["verified"] == "true" for row in rows)
    assert {row["provides_current_value"] for row in rows} == {"true", "false"}


def test_inherited_rule_and_proposal_contracts() -> None:
    frozen = gate.load_frozen_sources(REPO_ROOT)
    assert (
        gate._literal_tuple(frozen[gate.ROLE_CONTRACT_SOURCE], "WARHEAD_RULE_FIELDS")
        == gate.WARHEAD_RULE_FIELDS
    )
    assert gate.WARHEAD_RULE_FIELDS == (
        "reaction_family_id",
        "reaction_family_version",
        "target_residue_types",
        "target_residue_reactive_atom_name",
        "warhead_smarts",
        "ligand_reactive_atom_map_number",
        "warhead_atom_map_numbers",
        "warhead_attachment_atom_map_number",
        "expected_pre_reaction_bond_orders",
        "allowed_formal_charge_pattern",
        "allowed_match_count",
        "priority",
    )
    assert len(gate.PROPOSAL_FIELDS) == 22
    assert gate.PROPOSAL_STATUSES == (
        "not_materialized",
        "auto_exact_candidate",
        "ambiguous_candidate",
        "quarantined",
    )


def test_review_package_and_phase_a_state() -> None:
    frozen = gate.load_frozen_sources(REPO_ROOT)
    classes, assignments, rules, leaving_group_validations, reasons = gate._phase_a(
        frozen
    )
    assert reasons == []
    assert len(classes) == len(rules) == 7
    assert len(assignments) == 11
    assert len(leaving_group_validations) == 7
    manifest = json.loads(frozen[gate.REVIEW_PACKAGE_MANIFEST])
    assert manifest["transaction_succeeded"] is True
    assert manifest["review_package_materialized"] is True
    assert manifest["review_package_item_count"] == 18
    assert manifest["ready_for_family_identity_review_execution"] is True
    assert manifest["ready_for_rule_topology_review_execution"] is True
    assert manifest["ready_for_sample_assignment_review_execution"] is True
    assert manifest["ready_for_SMARTS_review_execution"] is False
    assert manifest["human_review_execution_completed"] is False


def test_local_graph_boundary_and_cys_sg_target() -> None:
    frozen = gate.load_frozen_sources(REPO_ROOT)
    rules = csv_rows(frozen[gate.RULE_REGISTRY])
    assert len(rules) == 7
    for row in rules:
        graph = json.loads(row["canonical_local_graph_rule_json"])
        canonical = gate.canonical_json(graph).encode()
        assert gate.sha256(canonical) == row["canonical_local_graph_rule_sha256"]
        assert graph["selected_signature_radius"] == 1
        assert graph["rule_kind"] == "canonical_local_graph_exact_match_v1"
        assert graph["center_atom"]["reactive"] is True
        assert graph["target_condition"]["residue"] == "CYS"
        assert graph["target_condition"]["residue_atom"] == "SG"
        assert row["approved_warhead_smarts"] == ""
        assert row["approved"] == "false"
    manifest = json.loads((OUTPUT_ROOT / gate.MANIFEST_FILE).read_text())
    assert (
        manifest["local_reaction_center_semantics"]
        == "radius_1_reaction_center_lower_bound_only"
    )
    assert manifest["complete_warhead_semantics"] == "not_available"


def test_parent_graph_and_reactive_mapping_coverage() -> None:
    frozen = gate.load_frozen_sources(REPO_ROOT)
    assignments = csv_rows(frozen[gate.ASSIGNMENT_AUTHORITY])
    atoms = csv_rows(frozen[gate.PARENT_ATOM_AUTHORITY])
    bonds = csv_rows(frozen[gate.PARENT_BOND_AUTHORITY])
    mappings = csv_rows(frozen[gate.ATOM_MAPPING_AUTHORITY])
    expected_components = {row["ligand_comp_id"] for row in assignments}
    assert expected_components == {row["ligand_comp_id"] for row in atoms}
    assert expected_components == {row["ligand_comp_id"] for row in bonds}
    for assignment in assignments:
        atom_sha = {
            row["component_parent_graph_sha256"]
            for row in atoms
            if row["ligand_comp_id"] == assignment["ligand_comp_id"]
        }
        bond_sha = {
            row["component_parent_graph_sha256"]
            for row in bonds
            if row["ligand_comp_id"] == assignment["ligand_comp_id"]
        }
        assert atom_sha == bond_sha == {assignment["component_parent_graph_sha256"]}
        reactive = [
            row
            for row in mappings
            if row["sample_index_row_id"] == assignment["sample_index_row_id"]
            and row["reactive_ligand_atom"] == "true"
        ]
        assert len(reactive) == 1
        assert (
            reactive[0]["parent_ccd_atom_id"]
            == assignment["ligand_reactive_parent_ccd_atom_id"]
        )
        assert (
            reactive[0]["component_parent_graph_sha256"]
            == assignment["component_parent_graph_sha256"]
        )


def test_reaction_delta_and_local_leaving_group_fail_closed_mutations() -> None:
    class_id = "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_EE022EB419200D14"
    rule, support, atoms, bonds, mappings = leaving_group_inputs(class_id)

    def mutated_rule(
        mutate_local=None, mutate_csv=None
    ) -> dict[str, str]:
        candidate = copy.deepcopy(rule)
        local = json.loads(candidate["canonical_local_graph_rule_json"])
        if mutate_local is not None:
            mutate_local(local)
        candidate["canonical_local_graph_rule_json"] = gate.canonical_json(local)
        if mutate_csv is not None:
            mutate_csv(candidate)
        return candidate

    mutations = (
        mutated_rule(
            lambda local: local["reaction_delta"].__setitem__("extra", "forbidden")
        ),
        mutated_rule(
            lambda local: local["reaction_delta"].__setitem__(
                "leaving_group_count", True
            )
        ),
        mutated_rule(
            lambda local: local["reaction_delta"].__setitem__(
                "leaving_group_count", -1
            )
        ),
        mutated_rule(
            lambda local: local["reaction_delta"].__setitem__(
                "leaving_group_elements", "F"
            )
        ),
        mutated_rule(
            lambda local: local["reaction_delta"].__setitem__(
                "leaving_group_elements", ["F", "F"]
            )
        ),
        mutated_rule(
            lambda local: local["reaction_delta"].__setitem__(
                "leaving_group_elements", ["Z", "F"]
            )
        ),
        mutated_rule(mutate_csv=lambda row: row.__setitem__(
            "required_leaving_group_count", "0"
        )),
        mutated_rule(mutate_csv=lambda row: row.__setitem__(
            "allowed_leaving_group_elements", "Cl"
        )),
        mutated_rule(mutate_csv=lambda row: row.__setitem__(
            "required_reaction_delta_class", "wrong_class"
        )),
        mutated_rule(
            lambda local: next(
                atom for atom in local["local_atoms"] if atom["is_leaving_group"]
            ).__setitem__("is_leaving_group", False)
        ),
        mutated_rule(
            lambda local: next(
                atom for atom in local["local_atoms"] if atom["is_leaving_group"]
            ).__setitem__("is_retained_observed", True)
        ),
        mutated_rule(
            lambda local: local.__setitem__(
                "local_bonds",
                [
                    bond
                    for bond in local["local_bonds"]
                    if bond["projected_disposition"]
                    != "verified_leaving_group_endpoint_missing"
                ],
            )
        ),
        mutated_rule(
            lambda local: next(
                bond
                for bond in local["local_bonds"]
                if bond["projected_disposition"]
                == "verified_leaving_group_endpoint_missing"
            ).__setitem__("projected_disposition", "retained_observed_bond")
        ),
    )
    for candidate in mutations:
        with pytest.raises(
            ValueError, match="^leaving_group_rule_contract_mismatch:"
        ):
            gate.validate_pre_reaction_leaving_group_semantics(
                candidate, support, atoms, bonds, mappings
            )


def test_parent_leaving_group_evidence_fail_closed_mutations() -> None:
    class_id = "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_EE022EB419200D14"
    rule, support, atoms, bonds, mappings = leaving_group_inputs(class_id)
    wrong_order = copy.deepcopy(bonds)
    target_bond = next(
        row
        for row in wrong_order
        if row["ligand_comp_id"] == "ZYA"
        and {row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]}
        == {"CM", "F1"}
    )
    target_bond["normalized_bond_order"] = "double"
    missing_atom = [
        row
        for row in copy.deepcopy(atoms)
        if not (row["ligand_comp_id"] == "ZYA" and row["ccd_atom_id"] == "F1")
    ]
    ambiguous_atoms = copy.deepcopy(atoms)
    f2 = copy.deepcopy(
        next(
            row
            for row in ambiguous_atoms
            if row["ligand_comp_id"] == "ZYA" and row["ccd_atom_id"] == "F1"
        )
    )
    f2["ccd_atom_id"] = "F2"
    ambiguous_atoms.append(f2)
    ambiguous_bonds = copy.deepcopy(bonds)
    cm_f2 = copy.deepcopy(
        next(
            row
            for row in ambiguous_bonds
            if row["ligand_comp_id"] == "ZYA"
            and {row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]}
            == {"CM", "F1"}
        )
    )
    if cm_f2["parent_ccd_atom_id_1"] == "F1":
        cm_f2["parent_ccd_atom_id_1"] = "F2"
    else:
        cm_f2["parent_ccd_atom_id_2"] = "F2"
    ambiguous_bonds.append(cm_f2)
    cases = (
        (atoms, wrong_order),
        (missing_atom, bonds),
        (ambiguous_atoms, ambiguous_bonds),
    )
    for candidate_atoms, candidate_bonds in cases:
        with pytest.raises(
            ValueError, match="^parent_leaving_group_evidence_mismatch:"
        ):
            gate.validate_pre_reaction_leaving_group_semantics(
                rule, support, candidate_atoms, candidate_bonds, mappings
            )


def test_formal_leaving_group_reconstruction_baseline() -> None:
    frozen = gate.load_frozen_sources(REPO_ROOT)
    classes, assignments, _rules, validations, reasons = gate._phase_a(frozen)
    assert reasons == []
    assert len(validations) == 7
    assert sum(value.leaving_group_count == 0 for value in validations.values()) == 6
    assert sum(value.leaving_group_count > 0 for value in validations.values()) == 1
    ee_class = next(
        row
        for row in classes
        if row["warhead_type_candidate_class_id"]
        == "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_EE022EB419200D14"
    )
    ee = validations[ee_class["warhead_rule_id"]]
    assert ee.leaving_group_count == 1
    assert ee.leaving_group_elements == ("F",)
    assert len(ee.sample_evidence) == 1
    evidence = ee.sample_evidence[0]
    assert evidence.ligand_comp_id == "ZYA"
    assert evidence.reactive_parent_atom_id == "CM"
    assert evidence.leaving_group_parent_atom_ids == ("F1",)
    assert evidence.leaving_group_bond_ids == ("CM|F1|single",)
    readiness = gate._readiness_rows(classes, assignments, validations)
    assert all(
        row["pre_reaction_leaving_group_semantics_available"]
        and row[
            "ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization"
        ]
        for row in readiness
    )
    missing = dict(validations)
    del missing[ee_class["warhead_rule_id"]]
    degraded = gate._readiness_rows(classes, assignments, missing)
    ee_row = next(
        row
        for row in degraded
        if row["warhead_rule_id"] == ee_class["warhead_rule_id"]
    )
    assert ee_row["pre_reaction_leaving_group_semantics_available"] is False
    assert (
        ee_row[
            "ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization"
        ]
        is False
    )


def test_proposal_identity_type_and_bond_contract() -> None:
    assert gate.PROPOSAL_ATOM_ID_NAMESPACE == "parent_ccd_atom_id"
    assert (
        gate.PROPOSAL_BOND_ID_ENCODING
        == "canonical_parent_ccd_endpoint_pair_and_normalized_order_v1"
    )
    assert len(gate.PROPOSAL_FIELDS) == len(gate.PROPOSAL_FIELD_TYPE_CONTRACT) == 22
    assert tuple(gate.PROPOSAL_FIELD_TYPE_CONTRACT) == gate.PROPOSAL_FIELDS
    assert gate.canonical_parent_bond_id("F1", "CM", "single") == "CM|F1|single"
    record, parent_ids = proposal_record()
    gate.validate_proposal_record(
        record, parent_ids, require_materialized_hash=True
    )
    for invalid_atom in ("observed_only", "rdkit_index_0"):
        candidate = copy.deepcopy(record)
        candidate["ligand_reactive_parent_atom_id"] = invalid_atom
        with pytest.raises(ValueError, match="proposal_atom_id_invalid"):
            gate.validate_proposal_record(
                candidate, parent_ids, require_materialized_hash=False
            )
    integer_atom = copy.deepcopy(record)
    integer_atom["local_reaction_center_atom_ids"] = [0]
    with pytest.raises(ValueError, match="proposal_field_type_invalid"):
        gate.validate_proposal_record(
            integer_atom, parent_ids, require_materialized_hash=False
        )


def test_proposal_list_status_and_exact_type_failures() -> None:
    record, parent_ids = proposal_record()
    bool_index = copy.deepcopy(record)
    bool_index["warhead_type_candidate_class_index_0based"] = True
    with pytest.raises(ValueError, match="proposal_field_type_invalid"):
        gate.validate_proposal_record(
            bool_index, parent_ids, require_materialized_hash=False
        )
    duplicate_atoms = copy.deepcopy(record)
    duplicate_atoms["local_reaction_center_atom_ids"] = ["A", "A"]
    with pytest.raises(ValueError, match="proposal_atom_list_invalid"):
        gate.validate_proposal_record(
            duplicate_atoms, parent_ids, require_materialized_hash=False
        )
    unsorted_atoms = copy.deepcopy(record)
    unsorted_atoms["local_reaction_center_atom_ids"] = ["B", "A"]
    with pytest.raises(ValueError, match="proposal_atom_list_invalid"):
        gate.validate_proposal_record(
            unsorted_atoms, parent_ids, require_materialized_hash=False
        )
    duplicate_bonds = copy.deepcopy(record)
    duplicate_bonds["local_reaction_center_bond_ids"] = [
        "A|B|single",
        "A|B|single",
    ]
    with pytest.raises(ValueError, match="proposal_bond_id_list_invalid"):
        gate.validate_proposal_record(
            duplicate_bonds, parent_ids, require_materialized_hash=False
        )
    unsorted_bonds = copy.deepcopy(record)
    unsorted_bonds["local_reaction_center_bond_ids"] = [
        "B|C|single",
        "A|B|single",
    ]
    with pytest.raises(ValueError, match="proposal_bond_id_list_invalid"):
        gate.validate_proposal_record(
            unsorted_bonds, parent_ids, require_materialized_hash=False
        )
    invalid_status = copy.deepcopy(record)
    invalid_status["proposal_status"] = "approved"
    with pytest.raises(ValueError, match="proposal_status_invalid"):
        gate.validate_proposal_record(
            invalid_status, parent_ids, require_materialized_hash=False
        )


def test_proposal_exact22_field_types_reject_every_wrong_exact_type() -> None:
    record, parent_ids = proposal_record()
    for field, contract in gate.PROPOSAL_FIELD_TYPE_CONTRACT.items():
        candidate = copy.deepcopy(record)
        candidate[field] = (
            True
            if contract == "exact_int"
            else ()
            if contract == "exact_list_str"
            else 1
        )
        with pytest.raises(ValueError, match=f"proposal_field_type_invalid:{field}"):
            gate.validate_proposal_record(
                candidate, parent_ids, require_materialized_hash=False
            )


def test_proposal_hash_excludes_self_and_includes_every_other_field() -> None:
    record, _parent_ids = proposal_record()
    expected = record["proposal_record_sha256"]
    changed_self = copy.deepcopy(record)
    changed_self["proposal_record_sha256"] = "f" * 64
    assert gate.proposal_record_sha256(changed_self) == expected
    for field in gate.PROPOSAL_FIELDS:
        if field == gate.PROPOSAL_HASH_EXCLUDED_FIELD:
            continue
        changed = copy.deepcopy(record)
        value = changed[field]
        if type(value) is int:
            changed[field] = value + 1
        elif type(value) is list:
            changed[field] = [*value, "variant"]
        else:
            changed[field] = value + "_variant"
        assert gate.proposal_record_sha256(changed) != expected, field
    assert gate.PROPOSAL_HASH_CANONICAL_JSON_CONTRACT == {
        "sort_keys": True,
        "separators": [",", ":"],
        "ensure_ascii": True,
        "encoding": "UTF-8",
        "excluded_field": "proposal_record_sha256",
        "included_field_count": 21,
    }


def test_exact16_contract_registry() -> None:
    rows = csv_rows((OUTPUT_ROOT / gate.CONTRACT_FILE).read_bytes())
    assert len(rows) == 16
    assert [row["contract_id"] for row in rows] == [
        f"SMARTS_GATE_{index:03d}" for index in range(1, 17)
    ]
    assert [row["semantic_name"] for row in rows] == [
        definition[0] for definition in gate.CONTRACT_DEFINITIONS
    ]
    assert all(row["fails_closed"] == row["verified"] == "true" for row in rows)


def test_current7_support_and_truthful_readiness() -> None:
    frozen = gate.load_frozen_sources(REPO_ROOT)
    assignments = csv_rows(frozen[gate.ASSIGNMENT_AUTHORITY])
    rows = csv_rows((OUTPUT_ROOT / gate.READINESS_FILE).read_bytes())
    assert len(rows) == 7
    assert [int(row["warhead_type_candidate_class_index_0based"]) for row in rows] == list(
        range(7)
    )
    true_inputs = (
        "local_reaction_center_rule_available",
        "parent_heavy_atom_authority_available",
        "parent_heavy_bond_authority_available",
        "parent_graph_SHA_verified",
        "reactive_parent_atom_mapping_available",
        "pre_reaction_leaving_group_semantics_available",
        "ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization",
        "verified",
    )
    closed = (
        "complete_warhead_atom_set_available",
        "exact_one_attachment_boundary_available",
        "deterministic_atom_map_policy_available",
        "SMARTS_query_semantics_frozen",
        "class_wide_exact_one_match_validation_available",
        "candidate_warhead_smarts_materialized",
        "ready_for_candidate_warhead_smarts_materialization",
        "ready_for_SMARTS_human_review",
        "approved_warhead_rule_available",
        "ready_for_role_proposal_generation",
        "ready_for_mask_materialization",
        "ready_for_model_integration",
        "ready_for_training",
    )
    for row in rows:
        supporting = [
            item
            for item in assignments
            if item["warhead_type_candidate_class_id"]
            == row["warhead_type_candidate_class_id"]
        ]
        assert row["supporting_sample_ids"].split(";") == sorted(
            item["sample_index_row_id"] for item in supporting
        )
        assert row["supporting_component_ids"].split(";") == sorted(
            {item["ligand_comp_id"] for item in supporting}
        )
        assert int(row["Current11_match_count"]) == len(supporting)
        assert int(row["Current11_unique_component_count"]) == len(
            {item["ligand_comp_id"] for item in supporting}
        )
        assert all(row[field] == "true" for field in true_inputs)
        assert all(row[field] == "false" for field in closed)
        assert row["candidate_warhead_smarts"] == ""
        assert row["candidate_warhead_smarts_status"] == "not_materialized"


def test_authority_gap_matrix_is_unresolved_and_complete() -> None:
    rows = csv_rows((OUTPUT_ROOT / gate.GAP_FILE).read_bytes())
    assert len(rows) == 49
    class_ids = {row["warhead_type_candidate_class_id"] for row in rows}
    assert len(class_ids) == 7
    assert {row["missing_authority"] for row in rows} == {
        definition[0] for definition in gate.GAP_DEFINITIONS
    }
    for class_id in class_ids:
        assert sum(row["warhead_type_candidate_class_id"] == class_id for row in rows) == 7
    assert all(row["would_block_atom_set_proposal"] == "false" for row in rows)
    assert all(row["would_block_SMARTS_materialization"] == "true" for row in rows)
    assert all(row["would_block_SMARTS_review"] == "true" for row in rows)
    assert all(row["verified"] == "true" for row in rows)


def test_exact32_typed_mutations_fail_closed() -> None:
    baseline = gate.GateScenario()
    assert len(gate.FAILURE_MUTATIONS) == 32
    signatures = set()
    for _case, field, value, expected in gate.FAILURE_MUTATIONS:
        original = getattr(baseline, field)
        assert type(value) is type(original)
        assert value != original
        observed = gate.observe_failure_scenario(
            dataclasses.replace(baseline, **{field: value})
        )
        assert expected in observed
        signatures.add(f"{field}={gate.canonical_json(value)}")
    assert len(signatures) == 32
    rows = csv_rows((OUTPUT_ROOT / gate.FAILURE_FILE).read_bytes())
    assert len(rows) == 32
    assert len({row["mutation_signature"] for row in rows}) == 32
    for row in rows:
        assert row["expected_reason"] in row["observed_reasons"].split(";")
        assert row["expected_reason_verified"] == row["fails_closed"] == "true"
        assert row["contract_registry_row_count"] == "0"
        assert row["readiness_matrix_row_count"] == "0"
        assert row["authority_gap_row_count"] == "0"
        assert row["proposal_materialization_ready"] == "false"
        assert row["SMARTS_materialization_ready"] == "false"
        assert row["role_proposal_generation_ready"] == "false"
        assert row["mask_materialization_ready"] == "false"
        assert row["model_integration_ready"] == "false"
        assert row["training_ready"] == "false"
        assert row["verified"] == "true"


def test_transaction_failure_is_header_only() -> None:
    contracts, readiness, gaps = gate.transaction_tables(
        ("injected_blocker",), gate.contract_rows(), ({"x": 1},), ({"y": 2},)
    )
    assert contracts == readiness == gaps == ()
    assert csv_rows(gate._csv_bytes(gate.CONTRACT_COLUMNS, contracts)) == []
    assert csv_rows(gate._csv_bytes(gate.READINESS_COLUMNS, readiness)) == []
    assert csv_rows(gate._csv_bytes(gate.GAP_COLUMNS, gaps)) == []


def test_manifest_is_truthful_and_downstream_closed() -> None:
    manifest = json.loads((OUTPUT_ROOT / gate.MANIFEST_FILE).read_text())
    assert manifest["transaction_succeeded"] is True
    assert manifest["candidate_smarts_gate_design_completed"] is True
    assert manifest["source_count"] == 15
    assert manifest["contract_count"] == 16
    assert manifest["candidate_class_count"] == 7
    assert manifest["current11_sample_count"] == 11
    assert manifest["authority_gap_row_count"] == 49
    assert manifest["failure_mutation_count"] == 32
    assert manifest["inherited_warhead_rule_fields"] == list(gate.WARHEAD_RULE_FIELDS)
    assert manifest["proposal_fields"] == list(gate.PROPOSAL_FIELDS)
    assert manifest["proposal_statuses"] == list(gate.PROPOSAL_STATUSES)
    assert manifest["proposal_record_count"] == 0
    assert manifest["proposal_atom_id_namespace"] == gate.PROPOSAL_ATOM_ID_NAMESPACE
    assert manifest["proposal_bond_id_encoding"] == gate.PROPOSAL_BOND_ID_ENCODING
    assert (
        manifest["proposal_field_type_contract"]
        == gate.PROPOSAL_FIELD_TYPE_CONTRACT
    )
    assert (
        manifest["proposal_hash_excluded_field"]
        == gate.PROPOSAL_HASH_EXCLUDED_FIELD
    )
    assert (
        manifest["proposal_hash_canonical_json_contract"]
        == gate.PROPOSAL_HASH_CANONICAL_JSON_CONTRACT
    )
    assert manifest["pre_reaction_leaving_group_semantics_available_count"] == 7
    assert manifest["leaving_group_class_count"] == 1
    assert manifest["zero_leaving_group_class_count"] == 6
    assert manifest["required_leaving_group_total_atom_count"] == 1
    for field in (
        "local_reaction_center_rule_available_count",
        "parent_heavy_atom_authority_available_count",
        "parent_heavy_bond_authority_available_count",
        "reactive_parent_atom_mapping_available_count",
        "warhead_atom_set_and_boundary_proposal_materialization_ready_count",
    ):
        assert manifest[field] == 7
    for field in (
        "complete_warhead_atom_set_available_count",
        "exact_one_attachment_boundary_available_count",
        "deterministic_atom_map_policy_available_count",
        "SMARTS_query_semantics_frozen_count",
        "candidate_warhead_smarts_materialized_count",
        "candidate_warhead_smarts_materialization_ready_count",
        "SMARTS_human_review_ready_count",
        "approved_reaction_family_available_count",
        "approved_warhead_rule_available_count",
        "approved_warhead_smarts_count",
        "human_gold_review_completed_count",
        "training_label_approved_count",
        "integrated_covalent_model_module_count",
    ):
        assert manifest[field] == 0
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest[
        "recommended_engineering_next_step"
    ] == (
        "materialize_covapie_current11_pre_reaction_warhead_atom_set_and_"
        "attachment_boundary_proposals_v1"
    )
    for field in (
        "candidate_smarts_materialized",
        "ready_for_candidate_warhead_smarts_materialization",
        "ready_for_SMARTS_review_execution",
        "ready_for_complete_human_review_execution",
        "ready_for_role_proposal_generation",
        "ready_for_minimal_seed_proposal_generation",
        "ready_for_mask_materialization",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
        "role_annotation_materialized",
        "minimal_seed_materialized",
        "mask_materialized",
        "tensor_materialized",
        "model_changed",
        "training_used",
        "warhead_type_model_head_integrated",
        "warhead_type_loss_integrated",
    ):
        assert manifest[field] is False


def test_materialized_outputs_match_builder_and_are_deterministic() -> None:
    first = gate.build_evidence_payloads(REPO_ROOT)
    second = gate.build_evidence_payloads(REPO_ROOT)
    assert first == second == output_payloads()
    manifest = json.loads(first[gate.MANIFEST_FILE])
    assert gate.MANIFEST_FILE not in manifest["output_sha256"]
    for name in gate.OUTPUT_FILES[:-1]:
        assert manifest["output_sha256"][name] == gate.sha256(first[name])


def test_no_timestamp_absolute_path_fake_review_or_smarts_value() -> None:
    payloads = output_payloads()
    for name, payload in payloads.items():
        text = payload.decode()
        assert str(REPO_ROOT) not in text
        assert "/cpfs" not in text
        assert '"timestamp"' not in text
        assert "created_at" not in text
    readiness = csv_rows(payloads[gate.READINESS_FILE])
    assert all(row["candidate_warhead_smarts"] == "" for row in readiness)
    frozen = gate.load_frozen_sources(REPO_ROOT)
    for path in (gate.CLASS_REVIEW_TEMPLATES, gate.SAMPLE_REVIEW_TEMPLATES):
        for row in csv_rows(frozen[path]):
            assert row["reviewer_id"] == ""
            assert row["review_rationale"] == ""
            assert row["review_notes"] == ""


def test_exact10_filesystem_safety_and_git_modes_when_committed() -> None:
    assert len(gate.EXACT10_PATHS) == 10
    for relative in gate.EXACT10_PATHS:
        path = REPO_ROOT / relative
        assert path.is_file()
        assert not path.is_symlink()
        assert stat.S_IMODE(path.stat().st_mode) in {0o644, 0o664}
        assert not path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        assert path.suffix not in {
            ".pt",
            ".ckpt",
            ".pth",
            ".pkl",
            ".lmdb",
            ".tar",
            ".zip",
            ".tgz",
            ".npz",
            ".tmp",
            ".part",
        }
    if gate.validate_execution_boundary_v1(REPO_ROOT) != "pre_commit":
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout.decode().strip()
        output = subprocess.run(
            [
                "git",
                "ls-tree",
                "-r",
                head,
                "--",
                *(path.as_posix() for path in gate.EXACT10_PATHS),
            ],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout.decode().splitlines()
        assert len(output) == 10
        assert all(line.startswith("100644 blob ") for line in output)


def test_import_subprocess_is_silent_and_side_effect_free(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "import covalent_ext."
                "covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1"
            ),
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert result.returncode == 0
    assert result.stdout == result.stderr == b""
    assert before == after


def test_shared_hermetic_exact4_lifecycle_matrix(tmp_path: Path) -> None:
    report = lifecycle_harness.exercise_hermetic_git_lifecycle_matrix(
        REPO_ROOT,
        tmp_path,
        base_commit=gate.BASE_COMMIT,
        formal_commit_subject=gate.FORMAL_COMMIT_SUBJECT,
        exact_paths=gate.EXACT10_PATHS,
    )
    assert report.base_commit == gate.BASE_COMMIT
    assert report.candidate_parent == gate.BASE_COMMIT
    assert report.candidate_subject == gate.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
    assert (
        report.pre_commit.lifecycle,
        report.detached_candidate_post_commit.lifecycle,
        report.formal_main_post_commit_unpushed.lifecycle,
        report.formal_main_post_push.lifecycle,
    ) == (
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    )

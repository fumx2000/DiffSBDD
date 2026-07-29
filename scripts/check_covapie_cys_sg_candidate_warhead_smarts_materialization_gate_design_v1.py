"""Independent checker for the candidate-warhead SMARTS gate design V1."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle_harness


BASE = "77e2d11135da4b3f07ee64411ad3c4634ba60693"
BASE_PARENT = "c0de1003ec1de9dd05e3c4204b458d1f3757d95d"
BASE_TREE = "ed9c6dc692dafe4ed69c528d4f1ea8a90bec4a6c"
BASE_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule review "
    "packages v1"
)
SUBJECT = (
    "add CovaPIE Cys SG candidate warhead SMARTS materialization gate design v1"
)
SCHEMA = "covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/derived/covalent_small" / SCHEMA

SOURCES = {
    "src/covalent_ext/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1.py": "052be7badc65a7eaeec1568e5954a2141a29c08bd0ef85c203e758daaa8b78ec",
    "data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_manifest.json": "677034c0b8822e0b1476e28d00bb8dda5c8e53f5f42fcda790d9c4a81fa8a90b",
    "data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1/covapie_review_package_index.csv": "b62a9d884b08b3b5132f64ca33531497343f208925e3a64eadd7980eee0d341f",
    "data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1/covapie_cys_sg_candidate_class_review_record_templates.csv": "596e218d1d29e16d65edfa1c804b63a528668ffc4083d4089427eda556f37ce1",
    "data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1/covapie_current11_sample_assignment_review_record_templates.csv": "662e95d3403a694da15dedd60dbdb81f98a9e404533693643b3721cd83a18bc1",
    "src/covalent_ext/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1.py": "08b7d7aeacfcd7065e6ea8aa2ae27b2cc4959d476fbb1568a5231307d7e308a1",
    "src/covalent_ext/covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py": "fe6c67940efef89290b2f276f9fb4c39245468181d52b219951a6f9ca7f454aa",
    "data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/covapie_current11_cys_sg_candidate_assignment_authority.csv": "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    "data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/covapie_cys_sg_warhead_type_candidate_class_vocabulary.csv": "e78b83340d9df0afa6bbffd5dc56708ee47023680367f7a8acd9883e7c21602d",
    "data/derived/covalent_small/covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/covapie_cys_sg_reaction_family_registry.csv": "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    "data/derived/covalent_small/covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/covapie_cys_sg_warhead_rule_registry.csv": "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py": "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    "data/derived/covalent_small/covapie_exact9_audited_local_ccd_parent_graph_authority_v1/covapie_exact9_parent_heavy_atom_authority.csv": "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    "data/derived/covalent_small/covapie_exact9_audited_local_ccd_parent_graph_authority_v1/covapie_exact9_parent_heavy_bond_authority.csv": "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    "data/derived/covalent_small/covapie_current11_observed_to_parent_atom_projection_authority_v1/covapie_current11_observed_to_parent_atom_mapping_authority.csv": "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
}
PATHS = {
    "manifest": list(SOURCES)[1],
    "packages": list(SOURCES)[2],
    "class_templates": list(SOURCES)[3],
    "sample_templates": list(SOURCES)[4],
    "assignments": list(SOURCES)[7],
    "classes": list(SOURCES)[8],
    "families": list(SOURCES)[9],
    "rules": list(SOURCES)[10],
    "role_source": list(SOURCES)[11],
    "atoms": list(SOURCES)[12],
    "bonds": list(SOURCES)[13],
    "mappings": list(SOURCES)[14],
}
OUTPUTS = (
    "covapie_candidate_smarts_gate_source_inventory.csv",
    "covapie_candidate_warhead_smarts_contract_registry.csv",
    "covapie_current7_candidate_warhead_smarts_materialization_readiness_matrix.csv",
    "covapie_candidate_warhead_smarts_input_authority_gap_matrix.csv",
    "covapie_candidate_warhead_smarts_materialization_gate_failure_matrix.csv",
    "covapie_candidate_warhead_smarts_materialization_gate_design_manifest.json",
)
EXACT10 = (
    "src/covalent_ext/covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1.py",
    "tests/test_covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1.py",
    "scripts/check_covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1.py",
    "docs/covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1_summary.md",
    *(f"data/derived/covalent_small/{SCHEMA}/{name}" for name in OUTPUTS),
)
WARHEAD_FIELDS = (
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
PROPOSAL_FIELDS = (
    "proposal_version",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "component_parent_graph_sha256",
    "ligand_reactive_parent_atom_id",
    "local_reaction_center_atom_ids",
    "local_reaction_center_bond_ids",
    "proposed_pre_reaction_warhead_atom_ids",
    "proposed_warhead_attachment_atom_id",
    "proposed_nonwarhead_boundary_atom_id",
    "proposed_attachment_boundary_bond_order",
    "required_leaving_group_atom_ids",
    "proposal_method",
    "proposal_status",
    "ambiguity_reasons",
    "source_assignment_record_sha256",
    "proposal_record_sha256",
)
PROPOSAL_TYPE_CONTRACT = {
    field: (
        "exact_int"
        if field == "warhead_type_candidate_class_index_0based"
        else "exact_list_str"
        if field
        in {
            "local_reaction_center_atom_ids",
            "local_reaction_center_bond_ids",
            "proposed_pre_reaction_warhead_atom_ids",
            "required_leaving_group_atom_ids",
            "ambiguity_reasons",
        }
        else "exact_str"
    )
    for field in PROPOSAL_FIELDS
}
PROPOSAL_STATUSES = (
    "not_materialized",
    "auto_exact_candidate",
    "ambiguous_candidate",
    "quarantined",
)
PROPOSAL_ATOM_ID_NAMESPACE = "parent_ccd_atom_id"
PROPOSAL_BOND_ID_ENCODING = (
    "canonical_parent_ccd_endpoint_pair_and_normalized_order_v1"
)
NORMALIZED_BOND_ORDERS = ("aromatic", "double", "single")
CONTRACT_NAMES = (
    "local reaction-center graph is not complete warhead",
    "pre-reaction parent graph is authoritative",
    "known reactive atom must be included",
    "leaving-group evidence uses pre-reaction parent graph",
    "complete warhead atom set is required",
    "warhead atom set must be connected",
    "attachment boundary must be exact-one",
    "attachment atom must be inside warhead set",
    "atom-map policy must be deterministic",
    "bond-order query semantics must be frozen",
    "formal-charge query semantics must be frozen",
    "aromaticity/H/chirality semantics must be frozen",
    "class-wide exact-one match validation is required",
    "candidate SMARTS is not approved SMARTS",
    "SMARTS human review remains independent",
    "downstream role/mask/model/training gates remain closed",
)
GAPS = {
    "complete_warhead_atom_set_authority",
    "attachment_boundary_authority",
    "deterministic_atom_map_policy",
    "bond_order_query_semantics",
    "formal_charge_query_semantics",
    "aromaticity_and_hydrogen_query_semantics",
    "class_wide_exact_one_complete_warhead_match_validation",
}
FAILURE_REASONS = (
    "BASE_source_missing",
    "BASE_source_SHA_mismatch",
    "review_package_transaction_not_succeeded",
    "review_package_materialized_false",
    "class_count_not_7",
    "sample_count_not_11",
    "duplicate_class_identity",
    "duplicate_sample_identity",
    "class_rule_family_link_mismatch",
    "sample_class_rule_family_link_mismatch",
    "canonical_local_graph_JSON_SHA_mismatch",
    "local_center_reactive_flag_missing",
    "target_condition_not_CYS_SG",
    "parent_atom_authority_missing",
    "parent_bond_authority_missing",
    "parent_graph_SHA_mismatch",
    "reactive_parent_atom_mapping_missing",
    "local_graph_incorrectly_declared_complete_warhead",
    "class_support_list_mismatch",
    "contract_count_not_16",
    "readiness_row_count_or_order_mismatch",
    "unresolved_authority_incorrectly_declared_available",
    "candidate_SMARTS_prefilled",
    "candidate_SMARTS_status_prematurely_advanced",
    "SMARTS_materialization_readiness_prematurely_opened",
    "SMARTS_review_readiness_prematurely_opened",
    "approved_rule_prematurely_opened",
    "downstream_readiness_opened",
    "partial_materialization_attempted",
    "execution_boundary_crossed",
    "leaving_group_rule_contract_mismatch",
    "parent_leaving_group_evidence_mismatch",
)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(
            "git failed: " + " ".join(args) + ": " + result.stderr.decode()
        )
    return result


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def base_payload(path: str) -> bytes:
    result = git("show", f"{BASE}:{path}", check=False)
    assert result.returncode == 0 and result.stdout, f"BASE source missing: {path}"
    assert digest(result.stdout) == SOURCES[path], f"BASE source SHA mismatch: {path}"
    return result.stdout


def rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode())))


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_bond_id(atom_1: str, atom_2: str, order: str) -> str:
    assert type(atom_1) is type(atom_2) is type(order) is str
    assert atom_1 and atom_2 and atom_1 != atom_2 and "|" not in atom_1 + atom_2
    assert order in NORMALIZED_BOND_ORDERS
    low, high = sorted((atom_1, atom_2), key=lambda value: value.encode("utf-8"))
    return f"{low}|{high}|{order}"


def independent_proposal_digest(record: dict[str, Any]) -> str:
    assert tuple(record) == PROPOSAL_FIELDS
    for field, contract in PROPOSAL_TYPE_CONTRACT.items():
        value = record[field]
        if contract == "exact_int":
            assert type(value) is int
        elif contract == "exact_list_str":
            assert type(value) is list
            assert all(type(item) is str for item in value)
        else:
            assert contract == "exact_str" and type(value) is str
    payload = {
        field: record[field]
        for field in PROPOSAL_FIELDS
        if field != "proposal_record_sha256"
    }
    assert len(payload) == 21
    return digest(canonical(payload).encode("utf-8"))


def literal_tuple(source: bytes, name: str) -> tuple[str, ...]:
    tree = ast.parse(source.decode())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            assert type(value) is tuple
            return value
    raise AssertionError(f"missing literal tuple: {name}")


def lifecycle() -> str:
    identity = git("show", "-s", "--format=%H%n%P%n%T%n%s", BASE).stdout.decode().splitlines()
    assert identity == [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    head = git("rev-parse", "HEAD").stdout.decode().strip()
    if head == BASE:
        return "pre_commit"
    raw = git("cat-file", "commit", head).stdout
    headers, separator, message = raw.partition(b"\n\n")
    assert separator
    parents = [
        line[7:].decode() for line in headers.splitlines() if line.startswith(b"parent ")
    ]
    assert parents == [BASE]
    subject, newline, body = message.partition(b"\n")
    assert newline and subject.decode() == SUBJECT and body == b""
    changed = {
        value.decode()
        for value in git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).stdout.split(b"\0")
        if value
    }
    assert changed == set(EXACT10)
    tree = git("ls-tree", "-r", "-z", head, "--", *EXACT10).stdout.split(b"\0")
    tree = [entry for entry in tree if entry]
    assert len(tree) == 10 and all(entry.startswith(b"100644 blob ") for entry in tree)
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch.returncode:
        return "detached_candidate_post_commit"
    assert branch.stdout.decode().strip() == "main"
    origin = git("rev-parse", "refs/remotes/origin/main").stdout.decode().strip()
    if origin == BASE:
        return "formal_main_post_commit_unpushed"
    assert origin == head
    return "formal_main_post_push"


def main() -> int:
    state = lifecycle()
    source_payloads = {path: base_payload(path) for path in SOURCES}
    manifest = json.loads(source_payloads[PATHS["manifest"]])
    packages = rows(source_payloads[PATHS["packages"]])
    class_templates = rows(source_payloads[PATHS["class_templates"]])
    sample_templates = rows(source_payloads[PATHS["sample_templates"]])
    assignments = rows(source_payloads[PATHS["assignments"]])
    classes = rows(source_payloads[PATHS["classes"]])
    families = rows(source_payloads[PATHS["families"]])
    rules = rows(source_payloads[PATHS["rules"]])
    atoms = rows(source_payloads[PATHS["atoms"]])
    bonds = rows(source_payloads[PATHS["bonds"]])
    mappings = rows(source_payloads[PATHS["mappings"]])

    assert manifest["transaction_succeeded"] is True
    assert manifest["review_package_materialized"] is True
    assert manifest["ready_for_family_identity_review_execution"] is True
    assert manifest["ready_for_rule_topology_review_execution"] is True
    assert manifest["ready_for_sample_assignment_review_execution"] is True
    assert manifest["ready_for_SMARTS_review_execution"] is False
    assert manifest["human_review_execution_completed"] is False
    assert len(packages) == 18 and all(
        row["package_item_materialized"] == row["verified"] == "true"
        for row in packages
    )
    assert len(class_templates) == len(classes) == len(families) == len(rules) == 7
    assert len(sample_templates) == len(assignments) == 11
    assert all(
        row["reaction_family_identity_review_decision"] == "not_reviewed"
        and row["warhead_rule_topology_review_decision"] == "not_reviewed"
        and row["warhead_smarts_review_status"] == "not_materialized"
        and row["candidate_warhead_smarts"] == ""
        and row["reviewer_id"] == row["review_rationale"] == row["review_notes"] == ""
        and row["review_record_sha256"] == ""
        for row in class_templates
    )
    assert all(
        row["sample_assignment_review_decision"] == "not_reviewed"
        and row["reviewer_id"] == row["review_rationale"] == row["review_notes"] == ""
        and row["review_record_sha256"] == ""
        for row in sample_templates
    )
    assert literal_tuple(source_payloads[PATHS["role_source"]], "WARHEAD_RULE_FIELDS") == WARHEAD_FIELDS

    class_by_id = {row["warhead_type_candidate_class_id"]: row for row in classes}
    family_by_id = {row["reaction_family_id"]: row for row in families}
    rule_by_id = {row["warhead_rule_id"]: row for row in rules}
    assert len(class_by_id) == len(family_by_id) == len(rule_by_id) == 7
    assert [int(row["warhead_type_candidate_class_index_0based"]) for row in classes] == list(range(7))
    leaving_specs_by_rule: dict[str, tuple[tuple[str, str], ...]] = {}
    for cls in classes:
        rule = rule_by_id[cls["warhead_rule_id"]]
        assert rule["reaction_family_id"] == cls["reaction_family_id"]
        assert cls["reaction_family_id"] in family_by_id
        local = json.loads(rule["canonical_local_graph_rule_json"])
        local_sha = digest(canonical(local).encode())
        assert local_sha == rule["canonical_local_graph_rule_sha256"]
        assert local_sha == cls["canonical_local_graph_rule_sha256"]
        assert local["center_atom"]["reactive"] is True
        assert local["selected_signature_radius"] == 1
        assert local["rule_kind"] == "canonical_local_graph_exact_match_v1"
        assert local["target_condition"]["residue"] == "CYS"
        assert local["target_condition"]["residue_atom"] == "SG"
        assert rule["approved_warhead_smarts"] == ""
        assert rule["approved"] == "false"
        delta = local["reaction_delta"]
        assert type(delta) is dict
        assert set(delta) == {
            "leaving_group_count",
            "leaving_group_elements",
            "reaction_delta_class",
        }
        count = delta["leaving_group_count"]
        elements = delta["leaving_group_elements"]
        assert type(count) is int and count >= 0
        assert type(elements) is list
        assert all(type(value) is str and value.strip() for value in elements)
        assert elements == sorted(elements) and len(elements) == len(set(elements))
        assert type(delta["reaction_delta_class"]) is str
        assert delta["reaction_delta_class"].strip()
        assert rule["required_leaving_group_count"].isdigit()
        assert int(rule["required_leaving_group_count"]) == count
        csv_elements = (
            []
            if rule["allowed_leaving_group_elements"] == ""
            else rule["allowed_leaving_group_elements"].split(";")
        )
        assert csv_elements == sorted(csv_elements)
        assert len(csv_elements) == len(set(csv_elements))
        assert csv_elements == elements
        assert rule["required_reaction_delta_class"] == delta["reaction_delta_class"]
        leaving_atoms = [
            atom
            for atom in local["local_atoms"]
            if atom["is_leaving_group"] is True
        ]
        assert len(leaving_atoms) == count
        assert sorted(atom["element"] for atom in leaving_atoms) == elements
        center_id = local["center_atom"]["canonical_local_atom_id"]
        specs = []
        for atom in leaving_atoms:
            assert atom["is_retained_observed"] is False
            matching = [
                bond
                for bond in local["local_bonds"]
                if {
                    bond["canonical_endpoint_1"],
                    bond["canonical_endpoint_2"],
                }
                == {center_id, atom["canonical_local_atom_id"]}
            ]
            assert len(matching) == 1
            bond = matching[0]
            assert (
                bond["projected_disposition"]
                == "verified_leaving_group_endpoint_missing"
            )
            assert bond["normalized_bond_order"] in NORMALIZED_BOND_ORDERS
            specs.append((atom["element"], bond["normalized_bond_order"]))
        missing_bonds = [
            bond
            for bond in local["local_bonds"]
            if bond["projected_disposition"]
            == "verified_leaving_group_endpoint_missing"
        ]
        assert len(missing_bonds) == count
        if count == 0:
            assert elements == [] and leaving_atoms == [] and missing_bonds == []
        leaving_specs_by_rule[rule["warhead_rule_id"]] = tuple(sorted(specs))

    atom_sha: dict[str, set[str]] = defaultdict(set)
    bond_sha: dict[str, set[str]] = defaultdict(set)
    reactive: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in atoms:
        assert row["verified"] == "true"
        atom_sha[row["ligand_comp_id"]].add(row["component_parent_graph_sha256"])
    for row in bonds:
        assert row["verified"] == "true"
        bond_sha[row["ligand_comp_id"]].add(row["component_parent_graph_sha256"])
    for row in mappings:
        if row["reactive_ligand_atom"] == "true":
            assert row["verified"] == "true"
            reactive[row["sample_index_row_id"]].append(row)
    support: dict[str, list[dict[str, str]]] = defaultdict(list)
    reconstructed_leaving_evidence: dict[
        str, tuple[str, tuple[str, ...], tuple[str, ...]]
    ] = {}
    assert len({row["sample_index_row_id"] for row in assignments}) == 11
    for assignment in assignments:
        cls = class_by_id[assignment["warhead_type_candidate_class_id"]]
        assert assignment["candidate_reaction_family_id"] == cls["reaction_family_id"]
        assert assignment["candidate_warhead_rule_id"] == cls["warhead_rule_id"]
        graph_sha = assignment["component_parent_graph_sha256"]
        assert atom_sha[assignment["ligand_comp_id"]] == {graph_sha}
        assert bond_sha[assignment["ligand_comp_id"]] == {graph_sha}
        match = reactive[assignment["sample_index_row_id"]]
        assert len(match) == 1
        assert match[0]["parent_ccd_atom_id"] == assignment["ligand_reactive_parent_ccd_atom_id"]
        assert match[0]["component_parent_graph_sha256"] == graph_sha
        reactive_id = match[0]["parent_ccd_atom_id"]
        component_atoms = [
            row
            for row in atoms
            if row["ligand_comp_id"] == assignment["ligand_comp_id"]
            and row["component_parent_graph_sha256"] == graph_sha
            and row["verified"] == "true"
        ]
        atom_by_id = {row["ccd_atom_id"]: row for row in component_atoms}
        assert len(atom_by_id) == len(component_atoms)
        assert reactive_id in atom_by_id
        local = json.loads(
            rule_by_id[cls["warhead_rule_id"]]["canonical_local_graph_rule_json"]
        )
        assert atom_by_id[reactive_id]["ccd_type_symbol"] == local["center_atom"]["element"]
        assert int(atom_by_id[reactive_id]["ccd_formal_charge"]) == local["center_atom"]["formal_charge"]
        adjacent = [
            row
            for row in bonds
            if row["ligand_comp_id"] == assignment["ligand_comp_id"]
            and row["component_parent_graph_sha256"] == graph_sha
            and row["verified"] == "true"
            and reactive_id
            in {row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]}
        ]
        for bond in adjacent:
            other = (
                bond["parent_ccd_atom_id_2"]
                if bond["parent_ccd_atom_id_1"] == reactive_id
                else bond["parent_ccd_atom_id_1"]
            )
            assert other in atom_by_id
        found_atoms = []
        found_bonds = []
        for element, order in leaving_specs_by_rule[cls["warhead_rule_id"]]:
            candidates = []
            for bond in adjacent:
                other = (
                    bond["parent_ccd_atom_id_2"]
                    if bond["parent_ccd_atom_id_1"] == reactive_id
                    else bond["parent_ccd_atom_id_1"]
                )
                if (
                    atom_by_id[other]["ccd_type_symbol"] == element
                    and bond["normalized_bond_order"] == order
                ):
                    candidates.append((other, bond))
            assert len(candidates) == 1
            other, bond = candidates[0]
            assert other not in found_atoms
            found_atoms.append(other)
            found_bonds.append(
                canonical_bond_id(
                    reactive_id, other, bond["normalized_bond_order"]
                )
            )
        assert len(found_atoms) == len(
            leaving_specs_by_rule[cls["warhead_rule_id"]]
        )
        reconstructed_leaving_evidence[assignment["sample_index_row_id"]] = (
            reactive_id,
            tuple(sorted(found_atoms, key=lambda value: value.encode("utf-8"))),
            tuple(sorted(found_bonds, key=lambda value: value.encode("utf-8"))),
        )
        support[assignment["warhead_type_candidate_class_id"]].append(assignment)
    for cls in classes:
        matches = support[cls["warhead_type_candidate_class_id"]]
        assert len(matches) == int(cls["Current11_match_count"])
        assert len({row["ligand_comp_id"] for row in matches}) == int(
            cls["Current11_unique_component_count"]
        )
    assert sum(not specs for specs in leaving_specs_by_rule.values()) == 6
    assert sum(bool(specs) for specs in leaving_specs_by_rule.values()) == 1
    assert reconstructed_leaving_evidence["CYS_SG_SAMPLE_INDEX_000005"] == (
        "CM",
        ("F1",),
        ("CM|F1|single",),
    )

    output = {name: (OUT / name).read_bytes() for name in OUTPUTS}
    inventory = rows(output[OUTPUTS[0]])
    contracts = rows(output[OUTPUTS[1]])
    readiness = rows(output[OUTPUTS[2]])
    gaps = rows(output[OUTPUTS[3]])
    failures = rows(output[OUTPUTS[4]])
    result_manifest = json.loads(output[OUTPUTS[5]])
    assert len(inventory) == 15
    assert [row["source_path"] for row in inventory] == list(SOURCES)
    assert all(row["BASE_SHA256"] == SOURCES[row["source_path"]] for row in inventory)
    assert len(contracts) == 16
    assert [row["contract_id"] for row in contracts] == [
        f"SMARTS_GATE_{index:03d}" for index in range(1, 17)
    ]
    assert [row["semantic_name"] for row in contracts] == list(CONTRACT_NAMES)
    assert all(row["fails_closed"] == row["verified"] == "true" for row in contracts)

    assert len(readiness) == 7
    assert [int(row["warhead_type_candidate_class_index_0based"]) for row in readiness] == list(range(7))
    for row in readiness:
        matches = sorted(
            support[row["warhead_type_candidate_class_id"]],
            key=lambda value: value["sample_index_row_id"],
        )
        assert row["supporting_sample_ids"].split(";") == [
            value["sample_index_row_id"] for value in matches
        ]
        assert row["supporting_component_ids"].split(";") == sorted(
            {value["ligand_comp_id"] for value in matches}
        )
        for field in (
            "local_reaction_center_rule_available",
            "parent_heavy_atom_authority_available",
            "parent_heavy_bond_authority_available",
            "parent_graph_SHA_verified",
            "reactive_parent_atom_mapping_available",
            "pre_reaction_leaving_group_semantics_available",
            "ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization",
            "verified",
        ):
            assert row[field] == "true"
        for field in (
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
        ):
            assert row[field] == "false"
        assert row["candidate_warhead_smarts"] == ""
        assert row["candidate_warhead_smarts_status"] == "not_materialized"

    assert len(gaps) == 49
    assert {row["missing_authority"] for row in gaps} == GAPS
    assert len({row["warhead_type_candidate_class_id"] for row in gaps}) == 7
    assert all(
        row["would_block_atom_set_proposal"] == "false"
        and row["would_block_SMARTS_materialization"] == "true"
        and row["would_block_SMARTS_review"] == "true"
        and row["verified"] == "true"
        for row in gaps
    )
    aromaticity_gap = [
        row
        for row in gaps
        if row["missing_authority"]
        == "aromaticity_and_hydrogen_query_semantics"
    ]
    assert len(aromaticity_gap) == 7
    assert all(
        row["current_evidence"]
        == (
            "normalized parent bond authority includes aromatic bond disposition, "
            "while atom-level aromaticity/H/chirality SMARTS query policy remains "
            "unfrozen"
        )
        for row in aromaticity_gap
    )
    assert len(failures) == 32
    assert [row["expected_reason"] for row in failures] == list(FAILURE_REASONS)
    assert len({row["mutation_signature"] for row in failures}) == 32
    assert all(
        row["expected_reason"] in row["observed_reasons"].split(";")
        and row["expected_reason_verified"] == "true"
        and row["fails_closed"] == "true"
        and row["contract_registry_row_count"] == "0"
        and row["readiness_matrix_row_count"] == "0"
        and row["authority_gap_row_count"] == "0"
        and row["proposal_materialization_ready"] == "false"
        and row["SMARTS_materialization_ready"] == "false"
        and row["role_proposal_generation_ready"] == "false"
        and row["mask_materialization_ready"] == "false"
        and row["model_integration_ready"] == "false"
        and row["training_ready"] == "false"
        and row["verified"] == "true"
        for row in failures
    )

    assert result_manifest["schema_version"] == SCHEMA
    assert result_manifest["transaction_succeeded"] is True
    assert result_manifest["source_count"] == 15
    assert result_manifest["contract_count"] == 16
    assert result_manifest["candidate_class_count"] == 7
    assert result_manifest["current11_sample_count"] == 11
    assert result_manifest["candidate_smarts_materialized"] is False
    assert result_manifest["ready_for_candidate_warhead_smarts_materialization"] is False
    assert result_manifest["ready_for_SMARTS_review_execution"] is False
    assert result_manifest["ready_for_role_proposal_generation"] is False
    assert result_manifest["ready_for_mask_materialization"] is False
    assert result_manifest["ready_for_model_integration"] is False
    assert result_manifest["ready_for_training"] is False
    assert result_manifest["integrated_covalent_model_module_count"] == 0
    assert result_manifest["planned_covalent_model_module_count"] == 5
    assert result_manifest["proposal_record_count"] == 0
    assert result_manifest["inherited_warhead_rule_fields"] == list(WARHEAD_FIELDS)
    assert result_manifest["proposal_fields"] == list(PROPOSAL_FIELDS)
    assert result_manifest["proposal_statuses"] == list(PROPOSAL_STATUSES)
    assert (
        result_manifest["proposal_atom_id_namespace"]
        == PROPOSAL_ATOM_ID_NAMESPACE
    )
    assert result_manifest["proposal_bond_id_encoding"] == PROPOSAL_BOND_ID_ENCODING
    assert result_manifest["proposal_field_type_contract"] == PROPOSAL_TYPE_CONTRACT
    assert result_manifest["proposal_hash_excluded_field"] == "proposal_record_sha256"
    assert result_manifest["proposal_hash_canonical_json_contract"] == {
        "sort_keys": True,
        "separators": [",", ":"],
        "ensure_ascii": True,
        "encoding": "UTF-8",
        "excluded_field": "proposal_record_sha256",
        "included_field_count": 21,
    }
    assert result_manifest["pre_reaction_leaving_group_semantics_available_count"] == 7
    assert result_manifest["leaving_group_class_count"] == 1
    assert result_manifest["zero_leaving_group_class_count"] == 6
    assert result_manifest["required_leaving_group_total_atom_count"] == 1
    assert result_manifest["failure_mutation_count"] == 32
    synthetic_proposal = {
        field: (
            0
            if contract == "exact_int"
            else []
            if contract == "exact_list_str"
            else field
        )
        for field, contract in PROPOSAL_TYPE_CONTRACT.items()
    }
    proposal_digest = independent_proposal_digest(synthetic_proposal)
    self_changed = dict(synthetic_proposal)
    self_changed["proposal_record_sha256"] = "f" * 64
    assert independent_proposal_digest(self_changed) == proposal_digest
    for field in PROPOSAL_FIELDS:
        if field == "proposal_record_sha256":
            continue
        changed = dict(synthetic_proposal)
        value = changed[field]
        changed[field] = (
            value + 1
            if type(value) is int
            else [*value, "variant"]
            if type(value) is list
            else value + "_variant"
        )
        assert independent_proposal_digest(changed) != proposal_digest
    assert result_manifest["output_sha256"] == {
        name: digest(output[name]) for name in OUTPUTS[:-1]
    }
    assert OUTPUTS[-1] not in result_manifest["output_sha256"]
    text = b"".join(output.values()).decode()
    assert str(ROOT) not in text and "/cpfs" not in text
    assert '"timestamp"' not in text and "created_at" not in text
    exact4 = lifecycle_harness.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        Path(tempfile.gettempdir()).resolve(),
        base_commit=BASE,
        formal_commit_subject=SUBJECT,
        exact_paths=tuple(Path(path) for path in EXACT10),
    )
    assert exact4.cleanup_verified is True
    assert exact4.candidate_parent == BASE
    assert exact4.candidate_subject == SUBJECT
    assert exact4.exact_path_count == 10
    assert (
        exact4.pre_commit.lifecycle,
        exact4.detached_candidate_post_commit.lifecycle,
        exact4.formal_main_post_commit_unpushed.lifecycle,
        exact4.formal_main_post_push.lifecycle,
    ) == (
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    )
    print(
        "candidate_smarts_gate_design_v1_ok "
        f"lifecycle={state} sources=15 contracts=16 classes=7 samples=11 "
        "leaving_semantics=7 proposal_ready=7 smarts_ready=0 failures=32 "
        "hermetic_exact4=4 cleanup_verified=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

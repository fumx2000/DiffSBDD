"""Materialize Current11 pre-reaction warhead atom-set/boundary proposals.

This module is intentionally proposal-only.  It neither constructs SMARTS nor
records human review decisions.  Every formal input is read from the frozen
BASE commit with ``git show``.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter, deque
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_"
    "proposals_v1"
)
PROPOSAL_VERSION = (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_"
    "proposal_v1"
)
PROPOSAL_METHOD = "exhaustive_exact_one_boundary_bridge_cut_enumeration_v1"
ENUMERATION_VERSION = (
    "covapie_current11_exact_one_boundary_bridge_candidate_enumeration_v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 pre-reaction warhead atom set and attachment "
    "boundary proposals v1"
)

BASE_COMMIT = "5cac27027c824cd38bad3479a59f586b2714142c"
BASE_PARENT = "77e2d11135da4b3f07ee64411ad3c4634ba60693"
BASE_TREE = "6837d6f4db8808eb784a80fc853c21ae34c86015"
BASE_SUBJECT = (
    "add CovaPIE Cys SG candidate warhead SMARTS materialization gate design v1"
)

OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
SOURCE_FILE = "covapie_warhead_proposal_materialization_source_inventory.csv"
PROPOSAL_FILE = (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_"
    "proposals.csv"
)
ENUMERATION_FILE = (
    "covapie_current11_exact_one_boundary_bridge_candidate_enumeration.csv"
)
READINESS_FILE = "covapie_current11_warhead_proposal_readiness_matrix.csv"
FAILURE_FILE = "covapie_warhead_proposal_materialization_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_"
    "proposals_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    PROPOSAL_FILE,
    ENUMERATION_FILE,
    READINESS_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)

PRODUCTION_PATH = Path("src/covalent_ext") / f"{SCHEMA_VERSION}.py"
TEST_PATH = Path("tests") / f"test_{SCHEMA_VERSION}.py"
CHECKER_PATH = Path("scripts") / f"check_{SCHEMA_VERSION}.py"
SUMMARY_PATH = Path("docs") / f"{SCHEMA_VERSION}_summary.md"
EXACT10_PATHS = (
    PRODUCTION_PATH,
    TEST_PATH,
    CHECKER_PATH,
    SUMMARY_PATH,
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)

DESIGN_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1.py"
)
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1"
)
DESIGN_MANIFEST = DESIGN_ROOT / (
    "covapie_candidate_warhead_smarts_materialization_gate_design_manifest.json"
)
DESIGN_READINESS = DESIGN_ROOT / (
    "covapie_current7_candidate_warhead_smarts_materialization_readiness_matrix.csv"
)
DESIGN_CONTRACT = DESIGN_ROOT / (
    "covapie_candidate_warhead_smarts_contract_registry.csv"
)
DESIGN_GAP = DESIGN_ROOT / (
    "covapie_candidate_warhead_smarts_input_authority_gap_matrix.csv"
)
DESIGN_FAILURE = DESIGN_ROOT / (
    "covapie_candidate_warhead_smarts_materialization_gate_failure_matrix.csv"
)
ASSIGNMENT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1"
)
ASSIGNMENTS = ASSIGNMENT_ROOT / (
    "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
CLASSES = ASSIGNMENT_ROOT / (
    "covapie_cys_sg_warhead_type_candidate_class_vocabulary.csv"
)
RULES = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/"
    "covapie_cys_sg_warhead_rule_registry.csv"
)
PARENT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1"
)
PARENT_ATOMS = PARENT_ROOT / "covapie_exact9_parent_heavy_atom_authority.csv"
PARENT_BONDS = PARENT_ROOT / "covapie_exact9_parent_heavy_bond_authority.csv"
MAPPINGS = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
    "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)
REVIEW_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1"
)
REVIEW_MANIFEST = REVIEW_ROOT / (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_"
    "manifest.json"
)
REVIEW_INDEX = REVIEW_ROOT / "covapie_review_package_index.csv"
CLASS_TEMPLATES = REVIEW_ROOT / (
    "covapie_cys_sg_candidate_class_review_record_templates.csv"
)
SAMPLE_TEMPLATES = REVIEW_ROOT / (
    "covapie_current11_sample_assignment_review_record_templates.csv"
)

FROZEN_BASE_SHA256 = {
    DESIGN_SOURCE: "5e57b0179b4f72782ea91b1945749121b32feaa1a9858d894c70bebca3f3c169",
    DESIGN_MANIFEST: "776b5097f6dafc4efee48178b3046ccce19c1bb084bc8be876b558ad7a184d7b",
    DESIGN_READINESS: "f4ee281ae0bcc68563c83f20e110fa0bd5ea35567590cb9c8e9045b3374596c8",
    DESIGN_CONTRACT: "ccda94bdd2b94bf3b0ac1cef842e05f01166f89c3749eb2c9e123cad3c6b6efa",
    DESIGN_GAP: "db146ef364acdb8d922ada27739caad646ff731b465fd1ba27a2ddadd35c20ec",
    DESIGN_FAILURE: "5376fff50533003188b028e4e7e4343cda883bc358ed60c69f00998225af0609",
    ASSIGNMENTS: "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    CLASSES: "e78b83340d9df0afa6bbffd5dc56708ee47023680367f7a8acd9883e7c21602d",
    RULES: "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    PARENT_ATOMS: "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    PARENT_BONDS: "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    MAPPINGS: "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    REVIEW_MANIFEST: "677034c0b8822e0b1476e28d00bb8dda5c8e53f5f42fcda790d9c4a81fa8a90b",
    REVIEW_INDEX: "b62a9d884b08b3b5132f64ca33531497343f208925e3a64eadd7980eee0d341f",
    CLASS_TEMPLATES: "596e218d1d29e16d65edfa1c804b63a528668ffc4083d4089427eda556f37ce1",
    SAMPLE_TEMPLATES: "662e95d3403a694da15dedd60dbdb81f98a9e404533693643b3721cd83a18bc1",
}
SOURCE_PATHS = tuple(FROZEN_BASE_SHA256)

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
PROPOSAL_HASH_EXCLUDED_FIELD = "proposal_record_sha256"
PARENT_NORMALIZED_BOND_ORDERS = ("aromatic", "double", "single")
PROPOSAL_FIELD_TYPE_CONTRACT = {
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

ENUMERATION_FIELDS = (
    "enumeration_version",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "component_parent_graph_sha256",
    "bridge_candidate_index_0based",
    "boundary_bond_id",
    "warhead_side_atom_ids",
    "warhead_side_atom_count",
    "nonwarhead_side_atom_count",
    "contains_local_reaction_center",
    "contains_required_leaving_groups",
    "warhead_side_connected",
    "exact_one_boundary_verified",
    "proper_subset",
    "candidate_admitted",
    "blocking_reasons",
    "bridge_candidate_record_sha256",
)
ENUMERATION_INT_FIELDS = {
    "warhead_type_candidate_class_index_0based",
    "bridge_candidate_index_0based",
    "warhead_side_atom_count",
    "nonwarhead_side_atom_count",
}
ENUMERATION_BOOL_FIELDS = {
    "contains_local_reaction_center",
    "contains_required_leaving_groups",
    "warhead_side_connected",
    "exact_one_boundary_verified",
    "proper_subset",
    "candidate_admitted",
}

SOURCE_COLUMNS = (
    "source_path",
    "BASE_SHA256",
    "source_row_count",
    "Current11_coverage",
    "fields_actually_used",
    "authority_class",
    "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "component_parent_graph_sha256",
    "ligand_reactive_parent_atom_id",
    "local_reaction_center_atom_count",
    "required_leaving_group_atom_count",
    "parent_bridge_count",
    "admitted_boundary_candidate_count",
    "proposal_status",
    "proposal_record_sha256",
    "proposal_materialized",
    "ready_for_proposal_human_review",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available",
    "ready_for_candidate_warhead_smarts_materialization",
    "ready_for_SMARTS_review_execution",
    "ready_for_role_proposal_generation",
    "ready_for_mask_materialization",
    "ready_for_model_integration",
    "ready_for_training",
    "blocking_reasons",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case",
    "mutation_signature",
    "mutated_field",
    "mutated_value_json",
    "expected_reason",
    "observed_reasons",
    "expected_reason_verified",
    "fails_closed",
    "proposal_row_count",
    "bridge_enumeration_row_count",
    "readiness_row_count",
    "SMARTS_ready",
    "role_ready",
    "mask_ready",
    "model_ready",
    "training_ready",
    "verified",
)
ASSIGNMENT_HASH_FIELDS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "target_residue_name",
    "target_residue_number",
    "target_residue_atom_name",
    "ligand_reactive_atom_name",
    "ligand_reactive_atom_element",
    "ligand_reactive_parent_ccd_atom_id",
    "component_parent_graph_sha256",
    "observed_graph_sha256",
    "radius_1_signature_sha256",
    "candidate_reaction_family_id",
    "candidate_warhead_rule_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "assignment_status",
    "review_status",
    "training_label_status",
)


@dataclass(frozen=True)
class ProposalScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    predecessor_transaction_succeeded: bool = True
    predecessor_proposal_readiness_count: int = 7
    class_count: int = 7
    sample_count: int = 11
    duplicate_class_identity: bool = False
    duplicate_sample_identity: bool = False
    class_rule_family_links_match: bool = True
    sample_class_rule_family_links_match: bool = True
    parent_atom_authority_present: bool = True
    parent_bond_authority_present: bool = True
    parent_graph_sha_matches: bool = True
    duplicate_parent_atom_id: bool = False
    duplicate_parent_bond: bool = False
    parent_bond_endpoint_present: bool = True
    parent_graph_connected: bool = True
    reactive_parent_mapping_exact_one: bool = True
    local_graph_json_sha_matches: bool = True
    local_reaction_center_degree_matches: bool = True
    local_neighbor_multiset_matches: bool = True
    leaving_group_evidence_matches: bool = True
    bridge_enumeration_deterministic: bool = True
    bridge_candidate_indices_contiguous: bool = True
    candidate_contains_local_center: bool = True
    candidate_contains_leaving_groups: bool = True
    candidate_warhead_side_connected: bool = True
    candidate_boundary_exact_one: bool = True
    auto_exact_candidate_count_valid: bool = True
    ambiguous_candidate_count_valid: bool = True
    quarantined_candidate_count_valid: bool = True
    unresolved_proposal_fields_blank: bool = True
    proposal_record_valid: bool = True
    bridge_candidate_record_valid: bool = True
    partial_materialization_attempted: bool = False
    downstream_readiness_opened: bool = False


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_source_missing"),
    ("BASE source SHA mismatch", "base_source_sha_matches", False, "BASE_source_SHA_mismatch"),
    ("predecessor transaction not succeeded", "predecessor_transaction_succeeded", False, "predecessor_transaction_not_succeeded"),
    ("predecessor proposal readiness not 7", "predecessor_proposal_readiness_count", 6, "predecessor_proposal_readiness_not_7"),
    ("class count not 7", "class_count", 6, "class_count_not_7"),
    ("sample count not 11", "sample_count", 10, "sample_count_not_11"),
    ("duplicate class identity", "duplicate_class_identity", True, "duplicate_class_identity"),
    ("duplicate sample identity", "duplicate_sample_identity", True, "duplicate_sample_identity"),
    ("class-rule-family link mismatch", "class_rule_family_links_match", False, "class_rule_family_link_mismatch"),
    ("sample-class-rule-family link mismatch", "sample_class_rule_family_links_match", False, "sample_class_rule_family_link_mismatch"),
    ("parent atom authority missing", "parent_atom_authority_present", False, "parent_atom_authority_missing"),
    ("parent bond authority missing", "parent_bond_authority_present", False, "parent_bond_authority_missing"),
    ("parent graph SHA mismatch", "parent_graph_sha_matches", False, "parent_graph_SHA_mismatch"),
    ("duplicate parent atom ID", "duplicate_parent_atom_id", True, "duplicate_parent_atom_ID"),
    ("duplicate parent bond", "duplicate_parent_bond", True, "duplicate_parent_bond"),
    ("parent bond endpoint missing", "parent_bond_endpoint_present", False, "parent_bond_endpoint_missing"),
    ("parent graph disconnected", "parent_graph_connected", False, "parent_graph_disconnected"),
    ("reactive parent mapping not exact-one", "reactive_parent_mapping_exact_one", False, "reactive_parent_mapping_not_exact_one"),
    ("local graph JSON/SHA mismatch", "local_graph_json_sha_matches", False, "local_graph_JSON_SHA_mismatch"),
    ("local reaction-center degree mismatch", "local_reaction_center_degree_matches", False, "local_reaction_center_degree_mismatch"),
    ("local neighbor multiset mismatch", "local_neighbor_multiset_matches", False, "local_neighbor_multiset_mismatch"),
    ("leaving-group evidence mismatch", "leaving_group_evidence_matches", False, "leaving_group_evidence_mismatch"),
    ("bridge enumeration nondeterministic", "bridge_enumeration_deterministic", False, "bridge_enumeration_nondeterministic"),
    ("bridge candidate index non-contiguous", "bridge_candidate_indices_contiguous", False, "bridge_candidate_index_non_contiguous"),
    ("candidate missing local reaction center", "candidate_contains_local_center", False, "candidate_missing_local_reaction_center"),
    ("candidate missing required leaving group", "candidate_contains_leaving_groups", False, "candidate_missing_required_leaving_group"),
    ("candidate warhead side disconnected", "candidate_warhead_side_connected", False, "candidate_warhead_side_disconnected"),
    ("candidate boundary not exact-one", "candidate_boundary_exact_one", False, "candidate_boundary_not_exact_one"),
    ("auto-exact status with candidate count not 1", "auto_exact_candidate_count_valid", False, "auto_exact_status_candidate_count_not_1"),
    ("ambiguous status with candidate count <=1", "ambiguous_candidate_count_valid", False, "ambiguous_status_candidate_count_not_multiple"),
    ("quarantined status with candidate count not 0", "quarantined_candidate_count_valid", False, "quarantined_status_candidate_count_not_0"),
    ("ambiguous/quarantined proposal fields prefilled", "unresolved_proposal_fields_blank", False, "ambiguous_or_quarantined_proposal_fields_prefilled"),
    ("proposal field/type/hash invalid", "proposal_record_valid", False, "proposal_field_type_or_hash_invalid"),
    ("bridge candidate field/type/hash invalid", "bridge_candidate_record_valid", False, "bridge_candidate_field_type_or_hash_invalid"),
    ("partial materialization attempted", "partial_materialization_attempted", True, "partial_materialization_attempted"),
    ("downstream readiness prematurely opened", "downstream_readiness_opened", True, "downstream_readiness_prematurely_opened"),
)


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    proposal_rows: tuple[Mapping[str, Any], ...]
    enumeration_rows: tuple[Mapping[str, Any], ...]
    readiness_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


def _git(
    repo_root: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(
            "git_command_failed:"
            + " ".join(arguments)
            + ":"
            + result.stderr.decode("utf-8", "replace")
        )
    return result


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _utf8_sorted(values: Iterable[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def canonical_parent_bond_id(left: str, right: str, order: str) -> str:
    if (
        type(left) is not str
        or type(right) is not str
        or not left
        or not right
        or left == right
        or "|" in left
        or "|" in right
        or order not in PARENT_NORMALIZED_BOND_ORDERS
    ):
        raise ValueError("canonical_parent_bond_ID_invalid")
    low, high = _utf8_sorted((left, right))
    return f"{low}|{high}|{order}"


def canonical_parent_graph_sha256(
    atoms: Sequence[Mapping[str, Any]], bonds: Sequence[Mapping[str, Any]]
) -> str:
    payload = {
        "atoms": [
            [row["ccd_atom_id"], row["ccd_type_symbol"], int(row["ccd_formal_charge"])]
            for row in sorted(atoms, key=lambda item: item["ccd_atom_id"])
        ],
        "bonds": [
            list(item)
            for item in sorted(
                (
                    min(row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]),
                    max(row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]),
                    row["normalized_bond_order"],
                )
                for row in bonds
            )
        ],
    }
    return sha256(canonical_json(payload).encode("utf-8"))


def proposal_record_sha256(record: Mapping[str, Any]) -> str:
    _validate_proposal_types(record)
    payload = {
        field: record[field]
        for field in PROPOSAL_FIELDS
        if field != PROPOSAL_HASH_EXCLUDED_FIELD
    }
    return sha256(canonical_json(payload).encode("utf-8"))


def bridge_candidate_record_sha256(record: Mapping[str, Any]) -> str:
    _validate_enumeration_types(record)
    payload = {
        field: record[field]
        for field in ENUMERATION_FIELDS
        if field != "bridge_candidate_record_sha256"
    }
    return sha256(canonical_json(payload).encode("utf-8"))


def _validate_proposal_types(record: Mapping[str, Any]) -> None:
    if type(record) is not dict or tuple(record) != PROPOSAL_FIELDS:
        raise ValueError("proposal_field_inventory_or_order_mismatch")
    for field, contract in PROPOSAL_FIELD_TYPE_CONTRACT.items():
        value = record[field]
        if contract == "exact_int" and type(value) is not int:
            raise ValueError(f"proposal_field_type_invalid:{field}")
        if contract == "exact_str" and type(value) is not str:
            raise ValueError(f"proposal_field_type_invalid:{field}")
        if contract == "exact_list_str" and (
            type(value) is not list or any(type(item) is not str for item in value)
        ):
            raise ValueError(f"proposal_field_type_invalid:{field}")


def _validate_enumeration_types(record: Mapping[str, Any]) -> None:
    if type(record) is not dict or tuple(record) != ENUMERATION_FIELDS:
        raise ValueError("bridge_candidate_field_inventory_or_order_mismatch")
    for field in ENUMERATION_FIELDS:
        value = record[field]
        if field in ENUMERATION_INT_FIELDS:
            valid = type(value) is int
        elif field == "warhead_side_atom_ids":
            valid = type(value) is list and all(type(item) is str for item in value)
        elif field in ENUMERATION_BOOL_FIELDS:
            valid = type(value) is bool
        else:
            valid = type(value) is str
        if not valid:
            raise ValueError(f"bridge_candidate_field_type_invalid:{field}")


def _reached(
    adjacency: Mapping[str, Sequence[tuple[str, str]]],
    start: str,
    skipped: frozenset[str] | None = None,
) -> set[str]:
    seen: set[str] = set()
    queue = deque([start])
    while queue:
        atom = queue.popleft()
        if atom in seen:
            continue
        seen.add(atom)
        for neighbor, _order in sorted(
            adjacency[atom], key=lambda item: item[0].encode("utf-8")
        ):
            if skipped is None or frozenset((atom, neighbor)) != skipped:
                if neighbor not in seen:
                    queue.append(neighbor)
    return seen


def enumerate_exact_one_boundary_candidates(
    atom_ids: Sequence[str],
    bonds: Sequence[tuple[str, str, str]],
    reactive_atom_id: str,
    local_reaction_center_atom_ids: Sequence[str],
    required_leaving_group_atom_ids: Sequence[str],
) -> list[dict[str, Any]]:
    """Enumerate every bridge, retaining explicit admission evidence."""

    ordered_atoms = _utf8_sorted(atom_ids)
    if len(ordered_atoms) != len(set(ordered_atoms)) or reactive_atom_id not in set(
        ordered_atoms
    ):
        raise ValueError("enumeration_atom_authority_invalid")
    adjacency: dict[str, list[tuple[str, str]]] = {
        atom_id: [] for atom_id in ordered_atoms
    }
    seen_edges: set[frozenset[str]] = set()
    ordered_bonds = sorted(
        bonds, key=lambda item: canonical_parent_bond_id(*item).encode("utf-8")
    )
    for left, right, order in ordered_bonds:
        edge = frozenset((left, right))
        if (
            left not in adjacency
            or right not in adjacency
            or left == right
            or edge in seen_edges
        ):
            raise ValueError("enumeration_bond_authority_invalid")
        canonical_parent_bond_id(left, right, order)
        seen_edges.add(edge)
        adjacency[left].append((right, order))
        adjacency[right].append((left, order))
    if _reached(adjacency, reactive_atom_id) != set(ordered_atoms):
        raise ValueError("enumeration_parent_graph_disconnected")

    local = set(local_reaction_center_atom_ids)
    leaving = set(required_leaving_group_atom_ids)
    rows: list[dict[str, Any]] = []
    for left, right, order in ordered_bonds:
        side = _reached(adjacency, reactive_atom_id, frozenset((left, right)))
        if side == set(ordered_atoms):
            continue
        other = set(ordered_atoms) - side
        boundary_count = sum(
            (a in side) != (b in side) for a, b, _bond_order in ordered_bonds
        )
        connected = bool(side) and _reached(
            {
                atom: [
                    (neighbor, bond_order)
                    for neighbor, bond_order in adjacency[atom]
                    if neighbor in side
                ]
                for atom in side
            },
            min(side, key=lambda value: value.encode("utf-8")),
        ) == side
        contains_local = local <= side
        contains_leaving = leaving <= side
        proper_subset = bool(side) and bool(other)
        exact_one = boundary_count == 1
        blockers = []
        if not contains_local:
            blockers.append("candidate_missing_local_reaction_center")
        if not contains_leaving:
            blockers.append("candidate_missing_required_leaving_group")
        if not connected:
            blockers.append("candidate_warhead_side_disconnected")
        if not exact_one:
            blockers.append("candidate_boundary_not_exact_one")
        if not proper_subset:
            blockers.append("candidate_not_proper_subset")
        rows.append(
            {
                "boundary_bond_id": canonical_parent_bond_id(left, right, order),
                "warhead_side_atom_ids": _utf8_sorted(side),
                "warhead_side_atom_count": len(side),
                "nonwarhead_side_atom_count": len(other),
                "contains_local_reaction_center": contains_local,
                "contains_required_leaving_groups": contains_leaving,
                "warhead_side_connected": connected,
                "exact_one_boundary_verified": exact_one,
                "proper_subset": proper_subset,
                "candidate_admitted": not blockers,
                "blocking_reasons": ";".join(_utf8_sorted(blockers)),
            }
        )
    rows.sort(key=lambda row: row["boundary_bond_id"].encode("utf-8"))
    return rows


def proposal_status_for_candidates(candidates: Sequence[Mapping[str, Any]]) -> str:
    count = sum(row["candidate_admitted"] is True for row in candidates)
    if count == 1:
        return "auto_exact_candidate"
    if count > 1:
        return "ambiguous_candidate"
    return "quarantined"


def _git_identity(repo_root: Path, commit: str) -> list[str]:
    return (
        _git(repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", commit)
        .stdout.decode()
        .splitlines()
    )


def validate_execution_boundary_v1(repo_root: Path) -> str:
    if _git_identity(repo_root, BASE_COMMIT) != [
        BASE_COMMIT,
        BASE_PARENT,
        BASE_TREE,
        BASE_SUBJECT,
    ]:
        raise ValueError("formal_BASE_identity_mismatch")
    head = _git(repo_root, "rev-parse", "HEAD").stdout.decode().strip()
    if head == BASE_COMMIT:
        return "pre_commit"
    raw = _git(repo_root, "cat-file", "commit", head).stdout
    headers, separator, message = raw.partition(b"\n\n")
    if not separator:
        raise ValueError("successor_commit_object_malformed")
    parents = tuple(
        line[7:].decode() for line in headers.splitlines() if line.startswith(b"parent ")
    )
    if parents != (BASE_COMMIT,):
        raise ValueError("successor_parent_not_exact_BASE")
    subject, newline, body = message.partition(b"\n")
    if not newline or subject.decode() != FORMAL_COMMIT_SUBJECT or body:
        raise ValueError("successor_message_invalid")
    changed = {
        item.decode()
        for item in _git(
            repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).stdout.split(b"\0")
        if item
    }
    if changed != {path.as_posix() for path in EXACT10_PATHS}:
        raise ValueError("successor_changed_path_inventory_mismatch")
    modes = [
        item.partition(b"\t")[0]
        for item in _git(
            repo_root,
            "ls-tree",
            "-r",
            "-z",
            head,
            "--",
            *(path.as_posix() for path in EXACT10_PATHS),
        ).stdout.split(b"\0")
        if item
    ]
    if len(modes) != 10 or any(not item.startswith(b"100644 blob ") for item in modes):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    if branch.stdout.decode().strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root, "rev-parse", "--verify", "refs/remotes/origin/main", check=False
    )
    if origin.returncode:
        raise ValueError("successor_origin_main_missing")
    if origin.stdout.decode().strip() == BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    if origin.stdout.decode().strip() == head:
        return "formal_main_post_push"
    raise ValueError("successor_origin_main_lifecycle_mismatch")


def base_bytes(repo_root: Path, path: Path) -> bytes:
    result = _git(
        repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}", check=False
    )
    if result.returncode or not result.stdout:
        raise ValueError(f"BASE_source_missing:{path.as_posix()}")
    return result.stdout


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    validate_execution_boundary_v1(repo_root)
    payloads = {}
    for path, expected in FROZEN_BASE_SHA256.items():
        payload = base_bytes(repo_root, path)
        if sha256(payload) != expected:
            raise ValueError(f"BASE_source_SHA_mismatch:{path.as_posix()}")
        payloads[path] = payload
    return payloads


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_bytes(
    columns: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _cell(row.get(field, "")) for field in columns})
    return stream.getvalue().encode("utf-8")


def _cell(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    if type(value) in (list, dict, tuple):
        return canonical_json(value)
    return str(value)


def _literal_tuple(source: bytes, name: str) -> tuple[str, ...]:
    tree = ast.parse(source.decode("utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if type(value) is tuple and all(type(item) is str for item in value):
                return value
    raise ValueError(f"literal_tuple_missing:{name}")


def _source_metadata(path: Path) -> tuple[str, str, str]:
    metadata = {
        DESIGN_SOURCE: ("11/11", "inherited Exact22 proposal constants and validation contract", "predecessor_production_contract"),
        DESIGN_MANIFEST: ("7/7;11/11", "transaction, proposal readiness, frozen fields/status/hash contract", "predecessor_manifest"),
        DESIGN_READINESS: ("7/7", "proposal materialization readiness and closed downstream gates", "predecessor_readiness"),
        DESIGN_CONTRACT: ("7/7", "atom-set, boundary, approval, and downstream contracts", "predecessor_contract_registry"),
        DESIGN_GAP: ("7/7", "unresolved complete-authority and SMARTS prerequisites", "predecessor_gap_evidence"),
        DESIGN_FAILURE: ("7/7", "predecessor fail-closed evidence", "predecessor_failure_evidence"),
        ASSIGNMENTS: ("11/11", "sample/class/rule/family/reactive atom/graph and assignment SHA", "assignment_authority"),
        CLASSES: ("7/7", "class identities, links, and support counts", "candidate_class_authority"),
        RULES: ("7/7", "radius-1 graph JSON/SHA and leaving-group contract", "warhead_rule_authority"),
        PARENT_ATOMS: ("11/11;9/9 components", "parent atom IDs/elements/charges/graph SHA/verified", "parent_atom_authority"),
        PARENT_BONDS: ("11/11;9/9 components", "parent endpoints/orders/graph SHA/verified", "parent_bond_authority"),
        MAPPINGS: ("11/11", "reactive mapping and retained-vs-leaving parent evidence", "observed_parent_mapping_authority"),
        REVIEW_MANIFEST: ("11/11", "review-package predecessor transaction state", "review_package_manifest"),
        REVIEW_INDEX: ("18/18", "class/sample package links and unreviewed state", "review_package_index"),
        CLASS_TEMPLATES: ("7/7", "blank class review decisions/reviewer/SMARTS", "blank_class_review_templates"),
        SAMPLE_TEMPLATES: ("11/11", "blank sample decisions/reviewer and assignment SHA", "blank_sample_review_templates"),
    }
    return metadata[path]


def _source_inventory(payloads: Mapping[Path, bytes]) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for path in SOURCE_PATHS:
        payload = payloads[path]
        coverage, fields, authority = _source_metadata(path)
        if path.suffix == ".csv":
            count = len(_csv_rows(payload))
        elif path.suffix == ".json":
            count = 1
        else:
            count = len(payload.decode("utf-8").splitlines())
        rows.append(
            {
                "source_path": path.as_posix(),
                "BASE_SHA256": sha256(payload),
                "source_row_count": count,
                "Current11_coverage": coverage,
                "fields_actually_used": fields,
                "authority_class": authority,
                "verified": True,
            }
        )
    return tuple(rows)


def _require(condition: bool, reason: str, reasons: list[str]) -> None:
    if not condition:
        reasons.append(reason)


def _validate_phase_a(payloads: Mapping[Path, bytes]) -> tuple[str, ...]:
    reasons: list[str] = []
    design_manifest = json.loads(payloads[DESIGN_MANIFEST])
    review_manifest = json.loads(payloads[REVIEW_MANIFEST])
    assignments = _csv_rows(payloads[ASSIGNMENTS])
    classes = _csv_rows(payloads[CLASSES])
    rules = _csv_rows(payloads[RULES])
    design_readiness = _csv_rows(payloads[DESIGN_READINESS])
    review_index = _csv_rows(payloads[REVIEW_INDEX])
    class_templates = _csv_rows(payloads[CLASS_TEMPLATES])
    sample_templates = _csv_rows(payloads[SAMPLE_TEMPLATES])
    mappings = _csv_rows(payloads[MAPPINGS])

    _require(design_manifest.get("transaction_succeeded") is True, "predecessor_transaction_not_succeeded", reasons)
    _require(review_manifest.get("transaction_succeeded") is True, "review_predecessor_transaction_not_succeeded", reasons)
    _require(design_manifest.get("warhead_atom_set_and_boundary_proposal_materialization_ready_count") == 7, "predecessor_proposal_readiness_not_7", reasons)
    _require(len(design_readiness) == 7 and all(row.get("ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization") == "true" for row in design_readiness), "predecessor_proposal_readiness_rows_invalid", reasons)
    _require(tuple(design_manifest.get("proposal_fields", ())) == PROPOSAL_FIELDS, "inherited_proposal_fields_mismatch", reasons)
    _require(tuple(design_manifest.get("proposal_statuses", ())) == PROPOSAL_STATUSES, "inherited_proposal_statuses_mismatch", reasons)
    _require(_literal_tuple(payloads[DESIGN_SOURCE], "PROPOSAL_FIELDS") == PROPOSAL_FIELDS, "inherited_source_proposal_fields_mismatch", reasons)
    _require(design_manifest.get("proposal_field_type_contract") == PROPOSAL_FIELD_TYPE_CONTRACT, "inherited_proposal_type_contract_mismatch", reasons)
    _require(len(classes) == 7, "class_count_not_7", reasons)
    _require(len(assignments) == 11, "sample_count_not_11", reasons)
    _require(len({row["warhead_type_candidate_class_id"] for row in classes}) == len(classes), "duplicate_class_identity", reasons)
    _require(len({row["sample_index_row_id"] for row in assignments}) == len(assignments), "duplicate_sample_identity", reasons)
    _require(len(rules) == 7, "rule_count_not_7", reasons)
    _require(
        all(row.get("verified") == "true" for row in (*assignments, *classes, *rules)),
        "assignment_class_or_rule_authority_unverified",
        reasons,
    )
    _require(
        all(row.get("verified") == "true" for row in mappings),
        "observed_parent_mapping_authority_unverified",
        reasons,
    )
    _require(
        len(review_index) == 18
        and all(
            row.get("verified") == "true"
            and row.get("package_item_materialized") == "true"
            and row.get("human_review_execution_completed") == "false"
            for row in review_index
        ),
        "review_package_index_boundary_invalid",
        reasons,
    )
    rule_by_id = {row["warhead_rule_id"]: row for row in rules}
    class_by_id = {row["warhead_type_candidate_class_id"]: row for row in classes}
    for row in classes:
        rule = rule_by_id.get(row["warhead_rule_id"])
        _require(rule is not None and rule["reaction_family_id"] == row["reaction_family_id"], "class_rule_family_link_mismatch", reasons)
    for row in assignments:
        class_row = class_by_id.get(row["warhead_type_candidate_class_id"])
        _require(
            class_row is not None
            and row["candidate_warhead_rule_id"] == class_row["warhead_rule_id"]
            and row["candidate_reaction_family_id"] == class_row["reaction_family_id"]
            and row["warhead_type_candidate_class_index_0based"] == class_row["warhead_type_candidate_class_index_0based"],
            "sample_class_rule_family_link_mismatch",
            reasons,
        )
        expected_assignment_sha = sha256(
            canonical_json(
                {
                    field: (
                        int(row[field])
                        if field
                        == "warhead_type_candidate_class_index_0based"
                        else row[field]
                    )
                    for field in ASSIGNMENT_HASH_FIELDS
                }
            ).encode("utf-8")
        )
        _require(
            row.get("assignment_record_sha256") == expected_assignment_sha,
            "assignment_record_SHA_mismatch",
            reasons,
        )
    _require(len(class_templates) == 7 and all(row["reaction_family_identity_review_decision"] == "not_reviewed" and row["warhead_rule_topology_review_decision"] == "not_reviewed" and not row["reviewer_id"] and not row["candidate_warhead_smarts"] for row in class_templates), "class_review_template_boundary_invalid", reasons)
    assignment_by_id = {
        row["sample_index_row_id"]: row for row in assignments
    }
    _require(
        len(sample_templates) == 11
        and all(
            row["sample_assignment_review_decision"] == "not_reviewed"
            and not row["reviewer_id"]
            and row["source_assignment_record_sha256"]
            == assignment_by_id[row["sample_index_row_id"]][
                "assignment_record_sha256"
            ]
            for row in sample_templates
        ),
        "sample_review_template_boundary_invalid",
        reasons,
    )
    return tuple(_utf8_sorted(set(reasons)))


def _validate_graph(
    atom_rows: Sequence[Mapping[str, str]],
    bond_rows: Sequence[Mapping[str, str]],
    expected_sha: str,
) -> tuple[dict[str, Mapping[str, str]], list[tuple[str, str, str]], dict[str, list[tuple[str, str]]]]:
    if not atom_rows:
        raise ValueError("parent_atom_authority_missing")
    if not bond_rows:
        raise ValueError("parent_bond_authority_missing")
    if any(row.get("verified") != "true" for row in (*atom_rows, *bond_rows)):
        raise ValueError("parent_authority_unverified")
    atom_by_id = {row["ccd_atom_id"]: row for row in atom_rows}
    if len(atom_by_id) != len(atom_rows):
        raise ValueError("duplicate_parent_atom_ID")
    seen: set[frozenset[str]] = set()
    edges = []
    adjacency = {atom_id: [] for atom_id in atom_by_id}
    for row in bond_rows:
        left, right = row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]
        order = row["normalized_bond_order"]
        if left == right:
            raise ValueError("parent_bond_self_loop")
        if left not in atom_by_id or right not in atom_by_id:
            raise ValueError("parent_bond_endpoint_missing")
        edge = frozenset((left, right))
        if edge in seen:
            raise ValueError("duplicate_parent_bond")
        if order not in PARENT_NORMALIZED_BOND_ORDERS:
            raise ValueError("parent_bond_order_invalid")
        seen.add(edge)
        edges.append((left, right, order))
        adjacency[left].append((right, order))
        adjacency[right].append((left, order))
    first = min(atom_by_id, key=lambda value: value.encode("utf-8"))
    if _reached(adjacency, first) != set(atom_by_id):
        raise ValueError("parent_graph_disconnected")
    actual_sha = canonical_parent_graph_sha256(atom_rows, bond_rows)
    if actual_sha != expected_sha:
        raise ValueError("parent_graph_SHA_mismatch")
    if any(row["component_parent_graph_sha256"] != expected_sha for row in (*atom_rows, *bond_rows)):
        raise ValueError("parent_graph_SHA_link_mismatch")
    return atom_by_id, edges, adjacency


def _local_and_leaving(
    sample: Mapping[str, str],
    rule: Mapping[str, str],
    atom_by_id: Mapping[str, Mapping[str, str]],
    adjacency: Mapping[str, Sequence[tuple[str, str]]],
    mapping_rows: Sequence[Mapping[str, str]],
) -> tuple[list[str], list[str], list[str]]:
    reactive_rows = [
        row
        for row in mapping_rows
        if row["sample_index_row_id"] == sample["sample_index_row_id"]
        and row["reactive_ligand_atom"] == "true"
    ]
    if len(reactive_rows) != 1:
        raise ValueError("reactive_parent_mapping_not_exact_one")
    reactive = reactive_rows[0]["parent_ccd_atom_id"]
    if reactive != sample["ligand_reactive_parent_ccd_atom_id"]:
        raise ValueError("reactive_parent_mapping_chain_mismatch")
    try:
        local = json.loads(rule["canonical_local_graph_rule_json"])
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("local_graph_JSON_invalid") from error
    if sha256(canonical_json(local).encode("utf-8")) != rule["canonical_local_graph_rule_sha256"]:
        raise ValueError("local_graph_JSON_SHA_mismatch")
    center = local.get("center_atom")
    target = local.get("target_condition")
    if (
        local.get("selected_signature_radius") != 1
        or type(center) is not dict
        or center.get("reactive") is not True
        or target != {"formed_bond_order": "single", "residue": "CYS", "residue_atom": "SG"}
    ):
        raise ValueError("local_graph_contract_mismatch")
    local_atoms = local.get("local_atoms")
    local_bonds = local.get("local_bonds")
    if type(local_atoms) is not list or type(local_bonds) is not list:
        raise ValueError("local_graph_inventory_invalid")
    center_id = center["canonical_local_atom_id"]
    noncenter = [
        atom for atom in local_atoms if atom.get("canonical_local_atom_id") != center_id
    ]
    if len(adjacency[reactive]) != len(noncenter):
        raise ValueError("local_reaction_center_degree_mismatch")
    observed_parent_ids = {
        row["parent_ccd_atom_id"]
        for row in mapping_rows
        if row["sample_index_row_id"] == sample["sample_index_row_id"]
        and row["verified"] == "true"
    }
    expected = []
    for atom in noncenter:
        atom_id = atom.get("canonical_local_atom_id")
        bonds = [
            bond
            for bond in local_bonds
            if {bond.get("canonical_endpoint_1"), bond.get("canonical_endpoint_2")}
            == {center_id, atom_id}
        ]
        if len(bonds) != 1:
            raise ValueError("local_neighbor_bond_not_exact_one")
        disposition = (
            "leaving"
            if atom.get("is_leaving_group") is True
            and atom.get("is_retained_observed") is False
            and bonds[0].get("projected_disposition")
            == "verified_leaving_group_endpoint_missing"
            else "retained"
            if atom.get("is_leaving_group") is False
            and atom.get("is_retained_observed") is True
            and bonds[0].get("projected_disposition") == "retained_observed_bond"
            else "invalid"
        )
        expected.append(
            (
                atom.get("element"),
                atom.get("formal_charge"),
                bonds[0].get("normalized_bond_order"),
                disposition,
            )
        )
    actual = []
    leaving = []
    center_bonds = []
    for neighbor, order in adjacency[reactive]:
        disposition = "retained" if neighbor in observed_parent_ids else "leaving"
        actual.append(
            (
                atom_by_id[neighbor]["ccd_type_symbol"],
                int(atom_by_id[neighbor]["ccd_formal_charge"]),
                order,
                disposition,
            )
        )
        center_bonds.append(canonical_parent_bond_id(reactive, neighbor, order))
        if disposition == "leaving":
            leaving.append(neighbor)
    if Counter(expected) != Counter(actual):
        raise ValueError("local_neighbor_multiset_mismatch")
    delta = local.get("reaction_delta")
    allowed = rule.get("allowed_leaving_group_elements", "").split(";") if rule.get("allowed_leaving_group_elements") else []
    if (
        type(delta) is not dict
        or delta.get("leaving_group_count") != int(rule["required_leaving_group_count"])
        or delta.get("leaving_group_elements") != allowed
        or delta.get("reaction_delta_class") != rule["required_reaction_delta_class"]
        or len(leaving) != delta.get("leaving_group_count")
        or sorted(atom_by_id[item]["ccd_type_symbol"] for item in leaving) != sorted(allowed)
    ):
        raise ValueError("leaving_group_evidence_mismatch")
    local_ids = _utf8_sorted([reactive, *(neighbor for neighbor, _ in adjacency[reactive])])
    leaving_ids = _utf8_sorted(leaving)
    if reactive not in local_ids or not set(leaving_ids) <= set(local_ids):
        raise ValueError("local_or_leaving_membership_invalid")
    return local_ids, _utf8_sorted(center_bonds), leaving_ids


def _identity_prefix(sample: Mapping[str, str]) -> dict[str, Any]:
    return {
        "sample_index_row_id": sample["sample_index_row_id"],
        "pdb_id": sample["pdb_id"],
        "ligand_comp_id": sample["ligand_comp_id"],
        "warhead_type_candidate_class_index_0based": int(
            sample["warhead_type_candidate_class_index_0based"]
        ),
        "warhead_type_candidate_class_id": sample[
            "warhead_type_candidate_class_id"
        ],
        "reaction_family_id": sample["candidate_reaction_family_id"],
        "warhead_rule_id": sample["candidate_warhead_rule_id"],
        "component_parent_graph_sha256": sample[
            "component_parent_graph_sha256"
        ],
    }


def _materialize_rows(
    payloads: Mapping[Path, bytes],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    assignments = sorted(
        _csv_rows(payloads[ASSIGNMENTS]), key=lambda row: row["sample_index_row_id"]
    )
    rules = {
        row["warhead_rule_id"]: row for row in _csv_rows(payloads[RULES])
    }
    parent_atoms = _csv_rows(payloads[PARENT_ATOMS])
    parent_bonds = _csv_rows(payloads[PARENT_BONDS])
    mappings = _csv_rows(payloads[MAPPINGS])
    proposals = []
    enumerations = []
    readiness = []
    for sample in assignments:
        component = sample["ligand_comp_id"]
        graph_sha = sample["component_parent_graph_sha256"]
        atom_rows = [
            row
            for row in parent_atoms
            if row["ligand_comp_id"] == component
            and row["component_parent_graph_sha256"] == graph_sha
        ]
        bond_rows = [
            row
            for row in parent_bonds
            if row["ligand_comp_id"] == component
            and row["component_parent_graph_sha256"] == graph_sha
        ]
        atom_by_id, edges, adjacency = _validate_graph(
            atom_rows, bond_rows, graph_sha
        )
        rule = rules[sample["candidate_warhead_rule_id"]]
        local_ids, local_bond_ids, leaving_ids = _local_and_leaving(
            sample, rule, atom_by_id, adjacency, mappings
        )
        raw_candidates = enumerate_exact_one_boundary_candidates(
            list(atom_by_id),
            edges,
            sample["ligand_reactive_parent_ccd_atom_id"],
            local_ids,
            leaving_ids,
        )
        identity = _identity_prefix(sample)
        sample_candidates = []
        for index, candidate in enumerate(raw_candidates):
            record = {
                "enumeration_version": ENUMERATION_VERSION,
                **identity,
                "bridge_candidate_index_0based": index,
                **candidate,
                "bridge_candidate_record_sha256": "",
            }
            record["bridge_candidate_record_sha256"] = (
                bridge_candidate_record_sha256(record)
            )
            _validate_enumeration_types(record)
            sample_candidates.append(record)
            enumerations.append(record)
        admitted = [row for row in sample_candidates if row["candidate_admitted"]]
        status = proposal_status_for_candidates(sample_candidates)
        warhead_ids: list[str] = []
        warhead_attachment = ""
        nonwarhead_boundary = ""
        boundary_order = ""
        ambiguity = []
        if status == "auto_exact_candidate":
            chosen = admitted[0]
            warhead_ids = chosen["warhead_side_atom_ids"]
            left, right, boundary_order = chosen["boundary_bond_id"].split("|")
            warhead_attachment = left if left in set(warhead_ids) else right
            nonwarhead_boundary = right if warhead_attachment == left else left
        elif status == "ambiguous_candidate":
            ambiguity = ["multiple_admissible_exact_one_boundary_candidates"]
        else:
            ambiguity = ["no_admissible_exact_one_boundary_candidate"]
        proposal = {
            "proposal_version": PROPOSAL_VERSION,
            **identity,
            "ligand_reactive_parent_atom_id": sample[
                "ligand_reactive_parent_ccd_atom_id"
            ],
            "local_reaction_center_atom_ids": local_ids,
            "local_reaction_center_bond_ids": local_bond_ids,
            "proposed_pre_reaction_warhead_atom_ids": warhead_ids,
            "proposed_warhead_attachment_atom_id": warhead_attachment,
            "proposed_nonwarhead_boundary_atom_id": nonwarhead_boundary,
            "proposed_attachment_boundary_bond_order": boundary_order,
            "required_leaving_group_atom_ids": leaving_ids,
            "proposal_method": PROPOSAL_METHOD,
            "proposal_status": status,
            "ambiguity_reasons": ambiguity,
            "source_assignment_record_sha256": sample[
                "assignment_record_sha256"
            ],
            "proposal_record_sha256": "",
        }
        proposal["proposal_record_sha256"] = proposal_record_sha256(proposal)
        _validate_proposal_types(proposal)
        if proposal["proposal_record_sha256"] != proposal_record_sha256(proposal):
            raise ValueError("proposal_record_SHA_mismatch")
        proposals.append(proposal)
        blockers = (
            "multiple_admissible_exact_one_boundary_candidates;"
            "human_proposal_review_missing;complete_warhead_atom_set_authority_unavailable;"
            "exact_one_attachment_boundary_authority_unavailable;"
            "candidate_warhead_SMARTS_not_materialized;human_gold_review_missing"
            if status == "ambiguous_candidate"
            else "no_admissible_exact_one_boundary_candidate;human_proposal_review_missing;"
            "complete_warhead_atom_set_authority_unavailable;"
            "exact_one_attachment_boundary_authority_unavailable;"
            "candidate_warhead_SMARTS_not_materialized;human_gold_review_missing"
            if status == "quarantined"
            else "human_proposal_review_missing;complete_warhead_atom_set_authority_unavailable;"
            "exact_one_attachment_boundary_authority_unavailable;"
            "candidate_warhead_SMARTS_not_materialized;human_gold_review_missing"
        )
        readiness.append(
            {
                **identity,
                "ligand_reactive_parent_atom_id": sample[
                    "ligand_reactive_parent_ccd_atom_id"
                ],
                "local_reaction_center_atom_count": len(local_ids),
                "required_leaving_group_atom_count": len(leaving_ids),
                "parent_bridge_count": len(sample_candidates),
                "admitted_boundary_candidate_count": len(admitted),
                "proposal_status": status,
                "proposal_record_sha256": proposal["proposal_record_sha256"],
                "proposal_materialized": True,
                "ready_for_proposal_human_review": True,
                "complete_warhead_atom_set_authority_available": False,
                "exact_one_attachment_boundary_authority_available": False,
                "ready_for_candidate_warhead_smarts_materialization": False,
                "ready_for_SMARTS_review_execution": False,
                "ready_for_role_proposal_generation": False,
                "ready_for_mask_materialization": False,
                "ready_for_model_integration": False,
                "ready_for_training": False,
                "blocking_reasons": blockers,
                "verified": True,
            }
        )
    if len(proposals) != 11 or len(readiness) != 11:
        raise ValueError("partial_materialization_attempted")
    return tuple(proposals), tuple(enumerations), tuple(readiness)


def observe_failure_scenario(scenario: ProposalScenario) -> tuple[str, ...]:
    checks = (
        (not scenario.base_source_present, "BASE_source_missing"),
        (not scenario.base_source_sha_matches, "BASE_source_SHA_mismatch"),
        (not scenario.predecessor_transaction_succeeded, "predecessor_transaction_not_succeeded"),
        (scenario.predecessor_proposal_readiness_count != 7, "predecessor_proposal_readiness_not_7"),
        (scenario.class_count != 7, "class_count_not_7"),
        (scenario.sample_count != 11, "sample_count_not_11"),
        (scenario.duplicate_class_identity, "duplicate_class_identity"),
        (scenario.duplicate_sample_identity, "duplicate_sample_identity"),
        (not scenario.class_rule_family_links_match, "class_rule_family_link_mismatch"),
        (not scenario.sample_class_rule_family_links_match, "sample_class_rule_family_link_mismatch"),
        (not scenario.parent_atom_authority_present, "parent_atom_authority_missing"),
        (not scenario.parent_bond_authority_present, "parent_bond_authority_missing"),
        (not scenario.parent_graph_sha_matches, "parent_graph_SHA_mismatch"),
        (scenario.duplicate_parent_atom_id, "duplicate_parent_atom_ID"),
        (scenario.duplicate_parent_bond, "duplicate_parent_bond"),
        (not scenario.parent_bond_endpoint_present, "parent_bond_endpoint_missing"),
        (not scenario.parent_graph_connected, "parent_graph_disconnected"),
        (not scenario.reactive_parent_mapping_exact_one, "reactive_parent_mapping_not_exact_one"),
        (not scenario.local_graph_json_sha_matches, "local_graph_JSON_SHA_mismatch"),
        (not scenario.local_reaction_center_degree_matches, "local_reaction_center_degree_mismatch"),
        (not scenario.local_neighbor_multiset_matches, "local_neighbor_multiset_mismatch"),
        (not scenario.leaving_group_evidence_matches, "leaving_group_evidence_mismatch"),
        (not scenario.bridge_enumeration_deterministic, "bridge_enumeration_nondeterministic"),
        (not scenario.bridge_candidate_indices_contiguous, "bridge_candidate_index_non_contiguous"),
        (not scenario.candidate_contains_local_center, "candidate_missing_local_reaction_center"),
        (not scenario.candidate_contains_leaving_groups, "candidate_missing_required_leaving_group"),
        (not scenario.candidate_warhead_side_connected, "candidate_warhead_side_disconnected"),
        (not scenario.candidate_boundary_exact_one, "candidate_boundary_not_exact_one"),
        (not scenario.auto_exact_candidate_count_valid, "auto_exact_status_candidate_count_not_1"),
        (not scenario.ambiguous_candidate_count_valid, "ambiguous_status_candidate_count_not_multiple"),
        (not scenario.quarantined_candidate_count_valid, "quarantined_status_candidate_count_not_0"),
        (not scenario.unresolved_proposal_fields_blank, "ambiguous_or_quarantined_proposal_fields_prefilled"),
        (not scenario.proposal_record_valid, "proposal_field_type_or_hash_invalid"),
        (not scenario.bridge_candidate_record_valid, "bridge_candidate_field_type_or_hash_invalid"),
        (scenario.partial_materialization_attempted, "partial_materialization_attempted"),
        (scenario.downstream_readiness_opened, "downstream_readiness_prematurely_opened"),
    )
    return tuple(reason for failed, reason in checks if failed)


def transaction_tables(
    scenario: ProposalScenario,
) -> tuple[tuple[object, ...], tuple[object, ...], tuple[object, ...]]:
    if observe_failure_scenario(scenario):
        return (), (), ()
    return (object(),), (object(),), (object(),)


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = ProposalScenario()
    rows = []
    signatures = set()
    for case, field, value, expected in FAILURE_MUTATIONS:
        if getattr(baseline, field) == value or type(getattr(baseline, field)) is not type(value):
            raise AssertionError(f"failure_mutation_type_or_delta_invalid:{field}")
        scenario = replace(baseline, **{field: value})
        observed = observe_failure_scenario(scenario)
        signature = sha256(
            canonical_json(
                {"mutated_field": field, "mutated_value": value}
            ).encode("utf-8")
        )
        if expected not in observed or signature in signatures:
            raise AssertionError(f"failure_mutation_invalid:{field}")
        signatures.add(signature)
        proposal, enumeration, readiness = transaction_tables(scenario)
        rows.append(
            {
                "failure_case": case,
                "mutation_signature": signature,
                "mutated_field": field,
                "mutated_value_json": canonical_json(value),
                "expected_reason": expected,
                "observed_reasons": ";".join(observed),
                "expected_reason_verified": True,
                "fails_closed": not proposal and not enumeration and not readiness,
                "proposal_row_count": len(proposal),
                "bridge_enumeration_row_count": len(enumeration),
                "readiness_row_count": len(readiness),
                "SMARTS_ready": False,
                "role_ready": False,
                "mask_ready": False,
                "model_ready": False,
                "training_ready": False,
                "verified": True,
            }
        )
    return tuple(rows)


def build_result(repo_root: Path) -> BuildResult:
    payloads = load_frozen_sources(repo_root)
    source_rows = _source_inventory(payloads)
    reasons = _validate_phase_a(payloads)
    failures = build_failure_rows()
    if reasons:
        return BuildResult(source_rows, (), (), (), failures, False, reasons)
    try:
        proposals, enumerations, readiness = _materialize_rows(payloads)
    except ValueError as error:
        return BuildResult(
            source_rows, (), (), (), failures, False, (str(error),)
        )
    return BuildResult(
        source_rows,
        proposals,
        enumerations,
        readiness,
        failures,
        True,
        (),
    )


def _manifest(
    result: BuildResult, output_sha256: Mapping[str, str]
) -> Mapping[str, Any]:
    statuses = Counter(row["proposal_status"] for row in result.proposal_rows)
    zero_bridges = sum(row["parent_bridge_count"] == 0 for row in result.readiness_rows)
    zero_admitted = sum(row["admitted_boundary_candidate_count"] == 0 for row in result.readiness_rows)
    multiple_admitted = sum(row["admitted_boundary_candidate_count"] > 1 for row in result.readiness_rows)
    next_step = (
        "materialize_covapie_current11_warhead_atom_set_and_attachment_"
        "boundary_review_packages_v1"
        if result.transaction_succeeded
        else "resolve_covapie_current11_warhead_proposal_materialization_blockers_v1"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "source_count": 16,
        "source_sha256": {
            path.as_posix(): digest for path, digest in FROZEN_BASE_SHA256.items()
        },
        "proposal_version": PROPOSAL_VERSION,
        "proposal_method": PROPOSAL_METHOD,
        "proposal_field_count": 22,
        "proposal_fields": list(PROPOSAL_FIELDS),
        "proposal_statuses": list(PROPOSAL_STATUSES),
        "proposal_atom_id_namespace": PROPOSAL_ATOM_ID_NAMESPACE,
        "proposal_bond_id_encoding": PROPOSAL_BOND_ID_ENCODING,
        "proposal_hash_included_field_count": 21,
        "bridge_enumeration_version": ENUMERATION_VERSION,
        "bridge_enumeration_field_count": 22,
        "bridge_enumeration_fields": list(ENUMERATION_FIELDS),
        "bridge_candidate_hash_included_field_count": 21,
        "candidate_class_count": 7,
        "current11_sample_count": 11,
        "unique_component_count": len({row["ligand_comp_id"] for row in result.proposal_rows}),
        "component_count": len({row["ligand_comp_id"] for row in result.proposal_rows}),
        "sample_count": len(result.proposal_rows),
        "class_count": len({row["warhead_type_candidate_class_id"] for row in result.proposal_rows}),
        "proposal_record_count": len(result.proposal_rows),
        "proposal_materialized_count": len(result.proposal_rows),
        "proposal_record_sha_valid_count": sum(
            row["proposal_record_sha256"] == proposal_record_sha256(row)
            for row in result.proposal_rows
        ),
        "auto_exact_candidate_count": statuses["auto_exact_candidate"],
        "ambiguous_candidate_count": statuses["ambiguous_candidate"],
        "quarantined_count": statuses["quarantined"],
        "not_materialized_count": statuses["not_materialized"],
        "proposal_status_count_total": sum(statuses.values()),
        "total_parent_bridge_count": len(result.enumeration_rows),
        "total_admitted_boundary_candidate_count": sum(
            row["candidate_admitted"] for row in result.enumeration_rows
        ),
        "samples_with_zero_parent_bridges": zero_bridges,
        "samples_with_zero_admitted_candidates": zero_admitted,
        "samples_with_multiple_admitted_candidates": multiple_admitted,
        "proposal_human_review_ready_count": sum(
            row["ready_for_proposal_human_review"] for row in result.readiness_rows
        ),
        "complete_warhead_atom_set_authority_available_count": 0,
        "exact_one_attachment_boundary_authority_available_count": 0,
        "candidate_warhead_smarts_materialized_count": 0,
        "candidate_warhead_smarts_materialization_ready_count": 0,
        "SMARTS_human_review_ready_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "approved_warhead_smarts_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "ready_for_role_proposal_generation": False,
        "ready_for_minimal_seed_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "role_annotation_materialized": False,
        "minimal_seed_materialized": False,
        "mask_materialized": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_used": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "transaction_succeeded": result.transaction_succeeded,
        "blocking_reasons": list(result.blocking_reasons),
        "failure_mutation_count": len(result.failure_rows),
        "failure_mutations_all_fail_closed": all(
            row["fails_closed"] for row in result.failure_rows
        ),
        "output_sha256": dict(output_sha256),
        "recommended_manual_action": (
            "perform_real_human_review_of_materialized_family_topology_and_"
            "sample_assignment_packages"
        ),
        "recommended_engineering_next_step": (
            next_step
        ),
        "recommended_next_step": next_step,
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        PROPOSAL_FILE: _csv_bytes(PROPOSAL_FIELDS, result.proposal_rows),
        ENUMERATION_FILE: _csv_bytes(ENUMERATION_FIELDS, result.enumeration_rows),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, result.readiness_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    output_sha = {name: sha256(payload) for name, payload in payloads.items()}
    payloads[MANIFEST_FILE] = (
        json.dumps(
            _manifest(result, output_sha),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    ).encode("utf-8")
    return payloads


def materialize(repo_root: Path) -> dict[str, bytes]:
    payloads = build_evidence_payloads(repo_root)
    destination = repo_root / OUTPUT_ROOT
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (destination / name).write_bytes(payload)
    return payloads


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    payloads = materialize(repo_root)
    print(
        "materialized="
        + str(len(payloads))
        + " output_root="
        + OUTPUT_ROOT.as_posix()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

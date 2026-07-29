"""Independent checker for Current11 warhead atom-set/boundary proposals."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, deque
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle


BASE = "5cac27027c824cd38bad3479a59f586b2714142c"
PARENT = "77e2d11135da4b3f07ee64411ad3c4634ba60693"
TREE = "6837d6f4db8808eb784a80fc853c21ae34c86015"
BASE_SUBJECT = (
    "add CovaPIE Cys SG candidate warhead SMARTS materialization gate design v1"
)
SUBJECT = (
    "add CovaPIE Current11 pre-reaction warhead atom set and attachment "
    "boundary proposals v1"
)
SCHEMA = (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_"
    "proposals_v1"
)
PROPOSAL_VERSION = (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_"
    "proposal_v1"
)
METHOD = "exhaustive_exact_one_boundary_bridge_cut_enumeration_v1"
ENUM_VERSION = (
    "covapie_current11_exact_one_boundary_bridge_candidate_enumeration_v1"
)
CURRENT_LIFECYCLES = (
    "pre_commit",
    "detached_candidate_post_commit",
    "formal_main_post_commit_unpushed",
    "formal_main_post_push",
)
OUT = ROOT / "data/derived/covalent_small" / SCHEMA

SOURCE = Path(
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
ASSIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1"
)
ASSIGNMENTS = ASSIGN_ROOT / (
    "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
CLASSES = ASSIGN_ROOT / (
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
ATOMS = PARENT_ROOT / "covapie_exact9_parent_heavy_atom_authority.csv"
BONDS = PARENT_ROOT / "covapie_exact9_parent_heavy_bond_authority.csv"
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
FROZEN = {
    SOURCE: "5e57b0179b4f72782ea91b1945749121b32feaa1a9858d894c70bebca3f3c169",
    DESIGN_MANIFEST: "776b5097f6dafc4efee48178b3046ccce19c1bb084bc8be876b558ad7a184d7b",
    DESIGN_READINESS: "f4ee281ae0bcc68563c83f20e110fa0bd5ea35567590cb9c8e9045b3374596c8",
    DESIGN_CONTRACT: "ccda94bdd2b94bf3b0ac1cef842e05f01166f89c3749eb2c9e123cad3c6b6efa",
    DESIGN_GAP: "db146ef364acdb8d922ada27739caad646ff731b465fd1ba27a2ddadd35c20ec",
    DESIGN_FAILURE: "5376fff50533003188b028e4e7e4343cda883bc358ed60c69f00998225af0609",
    ASSIGNMENTS: "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    CLASSES: "e78b83340d9df0afa6bbffd5dc56708ee47023680367f7a8acd9883e7c21602d",
    RULES: "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    ATOMS: "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    BONDS: "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    MAPPINGS: "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    REVIEW_MANIFEST: "677034c0b8822e0b1476e28d00bb8dda5c8e53f5f42fcda790d9c4a81fa8a90b",
    REVIEW_INDEX: "b62a9d884b08b3b5132f64ca33531497343f208925e3a64eadd7980eee0d341f",
    CLASS_TEMPLATES: "596e218d1d29e16d65edfa1c804b63a528668ffc4083d4089427eda556f37ce1",
    SAMPLE_TEMPLATES: "662e95d3403a694da15dedd60dbdb81f98a9e404533693643b3721cd83a18bc1",
}

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
ENUM_FIELDS = (
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
LIST_PROPOSAL_FIELDS = {
    "local_reaction_center_atom_ids",
    "local_reaction_center_bond_ids",
    "proposed_pre_reaction_warhead_atom_ids",
    "required_leaving_group_atom_ids",
    "ambiguity_reasons",
}
ENUM_INT_FIELDS = {
    "warhead_type_candidate_class_index_0based",
    "bridge_candidate_index_0based",
    "warhead_side_atom_count",
    "nonwarhead_side_atom_count",
}
ENUM_BOOL_FIELDS = {
    "contains_local_reaction_center",
    "contains_required_leaving_groups",
    "warhead_side_connected",
    "exact_one_boundary_verified",
    "proper_subset",
    "candidate_admitted",
}
EXPECTED_FAILURE_MUTATIONS = (
    ("base_source_present", False, "BASE_source_missing"),
    ("base_source_sha_matches", False, "BASE_source_SHA_mismatch"),
    ("predecessor_transaction_succeeded", False, "predecessor_transaction_not_succeeded"),
    ("predecessor_proposal_readiness_count", 6, "predecessor_proposal_readiness_not_7"),
    ("class_count", 6, "class_count_not_7"),
    ("sample_count", 10, "sample_count_not_11"),
    ("duplicate_class_identity", True, "duplicate_class_identity"),
    ("duplicate_sample_identity", True, "duplicate_sample_identity"),
    ("class_rule_family_links_match", False, "class_rule_family_link_mismatch"),
    ("sample_class_rule_family_links_match", False, "sample_class_rule_family_link_mismatch"),
    ("parent_atom_authority_present", False, "parent_atom_authority_missing"),
    ("parent_bond_authority_present", False, "parent_bond_authority_missing"),
    ("parent_graph_sha_matches", False, "parent_graph_SHA_mismatch"),
    ("duplicate_parent_atom_id", True, "duplicate_parent_atom_ID"),
    ("duplicate_parent_bond", True, "duplicate_parent_bond"),
    ("parent_bond_endpoint_present", False, "parent_bond_endpoint_missing"),
    ("parent_graph_connected", False, "parent_graph_disconnected"),
    ("reactive_parent_mapping_exact_one", False, "reactive_parent_mapping_not_exact_one"),
    ("local_graph_json_sha_matches", False, "local_graph_JSON_SHA_mismatch"),
    ("local_reaction_center_degree_matches", False, "local_reaction_center_degree_mismatch"),
    ("local_neighbor_multiset_matches", False, "local_neighbor_multiset_mismatch"),
    ("leaving_group_evidence_matches", False, "leaving_group_evidence_mismatch"),
    ("bridge_enumeration_deterministic", False, "bridge_enumeration_nondeterministic"),
    ("bridge_candidate_indices_contiguous", False, "bridge_candidate_index_non_contiguous"),
    ("candidate_contains_local_center", False, "candidate_missing_local_reaction_center"),
    ("candidate_contains_leaving_groups", False, "candidate_missing_required_leaving_group"),
    ("candidate_warhead_side_connected", False, "candidate_warhead_side_disconnected"),
    ("candidate_boundary_exact_one", False, "candidate_boundary_not_exact_one"),
    ("auto_exact_candidate_count_valid", False, "auto_exact_status_candidate_count_not_1"),
    ("ambiguous_candidate_count_valid", False, "ambiguous_status_candidate_count_not_multiple"),
    ("quarantined_candidate_count_valid", False, "quarantined_status_candidate_count_not_0"),
    ("unresolved_proposal_fields_blank", False, "ambiguous_or_quarantined_proposal_fields_prefilled"),
    ("proposal_record_valid", False, "proposal_field_type_or_hash_invalid"),
    ("bridge_candidate_record_valid", False, "bridge_candidate_field_type_or_hash_invalid"),
    ("partial_materialization_attempted", True, "partial_materialization_attempted"),
    ("downstream_readiness_opened", True, "downstream_readiness_prematurely_opened"),
)
EXACT10 = (
    Path("src/covalent_ext") / f"{SCHEMA}.py",
    Path("tests") / f"test_{SCHEMA}.py",
    Path("scripts") / f"check_{SCHEMA}.py",
    Path("docs") / f"{SCHEMA}_summary.md",
    *(Path("data/derived/covalent_small") / SCHEMA / name for name in (
        "covapie_warhead_proposal_materialization_source_inventory.csv",
        "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals.csv",
        "covapie_current11_exact_one_boundary_bridge_candidate_enumeration.csv",
        "covapie_current11_warhead_proposal_readiness_matrix.csv",
        "covapie_warhead_proposal_materialization_failure_matrix.csv",
        "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_manifest.json",
    )),
)


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def git_result(
    *args: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
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
            f"git_failed:{args!r}:{result.stderr.decode('utf-8', 'replace')}"
        )
    return result


def git(*args: str) -> bytes:
    result = git_result(*args)
    return result.stdout


def current_lifecycle() -> str:
    """Independently classify the actual repository lifecycle, fail closed."""

    identity = git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE
    ).decode().splitlines()
    assert identity == [BASE, PARENT, TREE, BASE_SUBJECT]
    head = git("rev-parse", "HEAD").decode().strip()
    if head == BASE:
        return "pre_commit"

    raw = git("cat-file", "commit", head)
    headers, separator, message = raw.partition(b"\n\n")
    assert separator, "current_successor_commit_malformed"
    parents = tuple(
        line[7:].decode("utf-8")
        for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    assert parents == (BASE,), "current_successor_parent_invalid"
    subject, newline, body = message.partition(b"\n")
    assert newline, "current_successor_message_malformed"
    assert subject.decode("utf-8") == SUBJECT, "current_successor_subject_invalid"
    assert body == b"", "current_successor_body_nonempty"

    changed_paths = {
        item.decode("utf-8")
        for item in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            head,
        ).split(b"\0")
        if item
    }
    expected_paths = {path.as_posix() for path in EXACT10}
    assert changed_paths == expected_paths, "current_successor_changed_paths_invalid"
    tree_rows = [
        item
        for item in git(
            "ls-tree",
            "-r",
            "-z",
            head,
            "--",
            *(path.as_posix() for path in EXACT10),
        ).split(b"\0")
        if item
    ]
    modes = tuple(
        row.partition(b"\t")[0].split(b" ", 1)[0].decode("ascii")
        for row in tree_rows
    )
    assert modes == ("100644",) * 10, "current_successor_git_modes_invalid"

    symbolic = git_result(
        "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    if symbolic.returncode:
        return "detached_candidate_post_commit"
    branch = symbolic.stdout.decode("utf-8").strip()
    assert branch == "main", "current_successor_branch_invalid"
    origin_main = git(
        "rev-parse", "--verify", "refs/remotes/origin/main"
    ).decode().strip()
    if origin_main == BASE:
        return "formal_main_post_commit_unpushed"
    if origin_main == head:
        return "formal_main_post_push"
    raise AssertionError("current_successor_origin_main_relation_invalid")


def base_payloads() -> dict[Path, bytes]:
    identity = git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE
    ).decode().splitlines()
    assert identity == [BASE, PARENT, TREE, BASE_SUBJECT]
    payloads = {}
    for path, expected in FROZEN.items():
        payload = git("show", f"{BASE}:{path.as_posix()}")
        assert digest(payload) == expected
        payloads[path] = payload
    return payloads


def csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def output_csv(name: str) -> tuple[list[str], list[dict[str, str]]]:
    text = (OUT / name).read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader.fieldnames or ()), list(reader)


def utf8(values: Sequence[str] | set[str]) -> list[str]:
    return sorted(values, key=lambda item: item.encode("utf-8"))


def bond_id(left: str, right: str, order: str) -> str:
    low, high = utf8((left, right))
    assert low != high and order in {"single", "double", "aromatic"}
    return f"{low}|{high}|{order}"


def graph_sha(
    atoms: Sequence[Mapping[str, str]], bonds: Sequence[Mapping[str, str]]
) -> str:
    value = {
        "atoms": [
            [row["ccd_atom_id"], row["ccd_type_symbol"], int(row["ccd_formal_charge"])]
            for row in sorted(atoms, key=lambda row: row["ccd_atom_id"])
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
    return digest(canonical(value).encode())


def tarjan_bridges(
    atom_ids: Sequence[str], edges: Sequence[tuple[str, str, str]]
) -> list[tuple[str, str, str]]:
    """Independent deterministic Tarjan bridge implementation."""

    adjacency = {atom: [] for atom in atom_ids}
    order_by_pair = {}
    for left, right, order in edges:
        adjacency[left].append(right)
        adjacency[right].append(left)
        order_by_pair[frozenset((left, right))] = order
    clock = 0
    entered: dict[str, int] = {}
    low: dict[str, int] = {}
    found: list[tuple[str, str, str]] = []

    def visit(atom: str, parent: str | None) -> None:
        nonlocal clock
        entered[atom] = low[atom] = clock
        clock += 1
        for neighbor in utf8(adjacency[atom]):
            if neighbor == parent:
                continue
            if neighbor in entered:
                low[atom] = min(low[atom], entered[neighbor])
            else:
                visit(neighbor, atom)
                low[atom] = min(low[atom], low[neighbor])
                if low[neighbor] > entered[atom]:
                    found.append(
                        (atom, neighbor, order_by_pair[frozenset((atom, neighbor))])
                    )

    visit(utf8(atom_ids)[0], None)
    assert len(entered) == len(atom_ids)
    return sorted(found, key=lambda item: bond_id(*item).encode())


def side_after_cut(
    atom_ids: Sequence[str],
    edges: Sequence[tuple[str, str, str]],
    reactive: str,
    cut: frozenset[str],
) -> set[str]:
    adjacency = {atom: [] for atom in atom_ids}
    for left, right, _order in edges:
        if frozenset((left, right)) != cut:
            adjacency[left].append(right)
            adjacency[right].append(left)
    seen = set()
    queue = deque([reactive])
    while queue:
        atom = queue.popleft()
        if atom in seen:
            continue
        seen.add(atom)
        queue.extend(item for item in utf8(adjacency[atom]) if item not in seen)
    return seen


def typed_proposal(row: Mapping[str, str]) -> dict[str, Any]:
    value = {}
    for field in PROPOSAL_FIELDS:
        if field == "warhead_type_candidate_class_index_0based":
            value[field] = int(row[field])
        elif field in LIST_PROPOSAL_FIELDS:
            value[field] = json.loads(row[field])
        else:
            value[field] = row[field]
    return value


def typed_enumeration(row: Mapping[str, str]) -> dict[str, Any]:
    value = {}
    for field in ENUM_FIELDS:
        if field in ENUM_INT_FIELDS:
            value[field] = int(row[field])
        elif field == "warhead_side_atom_ids":
            value[field] = json.loads(row[field])
        elif field in ENUM_BOOL_FIELDS:
            assert row[field] in {"true", "false"}
            value[field] = row[field] == "true"
        else:
            value[field] = row[field]
    return value


def proposal_sha(row: Mapping[str, Any]) -> str:
    return digest(
        canonical(
            {field: row[field] for field in PROPOSAL_FIELDS if field != "proposal_record_sha256"}
        ).encode()
    )


def enumeration_sha(row: Mapping[str, Any]) -> str:
    return digest(
        canonical(
            {
                field: row[field]
                for field in ENUM_FIELDS
                if field != "bridge_candidate_record_sha256"
            }
        ).encode()
    )


def rebuild(payloads: Mapping[Path, bytes]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    assignments = sorted(
        csv_rows(payloads[ASSIGNMENTS]), key=lambda row: row["sample_index_row_id"]
    )
    rules = {row["warhead_rule_id"]: row for row in csv_rows(payloads[RULES])}
    atoms_all = csv_rows(payloads[ATOMS])
    bonds_all = csv_rows(payloads[BONDS])
    maps_all = csv_rows(payloads[MAPPINGS])
    expected_proposals = []
    expected_enumerations = []
    for sample in assignments:
        sample_id = sample["sample_index_row_id"]
        component = sample["ligand_comp_id"]
        sha = sample["component_parent_graph_sha256"]
        atoms = [
            row
            for row in atoms_all
            if row["ligand_comp_id"] == component
            and row["component_parent_graph_sha256"] == sha
        ]
        bonds = [
            row
            for row in bonds_all
            if row["ligand_comp_id"] == component
            and row["component_parent_graph_sha256"] == sha
        ]
        assert atoms and bonds
        assert all(row["verified"] == "true" for row in (*atoms, *bonds))
        by_id = {row["ccd_atom_id"]: row for row in atoms}
        assert len(by_id) == len(atoms)
        edges = []
        pairs = set()
        adjacency = {atom: [] for atom in by_id}
        for row in bonds:
            left, right = row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]
            order = row["normalized_bond_order"]
            assert left in by_id and right in by_id and left != right
            assert frozenset((left, right)) not in pairs
            pairs.add(frozenset((left, right)))
            edges.append((left, right, order))
            adjacency[left].append((right, order))
            adjacency[right].append((left, order))
        assert graph_sha(atoms, bonds) == sha
        reactive_maps = [
            row
            for row in maps_all
            if row["sample_index_row_id"] == sample_id
            and row["reactive_ligand_atom"] == "true"
            and row["verified"] == "true"
        ]
        assert len(reactive_maps) == 1
        reactive = reactive_maps[0]["parent_ccd_atom_id"]
        assert reactive == sample["ligand_reactive_parent_ccd_atom_id"]
        observed = {
            row["parent_ccd_atom_id"]
            for row in maps_all
            if row["sample_index_row_id"] == sample_id
            and row["verified"] == "true"
        }
        rule = rules[sample["candidate_warhead_rule_id"]]
        local_json = json.loads(rule["canonical_local_graph_rule_json"])
        assert digest(canonical(local_json).encode()) == rule["canonical_local_graph_rule_sha256"]
        assert local_json["selected_signature_radius"] == 1
        assert local_json["center_atom"]["reactive"] is True
        assert local_json["target_condition"] == {
            "formed_bond_order": "single",
            "residue": "CYS",
            "residue_atom": "SG",
        }
        center_id = local_json["center_atom"]["canonical_local_atom_id"]
        noncenter = [
            atom
            for atom in local_json["local_atoms"]
            if atom["canonical_local_atom_id"] != center_id
        ]
        assert len(noncenter) == len(adjacency[reactive])
        expected_neighbors = []
        for atom in noncenter:
            local_id = atom["canonical_local_atom_id"]
            matching = [
                bond
                for bond in local_json["local_bonds"]
                if {
                    bond["canonical_endpoint_1"],
                    bond["canonical_endpoint_2"],
                }
                == {center_id, local_id}
            ]
            assert len(matching) == 1
            expected_neighbors.append(
                (
                    atom["element"],
                    atom["formal_charge"],
                    matching[0]["normalized_bond_order"],
                    "leaving" if atom["is_leaving_group"] else "retained",
                )
            )
        actual_neighbors = [
            (
                by_id[neighbor]["ccd_type_symbol"],
                int(by_id[neighbor]["ccd_formal_charge"]),
                order,
                "retained" if neighbor in observed else "leaving",
            )
            for neighbor, order in adjacency[reactive]
        ]
        assert Counter(expected_neighbors) == Counter(actual_neighbors)
        local_ids = utf8({reactive, *(neighbor for neighbor, _ in adjacency[reactive])})
        local_bonds = utf8(
            [bond_id(reactive, neighbor, order) for neighbor, order in adjacency[reactive]]
        )
        leaving = utf8(
            [neighbor for neighbor, _order in adjacency[reactive] if neighbor not in observed]
        )
        delta = local_json["reaction_delta"]
        assert len(leaving) == delta["leaving_group_count"]
        assert sorted(by_id[item]["ccd_type_symbol"] for item in leaving) == delta["leaving_group_elements"]

        bridges = tarjan_bridges(list(by_id), edges)
        candidates = []
        for index, (left, right, order) in enumerate(bridges):
            side = side_after_cut(
                list(by_id), edges, reactive, frozenset((left, right))
            )
            contains_local = set(local_ids) <= side
            contains_leaving = set(leaving) <= side
            blockers = []
            if not contains_local:
                blockers.append("candidate_missing_local_reaction_center")
            if not contains_leaving:
                blockers.append("candidate_missing_required_leaving_group")
            identity = {
                "sample_index_row_id": sample_id,
                "pdb_id": sample["pdb_id"],
                "ligand_comp_id": component,
                "warhead_type_candidate_class_index_0based": int(
                    sample["warhead_type_candidate_class_index_0based"]
                ),
                "warhead_type_candidate_class_id": sample[
                    "warhead_type_candidate_class_id"
                ],
                "reaction_family_id": sample["candidate_reaction_family_id"],
                "warhead_rule_id": sample["candidate_warhead_rule_id"],
                "component_parent_graph_sha256": sha,
            }
            row = {
                "enumeration_version": ENUM_VERSION,
                **identity,
                "bridge_candidate_index_0based": index,
                "boundary_bond_id": bond_id(left, right, order),
                "warhead_side_atom_ids": utf8(side),
                "warhead_side_atom_count": len(side),
                "nonwarhead_side_atom_count": len(by_id) - len(side),
                "contains_local_reaction_center": contains_local,
                "contains_required_leaving_groups": contains_leaving,
                "warhead_side_connected": True,
                "exact_one_boundary_verified": True,
                "proper_subset": True,
                "candidate_admitted": not blockers,
                "blocking_reasons": ";".join(utf8(blockers)),
                "bridge_candidate_record_sha256": "",
            }
            row["bridge_candidate_record_sha256"] = enumeration_sha(row)
            candidates.append(row)
            expected_enumerations.append(row)
        admitted = [row for row in candidates if row["candidate_admitted"]]
        status = (
            "auto_exact_candidate"
            if len(admitted) == 1
            else "ambiguous_candidate"
            if len(admitted) > 1
            else "quarantined"
        )
        warhead_ids = []
        attachment = nonwarhead = boundary_order = ""
        ambiguity = []
        if status == "auto_exact_candidate":
            chosen = admitted[0]
            warhead_ids = chosen["warhead_side_atom_ids"]
            left, right, boundary_order = chosen["boundary_bond_id"].split("|")
            attachment = left if left in set(warhead_ids) else right
            nonwarhead = right if attachment == left else left
        elif status == "ambiguous_candidate":
            ambiguity = ["multiple_admissible_exact_one_boundary_candidates"]
        else:
            ambiguity = ["no_admissible_exact_one_boundary_candidate"]
        proposal = {
            "proposal_version": PROPOSAL_VERSION,
            "sample_index_row_id": sample_id,
            "pdb_id": sample["pdb_id"],
            "ligand_comp_id": component,
            "warhead_type_candidate_class_index_0based": int(
                sample["warhead_type_candidate_class_index_0based"]
            ),
            "warhead_type_candidate_class_id": sample[
                "warhead_type_candidate_class_id"
            ],
            "reaction_family_id": sample["candidate_reaction_family_id"],
            "warhead_rule_id": sample["candidate_warhead_rule_id"],
            "component_parent_graph_sha256": sha,
            "ligand_reactive_parent_atom_id": reactive,
            "local_reaction_center_atom_ids": local_ids,
            "local_reaction_center_bond_ids": local_bonds,
            "proposed_pre_reaction_warhead_atom_ids": warhead_ids,
            "proposed_warhead_attachment_atom_id": attachment,
            "proposed_nonwarhead_boundary_atom_id": nonwarhead,
            "proposed_attachment_boundary_bond_order": boundary_order,
            "required_leaving_group_atom_ids": leaving,
            "proposal_method": METHOD,
            "proposal_status": status,
            "ambiguity_reasons": ambiguity,
            "source_assignment_record_sha256": sample["assignment_record_sha256"],
            "proposal_record_sha256": "",
        }
        proposal["proposal_record_sha256"] = proposal_sha(proposal)
        expected_proposals.append(proposal)
    return expected_proposals, expected_enumerations


def verify_failure_matrix() -> None:
    fields, rows = output_csv(
        "covapie_warhead_proposal_materialization_failure_matrix.csv"
    )
    assert len(fields) == 17 and len(rows) == len(EXPECTED_FAILURE_MUTATIONS) == 36
    assert len({row["mutation_signature"] for row in rows}) == 36
    for row, (field, expected_value, expected_reason) in zip(
        rows, EXPECTED_FAILURE_MUTATIONS
    ):
        value = json.loads(row["mutated_value_json"])
        assert row["mutated_field"] == field
        assert type(value) is type(expected_value) and value == expected_value
        assert row["expected_reason"] == expected_reason
        expected_signature = digest(
            canonical(
                {"mutated_field": row["mutated_field"], "mutated_value": value}
            ).encode()
        )
        assert row["mutation_signature"] == expected_signature
        assert row["expected_reason"] in row["observed_reasons"].split(";")
        assert row["expected_reason_verified"] == "true"
        assert row["fails_closed"] == "true"
        assert row["proposal_row_count"] == "0"
        assert row["bridge_enumeration_row_count"] == "0"
        assert row["readiness_row_count"] == "0"
        assert all(
            row[field] == "false"
            for field in ("SMARTS_ready", "role_ready", "mask_ready", "model_ready", "training_ready")
        )
        assert row["verified"] == "true"


def verify_lifecycle() -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="covapie_proposal_lifecycle_") as temp:
        report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
            ROOT,
            Path(temp),
            base_commit=BASE,
            formal_commit_subject=SUBJECT,
            exact_paths=EXACT10,
        )
    assert report.cleanup_verified is True
    assert report.candidate_parent == BASE
    assert report.candidate_subject == SUBJECT
    assert report.exact_path_count == 10
    states = (
        report.pre_commit,
        report.detached_candidate_post_commit,
        report.formal_main_post_commit_unpushed,
        report.formal_main_post_push,
    )
    assert tuple(state.lifecycle for state in states) == lifecycle.LIFECYCLES
    return report.candidate_commit, ",".join(state.lifecycle for state in states)


def run() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    import pytest
    import rdkit

    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"
    actual_lifecycle = current_lifecycle()
    assert actual_lifecycle in CURRENT_LIFECYCLES
    payloads = base_payloads()
    design_manifest = json.loads(payloads[DESIGN_MANIFEST])
    assert design_manifest["transaction_succeeded"] is True
    assert design_manifest[
        "warhead_atom_set_and_boundary_proposal_materialization_ready_count"
    ] == 7
    assert tuple(design_manifest["proposal_fields"]) == PROPOSAL_FIELDS
    assert len(csv_rows(payloads[CLASSES])) == 7
    assert len(csv_rows(payloads[ASSIGNMENTS])) == 11

    proposal_fields, proposal_rows = output_csv(
        "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals.csv"
    )
    enumeration_fields, enumeration_rows = output_csv(
        "covapie_current11_exact_one_boundary_bridge_candidate_enumeration.csv"
    )
    readiness_fields, readiness_rows = output_csv(
        "covapie_current11_warhead_proposal_readiness_matrix.csv"
    )
    assert tuple(proposal_fields) == PROPOSAL_FIELDS and len(proposal_rows) == 11
    assert tuple(enumeration_fields) == ENUM_FIELDS and len(enumeration_rows) == 200
    assert len(readiness_fields) == 27 and len(readiness_rows) == 11
    actual_proposals = [typed_proposal(row) for row in proposal_rows]
    actual_enumerations = [typed_enumeration(row) for row in enumeration_rows]
    expected_proposals, expected_enumerations = rebuild(payloads)
    assert actual_proposals == expected_proposals
    assert actual_enumerations == expected_enumerations
    assert all(row["proposal_record_sha256"] == proposal_sha(row) for row in actual_proposals)
    assert all(
        row["bridge_candidate_record_sha256"] == enumeration_sha(row)
        for row in actual_enumerations
    )
    assert Counter(row["proposal_status"] for row in actual_proposals) == {
        "ambiguous_candidate": 11
    }
    assert sum(row["candidate_admitted"] for row in actual_enumerations) == 185
    assert all(
        not row["proposed_pre_reaction_warhead_atom_ids"]
        and not row["proposed_warhead_attachment_atom_id"]
        and not row["proposed_nonwarhead_boundary_atom_id"]
        and not row["proposed_attachment_boundary_bond_order"]
        for row in actual_proposals
    )
    for row in readiness_rows:
        assert row["proposal_materialized"] == "true"
        assert row["ready_for_proposal_human_review"] == "true"
        assert all(
            row[field] == "false"
            for field in (
                "complete_warhead_atom_set_authority_available",
                "exact_one_attachment_boundary_authority_available",
                "ready_for_candidate_warhead_smarts_materialization",
                "ready_for_SMARTS_review_execution",
                "ready_for_role_proposal_generation",
                "ready_for_mask_materialization",
                "ready_for_model_integration",
                "ready_for_training",
            )
        )
    verify_failure_matrix()

    manifest_payload = (OUT / (
        "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_"
        "proposals_manifest.json"
    )).read_bytes()
    manifest = json.loads(manifest_payload)
    assert manifest["transaction_succeeded"] is True
    assert manifest["source_count"] == 16
    assert manifest["proposal_record_count"] == 11
    assert manifest["ambiguous_candidate_count"] == 11
    assert manifest["auto_exact_candidate_count"] == 0
    assert manifest["quarantined_count"] == 0
    assert manifest["not_materialized_count"] == 0
    assert manifest["total_parent_bridge_count"] == 200
    assert manifest["total_admitted_boundary_candidate_count"] == 185
    assert manifest["failure_mutation_count"] == 36
    assert "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_manifest.json" not in manifest["output_sha256"]
    for name, expected in manifest["output_sha256"].items():
        assert digest((OUT / name).read_bytes()) == expected
    rendered = manifest_payload.decode()
    assert re.search(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", rendered) is None
    assert str(ROOT) not in rendered
    assert manifest["approved_warhead_rule_available_count"] == 0
    assert manifest["approved_warhead_smarts_count"] == 0
    assert manifest["role_annotation_materialized"] is False
    assert manifest["mask_materialized"] is False
    assert manifest["model_changed"] is False
    assert manifest["training_used"] is False
    candidate, lifecycle_names = verify_lifecycle()
    print("checker=passed")
    print("python=3.10.4 pytest=9.1.0 rdkit=2022.03.2")
    print("sources=16 proposals=11 bridges=200 admitted=185")
    print("statuses=auto:0,ambiguous:11,quarantined:0,not_materialized:0")
    print("failure_mutations=36 all_fail_closed=true")
    print("current_lifecycle=" + actual_lifecycle)
    print("hermetic_lifecycle=" + lifecycle_names)
    print("candidate_commit=" + candidate)


if __name__ == "__main__":
    run()

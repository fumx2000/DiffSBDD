#!/usr/bin/env python3
"""Independent checker for Current11 warhead/boundary review packages v1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
BASE = "ec9b1efbcfc49eeda55d7318b38daec67455343a"
BASE_IDENTITY = (
    BASE,
    "5cac27027c824cd38bad3479a59f586b2714142c",
    "4ac36dc3946d2bcad3bb345862d90a2daa677c15",
    "add CovaPIE Current11 pre-reaction warhead atom set and attachment boundary proposals v1",
)
SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review packages v1"
)
SCHEMA = "covapie_current11_warhead_atom_set_and_attachment_boundary_review_packages_v1"
OUTPUT = Path("data/derived/covalent_small") / SCHEMA
CANDIDATE_SET_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_candidate_set_v1"
)
OPTION_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_review_option_v1"
)
REVIEW_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_human_review_record_v1"
)
REVIEW_UNIT = "sample_warhead_atom_set_and_attachment_boundary"
INDEX_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_package_index_v1"
)
SOURCE_FILE = "covapie_warhead_boundary_review_package_source_inventory.csv"
INDEX_FILE = "covapie_current11_warhead_boundary_review_package_index.csv"
OPTION_FILE = "covapie_current11_warhead_boundary_candidate_review_options.csv"
TEMPLATE_FILE = "covapie_current11_warhead_boundary_review_record_templates.csv"
FAILURE_FILE = "covapie_warhead_boundary_review_package_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE, INDEX_FILE, OPTION_FILE, TEMPLATE_FILE, FAILURE_FILE, MANIFEST_FILE,
)
EXACT10 = (
    Path("src/covalent_ext") / f"{SCHEMA}.py",
    Path("tests") / f"test_{SCHEMA}.py",
    Path("scripts") / f"check_{SCHEMA}.py",
    Path("docs") / f"{SCHEMA}_summary.md",
    *(OUTPUT / name for name in OUTPUT_FILES),
)

PROPOSAL_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals_v1"
)
PROPOSAL_SOURCE = Path("src/covalent_ext") / (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals_v1.py"
)
PROPOSALS = PROPOSAL_ROOT / (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals.csv"
)
ENUMERATIONS = (
    PROPOSAL_ROOT / "covapie_current11_exact_one_boundary_bridge_candidate_enumeration.csv"
)
READINESS = PROPOSAL_ROOT / "covapie_current11_warhead_proposal_readiness_matrix.csv"
PREDECESSOR_FAILURE = (
    PROPOSAL_ROOT / "covapie_warhead_proposal_materialization_failure_matrix.csv"
)
PROPOSAL_MANIFEST = PROPOSAL_ROOT / (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals_manifest.json"
)
ASSIGNMENTS = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/"
    "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
PARENT_ATOMS = Path(
    "data/derived/covalent_small/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1/"
    "covapie_exact9_parent_heavy_atom_authority.csv"
)
PARENT_BONDS = Path(
    "data/derived/covalent_small/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1/"
    "covapie_exact9_parent_heavy_bond_authority.csv"
)
MAPPINGS = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
    "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)
RULES = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/"
    "covapie_cys_sg_warhead_rule_registry.csv"
)
PRIOR = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1"
)
PRIOR_MANIFEST = PRIOR / (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_"
    "review_packages_manifest.json"
)
PRIOR_INDEX = PRIOR / "covapie_review_package_index.csv"
PRIOR_CLASS = PRIOR / "covapie_cys_sg_candidate_class_review_record_templates.csv"
PRIOR_SAMPLE = PRIOR / "covapie_current11_sample_assignment_review_record_templates.csv"
EXPECTED_SHA = {
    PROPOSAL_SOURCE: "f50c9f4c0940b8e6c34cc0715a4160bf613511d61a1421f9e1bc7d2b71a27b25",
    PROPOSALS: "7e72fc157bb52cc2d5cba0c3fd2a7ac88f92bc50a35d001cfff0c2bf3296b4b0",
    ENUMERATIONS: "968105718614996fdee98ace96fd1362c86814ebdb774491328f6db66e380b2a",
    READINESS: "1c37feec87d2b79d27912d587ad9b8f07e9f3d8f2c8f4d5464f5f19ffc19b916",
    PREDECESSOR_FAILURE: "1a9a96145c190da98740526e9306c1688650dd63e711f84193fedf02fd3fb14d",
    PROPOSAL_MANIFEST: "fed5f97d177b9a0f91ec7eebf8ea3081662731e50ca6a74f3898f3068a5e6b79",
    ASSIGNMENTS: "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    PARENT_ATOMS: "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    PARENT_BONDS: "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    MAPPINGS: "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    RULES: "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    PRIOR_MANIFEST: "677034c0b8822e0b1476e28d00bb8dda5c8e53f5f42fcda790d9c4a81fa8a90b",
    PRIOR_INDEX: "b62a9d884b08b3b5132f64ca33531497343f208925e3a64eadd7980eee0d341f",
    PRIOR_CLASS: "596e218d1d29e16d65edfa1c804b63a528668ffc4083d4089427eda556f37ce1",
    PRIOR_SAMPLE: "662e95d3403a694da15dedd60dbdb81f98a9e404533693643b3721cd83a18bc1",
}

PROPOSAL_FIELDS = (
    "proposal_version", "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "component_parent_graph_sha256", "ligand_reactive_parent_atom_id",
    "local_reaction_center_atom_ids", "local_reaction_center_bond_ids",
    "proposed_pre_reaction_warhead_atom_ids",
    "proposed_warhead_attachment_atom_id",
    "proposed_nonwarhead_boundary_atom_id",
    "proposed_attachment_boundary_bond_order",
    "required_leaving_group_atom_ids", "proposal_method", "proposal_status",
    "ambiguity_reasons", "source_assignment_record_sha256",
    "proposal_record_sha256",
)
ENUM_FIELDS = (
    "enumeration_version", "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "component_parent_graph_sha256", "bridge_candidate_index_0based",
    "boundary_bond_id", "warhead_side_atom_ids", "warhead_side_atom_count",
    "nonwarhead_side_atom_count", "contains_local_reaction_center",
    "contains_required_leaving_groups", "warhead_side_connected",
    "exact_one_boundary_verified", "proper_subset", "candidate_admitted",
    "blocking_reasons", "bridge_candidate_record_sha256",
)
OPTION_FIELDS = (
    "package_option_version", "package_item_order_0based",
    "option_order_within_sample_0based", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_candidate_set_sha256",
    "source_bridge_candidate_index_0based",
    "source_bridge_candidate_record_sha256", "boundary_bond_id",
    "warhead_attachment_atom_id", "nonwarhead_boundary_atom_id",
    "boundary_bond_order", "warhead_side_atom_ids",
    "warhead_extra_atom_ids_beyond_local_center",
    "local_reaction_center_atom_ids", "required_leaving_group_atom_ids",
    "warhead_side_atom_count", "nonwarhead_side_atom_count",
    "candidate_admitted", "review_eligible", "blocking_reasons",
    "package_option_record_sha256",
)
REVIEW_FIELDS = (
    "review_record_version", "review_unit_type", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_assignment_record_sha256",
    "source_candidate_set_sha256", "total_candidate_count",
    "admitted_candidate_count", "review_decision",
    "selected_bridge_candidate_index_0based",
    "selected_bridge_candidate_record_sha256", "reviewed_warhead_atom_ids",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order", "reviewed_boundary_bond_id",
    "reviewer_id", "review_rationale", "review_notes", "review_record_sha256",
)
INDEX_FIELDS = (
    "package_index_version", "package_item_order_0based",
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_assignment_record_sha256",
    "source_candidate_set_sha256", "total_candidate_count",
    "admitted_candidate_count", "source_proposal_status",
    "candidate_option_row_start_0based", "candidate_option_row_end_exclusive",
    "review_record_version", "unreviewed_template_payload_sha256",
    "review_options_materialized", "review_template_materialized",
    "ready_for_human_review", "human_review_completed",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available",
    "ready_for_candidate_warhead_smarts_materialization",
    "ready_for_role_proposal_generation", "blocking_reasons", "verified",
)
LIST_PROPOSAL = {
    "local_reaction_center_atom_ids", "local_reaction_center_bond_ids",
    "proposed_pre_reaction_warhead_atom_ids", "required_leaving_group_atom_ids",
    "ambiguity_reasons",
}
INT_ENUM = {
    "warhead_type_candidate_class_index_0based", "bridge_candidate_index_0based",
    "warhead_side_atom_count", "nonwarhead_side_atom_count",
}
BOOL_ENUM = {
    "contains_local_reaction_center", "contains_required_leaving_groups",
    "warhead_side_connected", "exact_one_boundary_verified", "proper_subset",
    "candidate_admitted",
}
SHA = re.compile(r"[0-9a-f]{64}")


def run_git(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *args), cwd=ROOT, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode())
    return result.stdout


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode())))


def base_payload(path: Path) -> bytes:
    payload = run_git("show", f"{BASE}:{path.as_posix()}")
    assert payload and digest(payload) == EXPECTED_SHA[path]
    return payload


def parse_int(value: str) -> int:
    assert value and value.isdecimal() and (value == "0" or not value.startswith("0"))
    return int(value)


def parse_bool(value: str) -> bool:
    assert value in ("true", "false")
    return value == "true"


def typed_proposal(row: Mapping[str, str]) -> dict[str, Any]:
    assert tuple(row) == PROPOSAL_FIELDS
    result = {}
    for field in PROPOSAL_FIELDS:
        if field == "warhead_type_candidate_class_index_0based":
            result[field] = parse_int(row[field])
        elif field in LIST_PROPOSAL:
            result[field] = json.loads(row[field])
            assert type(result[field]) is list
        else:
            result[field] = row[field]
    expected = digest(canonical({
        field: result[field] for field in PROPOSAL_FIELDS
        if field != "proposal_record_sha256"
    }).encode())
    assert result["proposal_record_sha256"] == expected
    return result


def typed_candidate(row: Mapping[str, str]) -> dict[str, Any]:
    assert tuple(row) == ENUM_FIELDS
    result = {}
    for field in ENUM_FIELDS:
        if field in INT_ENUM:
            result[field] = parse_int(row[field])
        elif field in BOOL_ENUM:
            result[field] = parse_bool(row[field])
        elif field == "warhead_side_atom_ids":
            result[field] = json.loads(row[field])
        else:
            result[field] = row[field]
    expected = digest(canonical({
        field: result[field] for field in ENUM_FIELDS
        if field != "bridge_candidate_record_sha256"
    }).encode())
    assert result["bridge_candidate_record_sha256"] == expected
    return result


def typed_option(row: Mapping[str, str]) -> dict[str, Any]:
    assert tuple(row) == OPTION_FIELDS
    ints = {
        "package_item_order_0based", "option_order_within_sample_0based",
        "warhead_type_candidate_class_index_0based",
        "source_bridge_candidate_index_0based", "warhead_side_atom_count",
        "nonwarhead_side_atom_count",
    }
    bools = {"candidate_admitted", "review_eligible"}
    lists = {
        "warhead_side_atom_ids", "warhead_extra_atom_ids_beyond_local_center",
        "local_reaction_center_atom_ids", "required_leaving_group_atom_ids",
    }
    result = {}
    for field in OPTION_FIELDS:
        result[field] = (
            parse_int(row[field]) if field in ints
            else parse_bool(row[field]) if field in bools
            else json.loads(row[field]) if field in lists
            else row[field]
        )
    assert result["review_eligible"] is result["candidate_admitted"]
    assert result["package_option_record_sha256"] == digest(canonical({
        field: result[field] for field in OPTION_FIELDS
        if field != "package_option_record_sha256"
    }).encode())
    return result


def typed_template(row: Mapping[str, str]) -> dict[str, Any]:
    assert tuple(row) == REVIEW_FIELDS
    ints = {
        "warhead_type_candidate_class_index_0based", "total_candidate_count",
        "admitted_candidate_count",
    }
    result = {}
    for field in REVIEW_FIELDS:
        if field in ints:
            result[field] = parse_int(row[field])
        elif field == "selected_bridge_candidate_index_0based":
            result[field] = None if row[field] == "" else parse_int(row[field])
        elif field == "reviewed_warhead_atom_ids":
            result[field] = json.loads(row[field])
        else:
            result[field] = row[field]
    return result


def current_lifecycle() -> str:
    assert tuple(
        run_git("show", "-s", "--format=%H%n%P%n%T%n%s", BASE).decode().splitlines()
    ) == BASE_IDENTITY
    head = run_git("rev-parse", "HEAD").decode().strip()
    if head == BASE:
        return "pre_commit"
    raw = run_git("cat-file", "commit", head)
    headers, separator, message = raw.partition(b"\n\n")
    assert separator
    parents = tuple(
        line[7:].decode() for line in headers.splitlines() if line.startswith(b"parent ")
    )
    subject, newline, body = message.partition(b"\n")
    assert parents == (BASE,) and newline and subject.decode() == SUBJECT and not body
    changed = {
        item.decode() for item in run_git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).split(b"\0") if item
    }
    assert changed == {path.as_posix() for path in EXACT10}
    branch = subprocess.run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"), cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    assert branch.stdout.decode().strip() == "main"
    origin = run_git("rev-parse", "origin/main").decode().strip()
    if origin == BASE:
        return "formal_main_post_commit_unpushed"
    assert origin == head
    return "formal_main_post_push"


def check() -> tuple[str, str]:
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:3] == (3, 10, 4)
    assert tuple(
        run_git("show", "-s", "--format=%H%n%P%n%T%n%s", BASE).decode().splitlines()
    ) == BASE_IDENTITY
    frozen = {path: base_payload(path) for path in EXPECTED_SHA}
    proposals = [typed_proposal(row) for row in rows(frozen[PROPOSALS])]
    candidates = [typed_candidate(row) for row in rows(frozen[ENUMERATIONS])]
    readiness = rows(frozen[READINESS])
    parent_atoms = rows(frozen[PARENT_ATOMS])
    parent_bonds = rows(frozen[PARENT_BONDS])
    assert (len(proposals), len(candidates), len(readiness)) == (11, 200, 11)
    assert len(rows(frozen[PREDECESSOR_FAILURE])) == 36
    assert all(
        row["proposal_status"] == "ambiguous_candidate"
        and row["ambiguity_reasons"]
        == ["multiple_admissible_exact_one_boundary_candidates"]
        and row["proposed_pre_reaction_warhead_atom_ids"] == []
        and not row["proposed_warhead_attachment_atom_id"]
        and not row["proposed_nonwarhead_boundary_atom_id"]
        and not row["proposed_attachment_boundary_bond_order"]
        for row in proposals
    )
    for candidate in candidates:
        graph_atoms = {
            row["ccd_atom_id"] for row in parent_atoms
            if row["ligand_comp_id"] == candidate["ligand_comp_id"]
            and row["component_parent_graph_sha256"]
            == candidate["component_parent_graph_sha256"]
        }
        graph_bonds = [
            row for row in parent_bonds
            if row["ligand_comp_id"] == candidate["ligand_comp_id"]
            and row["component_parent_graph_sha256"]
            == candidate["component_parent_graph_sha256"]
        ]
        warhead = candidate["warhead_side_atom_ids"]
        warhead_set = set(warhead)
        assert warhead == sorted(warhead, key=lambda value: value.encode())
        assert len(warhead) == len(warhead_set) and warhead_set < graph_atoms
        left, right, order = candidate["boundary_bond_id"].split("|")
        assert [left, right] == sorted((left, right), key=lambda value: value.encode())
        assert sum(
            {
                bond["parent_ccd_atom_id_1"], bond["parent_ccd_atom_id_2"]
            } == {left, right}
            and bond["normalized_bond_order"] == order
            for bond in graph_bonds
        ) == 1
        assert sum(
            (bond["parent_ccd_atom_id_1"] in warhead_set)
            != (bond["parent_ccd_atom_id_2"] in warhead_set)
            for bond in graph_bonds
        ) == 1
    predecessor = json.loads(frozen[PROPOSAL_MANIFEST])
    assert predecessor["transaction_succeeded"] is True
    assert predecessor["total_admitted_boundary_candidate_count"] == 185
    assert predecessor["complete_warhead_atom_set_authority_available_count"] == 0
    assert predecessor["exact_one_attachment_boundary_authority_available_count"] == 0
    assert predecessor["ready_for_training"] is False

    output_payloads = {
        name: (ROOT / OUTPUT / name).read_bytes() for name in OUTPUT_FILES
    }
    source_rows = rows(output_payloads[SOURCE_FILE])
    assert len(source_rows) == 15
    assert [row["source_path"] for row in source_rows] == [
        path.as_posix() for path in EXPECTED_SHA
    ]
    assert all(
        row["BASE_SHA256"] == EXPECTED_SHA[Path(row["source_path"])]
        and row["verified"] == "true" for row in source_rows
    )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate["sample_index_row_id"]].append(candidate)
    set_sha = {}
    proposal_by_sample = {row["sample_index_row_id"]: row for row in proposals}
    expected_options = []
    for proposal in sorted(proposals, key=lambda row: row["sample_index_row_id"]):
        sample = proposal["sample_index_row_id"]
        sample_candidates = sorted(
            grouped[sample], key=lambda row: row["bridge_candidate_index_0based"]
        )
        assert [row["bridge_candidate_index_0based"] for row in sample_candidates] == list(
            range(len(sample_candidates))
        )
        all_shas = [row["bridge_candidate_record_sha256"] for row in sample_candidates]
        admitted = [
            row["bridge_candidate_record_sha256"] for row in sample_candidates
            if row["candidate_admitted"]
        ]
        payload = {
            "candidate_set_version": CANDIDATE_SET_VERSION,
            "sample_index_row_id": sample,
            "source_proposal_record_sha256": proposal["proposal_record_sha256"],
            "all_bridge_candidate_record_sha256s": all_shas,
            "admitted_bridge_candidate_record_sha256s": admitted,
        }
        set_sha[sample] = digest(canonical(payload).encode())
        for candidate in sample_candidates:
            left, right, order = candidate["boundary_bond_id"].split("|")
            warhead = set(candidate["warhead_side_atom_ids"])
            assert (left in warhead) != (right in warhead)
            attachment = left if left in warhead else right
            nonwarhead = right if attachment == left else left
            expected_options.append((
                sample, candidate["bridge_candidate_index_0based"],
                candidate["bridge_candidate_record_sha256"], set_sha[sample],
                attachment, nonwarhead, order,
                sorted(
                    warhead - set(proposal["local_reaction_center_atom_ids"]),
                    key=lambda value: value.encode(),
                ),
            ))
    assert len(set(set_sha.values())) == 11

    options = [typed_option(row) for row in rows(output_payloads[OPTION_FILE])]
    assert len(options) == 200
    assert sum(row["review_eligible"] for row in options) == 185
    for order, (option, expected) in enumerate(zip(options, expected_options)):
        assert option["package_item_order_0based"] == order
        assert (
            option["sample_index_row_id"],
            option["source_bridge_candidate_index_0based"],
            option["source_bridge_candidate_record_sha256"],
            option["source_candidate_set_sha256"],
            option["warhead_attachment_atom_id"],
            option["nonwarhead_boundary_atom_id"],
            option["boundary_bond_order"],
            option["warhead_extra_atom_ids_beyond_local_center"],
        ) == expected

    templates = [typed_template(row) for row in rows(output_payloads[TEMPLATE_FILE])]
    assert len(templates) == 11
    template_by_sample = {row["sample_index_row_id"]: row for row in templates}
    for row in templates:
        assert row["review_record_version"] == REVIEW_VERSION
        assert row["review_unit_type"] == REVIEW_UNIT
        assert row["review_decision"] == "not_reviewed"
        assert row["selected_bridge_candidate_index_0based"] is None
        assert not row["selected_bridge_candidate_record_sha256"]
        assert row["reviewed_warhead_atom_ids"] == []
        assert not any(row[field] for field in (
            "reviewed_warhead_attachment_atom_id",
            "reviewed_nonwarhead_boundary_atom_id",
            "reviewed_attachment_boundary_bond_order", "reviewed_boundary_bond_id",
            "reviewer_id", "review_rationale", "review_notes", "review_record_sha256",
        ))

    indexes = rows(output_payloads[INDEX_FILE])
    assert len(indexes) == 11 and tuple(indexes[0]) == INDEX_FIELDS
    cursor = 0
    for order, row in enumerate(indexes):
        template = template_by_sample[row["sample_index_row_id"]]
        template_digest = digest(canonical({
            field: template[field] for field in REVIEW_FIELDS
            if field != "review_record_sha256"
        }).encode())
        assert row["package_index_version"] == INDEX_VERSION
        assert parse_int(row["package_item_order_0based"]) == order
        assert parse_int(row["candidate_option_row_start_0based"]) == cursor
        cursor = parse_int(row["candidate_option_row_end_exclusive"])
        assert row["source_candidate_set_sha256"] == set_sha[row["sample_index_row_id"]]
        assert row["unreviewed_template_payload_sha256"] == template_digest
        assert row["ready_for_human_review"] == "true"
        assert row["human_review_completed"] == "false"
        assert row["complete_warhead_atom_set_authority_available"] == "false"
        assert row["exact_one_attachment_boundary_authority_available"] == "false"
        assert row["ready_for_candidate_warhead_smarts_materialization"] == "false"
        assert row["ready_for_role_proposal_generation"] == "false"
    assert cursor == 200

    failures = rows(output_payloads[FAILURE_FILE])
    assert len(failures) == 38
    assert len({row["mutation_signature"] for row in failures}) == 38
    assert all(
        row["expected_reason"] in row["observed_reasons"].split(";")
        and row["expected_reason_verified"] == row["fails_closed"] == "true"
        and row["option_row_count"] == row["template_row_count"]
        == row["package_index_row_count"] == "0"
        and row["human_review_completed"] == "false"
        and row["complete_warhead_atom_set_authority_available"] == "false"
        and row["SMARTS_ready"] == row["role_ready"] == row["mask_ready"]
        == row["model_ready"] == row["training_ready"] == "false"
        for row in failures
    )
    manifest = json.loads(output_payloads[MANIFEST_FILE])
    for name in OUTPUT_FILES[:-1]:
        assert manifest["output_sha256"][name] == digest(output_payloads[name])
    assert MANIFEST_FILE not in manifest["output_sha256"]
    expected_manifest = {
        "source_count": 15, "candidate_set_count": 11,
        "candidate_set_sha_unique_count": 11, "package_option_record_count": 200,
        "review_eligible_option_count": 185, "review_ineligible_option_count": 15,
        "review_template_count": 11, "package_index_count": 11,
        "warhead_boundary_human_review_completed_count": 0,
        "complete_warhead_atom_set_authority_available_count": 0,
        "exact_one_attachment_boundary_authority_available_count": 0,
        "candidate_warhead_smarts_materialized_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "approved_warhead_smarts_count": 0, "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "integrated_covalent_model_module_count": 0,
        "planned_covalent_model_module_count": 5,
        "failure_mutation_count": 38,
    }
    assert all(manifest[key] == value for key, value in expected_manifest.items())
    assert manifest["transaction_succeeded"] is True
    assert all(manifest[key] is False for key in (
        "ready_for_role_proposal_generation",
        "ready_for_minimal_seed_proposal_generation",
        "ready_for_mask_materialization", "ready_for_tensorization",
        "ready_for_model_integration", "ready_for_training",
        "role_annotation_materialized", "minimal_seed_materialized",
        "mask_materialized", "tensor_materialized", "model_changed", "training_used",
    ))
    assert "/cpfs" not in json.dumps(manifest)
    assert "timestamp" not in json.dumps(manifest).casefold()

    # Independently exercise the four decision shapes with synthetic data.
    synthetic = dict(templates[0])
    assert synthetic["review_decision"] == "not_reviewed"
    eligible = next(row for row in options if row["review_eligible"])
    selected = dict(synthetic)
    selected.update({
        "review_decision": "select_admitted_candidate",
        "selected_bridge_candidate_index_0based":
            eligible["source_bridge_candidate_index_0based"],
        "selected_bridge_candidate_record_sha256":
            eligible["source_bridge_candidate_record_sha256"],
        "reviewed_warhead_atom_ids": eligible["warhead_side_atom_ids"],
        "reviewed_warhead_attachment_atom_id": eligible["warhead_attachment_atom_id"],
        "reviewed_nonwarhead_boundary_atom_id": eligible["nonwarhead_boundary_atom_id"],
        "reviewed_attachment_boundary_bond_order": eligible["boundary_bond_order"],
        "reviewed_boundary_bond_id": eligible["boundary_bond_id"],
        "reviewer_id": "human-reviewer", "review_rationale": "Inspected evidence.",
    })
    selected["review_record_sha256"] = digest(canonical({
        field: selected[field] for field in REVIEW_FIELDS
        if field != "review_record_sha256"
    }).encode())
    assert SHA.fullmatch(selected["review_record_sha256"])
    revise = dict(synthetic)
    revise.update({
        "review_decision": "revise_atom_set_and_boundary",
        "reviewed_warhead_atom_ids": ["A", "B"],
        "reviewed_warhead_attachment_atom_id": "B",
        "reviewed_nonwarhead_boundary_atom_id": "C",
        "reviewed_attachment_boundary_bond_order": "single",
        "reviewed_boundary_bond_id": "B|C|single",
        "reviewer_id": "human-reviewer", "review_rationale": "Inspected graph.",
    })
    graph = {"A": {"B"}, "B": {"A"}}
    seen, queue = set(), deque(["A"])
    while queue:
        node = queue.popleft()
        if node not in seen:
            seen.add(node)
            queue.extend(graph.get(node, set()) - seen)
    assert seen == {"A", "B"}
    quarantine = dict(synthetic)
    quarantine.update({
        "review_decision": "quarantine", "reviewer_id": "human-reviewer",
        "review_rationale": "Insufficient authority.",
    })
    assert quarantine["selected_bridge_candidate_index_0based"] is None
    assert quarantine["reviewed_warhead_atom_ids"] == []
    assert selected["review_decision"] != revise["review_decision"] != quarantine["review_decision"]
    return current_lifecycle(), manifest["recommended_engineering_next_step"]


def main() -> int:
    actual, next_step = check()
    sys.path.insert(0, str(ROOT / "src"))
    from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as harness

    with tempfile.TemporaryDirectory(prefix="covapie-review-package-check-") as temp:
        workspace = Path(temp)
        report = harness.exercise_hermetic_git_lifecycle_matrix(
            ROOT, workspace, base_commit=BASE, formal_commit_subject=SUBJECT,
            exact_paths=EXACT10,
        )
    assert report.exact_path_count == 10 and report.candidate_parent == BASE
    assert tuple(
        state.lifecycle for state in (
            report.pre_commit, report.detached_candidate_post_commit,
            report.formal_main_post_commit_unpushed, report.formal_main_post_push,
        )
    ) == harness.LIFECYCLES
    print("checker=passed")
    print("sources=15 packages=11 options=200 eligible=185 templates=11")
    print("reviews_completed=0 complete_authority=0 boundary_authority=0")
    print("failure_mutations=38 all_fail_closed=true")
    print("current_lifecycle=" + actual)
    print("hermetic_lifecycle=" + ",".join(harness.LIFECYCLES))
    print("candidate_commit=" + report.candidate_commit)
    print("recommended_next_step=" + next_step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

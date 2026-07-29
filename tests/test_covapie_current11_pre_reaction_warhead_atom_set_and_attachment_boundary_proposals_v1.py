from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import itertools
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import rdkit


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (
    covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1
    as proposal,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle


PYTEST_VERSION = "9.1.0"
RDKIT_VERSION = "2022.03.2"
ACTUAL_LIFECYCLES = (
    "pre_commit",
    "detached_candidate_post_commit",
    "formal_main_post_commit_unpushed",
    "formal_main_post_push",
)
ACTUAL_BASE = "5cac27027c824cd38bad3479a59f586b2714142c"
ACTUAL_BASE_IDENTITY = (
    ACTUAL_BASE,
    "77e2d11135da4b3f07ee64411ad3c4634ba60693",
    "6837d6f4db8808eb784a80fc853c21ae34c86015",
    "add CovaPIE Cys SG candidate warhead SMARTS materialization gate design v1",
)
ACTUAL_SUCCESSOR_SUBJECT = (
    "add CovaPIE Current11 pre-reaction warhead atom set and attachment "
    "boundary proposals v1"
)
ACTUAL_EXACT10_PATHS = (
    "src/covalent_ext/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1.py",
    "tests/test_covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1.py",
    "scripts/check_covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1.py",
    "docs/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1_summary.md",
    "data/derived/covalent_small/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1/covapie_warhead_proposal_materialization_source_inventory.csv",
    "data/derived/covalent_small/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals.csv",
    "data/derived/covalent_small/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1/covapie_current11_exact_one_boundary_bridge_candidate_enumeration.csv",
    "data/derived/covalent_small/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1/covapie_current11_warhead_proposal_readiness_matrix.csv",
    "data/derived/covalent_small/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1/covapie_warhead_proposal_materialization_failure_matrix.csv",
    "data/derived/covalent_small/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1/covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_manifest.json",
)
FORBIDDEN_SUFFIXES = {
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


@pytest.fixture(scope="module")
def result():
    value = proposal.build_result(ROOT)
    assert value.transaction_succeeded is True
    assert value.blocking_reasons == ()
    return value


@pytest.fixture(scope="module")
def payloads():
    return proposal.load_frozen_sources(ROOT)


def _csv(payload: bytes):
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _git(*arguments: str, check: bool = True):
    value = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check:
        assert value.returncode == 0, value.stderr.decode("utf-8", "replace")
    return value


def _git_at(repo_root: Path, *arguments: str, check: bool = True):
    value = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check:
        assert value.returncode == 0, value.stderr.decode("utf-8", "replace")
    return value


def _classify_actual_lifecycle(
    *,
    head: str,
    successor_parents: tuple[str, ...] = (),
    successor_subject: str = "",
    successor_body: str = "",
    changed_paths: frozenset[str] = frozenset(),
    git_modes: tuple[str, ...] = (),
    branch: str | None = "main",
    origin_main: str = ACTUAL_BASE,
) -> str:
    """Pure fail-closed classifier for the actual repository lifecycle."""

    if head == ACTUAL_BASE:
        return "pre_commit"
    assert successor_parents == (ACTUAL_BASE,), "actual_successor_parent_invalid"
    assert (
        successor_subject == ACTUAL_SUCCESSOR_SUBJECT
    ), "actual_successor_subject_invalid"
    assert successor_body == "", "actual_successor_body_nonempty"
    assert changed_paths == frozenset(
        ACTUAL_EXACT10_PATHS
    ), "actual_successor_changed_paths_invalid"
    assert git_modes == ("100644",) * 10, "actual_successor_git_modes_invalid"
    if branch is None:
        return "detached_candidate_post_commit"
    assert branch == "main", "actual_successor_branch_invalid"
    if origin_main == ACTUAL_BASE:
        return "formal_main_post_commit_unpushed"
    if origin_main == head:
        return "formal_main_post_push"
    raise AssertionError("actual_successor_origin_main_relation_invalid")


def expected_actual_lifecycle(repo_root: Path) -> str:
    """Independently derive actual lifecycle from Git, without production code."""

    identity = _git_at(
        repo_root,
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        ACTUAL_BASE,
    ).stdout.decode().splitlines()
    assert tuple(identity) == ACTUAL_BASE_IDENTITY, "actual_BASE_identity_invalid"
    head = _git_at(repo_root, "rev-parse", "HEAD").stdout.decode().strip()
    if head == ACTUAL_BASE:
        return _classify_actual_lifecycle(head=head)

    raw = _git_at(repo_root, "cat-file", "commit", head).stdout
    headers, separator, message = raw.partition(b"\n\n")
    assert separator, "actual_successor_commit_malformed"
    parents = tuple(
        line[7:].decode("utf-8")
        for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    subject, newline, body = message.partition(b"\n")
    assert newline, "actual_successor_message_malformed"
    changed_paths = frozenset(
        item.decode("utf-8")
        for item in _git_at(
            repo_root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            head,
        ).stdout.split(b"\0")
        if item
    )
    tree_rows = [
        item
        for item in _git_at(
            repo_root,
            "ls-tree",
            "-r",
            "-z",
            head,
            "--",
            *ACTUAL_EXACT10_PATHS,
        ).stdout.split(b"\0")
        if item
    ]
    modes = tuple(
        row.partition(b"\t")[0].split(b" ", 1)[0].decode("ascii")
        for row in tree_rows
    )
    symbolic = _git_at(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    branch = (
        symbolic.stdout.decode("utf-8").strip()
        if symbolic.returncode == 0
        else None
    )
    origin_main = (
        _git_at(
            repo_root, "rev-parse", "--verify", "refs/remotes/origin/main"
        )
        .stdout.decode()
        .strip()
        if branch is not None
        else ACTUAL_BASE
    )
    return _classify_actual_lifecycle(
        head=head,
        successor_parents=parents,
        successor_subject=subject.decode("utf-8"),
        successor_body=body.decode("utf-8"),
        changed_paths=changed_paths,
        git_modes=modes,
        branch=branch,
        origin_main=origin_main,
    )


def _valid_successor_state(**overrides):
    values = {
        "head": "1" * 40,
        "successor_parents": (ACTUAL_BASE,),
        "successor_subject": ACTUAL_SUCCESSOR_SUBJECT,
        "successor_body": "",
        "changed_paths": frozenset(ACTUAL_EXACT10_PATHS),
        "git_modes": ("100644",) * 10,
        "branch": None,
        "origin_main": ACTUAL_BASE,
    }
    values.update(overrides)
    return values


def _load_checker_module():
    path = (
        ROOT
        / "scripts"
        / "check_covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        "covapie_warhead_proposal_checker_actual_lifecycle", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _identity(record):
    return {
        field: record[field]
        for field in (
            "sample_index_row_id",
            "pdb_id",
            "ligand_comp_id",
            "warhead_type_candidate_class_index_0based",
            "warhead_type_candidate_class_id",
            "reaction_family_id",
            "warhead_rule_id",
            "component_parent_graph_sha256",
        )
    }


def _admitted_sets_bruteforce(atoms, bonds, reactive, local, leaving):
    atom_set = set(atoms)
    values = []
    others = sorted(atom_set - {reactive})
    for count in range(len(others) + 1):
        for extra in itertools.combinations(others, count):
            side = {reactive, *extra}
            if side == atom_set or not set(local) <= side or not set(leaving) <= side:
                continue
            induced = [(a, b) for a, b, _ in bonds if a in side and b in side]
            reached = {reactive}
            changed = True
            while changed:
                changed = False
                for left, right in induced:
                    if left in reached and right not in reached:
                        reached.add(right)
                        changed = True
                    if right in reached and left not in reached:
                        reached.add(left)
                        changed = True
            boundary = [
                (a, b, order)
                for a, b, order in bonds
                if (a in side) != (b in side)
            ]
            if reached == side and len(boundary) == 1:
                values.append(proposal._utf8_sorted(side))
    return sorted(values)


def test_fixed_runtime_versions():
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == PYTEST_VERSION
    assert rdkit.__version__ == RDKIT_VERSION
    assert Path(sys.executable).resolve() == Path(
        "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
        "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
    ).resolve()


def test_formal_base_identity_and_execution_boundary():
    assert _git("show", "-s", "--format=%H%n%P%n%T%n%s", proposal.BASE_COMMIT).stdout.decode().splitlines() == [
        proposal.BASE_COMMIT,
        proposal.BASE_PARENT,
        proposal.BASE_TREE,
        proposal.BASE_SUBJECT,
    ]
    expected = expected_actual_lifecycle(ROOT)
    observed = proposal.validate_execution_boundary_v1(ROOT)
    assert type(expected) is type(observed) is str
    assert expected == observed
    assert observed in ACTUAL_LIFECYCLES


def test_actual_lifecycle_vocabulary_and_current_state():
    assert ACTUAL_LIFECYCLES == lifecycle.LIFECYCLES
    observed = expected_actual_lifecycle(ROOT)
    assert observed in ACTUAL_LIFECYCLES
    if _git("rev-parse", "HEAD").stdout.decode().strip() == ACTUAL_BASE:
        assert observed == "pre_commit"


def test_checker_independent_current_lifecycle_matches_test_authority():
    checker = _load_checker_module()
    observed = checker.current_lifecycle()
    assert type(observed) is str
    assert observed == expected_actual_lifecycle(ROOT)
    assert observed in ACTUAL_LIFECYCLES
    if _git("rev-parse", "HEAD").stdout.decode().strip() == ACTUAL_BASE:
        assert observed == "pre_commit"


def test_actual_lifecycle_pure_helper_all_exact4():
    assert _classify_actual_lifecycle(head=ACTUAL_BASE) == "pre_commit"
    assert (
        _classify_actual_lifecycle(**_valid_successor_state())
        == "detached_candidate_post_commit"
    )
    committed = _valid_successor_state(branch="main", origin_main=ACTUAL_BASE)
    assert (
        _classify_actual_lifecycle(**committed)
        == "formal_main_post_commit_unpushed"
    )
    pushed = _valid_successor_state(branch="main")
    pushed["origin_main"] = pushed["head"]
    assert _classify_actual_lifecycle(**pushed) == "formal_main_post_push"


def test_actual_lifecycle_unknown_branch_and_origin_drift_fail_closed():
    with pytest.raises(AssertionError, match="branch_invalid"):
        _classify_actual_lifecycle(
            **_valid_successor_state(branch="release", origin_main=ACTUAL_BASE)
        )
    with pytest.raises(AssertionError, match="origin_main_relation_invalid"):
        _classify_actual_lifecycle(
            **_valid_successor_state(branch="main", origin_main="2" * 40)
        )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"successor_parents": ("2" * 40,)}, "parent_invalid"),
        ({"successor_subject": "wrong subject"}, "subject_invalid"),
        ({"successor_body": "unexpected body\n"}, "body_nonempty"),
        ({"changed_paths": frozenset()}, "changed_paths_invalid"),
        ({"git_modes": ("100755",) + ("100644",) * 9}, "git_modes_invalid"),
    ),
)
def test_actual_lifecycle_successor_identity_fail_closed(overrides, reason):
    with pytest.raises(AssertionError, match=reason):
        _classify_actual_lifecycle(**_valid_successor_state(**overrides))


def test_exact16_are_loaded_only_from_base_and_sha_frozen(payloads):
    assert len(payloads) == len(proposal.FROZEN_BASE_SHA256) == 16
    for path, expected in proposal.FROZEN_BASE_SHA256.items():
        assert hashlib.sha256(payloads[path]).hexdigest() == expected
        assert _git("cat-file", "-e", f"{proposal.BASE_COMMIT}:{path.as_posix()}").returncode == 0


def test_inherited_exact22_status_type_and_hash_contract(payloads):
    manifest = json.loads(payloads[proposal.DESIGN_MANIFEST])
    assert tuple(manifest["proposal_fields"]) == proposal.PROPOSAL_FIELDS
    assert len(proposal.PROPOSAL_FIELDS) == 22
    assert tuple(manifest["proposal_statuses"]) == proposal.PROPOSAL_STATUSES
    assert manifest["proposal_field_type_contract"] == proposal.PROPOSAL_FIELD_TYPE_CONTRACT
    assert manifest["proposal_hash_canonical_json_contract"]["included_field_count"] == 21
    assert proposal.PROPOSAL_ATOM_ID_NAMESPACE == "parent_ccd_atom_id"
    assert proposal.PROPOSAL_BOND_ID_ENCODING == "canonical_parent_ccd_endpoint_pair_and_normalized_order_v1"


def test_source_inventory_exact16_and_required_columns(result):
    assert len(result.source_rows) == 16
    assert tuple(result.source_rows[0]) == proposal.SOURCE_COLUMNS
    assert all(row["verified"] is True for row in result.source_rows)
    assert {row["source_path"] for row in result.source_rows} == {
        path.as_posix() for path in proposal.SOURCE_PATHS
    }
    assert all(
        row["BASE_SHA256"]
        == proposal.FROZEN_BASE_SHA256[Path(row["source_path"])]
        for row in result.source_rows
    )


def test_parent_atom_bond_graph_authority_connected_and_sha(payloads):
    assignments = _csv(payloads[proposal.ASSIGNMENTS])
    atoms = _csv(payloads[proposal.PARENT_ATOMS])
    bonds = _csv(payloads[proposal.PARENT_BONDS])
    for sample in assignments:
        component = sample["ligand_comp_id"]
        digest = sample["component_parent_graph_sha256"]
        selected_atoms = [
            row
            for row in atoms
            if row["ligand_comp_id"] == component
            and row["component_parent_graph_sha256"] == digest
        ]
        selected_bonds = [
            row
            for row in bonds
            if row["ligand_comp_id"] == component
            and row["component_parent_graph_sha256"] == digest
        ]
        by_id, edges, adjacency = proposal._validate_graph(
            selected_atoms, selected_bonds, digest
        )
        assert len(by_id) == len(selected_atoms)
        assert len(edges) == len(selected_bonds)
        assert proposal._reached(adjacency, next(iter(by_id))) == set(by_id)
        assert proposal.canonical_parent_graph_sha256(
            tuple(reversed(selected_atoms)), tuple(reversed(selected_bonds))
        ) == digest


def test_reactive_local_center_multiset_and_leaving_group_rebuild(payloads):
    assignments = _csv(payloads[proposal.ASSIGNMENTS])
    rules = {
        row["warhead_rule_id"]: row for row in _csv(payloads[proposal.RULES])
    }
    atoms = _csv(payloads[proposal.PARENT_ATOMS])
    bonds = _csv(payloads[proposal.PARENT_BONDS])
    mappings = _csv(payloads[proposal.MAPPINGS])
    total_leaving = 0
    for sample in assignments:
        component = sample["ligand_comp_id"]
        digest = sample["component_parent_graph_sha256"]
        by_id, _edges, adjacency = proposal._validate_graph(
            [
                row
                for row in atoms
                if row["ligand_comp_id"] == component
                and row["component_parent_graph_sha256"] == digest
            ],
            [
                row
                for row in bonds
                if row["ligand_comp_id"] == component
                and row["component_parent_graph_sha256"] == digest
            ],
            digest,
        )
        local, local_bonds, leaving = proposal._local_and_leaving(
            sample,
            rules[sample["candidate_warhead_rule_id"]],
            by_id,
            adjacency,
            mappings,
        )
        reactive = sample["ligand_reactive_parent_ccd_atom_id"]
        assert local == proposal._utf8_sorted(
            {reactive, *(neighbor for neighbor, _ in adjacency[reactive])}
        )
        assert len(local_bonds) == len(adjacency[reactive])
        assert reactive in local and set(leaving) <= set(local)
        total_leaving += len(leaving)
    assert total_leaving == 1


@pytest.mark.parametrize(
    ("atoms", "bonds", "reactive", "local", "leaving", "bridge_count", "admitted", "status"),
    (
        (
            ("A", "B", "C"),
            (("A", "B", "single"), ("B", "C", "single")),
            "A",
            ("A", "B"),
            (),
            2,
            1,
            "auto_exact_candidate",
        ),
        (
            ("A", "B", "C", "D"),
            (
                ("A", "B", "single"),
                ("B", "C", "single"),
                ("C", "D", "single"),
            ),
            "A",
            ("A", "B"),
            (),
            3,
            2,
            "ambiguous_candidate",
        ),
        (
            ("A", "B", "C"),
            (
                ("A", "B", "single"),
                ("B", "C", "single"),
                ("C", "A", "single"),
            ),
            "A",
            ("A", "B"),
            (),
            0,
            0,
            "quarantined",
        ),
        (
            ("A", "B"),
            (("A", "B", "single"),),
            "A",
            ("A", "B"),
            (),
            1,
            0,
            "quarantined",
        ),
        (
            ("A", "B"),
            (("A", "B", "single"),),
            "A",
            ("A",),
            ("B",),
            1,
            0,
            "quarantined",
        ),
    ),
)
def test_synthetic_unique_multiple_cycle_local_and_leaving_contracts(
    atoms, bonds, reactive, local, leaving, bridge_count, admitted, status
):
    rows = proposal.enumerate_exact_one_boundary_candidates(
        atoms, bonds, reactive, local, leaving
    )
    assert len(rows) == bridge_count
    assert sum(row["candidate_admitted"] for row in rows) == admitted
    assert proposal.proposal_status_for_candidates(rows) == status
    assert [row["boundary_bond_id"] for row in rows] == sorted(
        row["boundary_bond_id"] for row in rows
    )
    if atoms == ("A", "B") and local == ("A", "B"):
        assert rows[0]["contains_local_reaction_center"] is False
        assert "candidate_missing_local_reaction_center" in rows[0]["blocking_reasons"]
    if atoms == ("A", "B") and leaving == ("B",):
        assert rows[0]["contains_required_leaving_groups"] is False
        assert "candidate_missing_required_leaving_group" in rows[0]["blocking_reasons"]


def test_bridge_enumeration_is_complete_for_exact_one_boundary_sets():
    atoms = ("A", "B", "C", "D", "E")
    bonds = (
        ("A", "B", "single"),
        ("B", "C", "single"),
        ("C", "D", "single"),
        ("C", "E", "single"),
    )
    local = ("A", "B")
    rows = proposal.enumerate_exact_one_boundary_candidates(
        atoms, bonds, "A", local, ()
    )
    enumerated = sorted(
        row["warhead_side_atom_ids"] for row in rows if row["candidate_admitted"]
    )
    assert enumerated == _admitted_sets_bruteforce(
        atoms, bonds, "A", local, ()
    )


def test_canonical_bond_id_utf8_sorted_and_normalized_order_closed():
    assert proposal.canonical_parent_bond_id("B", "A", "single") == "A|B|single"
    with pytest.raises(ValueError, match="invalid"):
        proposal.canonical_parent_bond_id("A", "B", "triple")
    with pytest.raises(ValueError, match="invalid"):
        proposal.canonical_parent_bond_id("A", "A", "single")


def test_exact11_proposals_type_hash_and_ambiguity_semantics(result):
    assert len(result.proposal_rows) == 11
    assert Counter(row["proposal_status"] for row in result.proposal_rows) == {
        "ambiguous_candidate": 11
    }
    identities = set()
    hashes = set()
    for row in result.proposal_rows:
        assert tuple(row) == proposal.PROPOSAL_FIELDS
        proposal._validate_proposal_types(row)
        assert row["proposal_record_sha256"] == proposal.proposal_record_sha256(row)
        assert re.fullmatch(r"[0-9a-f]{64}", row["proposal_record_sha256"])
        assert row["proposed_pre_reaction_warhead_atom_ids"] == []
        assert row["proposed_warhead_attachment_atom_id"] == ""
        assert row["proposed_nonwarhead_boundary_atom_id"] == ""
        assert row["proposed_attachment_boundary_bond_order"] == ""
        assert row["ambiguity_reasons"] == [
            "multiple_admissible_exact_one_boundary_candidates"
        ]
        identities.add(row["sample_index_row_id"])
        hashes.add(row["proposal_record_sha256"])
    assert len(identities) == len(hashes) == 11


def test_enumeration_exact22_types_hash_indices_and_actual_counts(result):
    assert len(proposal.ENUMERATION_FIELDS) == 22
    assert len(result.enumeration_rows) == 200
    assert sum(row["candidate_admitted"] for row in result.enumeration_rows) == 185
    by_sample = {}
    for row in result.enumeration_rows:
        assert tuple(row) == proposal.ENUMERATION_FIELDS
        proposal._validate_enumeration_types(row)
        assert row["bridge_candidate_record_sha256"] == proposal.bridge_candidate_record_sha256(row)
        assert row["warhead_side_atom_ids"] == proposal._utf8_sorted(
            row["warhead_side_atom_ids"]
        )
        assert row["warhead_side_connected"] is True
        assert row["exact_one_boundary_verified"] is True
        assert row["proper_subset"] is True
        by_sample.setdefault(row["sample_index_row_id"], []).append(row)
    assert set(by_sample) == {
        f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
    }
    for rows in by_sample.values():
        assert [row["bridge_candidate_index_0based"] for row in rows] == list(
            range(len(rows))
        )
        assert [row["boundary_bond_id"] for row in rows] == sorted(
            (row["boundary_bond_id"] for row in rows),
            key=lambda value: value.encode("utf-8"),
        )


def test_readiness_exact11_human_proposal_ready_downstream_closed(result):
    assert len(result.readiness_rows) == 11
    assert [row["sample_index_row_id"] for row in result.readiness_rows] == sorted(
        row["sample_index_row_id"] for row in result.readiness_rows
    )
    assert all(row["proposal_materialized"] is True for row in result.readiness_rows)
    assert all(
        row["ready_for_proposal_human_review"] is True
        for row in result.readiness_rows
    )
    closed = (
        "complete_warhead_atom_set_authority_available",
        "exact_one_attachment_boundary_authority_available",
        "ready_for_candidate_warhead_smarts_materialization",
        "ready_for_SMARTS_review_execution",
        "ready_for_role_proposal_generation",
        "ready_for_mask_materialization",
        "ready_for_model_integration",
        "ready_for_training",
    )
    assert all(not row[field] for row in result.readiness_rows for field in closed)
    assert sum(row["parent_bridge_count"] for row in result.readiness_rows) == 200
    assert sum(
        row["admitted_boundary_candidate_count"] for row in result.readiness_rows
    ) == 185


def test_repeated_component_topology_consistent_but_proposal_identity_distinct(result):
    jug = [
        row
        for row in result.proposal_rows
        if row["ligand_comp_id"] == "JUG"
    ]
    assert len(jug) == 3
    topology = {
        (
            tuple(row["local_reaction_center_atom_ids"]),
            tuple(row["local_reaction_center_bond_ids"]),
            tuple(row["required_leaving_group_atom_ids"]),
        )
        for row in jug
    }
    assert len(topology) == 1
    bridge_topology = []
    for sample in jug:
        rows = [
            row
            for row in result.enumeration_rows
            if row["sample_index_row_id"] == sample["sample_index_row_id"]
        ]
        bridge_topology.append(
            tuple(
                (
                    row["boundary_bond_id"],
                    tuple(row["warhead_side_atom_ids"]),
                    row["candidate_admitted"],
                )
                for row in rows
            )
        )
    assert len(set(bridge_topology)) == 1
    assert len({row["proposal_record_sha256"] for row in jug}) == 3


def test_failure_matrix_exact36_typed_unique_and_all_header_only(result):
    assert len(proposal.FAILURE_MUTATIONS) == len(result.failure_rows) == 36
    assert proposal.ProposalScenario.__dataclass_params__.frozen is True
    assert len({row["mutation_signature"] for row in result.failure_rows}) == 36
    baseline = proposal.ProposalScenario()
    for definition, row in zip(proposal.FAILURE_MUTATIONS, result.failure_rows):
        case, field, value, reason = definition
        assert row["failure_case"] == case
        assert type(getattr(baseline, field)) is type(value)
        assert getattr(baseline, field) != value
        assert row["expected_reason"] == reason
        assert reason in row["observed_reasons"].split(";")
        assert row["expected_reason_verified"] is True
        assert row["fails_closed"] is True
        assert row["proposal_row_count"] == 0
        assert row["bridge_enumeration_row_count"] == 0
        assert row["readiness_row_count"] == 0
        assert not any(
            row[field]
            for field in (
                "SMARTS_ready",
                "role_ready",
                "mask_ready",
                "model_ready",
                "training_ready",
            )
        )
        scenario = proposal.replace(baseline, **{field: value})
        assert proposal.transaction_tables(scenario) == ((), (), ())


def test_success_transaction_not_confused_by_normal_ambiguity():
    tables = proposal.transaction_tables(proposal.ProposalScenario())
    assert all(len(table) == 1 for table in tables)
    scenario = proposal.replace(
        proposal.ProposalScenario(), bridge_candidate_indices_contiguous=False
    )
    assert proposal.transaction_tables(scenario) == ((), (), ())


def test_no_smarts_approval_role_mask_model_or_training_materialized(result):
    assert not any(
        "smarts" in field.lower()
        for field in (*proposal.PROPOSAL_FIELDS, *proposal.ENUMERATION_FIELDS)
    )
    for row in result.proposal_rows:
        rendered = proposal.canonical_json(row).lower()
        assert "approved" not in rendered
        assert "reviewer" not in rendered
        assert "semantic_name" not in rendered
    manifest = proposal._manifest(result, {})
    assert manifest["candidate_warhead_smarts_materialized_count"] == 0
    assert manifest["approved_reaction_family_available_count"] == 0
    assert manifest["approved_warhead_rule_available_count"] == 0
    assert manifest["approved_warhead_smarts_count"] == 0
    assert manifest["role_annotation_materialized"] is False
    assert manifest["minimal_seed_materialized"] is False
    assert manifest["mask_materialized"] is False
    assert manifest["tensor_materialized"] is False
    assert manifest["model_changed"] is False
    assert manifest["training_used"] is False
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["planned_covalent_model_module_count"] == 5


def test_manifest_actual_counts_contract_and_no_self_hash(result):
    names = {
        name: proposal.sha256(payload)
        for name, payload in proposal.build_evidence_payloads(ROOT).items()
        if name != proposal.MANIFEST_FILE
    }
    manifest = proposal._manifest(result, names)
    assert manifest["source_count"] == 16
    assert manifest["candidate_class_count"] == 7
    assert manifest["current11_sample_count"] == 11
    assert manifest["unique_component_count"] == 9
    assert manifest["proposal_record_count"] == 11
    assert manifest["proposal_record_sha_valid_count"] == 11
    assert manifest["auto_exact_candidate_count"] == 0
    assert manifest["ambiguous_candidate_count"] == 11
    assert manifest["quarantined_count"] == 0
    assert manifest["not_materialized_count"] == 0
    assert manifest["proposal_status_count_total"] == 11
    assert manifest["total_parent_bridge_count"] == 200
    assert manifest["total_admitted_boundary_candidate_count"] == 185
    assert manifest["samples_with_zero_parent_bridges"] == 0
    assert manifest["samples_with_zero_admitted_candidates"] == 0
    assert manifest["samples_with_multiple_admitted_candidates"] == 11
    assert manifest["proposal_human_review_ready_count"] == 11
    assert manifest["failure_mutation_count"] == 36
    assert manifest["failure_mutations_all_fail_closed"] is True
    assert proposal.MANIFEST_FILE not in manifest["output_sha256"]


def test_payloads_are_byte_deterministic_and_match_materialized_files():
    first = proposal.build_evidence_payloads(ROOT)
    second = proposal.build_evidence_payloads(ROOT)
    assert first == second
    assert set(first) == set(proposal.OUTPUT_FILES)
    for name, payload in first.items():
        assert (ROOT / proposal.OUTPUT_ROOT / name).read_bytes() == payload


def test_isolated_import_has_no_output_or_files(tmp_path):
    before = tuple(tmp_path.iterdir())
    environment = {
        "PYTHONPATH": str(ROOT / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PATH": os.environ["PATH"],
    }
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext."
            "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
            "boundary_proposals_v1",
        ),
        cwd=tmp_path,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""
    assert tuple(tmp_path.iterdir()) == before


def test_manifest_has_no_timestamp_absolute_path_or_self_digest():
    payload = (ROOT / proposal.OUTPUT_ROOT / proposal.MANIFEST_FILE).read_text(
        encoding="utf-8"
    )
    assert re.search(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", payload) is None
    assert str(ROOT) not in payload
    manifest = json.loads(payload)
    assert proposal.MANIFEST_FILE not in manifest["output_sha256"]


def test_exact10_filesystem_modes_symlinks_sizes_and_forbidden_suffixes():
    assert len(proposal.EXACT10_PATHS) == 10
    assert len(set(proposal.EXACT10_PATHS)) == 10
    for relative in proposal.EXACT10_PATHS:
        path = ROOT / relative
        assert path.exists() and path.is_file() and not path.is_symlink()
        assert stat.S_IMODE(path.stat(follow_symlinks=False).st_mode) in {
            0o644,
            0o664,
        }
        assert path.stat().st_size <= 5 * 1024 * 1024
        assert path.suffix.lower() not in FORBIDDEN_SUFFIXES


def test_shared_hermetic_lifecycle_exact4_and_cleanup(tmp_path):
    workspace = tmp_path / "lifecycle"
    workspace.mkdir()
    before_status = _git(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    ).stdout
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        workspace,
        base_commit=proposal.BASE_COMMIT,
        formal_commit_subject=proposal.FORMAL_COMMIT_SUBJECT,
        exact_paths=proposal.EXACT10_PATHS,
    )
    after_status = _git(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    ).stdout
    assert before_status == after_status
    assert report.cleanup_verified is True
    assert report.candidate_parent == proposal.BASE_COMMIT
    assert report.candidate_subject == proposal.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    states = (
        report.pre_commit,
        report.detached_candidate_post_commit,
        report.formal_main_post_commit_unpushed,
        report.formal_main_post_push,
    )
    assert tuple(state.lifecycle for state in states) == lifecycle.LIFECYCLES
    assert tuple(workspace.iterdir()) == ()

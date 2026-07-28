#!/usr/bin/env python3
"""Independent checker for Current11 observed atom projection authority v1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_current11_observed_to_parent_atom_projection_authority_v1 as contract,
)

EXACT10 = (
    Path(
        "src/covalent_ext/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
    ),
    Path(
        "docs/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1_summary.md"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
        "covapie_observed_atom_projection_source_inventory.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
        "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
        "covapie_current11_parent_and_observed_projected_bond_authority.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
        "covapie_current11_observed_projection_readiness_matrix.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
        "covapie_current11_observed_projection_failure_matrix.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
        "covapie_current11_observed_to_parent_atom_projection_authority_manifest.json"
    ),
)


def _git_process(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    return result


def _git(*arguments: str) -> bytes:
    result = _git_process(*arguments)
    if result.returncode:
        raise AssertionError(
            "git failed: " + " ".join(arguments) + ":"
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result.stdout


def validate_execution_boundary_independent() -> str:
    """Independently validate the same closed Exact4 Git lifecycle."""

    shown = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", contract.BASE_COMMIT
    ).decode().splitlines()
    assert shown == [
        contract.BASE_COMMIT,
        contract.BASE_PARENT,
        contract.BASE_TREE,
        contract.BASE_SUBJECT,
    ]
    assert _git("diff", "--name-only", "-z") == b""
    assert _git("diff", "--cached", "--name-only", "-z") == b""

    head = _git("rev-parse", "HEAD").decode().strip()
    exact_names = tuple(path.as_posix() for path in EXACT10)
    if head == contract.BASE_COMMIT:
        untracked = tuple(
            item.decode("utf-8")
            for item in _git(
                "ls-files", "--others", "--exclude-standard", "-z"
            ).split(b"\0")
            if item
        )
        assert len(untracked) == len(exact_names)
        assert set(untracked) == set(exact_names)
        return "pre_commit"

    assert _git("ls-files", "--others", "--exclude-standard", "-z") == b""
    commit_payload = _git("cat-file", "commit", head)
    headers, separator, message = commit_payload.partition(b"\n\n")
    assert separator
    parents = tuple(
        line.removeprefix(b"parent ").decode("ascii")
        for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    assert parents == (contract.BASE_COMMIT,)
    subject, subject_separator, body = message.partition(b"\n")
    assert subject_separator
    assert subject.decode("utf-8") == contract.FORMAL_COMMIT_SUBJECT
    assert body == b""

    changed = tuple(
        item.decode("utf-8")
        for item in _git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).split(b"\0")
        if item
    )
    assert len(changed) == len(exact_names)
    assert set(changed) == set(exact_names)
    tree_rows = tuple(
        item
        for item in _git(
            "ls-tree", "-r", "-z", head, "--", *exact_names
        ).split(b"\0")
        if item
    )
    observed_names = []
    for row in tree_rows:
        metadata, tab, name = row.partition(b"\t")
        assert tab and metadata.startswith(b"100644 blob ")
        observed_names.append(name.decode("utf-8"))
    assert len(observed_names) == len(exact_names)
    assert set(observed_names) == set(exact_names)

    branch = _git_process("symbolic-ref", "--quiet", "--short", "HEAD")
    if branch.returncode != 0:
        return "detached_candidate_post_commit"
    assert branch.stdout.decode().strip() == "main"
    origin_main = _git("rev-parse", "--verify", "refs/remotes/origin/main")
    if origin_main.decode().strip() == contract.BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    assert origin_main.decode().strip() == head
    return "formal_main_post_push"


def _base(path: Path) -> bytes:
    return _git("show", f"{contract.BASE_COMMIT}:{path.as_posix()}")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _artifact(name: str) -> bytes:
    return (ROOT / contract.OUTPUT_ROOT / name).read_bytes()


def _bool(value: str) -> bool:
    assert value in ("true", "false")
    return value == "true"


def _source_bool(value: str) -> bool:
    assert value in ("True", "False")
    return value == "True"


def _graph_sha(
    atoms: Iterable[tuple[str, str, int]],
    bonds: Iterable[tuple[str, str, str]],
) -> str:
    payload = {
        "atoms": [
            list(row) for row in sorted(
                (name, element, int(charge))
                for name, element, charge in atoms
            )
        ],
        "bonds": [
            list(row) for row in sorted(
                (min(left, right), max(left, right), order)
                for left, right, order in bonds
            )
        ],
    }
    return _sha(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    )


def _connected(vertices: set[str], edges: set[tuple[str, str]]) -> bool:
    adjacency = {vertex: set() for vertex in vertices}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    visited: set[str] = set()
    queue = deque([min(vertices)])
    while queue:
        vertex = queue.popleft()
        if vertex in visited:
            continue
        visited.add(vertex)
        queue.extend(sorted(adjacency[vertex] - visited))
    return visited == vertices


def _independent_failure_reasons(mutated: dict[str, Any]) -> tuple[str, ...]:
    mapping = {
        "observed_source_present": (False, "observed_source_missing"),
        "observed_source_base_tracked":
            (False, "observed_source_not_BASE_tracked"),
        "sample_coverage_complete": (False, "sample_coverage_incomplete"),
        "atom_row_coverage_complete": (False, "atom_row_coverage_incomplete"),
        "duplicate_sample_identity_count": (1, "duplicate_sample_identity"),
        "duplicate_observed_atom_name_count":
            (1, "duplicate_observed_atom_name"),
        "duplicate_source_full_row_index_count":
            (1, "duplicate_source_full_row_index"),
        "duplicate_retained_local_index_count":
            (1, "duplicate_retained_local_index"),
        "retained_local_indices_contiguous":
            (False, "retained_local_index_noncontiguous"),
        "observed_atom_name_present": (False, "observed_atom_name_missing"),
        "parent_ccd_atom_present": (False, "parent_CCD_atom_missing"),
        "element_matches": (False, "observed_parent_element_mismatch"),
        "reactive_atom_count": {
            0: "reactive_ligand_atom_absent",
            2: "reactive_ligand_atom_duplicated",
        },
        "unexpected_observed_atom_count": (1, "unexpected_observed_atom"),
        "unexplained_parent_atom_missing_count":
            (1, "unexplained_parent_atom_missing"),
        "leaving_group_evidence_consistent":
            (False, "leaving_group_evidence_inconsistent"),
        "leaving_group_parent_bond_present":
            (False, "leaving_group_parent_bond_missing"),
        "projected_bond_endpoint_complete":
            (False, "projected_bond_endpoint_missing"),
        "duplicate_projected_bond_count": (1, "duplicate_projected_bond"),
        "observed_graph_connected": (False, "observed_graph_disconnected"),
        "graph_sha_deterministic":
            (False, "observed_graph_SHA_nondeterministic"),
        "partial_materialization_attempted":
            (True, "partial_materialization_attempted"),
        "execution_boundary_crossed": (True, "execution_boundary_crossed"),
    }
    assert len(mutated) == 1
    field, value = next(iter(mutated.items()))
    expectation = mapping[field]
    if isinstance(expectation, dict):
        return (expectation[value],)
    expected_value, reason = expectation
    assert value == expected_value
    return (reason,)


def check() -> dict[str, Any]:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)

    lifecycle = validate_execution_boundary_independent()

    base_payloads = {}
    for path, expected_sha in contract.FROZEN_BASE_SHA256.items():
        payload = _base(path)
        assert _sha(payload) == expected_sha
        assert _git("cat-file", "-e", f"{contract.BASE_COMMIT}:{path.as_posix()}") == b""
        base_payloads[path] = payload

    samples = _rows(base_payloads[contract.PARENT_READINESS])
    assert len(samples) == 11
    identities = {
        (row["sample_index_row_id"], row["pdb_id"], row["ligand_comp_id"])
        for row in samples
    }
    assert len(identities) == 11
    assert len({row["ligand_comp_id"] for row in samples}) == 9
    sample_by_id = {row["sample_index_row_id"]: row for row in samples}

    source_tables = {
        path: _rows(base_payloads[path]) for path in contract.LIGAND_ATOM_TABLES
    }
    projection = [
        row for row in _rows(base_payloads[contract.HEAVY_PROJECTION])
        if row["domain"] == "ligand_atom"
        and row["retained_for_checkpoint_model"] == "true"
    ]
    assert len(projection) == 323
    observed: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    reactive_source_rows: dict[str, tuple[str, int]] = {}
    for row in projection:
        sample_id = row["sample_index_row_id"]
        sample = sample_by_id[sample_id]
        source_path = Path(row["source_table_path"])
        assert source_path in source_tables
        assert row["source_table_sha256"] == contract.FROZEN_BASE_SHA256[source_path]
        source_index = int(row["source_atom_row_index_0based"])
        local_index = int(row["projected_heavy_atom_row_index_0based"])
        source = source_tables[source_path][source_index]
        assert source["pdb_id"] == sample["pdb_id"]
        assert source["ligand_comp_id"] == sample["ligand_comp_id"]
        assert source["type_symbol"] == row["type_symbol"]
        atom_name = source["atom_name"]
        assert atom_name and atom_name not in observed[sample_id]
        observed[sample_id][atom_name] = {
            "type_symbol": source["type_symbol"],
            "source_index": source_index,
            "local_index": local_index,
            "reactive": _source_bool(source["is_covalent_ligand_atom"]),
            "source_path": source_path.as_posix(),
            "source_sha": contract.FROZEN_BASE_SHA256[source_path],
        }
        if observed[sample_id][atom_name]["reactive"]:
            assert sample_id not in reactive_source_rows
            reactive_source_rows[sample_id] = (source_path.as_posix(), source_index)
    assert set(observed) == set(sample_by_id)
    assert len(reactive_source_rows) == 11
    for sample_id, atom_map in observed.items():
        local = [int(row["local_index"]) for row in atom_map.values()]
        source = [int(row["source_index"]) for row in atom_map.values()]
        assert sorted(local) == list(range(len(atom_map)))
        assert len(source) == len(set(source))
        assert sum(bool(row["reactive"]) for row in atom_map.values()) == 1

    pair_rows = [
        row for row in _rows(base_payloads[contract.ATOM_PAIR_MAPPING])
        if row["entity_role"] == "ligand_atom"
    ]
    assert len(pair_rows) == 11
    for row in pair_rows:
        path, index = reactive_source_rows[row["sample_index_row_id"]]
        assert row["target_table_path"] == path
        assert int(row["matched_row_index_0based"]) == index
        assert row["mapping_reason"] == "exact_one_identity_mapping"

    parent_atoms_by_component: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in _rows(base_payloads[contract.PARENT_ATOMS]):
        parent_atoms_by_component[row["ligand_comp_id"]][row["ccd_atom_id"]] = row
    parent_bonds_by_component: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _rows(base_payloads[contract.PARENT_BONDS]):
        parent_bonds_by_component[row["ligand_comp_id"]].append(row)
    assert sum(
        len(parent_atoms_by_component[row["ligand_comp_id"]]) for row in samples
    ) == 324
    assert sum(
        len(parent_bonds_by_component[row["ligand_comp_id"]]) for row in samples
    ) == 337

    evidence = {
        row["sample_index_row_id"]: row
        for row in _rows(base_payloads[contract.GRAPH_EVIDENCE])
    }
    missing = []
    graph_shas: dict[str, str] = {}
    independent_bonds: list[dict[str, Any]] = []
    projected_count = 0
    dispositions = Counter()
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        component = sample["ligand_comp_id"]
        atom_map = observed[sample_id]
        parent_map = parent_atoms_by_component[component]
        assert set(atom_map) <= set(parent_map)
        missing_ids = sorted(set(parent_map) - set(atom_map))
        missing.extend((sample_id, component, atom_id) for atom_id in missing_ids)
        allowed = set(filter(None, evidence[sample_id]["leaving_group_atom_ids"].split(";")))
        edges = set()
        graph_bonds = []
        for parent_bond in parent_bonds_by_component[component]:
            left = parent_bond["parent_ccd_atom_id_1"]
            right = parent_bond["parent_ccd_atom_id_2"]
            edge = (min(left, right), max(left, right))
            assert left != right and edge not in edges
            edges.add(edge)
            left_present = left in atom_map
            right_present = right in atom_map
            if left_present and right_present:
                projected = True
                disposition = "retained_observed_bond"
                graph_bonds.append((*edge, parent_bond["normalized_bond_order"]))
                projected_count += 1
            else:
                missing_endpoints = {
                    endpoint for endpoint, present
                    in ((left, left_present), (right, right_present))
                    if not present
                }
                assert missing_endpoints <= allowed
                assert evidence[sample_id]["reaction_delta_class"] == (
                    "covalent_leaving_group_loss"
                )
                assert evidence[sample_id]["parent_leaving_group_bond_verified"] == "True"
                projected = False
                disposition = "verified_leaving_group_endpoint_missing"
            dispositions[disposition] += 1
            independent_bonds.append({
                "sample_id": sample_id,
                "left": left,
                "right": right,
                "order": parent_bond["normalized_bond_order"],
                "left_index": (
                    str(atom_map[left]["local_index"]) if left_present else ""
                ),
                "right_index": (
                    str(atom_map[right]["local_index"]) if right_present else ""
                ),
                "projected": projected,
                "disposition": disposition,
            })
        graph_edges = {(left, right) for left, right, _order in graph_bonds}
        assert _connected(set(atom_map), graph_edges)
        atom_payload = [
            (
                name,
                str(values["type_symbol"]),
                int(parent_map[name]["ccd_formal_charge"]),
            )
            for name, values in atom_map.items()
        ]
        sha = _graph_sha(atom_payload, graph_bonds)
        assert sha == _graph_sha(reversed(atom_payload), graph_bonds)
        assert sha == _graph_sha(atom_payload, reversed(graph_bonds))
        graph_shas[sample_id] = sha

    assert missing == [
        ("CYS_SG_SAMPLE_INDEX_000005", "ZYA", "F1")
    ]
    assert "F1" in parent_atoms_by_component["ZYA"]
    f1_bonds = [
        row for row in parent_bonds_by_component["ZYA"]
        if "F1" in (row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"])
    ]
    assert f1_bonds
    assert evidence["CYS_SG_SAMPLE_INDEX_000005"]["reaction_delta_class"] == (
        "covalent_leaving_group_loss"
    )
    assert evidence["CYS_SG_SAMPLE_INDEX_000005"]["leaving_group_atom_ids"] == "F1"
    assert projected_count == 336
    assert dispositions == {
        "retained_observed_bond": 336,
        "verified_leaving_group_endpoint_missing": 1,
    }

    mapping_rows = _rows(_artifact(contract.MAPPING_FILE))
    assert len(mapping_rows) == 323
    output_mapping = {
        (row["sample_index_row_id"], row["observed_atom_name"]): row
        for row in mapping_rows
    }
    assert len(output_mapping) == 323
    for sample_id, atom_map in observed.items():
        sample = sample_by_id[sample_id]
        parent_map = parent_atoms_by_component[sample["ligand_comp_id"]]
        for atom_name, values in atom_map.items():
            row = output_mapping[(sample_id, atom_name)]
            parent = parent_map[atom_name]
            assert row["pdb_id"] == sample["pdb_id"]
            assert row["ligand_comp_id"] == sample["ligand_comp_id"]
            assert row["observed_type_symbol"] == values["type_symbol"]
            assert int(row["source_full_atom_row_index"]) == values["source_index"]
            assert int(row["retained_heavy_local_index_0based"]) == values["local_index"]
            assert row["parent_ccd_atom_id"] == atom_name
            assert row["parent_ccd_type_symbol"] == values["type_symbol"]
            assert row["parent_ccd_formal_charge"] == parent["ccd_formal_charge"]
            assert row["parent_ccd_heavy_atom_row_index_0based"] == (
                parent["ccd_heavy_atom_row_index_0based"]
            )
            assert _bool(row["atom_name_exact_match"])
            assert _bool(row["element_exact_match"])
            assert _bool(row["reactive_ligand_atom"]) == values["reactive"]
            assert row["observed_graph_sha256"] == graph_shas[sample_id]
            assert row["mapping_authority_source_path"] == values["source_path"]
            assert row["mapping_authority_source_sha256"] == values["source_sha"]
            assert row["authority_class"] == contract.AUTHORITY_CLASS
            assert _bool(row["verified"])

    bond_rows = _rows(_artifact(contract.BOND_FILE))
    assert len(bond_rows) == len(independent_bonds) == 337
    for actual, expected in zip(bond_rows, independent_bonds):
        assert actual["sample_index_row_id"] == expected["sample_id"]
        assert actual["parent_ccd_atom_id_1"] == expected["left"]
        assert actual["parent_ccd_atom_id_2"] == expected["right"]
        assert actual["normalized_bond_order"] == expected["order"]
        assert actual["retained_heavy_local_index_1"] == expected["left_index"]
        assert actual["retained_heavy_local_index_2"] == expected["right_index"]
        assert _bool(actual["projected_to_observed_graph"]) == expected["projected"]
        assert actual["projection_disposition"] == expected["disposition"]
        assert actual["observed_graph_sha256"] == graph_shas[expected["sample_id"]]
        assert _bool(actual["verified"])

    readiness = _rows(_artifact(contract.READINESS_FILE))
    assert len(readiness) == 11
    for row in readiness:
        for field in (
            "parent_component_graph_authority_available",
            "observed_atom_projection_exact",
            "observed_projected_graph_available",
            "parent_graph_valid",
            "observed_graph_valid",
            "pre_reaction_connectivity_available",
            "pre_reaction_bond_order_available",
            "reactive_ligand_atom_available",
            "retained_local_index_contiguous",
        ):
            assert _bool(row[field])
        for field in (
            "reaction_family_label_available",
            "approved_warhead_rule_available",
            "role_proposal_available",
            "minimal_seed_proposal_available",
            "human_gold_review_completed",
            "ready_for_mask_materialization",
            "ready_for_tensorization",
            "ready_for_model_integration",
            "ready_for_training",
        ):
            assert not _bool(row[field])
        assert row["planned_covalent_model_module_count"] == "5"
        assert row["integrated_covalent_model_module_count"] == "0"
        assert row["observed_graph_sha256"] == graph_shas[row["sample_index_row_id"]]

    inventory = _rows(_artifact(contract.SOURCE_INVENTORY_FILE))
    assert len(inventory) == len(contract.FROZEN_BASE_SHA256) == 21
    inventory_by_path = {row["source_path"]: row for row in inventory}
    for path, expected_sha in contract.FROZEN_BASE_SHA256.items():
        row = inventory_by_path[path.as_posix()]
        assert row["source_sha256"] == expected_sha
        assert _bool(row["BASE_tracked"])
        assert _bool(row["verified"])
        if path in contract.LIGAND_ATOM_TABLES:
            assert _bool(row["row_level_atom_names_present"])
        else:
            assert row["row_level_atom_names_present"] == "false"

    failure_rows = _rows(_artifact(contract.FAILURE_FILE))
    assert len(failure_rows) == len(contract.FAILURE_MUTATIONS) == 24
    signatures = set()
    for row in failure_rows:
        mutated = json.loads(row["mutated_fields"])
        reasons = _independent_failure_reasons(mutated)
        signature = _sha(
            json.dumps(mutated, sort_keys=True, separators=(",", ":")).encode()
        )
        assert row["mutation_signature"] == signature
        assert signature not in signatures
        signatures.add(signature)
        assert tuple(row["observed_reasons"].split(";")) == reasons
        assert row["expected_reasons"] in reasons
        for field in (
            "expected_reasons_verified", "fails_closed", "verified"
        ):
            assert _bool(row[field])
        for field in (
            "ready_for_reaction_family_rule_design",
            "ready_for_role_proposal_generation",
            "ready_for_mask_materialization",
            "ready_for_model_integration",
            "ready_for_training",
        ):
            assert not _bool(row[field])

    manifest_payload = _artifact(contract.MANIFEST_FILE)
    manifest = json.loads(manifest_payload)
    assert "covapie_current11_observed_to_parent_atom_projection_authority_manifest.json" not in (
        manifest["output_sha256"]
    )
    for name in contract.OUTPUT_FILES[:-1]:
        assert manifest["output_sha256"][name] == _sha(_artifact(name))
    assert manifest["transaction_succeeded"] is True
    assert manifest["exact_mapping_count"] == 323
    assert manifest["parent_sample_expanded_heavy_atom_count"] == 324
    assert manifest["parent_sample_expanded_bond_count"] == 337
    assert manifest["projected_observed_bond_count"] == 336
    assert manifest["reactive_ligand_atom_count"] == 11
    assert manifest["unexplained_missing_parent_atom_count"] == 0
    assert manifest["observed_graph_sha256_by_sample"] == graph_shas
    assert manifest["reaction_family_label_available_count"] == 0
    assert manifest["approved_warhead_rule_available_count"] == 0
    assert manifest["role_proposal_available_count"] == 0
    assert manifest["minimal_seed_proposal_available_count"] == 0
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["ready_for_training"] is False

    return {
        "lifecycle": lifecycle,
        "mapping_count": len(mapping_rows),
        "parent_expanded_atom_count": 324,
        "parent_expanded_bond_count": len(bond_rows),
        "projected_bond_count": projected_count,
        "leaving_group_bond_count":
            dispositions["verified_leaving_group_endpoint_missing"],
        "graph_count": len(graph_shas),
        "failure_count": len(failure_rows),
        "manifest_sha256": _sha(manifest_payload),
    }


def main() -> int:
    result = check()
    print(
        "current11_observed_projection_checker=passed "
        f"mapping={result['mapping_count']} "
        f"parent_atoms={result['parent_expanded_atom_count']} "
        f"parent_bonds={result['parent_expanded_bond_count']} "
        f"projected_bonds={result['projected_bond_count']} "
        f"leaving_group_bonds={result['leaving_group_bond_count']} "
        f"graphs={result['graph_count']} "
        f"failures={result['failure_count']}"
    )
    print("manifest_sha256=" + result["manifest_sha256"])
    print("ready_for_training=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

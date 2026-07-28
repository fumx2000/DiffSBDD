#!/usr/bin/env python3
"""Independent checker for Exact9 audited local CCD parent graph authority."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import os
import re
import shlex
import stat
import subprocess
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_exact9_audited_local_ccd_parent_graph_authority_v1 as authority,
)


EXACT10 = (
    Path("src/covalent_ext/covapie_exact9_audited_local_ccd_parent_graph_authority_v1.py"),
    Path("tests/test_covapie_exact9_audited_local_ccd_parent_graph_authority_v1.py"),
    Path("scripts/check_covapie_exact9_audited_local_ccd_parent_graph_authority_v1.py"),
    Path("docs/covapie_exact9_audited_local_ccd_parent_graph_authority_v1_summary.md"),
    *(authority.OUTPUT_ROOT / name for name in authority.OUTPUT_FILES),
)
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
)
EXPECTED_FAILURE_CASES = (
    "payload missing", "payload not regular", "payload symlink",
    "payload empty", "payload oversize", "payload mode invalid",
    "payload not ignored", "payload tracked", "payload staged",
    "payload SHA mismatch", "BASE audit SHA mismatch", "decode failure",
    "component identity missing", "component identity mismatch",
    "atom loop missing", "bond loop missing", "charge invalid",
    "all-hydrogen component", "unsupported element",
    "unsupported bond order", "duplicate parent atom or edge",
    "parent graph disconnected", "partial materialization attempted",
    "execution boundary crossed",
)
FALSE_READINESS_FIELDS = (
    "observed_atom_projection_exact", "observed_projected_graph_available",
    "reaction_family_label_available", "approved_warhead_rule_available",
    "role_proposal_generation_ready", "minimal_seed_proposal_generation_ready",
    "human_gold_review_completed", "ready_for_mask_materialization",
    "ready_for_tensorization", "ready_for_model_integration",
    "ready_for_training",
)


def _git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(
            result.stderr.decode("utf-8", "backslashreplace").strip()
        )
    return result


def _base_bytes(path: Path) -> bytes:
    payload = _git(
        "show", f"{authority.BASE_COMMIT}:{path.as_posix()}"
    ).stdout
    assert hashlib.sha256(payload).hexdigest() == authority.FROZEN_BASE_SHA256[path]
    return payload


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8", "strict"))))


def _artifact_rows(name: str) -> list[dict[str, str]]:
    return _rows((ROOT / authority.OUTPUT_ROOT / name).read_bytes())


def _bool(value: str) -> bool:
    assert value in ("true", "false", "True", "False")
    return value.lower() == "true"


def _parse_loop(
    text: str,
    prefix: str,
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if lines[index].strip() != "loop_":
            index += 1
            continue
        index += 1
        tags: list[str] = []
        while index < len(lines) and lines[index].strip().startswith("_"):
            tags.append(lines[index].strip().split()[0])
            index += 1
        if not tags or not any(tag.startswith(prefix) for tag in tags):
            continue
        tokens: list[str] = []
        while index < len(lines):
            stripped = lines[index].strip()
            if (
                not stripped
                or stripped.startswith("#")
                or stripped == "loop_"
                or stripped.startswith("_")
                or stripped.startswith("data_")
            ):
                break
            tokens.extend(shlex.split(lines[index], comments=False, posix=True))
            index += 1
        assert len(tokens) % len(tags) == 0
        return tuple(tags), [
            dict(zip(tags, tokens[offset:offset + len(tags)]))
            for offset in range(0, len(tokens), len(tags))
        ]
    return (), []


def _normalize_independently(value_order: str, aromatic_flag: str) -> str:
    order = value_order.strip().upper()
    flag = aromatic_flag.strip().upper()
    assert flag in ("Y", "N")
    if flag == "Y":
        assert order in ("SING", "DOUB", "AROM")
        return "aromatic"
    mapping = {"SING": "single", "DOUB": "double", "TRIP": "triple"}
    assert order in mapping
    return mapping[order]


def _component_count(
    vertices: set[str],
    edges: set[tuple[str, str]],
) -> int:
    adjacency = {vertex: set() for vertex in vertices}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    remaining = set(vertices)
    count = 0
    while remaining:
        count += 1
        queue = deque([min(remaining)])
        visited: set[str] = set()
        while queue:
            vertex = queue.popleft()
            if vertex in visited:
                continue
            visited.add(vertex)
            queue.extend(sorted(adjacency[vertex] - visited))
        remaining -= visited
    return count


def _graph_sha(
    atoms: Iterable[tuple[str, str, int]],
    bonds: Iterable[tuple[str, str, str]],
) -> str:
    payload = {
        "atoms": [
            [atom_id, element.upper(), charge]
            for atom_id, element, charge in sorted(atoms)
        ],
        "bonds": [
            list(edge)
            for edge in sorted(
                (min(left, right), max(left, right), order)
                for left, right, order in bonds
            )
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _rebuild_component(
    component: str,
    expected_sha: str,
) -> dict[str, Any]:
    relative = authority.CCD_ROOT / f"{component}.cif"
    absolute = ROOT / relative
    file_stat = os.lstat(absolute)
    assert stat.S_ISREG(file_stat.st_mode)
    assert not stat.S_ISLNK(file_stat.st_mode)
    assert 0 < file_stat.st_size < authority.MAX_PAYLOAD_SIZE_BYTES
    assert stat.S_IMODE(file_stat.st_mode) == 0o644
    assert _git("check-ignore", "-q", "--", relative.as_posix(), check=False).returncode == 0
    assert _git(
        "cat-file", "-e", f"{authority.BASE_COMMIT}:{relative.as_posix()}",
        check=False,
    ).returncode != 0
    assert not _git(
        "diff", "--cached", "--name-only", "--", relative.as_posix()
    ).stdout
    payload = absolute.read_bytes()
    observed_sha = hashlib.sha256(payload).hexdigest()
    assert observed_sha == expected_sha
    text = payload.decode("utf-8", "strict")

    data_ids = [
        stripped[5:].strip()
        for line in text.splitlines()
        if (stripped := line.strip()).startswith("data_")
    ]
    comp_ids = []
    for line in text.splitlines():
        tokens = shlex.split(line.strip(), comments=False, posix=True)
        if len(tokens) == 2 and tokens[0] == "_chem_comp.id":
            comp_ids.append(tokens[1])
    assert data_ids == [component]
    assert comp_ids == [component]

    atom_tags, atom_rows = _parse_loop(text, "_chem_comp_atom.")
    bond_tags, bond_rows = _parse_loop(text, "_chem_comp_bond.")
    assert atom_tags and bond_tags
    atom_required = {
        "_chem_comp_atom.atom_id", "_chem_comp_atom.type_symbol",
        "_chem_comp_atom.charge",
    }
    bond_required = {
        "_chem_comp_bond.atom_id_1", "_chem_comp_bond.atom_id_2",
        "_chem_comp_bond.value_order",
        "_chem_comp_bond.pdbx_aromatic_flag",
    }
    assert atom_required <= set(atom_tags)
    assert bond_required <= set(bond_tags)

    source_atoms: list[tuple[str, str, int]] = []
    for row in atom_rows:
        atom_id = row["_chem_comp_atom.atom_id"]
        element = row["_chem_comp_atom.type_symbol"].strip().upper()
        charge = row["_chem_comp_atom.charge"].strip()
        assert atom_id
        assert element
        assert re.fullmatch(r"[+-]?\d+", charge)
        source_atoms.append((atom_id, element, int(charge)))
    assert len({atom[0] for atom in source_atoms}) == len(source_atoms)
    element_by_id = {atom_id: element for atom_id, element, _ in source_atoms}
    hydrogen_ids = {
        atom_id
        for atom_id, element, _ in source_atoms
        if element in authority.EXPLICIT_HYDROGEN_TYPE_SYMBOLS
    }
    heavy_atoms = tuple(
        atom for atom in source_atoms if atom[0] not in hydrogen_ids
    )
    assert heavy_atoms
    assert all(
        atom[1] in authority.SUPPORTED_ELEMENTS
        and atom[1] not in authority.EXPLICIT_HYDROGEN_TYPE_SYMBOLS
        for atom in heavy_atoms
    )
    heavy_ids = {atom[0] for atom in heavy_atoms}

    normalized_bonds: list[tuple[str, str, str, str, str]] = []
    hydrogen_bond_count = 0
    undirected: set[tuple[str, str]] = set()
    for row in bond_rows:
        left = row["_chem_comp_bond.atom_id_1"]
        right = row["_chem_comp_bond.atom_id_2"]
        assert left in element_by_id and right in element_by_id
        if left in hydrogen_ids or right in hydrogen_ids:
            hydrogen_bond_count += 1
            continue
        assert left != right
        canonical = (min(left, right), max(left, right))
        assert canonical not in undirected
        undirected.add(canonical)
        source_order = row["_chem_comp_bond.value_order"].strip().upper()
        source_flag = row["_chem_comp_bond.pdbx_aromatic_flag"].strip().upper()
        normalized_bonds.append((
            *canonical, source_order, source_flag,
            _normalize_independently(source_order, source_flag),
        ))
    assert all(left in heavy_ids and right in heavy_ids for left, right in undirected)
    assert _component_count(heavy_ids, undirected) == 1
    graph_edges = tuple((left, right, order) for left, right, _, _, order in normalized_bonds)
    graph_sha = _graph_sha(heavy_atoms, graph_edges)
    assert graph_sha == _graph_sha(tuple(reversed(heavy_atoms)), graph_edges)
    assert graph_sha == _graph_sha(heavy_atoms, tuple(reversed(graph_edges)))
    return {
        "relative_path": relative.as_posix(),
        "sha256": observed_sha,
        "file_size_bytes": file_stat.st_size,
        "source_atom_count": len(source_atoms),
        "hydrogen_atom_count": len(hydrogen_ids),
        "heavy_atoms": heavy_atoms,
        "source_bond_count": len(bond_rows),
        "hydrogen_bond_count": hydrogen_bond_count,
        "heavy_bonds": tuple(sorted(normalized_bonds)),
        "graph_sha": graph_sha,
    }


def _expected_audit() -> dict[str, dict[str, str]]:
    rows = _rows(_base_bytes(authority.CCD_AUDIT))
    assert len(rows) == 9
    assert tuple(row["het_id"] for row in rows) == authority.EXACT9_COMPONENTS
    assert len({row["sha256"] for row in rows}) == 9
    by_component = {row["het_id"]: row for row in rows}
    for component, path in zip(authority.EXACT9_COMPONENTS, authority.EXACT9_PATHS):
        row = by_component[component]
        assert row["ccd_raw_path"] == path.as_posix()
        assert re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
        assert all(
            _bool(row[field])
            for field in ("file_exists", "integrity_passed", "ccd_audit_passed")
        )
        assert row["blocking_reasons"] == ""
    return by_component


def _check_base() -> None:
    shown = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", authority.BASE_COMMIT
    ).stdout.decode().splitlines()
    assert shown == [
        authority.BASE_COMMIT, authority.BASE_PARENT, authority.BASE_TREE,
        authority.BASE_SUBJECT,
    ]
    for path in authority.FROZEN_BASE_SHA256:
        _base_bytes(path)
    assert _git(
        "rev-parse", f"{authority.BASE_COMMIT}:.gitignore"
    ).stdout.decode().strip() == authority.GITIGNORE_BLOB


def _check_exact10() -> None:
    assert len(EXACT10) == len(set(EXACT10)) == 10
    assert not any(path.as_posix().startswith("data/raw/") for path in EXACT10)
    assert set(path.name for path in EXACT10[4:]) == set(authority.OUTPUT_FILES)
    for path in EXACT10:
        absolute = ROOT / path
        assert absolute.is_file() and not absolute.is_symlink()
        assert stat.S_IMODE(os.lstat(absolute).st_mode) == 0o644
        assert path.suffix.lower() not in FORBIDDEN_SUFFIXES
    generated = {path.name for path in (ROOT / authority.OUTPUT_ROOT).iterdir()}
    assert generated == set(authority.OUTPUT_FILES)


def _check_authority(
    rebuilt: Mapping[str, Mapping[str, Any]],
) -> tuple[int, int, Counter[str]]:
    admission = _artifact_rows(authority.ADMISSION_FILE)
    atoms = _artifact_rows(authority.ATOM_FILE)
    bonds = _artifact_rows(authority.BOND_FILE)
    assert len(admission) == 9
    assert tuple(row["ligand_comp_id"] for row in admission) == authority.EXACT9_COMPONENTS
    admission_by_component = {row["ligand_comp_id"]: row for row in admission}
    expected_atom_rows = []
    expected_bond_rows = []
    for component in authority.EXACT9_COMPONENTS:
        rebuilt_component = rebuilt[component]
        row = admission_by_component[component]
        assert row["source_relative_path"] == rebuilt_component["relative_path"]
        assert row["expected_sha256"] == row["observed_sha256"] == rebuilt_component["sha256"]
        assert int(row["file_size_bytes"]) == rebuilt_component["file_size_bytes"]
        assert row["mode"] == "0644"
        assert all(
            _bool(row[field])
            for field in (
                "file_exists", "regular_file", "ignored_by_project_gitignore",
                "BASE_audit_integrity_passed", "payload_sha_matches",
                "decode_passed", "component_identity_passed", "parse_passed",
                "verified",
            )
        )
        assert not _bool(row["symlink"])
        assert not _bool(row["BASE_tracked"])
        assert not _bool(row["staged"])
        assert int(row["source_atom_row_count"]) == rebuilt_component["source_atom_count"]
        assert int(row["explicit_hydrogen_atom_count"]) == rebuilt_component["hydrogen_atom_count"]
        assert int(row["parent_heavy_atom_count"]) == len(rebuilt_component["heavy_atoms"])
        assert int(row["source_bond_row_count"]) == rebuilt_component["source_bond_count"]
        assert int(row["hydrogen_involving_bond_count"]) == rebuilt_component["hydrogen_bond_count"]
        assert int(row["parent_heavy_bond_count"]) == len(rebuilt_component["heavy_bonds"])
        assert int(row["unsupported_bond_order_count"]) == 0
        assert int(row["parent_component_count"]) == 1
        assert row["parent_graph_sha256"] == rebuilt_component["graph_sha"]
        assert row["admission_disposition"] == "admitted_sha_attested_local_ccd"
        assert row["blocking_reasons"] == ""
        for index, (atom_id, element, charge) in enumerate(rebuilt_component["heavy_atoms"]):
            expected_atom_rows.append((
                component, rebuilt_component["relative_path"],
                rebuilt_component["sha256"], atom_id, element, str(charge),
                str(index), rebuilt_component["graph_sha"],
            ))
        for left, right, source_order, source_flag, normalized in rebuilt_component["heavy_bonds"]:
            expected_bond_rows.append((
                component, rebuilt_component["relative_path"],
                rebuilt_component["sha256"], left, right, source_order,
                source_flag, normalized, rebuilt_component["graph_sha"],
            ))
    observed_atom_rows = [
        (
            row["ligand_comp_id"], row["ccd_source_relative_path"],
            row["ccd_source_sha256"], row["ccd_atom_id"],
            row["ccd_type_symbol"], row["ccd_formal_charge"],
            row["ccd_heavy_atom_row_index_0based"],
            row["component_parent_graph_sha256"],
        )
        for row in atoms
    ]
    observed_bond_rows = [
        (
            row["ligand_comp_id"], row["ccd_source_relative_path"],
            row["ccd_source_sha256"], row["parent_ccd_atom_id_1"],
            row["parent_ccd_atom_id_2"], row["source_value_order"],
            row["source_aromatic_flag"], row["normalized_bond_order"],
            row["component_parent_graph_sha256"],
        )
        for row in bonds
    ]
    assert observed_atom_rows == expected_atom_rows
    assert observed_bond_rows == expected_bond_rows
    assert all(
        row["ccd_parser_contract_version"] == authority.PARSER_CONTRACT_VERSION
        and row["authority_class"] == authority.AUTHORITY_CLASS
        and _bool(row["verified"])
        for row in atoms
    )
    assert all(
        row["authority_class"] == authority.AUTHORITY_CLASS
        and row["normalized_bond_order"] in authority.NORMALIZED_BOND_ORDERS
        and _bool(row["verified"])
        for row in bonds
    )
    return len(atoms), len(bonds), Counter(
        row["normalized_bond_order"] for row in bonds
    )


def _check_current11(rebuilt: Mapping[str, Mapping[str, Any]]) -> int:
    index_rows = _rows(_base_bytes(authority.FINAL_INDEX))
    graph_rows = _rows(_base_bytes(authority.GRAPH_EVIDENCE))
    readiness = _artifact_rows(authority.READINESS_FILE)
    assert len(index_rows) == len(graph_rows) == len(readiness) == 11
    graph_by_id = {row["sample_index_row_id"]: row for row in graph_rows}
    readiness_by_id = {row["sample_index_row_id"]: row for row in readiness}
    assert set(row["ligand_comp_id"] for row in index_rows) == set(authority.EXACT9_COMPONENTS)
    expanded_total = 0
    for index_row in index_rows:
        row_id = index_row["sample_index_row_id"]
        support = graph_by_id[row_id]
        ready = readiness_by_id[row_id]
        component = index_row["ligand_comp_id"]
        assert (
            support["pdb_id"] == ready["pdb_id"] == index_row["pdb_id"]
            and support["ligand_comp_id"] == ready["ligand_comp_id"] == component
        )
        derived_count = len(rebuilt[component]["heavy_atoms"])
        supporting_count = int(support["parent_ccd_heavy_atom_count"])
        expanded_total += derived_count
        assert derived_count == supporting_count
        assert int(ready["derived_parent_heavy_atom_count"]) == derived_count
        assert int(ready["supporting_parent_heavy_atom_count"]) == supporting_count
        assert all(
            _bool(ready[field])
            for field in (
                "local_ccd_admitted",
                "component_parent_atom_authority_available",
                "component_parent_bond_order_authority_available",
                "component_parent_graph_valid",
                "parent_heavy_atom_count_matches",
                "verified",
            )
        )
        assert ready["component_parent_graph_sha256"] == rebuilt[component]["graph_sha"]
        assert all(not _bool(ready[field]) for field in FALSE_READINESS_FIELDS)
    assert expanded_total == 324
    return expanded_total


def _check_failures() -> None:
    rows = _artifact_rows(authority.FAILURE_FILE)
    assert len(rows) == 24
    assert tuple(row["failure_case"] for row in rows) == EXPECTED_FAILURE_CASES
    assert len({row["mutation_signature"] for row in rows}) == 24
    for row in rows:
        fields = json.loads(row["mutated_fields"])
        assert json.dumps(fields, sort_keys=True, separators=(",", ":")) == row["mutated_fields"]
        assert hashlib.sha256(row["mutated_fields"].encode()).hexdigest() == row["mutation_signature"]
        assert fields
        for name, value in fields.items():
            baseline = getattr(authority.BASELINE_SCENARIO, name)
            assert type(value) is type(baseline)
            assert value != baseline
        expected = set(filter(None, row["expected_reasons"].split(";")))
        observed_values = tuple(
            filter(None, row["observed_reasons"].split(";"))
        )
        observed = set(observed_values)
        independently_observed = _independent_scenario_reasons(
            {
                field.name: fields.get(
                    field.name,
                    getattr(authority.BASELINE_SCENARIO, field.name),
                )
                for field in dataclasses.fields(authority.FailureScenario)
            }
        )
        assert observed_values == independently_observed
        assert expected <= observed
        assert all(
            _bool(row[field])
            for field in (
                "expected_reasons_verified", "fails_closed", "verified",
            )
        )
        assert all(
            not _bool(row[field])
            for field in (
                "ready_for_current11_observed_projection",
                "ready_for_reaction_family_rule_design",
                "ready_for_role_proposal_generation",
                "ready_for_mask_materialization",
                "ready_for_model_integration", "ready_for_training",
            )
        )


def _independent_scenario_reasons(scenario: Mapping[str, Any]) -> tuple[str, ...]:
    checks = (
        (not scenario["payload_exists"], "payload_missing"),
        (not scenario["regular_file"], "payload_not_regular"),
        (scenario["symlink"], "payload_symlink"),
        (scenario["file_size_bytes"] == 0, "payload_empty"),
        (
            scenario["file_size_bytes"] >= authority.MAX_PAYLOAD_SIZE_BYTES,
            "payload_oversize",
        ),
        (scenario["mode"] != 0o644, "payload_mode_invalid"),
        (
            not scenario["ignored_by_project_gitignore"],
            "payload_not_ignored",
        ),
        (scenario["raw_tracked"], "payload_raw_tracked"),
        (scenario["raw_staged"], "payload_raw_staged"),
        (not scenario["payload_sha_matches"], "payload_sha_mismatch"),
        (not scenario["base_audit_sha_matches"], "base_audit_sha_mismatch"),
        (not scenario["decode_passed"], "payload_decode_failed"),
        (
            not scenario["component_identity_present"],
            "ccd_component_identity_missing",
        ),
        (
            not scenario["component_identity_matches"],
            "ccd_component_identity_mismatch",
        ),
        (not scenario["atom_loop_present"], "chem_comp_atom_loop_missing"),
        (not scenario["bond_loop_present"], "chem_comp_bond_loop_missing"),
        (
            not scenario["charge_valid"],
            "chem_comp_atom_charge_missing_or_invalid",
        ),
        (
            scenario["parent_heavy_atom_count"] == 0,
            "parent_heavy_atom_table_empty",
        ),
        (scenario["unsupported_element_count"] > 0, "unsupported_element"),
        (
            scenario["unsupported_bond_order_count"] > 0,
            "unsupported_ccd_bond_order",
        ),
        (
            scenario["duplicate_parent_atom_or_edge_count"] > 0,
            "duplicate_parent_atom_or_edge",
        ),
        (
            scenario["parent_component_count"] != 1,
            "parent_graph_disconnected",
        ),
        (
            scenario["partial_materialization_attempted"],
            "partial_materialization_attempted",
        ),
        (
            scenario["execution_boundary_crossed"],
            "execution_boundary_crossed",
        ),
    )
    return tuple(reason for condition, reason in checks if condition)


def _check_manifest(
    atom_count: int,
    bond_count: int,
    order_counts: Counter[str],
    expanded_total: int,
) -> None:
    manifest_path = ROOT / authority.OUTPUT_ROOT / authority.MANIFEST_FILE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == authority.SCHEMA_VERSION
    assert manifest["formal_base"] == {
        "commit": authority.BASE_COMMIT, "parent": authority.BASE_PARENT,
        "tree": authority.BASE_TREE, "subject": authority.BASE_SUBJECT,
    }
    assert manifest["formal_commit_subject"] == authority.FORMAL_COMMIT_SUBJECT
    assert manifest["exact9_component_count"] == 9
    assert manifest["exact9_local_ccd_admitted_count"] == 9
    assert manifest["exact9_parent_atom_authority_available_count"] == 9
    assert manifest["exact9_parent_bond_authority_available_count"] == 9
    assert manifest["exact9_parent_graph_valid_count"] == 9
    assert manifest["unique_component_parent_atom_row_count"] == atom_count
    assert manifest["unique_component_parent_bond_row_count"] == bond_count
    assert manifest["bond_order_distribution"] == {
        order: order_counts[order] for order in authority.NORMALIZED_BOND_ORDERS
    }
    assert manifest["unsupported_bond_order_count"] == 0
    assert manifest["current11_row_count"] == 11
    assert manifest["current11_parent_component_graph_coverage_count"] == 11
    assert manifest["current11_parent_component_bond_order_coverage_count"] == 11
    assert manifest["current11_sample_expanded_parent_atom_occurrence_count"] == expanded_total == 324
    assert manifest["supporting_parent_atom_occurrence_expected_count"] == 324
    assert manifest["supporting_parent_atom_occurrence_count_matches"] is True
    zero_fields = (
        "current11_observed_atom_projection_exact_count",
        "current11_observed_projected_graph_available_count",
        "reaction_family_label_available_count",
        "approved_warhead_rule_available_count",
        "role_proposal_generation_ready_count",
        "minimal_seed_proposal_generation_ready_count",
        "human_gold_review_completed_count",
        "integrated_covalent_model_module_count",
    )
    assert all(manifest[field] == 0 for field in zero_fields)
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["failure_matrix_row_count"] == 24
    assert manifest["failure_mutation_signatures_unique"] is True
    assert manifest["failure_expected_reasons_verified"] is True
    assert manifest["transaction_phase_a_passed"] is True
    assert manifest["transaction_phase_b_passed"] is True
    assert manifest["transaction_authority_materialized"] is True
    assert manifest["raw_payload_read"] is True
    assert manifest["raw_payload_modified"] is False
    assert manifest["raw_payload_tracked"] is False
    assert manifest["raw_payload_staged"] is False
    assert manifest["network_used"] is False
    assert manifest["download_performed"] is False
    assert all(
        manifest[field] is False
        for field in (
            "role_or_seed_materialized", "mask_materialized",
            "tensor_materialized", "model_changed", "training_used",
            "ready_for_mask_materialization", "ready_for_tensorization",
            "ready_for_model_integration", "ready_for_training",
        )
    )
    assert manifest["outcome"] == "exact9_parent_component_graph_authority_materialized"
    assert manifest["recommended_next_step"] == (
        "materialize_covapie_current11_observed_to_parent_atom_"
        "projection_authority_v1"
    )
    assert authority.MANIFEST_FILE not in manifest["evidence_sha256"]
    assert manifest["evidence_sha256"] == {
        name: hashlib.sha256(
            (ROOT / authority.OUTPUT_ROOT / name).read_bytes()
        ).hexdigest()
        for name in authority.OUTPUT_FILES
        if name != authority.MANIFEST_FILE
    }
    assert not any(str(ROOT) in value for value in _strings(manifest))


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def main() -> int:
    _check_base()
    _check_exact10()
    audit = _expected_audit()
    rebuilt = {
        component: _rebuild_component(component, audit[component]["sha256"])
        for component in authority.EXACT9_COMPONENTS
    }
    atom_count, bond_count, order_counts = _check_authority(rebuilt)
    expanded_total = _check_current11(rebuilt)
    _check_failures()
    _check_manifest(atom_count, bond_count, order_counts, expanded_total)
    print(
        "CovaPIE Exact9 audited local CCD parent graph authority v1 "
        f"verified: components=9 atoms={atom_count} bonds={bond_count} "
        f"current11=11 expanded_atoms={expanded_total} failures=24 "
        "training=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Materialize SHA-attested Exact9 heavy-only CCD parent graph authority."""

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
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from covalent_ext.covapie_current11_pre_reaction_graph_and_bond_order_authority_v1 import (
    EXPLICIT_HYDROGEN_TYPE_SYMBOLS,
    SUPPORTED_ELEMENTS,
    ParentAtom,
    ParentBond,
    canonicalize_element_symbol_v1,
    normalize_bond_order,
    parse_ccd_component_with_stats,
)


BASE_COMMIT = "f8f6945c86a4258387e57691e206753d0b193793"
BASE_PARENT = "83582df5e59d244a1648f6fcf50a2c982e2d702c"
BASE_TREE = "43b748f4c6b45d657357789e8357518c1c6cd162"
BASE_SUBJECT = "add CovaPIE audited local CCD cache ignore contract v1"
FORMAL_COMMIT_SUBJECT = "add CovaPIE Exact9 audited CCD parent graph authority v1"
SCHEMA_VERSION = "covapie_exact9_audited_local_ccd_parent_graph_authority_v1"
PARSER_CONTRACT_VERSION = (
    "covapie_current11_pre_reaction_graph_and_bond_order_authority_v1"
)
AUTHORITY_CLASS = "sha_attested_local_ccd_derived_authority"
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
CCD_ROOT = Path(
    "data/raw/covalent_sources/ccd/independence_evidence_batch_000001"
)
EXACT9_COMPONENTS = (
    "JUG", "E64", "ZYA", "PCM", "INP", "INA", "IN6", "IN3", "UFP",
)
EXACT9_PATHS = tuple(CCD_ROOT / f"{component}.cif" for component in EXACT9_COMPONENTS)
MAX_PAYLOAD_SIZE_BYTES = 5 * 1024 * 1024
NORMALIZED_BOND_ORDERS = ("single", "double", "triple", "aromatic")

PREDECESSOR_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_pre_reaction_graph_and_bond_order_authority_v1.py"
)
PREDECESSOR_SUMMARY = Path(
    "docs/covapie_current11_pre_reaction_graph_and_bond_order_authority_v1_summary.md"
)
PREDECESSOR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_pre_reaction_graph_and_bond_order_authority_v1"
)
PREDECESSOR_MANIFEST = PREDECESSOR_ROOT / (
    "covapie_current11_pre_reaction_graph_and_bond_order_authority_manifest.json"
)
PREDECESSOR_INVENTORY = PREDECESSOR_ROOT / (
    "covapie_pre_reaction_graph_source_inventory.csv"
)
PREDECESSOR_READINESS = PREDECESSOR_ROOT / (
    "covapie_current11_graph_authority_readiness_matrix.csv"
)
CCD_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ccd_acquisition_integrity_audit.csv"
)
GRAPH_EVIDENCE = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv"
)
FINAL_INDEX = Path(
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/"
    "final_dataset_index.csv"
)
GITIGNORE = Path(".gitignore")

FROZEN_BASE_SHA256 = {
    PREDECESSOR_SOURCE:
        "fc3afac00655c4e0857d12464d7e9c658bb8ac86bde2f845149d26bdda4ad284",
    PREDECESSOR_SUMMARY:
        "1a15fb1a932a2aa05f063eb2755f0e7c4fa61ef377ee6972493ecc0413503fb8",
    PREDECESSOR_MANIFEST:
        "4a3ab3ba6edf83f7f85f9418e5146a63814f5dec383a38ff61a7bcfc2df68626",
    PREDECESSOR_INVENTORY:
        "aa8fd4aef9d549280777fa39fc22be396fbf09af15b0fb029bd7ff54b576f1af",
    PREDECESSOR_READINESS:
        "ed136fcda0997119fb84404cbea2e304b4e68946d65cae41a67b2e6c52404606",
    CCD_AUDIT:
        "79cf1ef3ccb3431b804fbf7af8bb12eb654615d332df002c70d8b0fa011ca848",
    GRAPH_EVIDENCE:
        "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
    FINAL_INDEX:
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    GITIGNORE:
        "90e01afd4f9e028671bd39d23a19dcb06af2a63d100025a786a6b94994e36345",
}
GITIGNORE_BLOB = "af41f27891066b08a515438dc305c5449a5a488b"

ADMISSION_FILE = "covapie_exact9_local_ccd_admission_audit.csv"
ATOM_FILE = "covapie_exact9_parent_heavy_atom_authority.csv"
BOND_FILE = "covapie_exact9_parent_heavy_bond_authority.csv"
READINESS_FILE = "covapie_current11_parent_component_graph_readiness_matrix.csv"
FAILURE_FILE = "covapie_exact9_parent_graph_authority_failure_matrix.csv"
MANIFEST_FILE = "covapie_exact9_audited_local_ccd_parent_graph_authority_manifest.json"
OUTPUT_FILES = (
    ADMISSION_FILE, ATOM_FILE, BOND_FILE, READINESS_FILE, FAILURE_FILE,
    MANIFEST_FILE,
)

ADMISSION_COLUMNS = (
    "ligand_comp_id", "source_relative_path", "expected_sha256",
    "observed_sha256", "file_exists", "regular_file", "symlink",
    "file_size_bytes", "mode", "ignored_by_project_gitignore",
    "BASE_tracked", "staged", "BASE_audit_integrity_passed",
    "payload_sha_matches", "decode_passed", "component_identity_passed",
    "parse_passed", "source_atom_row_count",
    "explicit_hydrogen_atom_count", "parent_heavy_atom_count",
    "source_bond_row_count", "hydrogen_involving_bond_count",
    "parent_heavy_bond_count", "unsupported_bond_order_count",
    "parent_component_count", "parent_graph_sha256",
    "admission_disposition", "blocking_reasons", "verified",
)
ATOM_COLUMNS = (
    "ligand_comp_id", "ccd_source_relative_path", "ccd_source_sha256",
    "ccd_parser_contract_version", "ccd_atom_id", "ccd_type_symbol",
    "ccd_formal_charge", "ccd_heavy_atom_row_index_0based",
    "component_parent_graph_sha256", "authority_class", "verified",
)
BOND_COLUMNS = (
    "ligand_comp_id", "ccd_source_relative_path", "ccd_source_sha256",
    "parent_ccd_atom_id_1", "parent_ccd_atom_id_2", "source_value_order",
    "source_aromatic_flag", "normalized_bond_order",
    "component_parent_graph_sha256", "authority_class", "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "local_ccd_admitted", "component_parent_atom_authority_available",
    "component_parent_bond_order_authority_available",
    "component_parent_graph_valid", "component_parent_graph_sha256",
    "supporting_parent_heavy_atom_count", "derived_parent_heavy_atom_count",
    "parent_heavy_atom_count_matches", "observed_atom_projection_exact",
    "observed_projected_graph_available", "reaction_family_label_available",
    "approved_warhead_rule_available", "role_proposal_generation_ready",
    "minimal_seed_proposal_generation_ready", "human_gold_review_completed",
    "ready_for_mask_materialization", "ready_for_tensorization",
    "ready_for_model_integration", "ready_for_training", "blocking_reasons",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case", "mutation_signature", "mutated_fields",
    "expected_reasons", "observed_reasons", "expected_reasons_verified",
    "fails_closed", "ready_for_current11_observed_projection",
    "ready_for_reaction_family_rule_design",
    "ready_for_role_proposal_generation", "ready_for_mask_materialization",
    "ready_for_model_integration", "ready_for_training", "verified",
)

ADMISSION_DISPOSITIONS = (
    "admitted_sha_attested_local_ccd", "blocked_missing",
    "blocked_not_regular", "blocked_symlink", "blocked_empty",
    "blocked_oversize", "blocked_mode", "blocked_not_ignored",
    "blocked_raw_tracked", "blocked_raw_staged", "blocked_sha_mismatch",
    "blocked_audit_mismatch", "blocked_decode",
    "blocked_component_identity", "blocked_parse",
    "blocked_graph_validation",
)


@dataclass(frozen=True)
class ComponentAuthority:
    ligand_comp_id: str
    source_path: Path
    expected_sha256: str
    observed_sha256: str
    atoms: tuple[ParentAtom, ...]
    bonds: tuple[ParentBond, ...]
    normalized_bonds: tuple[tuple[str, str, str, str, str], ...]
    source_atom_row_count: int
    explicit_hydrogen_atom_count: int
    source_bond_row_count: int
    hydrogen_involving_bond_count: int
    parent_component_count: int
    graph_sha256: str
    admission_row: Mapping[str, Any]


@dataclass(frozen=True)
class FailureScenario:
    payload_exists: bool = True
    regular_file: bool = True
    symlink: bool = False
    file_size_bytes: int = 1
    mode: int = 0o644
    ignored_by_project_gitignore: bool = True
    raw_tracked: bool = False
    raw_staged: bool = False
    payload_sha_matches: bool = True
    base_audit_sha_matches: bool = True
    decode_passed: bool = True
    component_identity_present: bool = True
    component_identity_matches: bool = True
    atom_loop_present: bool = True
    bond_loop_present: bool = True
    charge_valid: bool = True
    parent_heavy_atom_count: int = 1
    unsupported_element_count: int = 0
    unsupported_bond_order_count: int = 0
    duplicate_parent_atom_or_edge_count: int = 0
    parent_component_count: int = 1
    partial_materialization_attempted: bool = False
    execution_boundary_crossed: bool = False


@dataclass(frozen=True)
class ScenarioObservation:
    reasons: tuple[str, ...]
    fails_closed: bool
    ready_for_current11_observed_projection: bool
    ready_for_reaction_family_rule_design: bool
    ready_for_role_proposal_generation: bool
    ready_for_mask_materialization: bool
    ready_for_model_integration: bool
    ready_for_training: bool


BASELINE_SCENARIO = FailureScenario()
FAILURE_MUTATIONS: dict[str, dict[str, Any]] = {
    "payload missing": {
        "fields": {"payload_exists": False},
        "expected_reasons": ("payload_missing",),
    },
    "payload not regular": {
        "fields": {"regular_file": False},
        "expected_reasons": ("payload_not_regular",),
    },
    "payload symlink": {
        "fields": {"symlink": True},
        "expected_reasons": ("payload_symlink",),
    },
    "payload empty": {
        "fields": {"file_size_bytes": 0},
        "expected_reasons": ("payload_empty",),
    },
    "payload oversize": {
        "fields": {"file_size_bytes": MAX_PAYLOAD_SIZE_BYTES},
        "expected_reasons": ("payload_oversize",),
    },
    "payload mode invalid": {
        "fields": {"mode": 0o600},
        "expected_reasons": ("payload_mode_invalid",),
    },
    "payload not ignored": {
        "fields": {"ignored_by_project_gitignore": False},
        "expected_reasons": ("payload_not_ignored",),
    },
    "payload tracked": {
        "fields": {"raw_tracked": True},
        "expected_reasons": ("payload_raw_tracked",),
    },
    "payload staged": {
        "fields": {"raw_staged": True},
        "expected_reasons": ("payload_raw_staged",),
    },
    "payload SHA mismatch": {
        "fields": {"payload_sha_matches": False},
        "expected_reasons": ("payload_sha_mismatch",),
    },
    "BASE audit SHA mismatch": {
        "fields": {"base_audit_sha_matches": False},
        "expected_reasons": ("base_audit_sha_mismatch",),
    },
    "decode failure": {
        "fields": {"decode_passed": False},
        "expected_reasons": ("payload_decode_failed",),
    },
    "component identity missing": {
        "fields": {"component_identity_present": False},
        "expected_reasons": ("ccd_component_identity_missing",),
    },
    "component identity mismatch": {
        "fields": {"component_identity_matches": False},
        "expected_reasons": ("ccd_component_identity_mismatch",),
    },
    "atom loop missing": {
        "fields": {"atom_loop_present": False},
        "expected_reasons": ("chem_comp_atom_loop_missing",),
    },
    "bond loop missing": {
        "fields": {"bond_loop_present": False},
        "expected_reasons": ("chem_comp_bond_loop_missing",),
    },
    "charge invalid": {
        "fields": {"charge_valid": False},
        "expected_reasons": ("chem_comp_atom_charge_missing_or_invalid",),
    },
    "all-hydrogen component": {
        "fields": {"parent_heavy_atom_count": 0},
        "expected_reasons": ("parent_heavy_atom_table_empty",),
    },
    "unsupported element": {
        "fields": {"unsupported_element_count": 1},
        "expected_reasons": ("unsupported_element",),
    },
    "unsupported bond order": {
        "fields": {"unsupported_bond_order_count": 1},
        "expected_reasons": ("unsupported_ccd_bond_order",),
    },
    "duplicate parent atom or edge": {
        "fields": {"duplicate_parent_atom_or_edge_count": 1},
        "expected_reasons": ("duplicate_parent_atom_or_edge",),
    },
    "parent graph disconnected": {
        "fields": {"parent_component_count": 2},
        "expected_reasons": ("parent_graph_disconnected",),
    },
    "partial materialization attempted": {
        "fields": {"partial_materialization_attempted": True},
        "expected_reasons": ("partial_materialization_attempted",),
    },
    "execution boundary crossed": {
        "fields": {"execution_boundary_crossed": True},
        "expected_reasons": ("execution_boundary_crossed",),
    },
}


def _git(
    repo_root: Path,
    *arguments: str,
    check: bool = True,
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
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip())
    return result


def base_bytes(repo_root: Path, path: Path) -> bytes:
    payload = _git(
        repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}"
    ).stdout
    expected = FROZEN_BASE_SHA256[path]
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"frozen_BASE_SHA256_mismatch:{path.as_posix()}")
    return payload


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8", "strict"))))


def _csv_bytes(
    columns: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({
            column: (
                "true" if row.get(column) is True
                else "false" if row.get(column) is False
                else row.get(column, "")
            )
            for column in columns
        })
    return stream.getvalue().encode("utf-8")


def _exact_bool(value: str) -> bool:
    if value not in ("True", "False", "true", "false"):
        raise ValueError("boolean_field_invalid")
    return value.lower() == "true"


def load_expected_audit(repo_root: Path) -> dict[str, dict[str, str]]:
    rows = _csv_rows(base_bytes(repo_root, CCD_AUDIT))
    if len(rows) != 9:
        raise ValueError("BASE_audit_not_Exact9")
    by_component = {row["het_id"]: row for row in rows}
    if (
        len(by_component) != 9
        or tuple(row["het_id"] for row in rows) != EXACT9_COMPONENTS
        or set(by_component) != set(EXACT9_COMPONENTS)
    ):
        raise ValueError("BASE_audit_component_closed_set_mismatch")
    shas: list[str] = []
    for component, expected_path in zip(EXACT9_COMPONENTS, EXACT9_PATHS):
        row = by_component[component]
        expected_sha = row["sha256"]
        if row["ccd_raw_path"] != expected_path.as_posix():
            raise ValueError("BASE_audit_path_identity_mismatch")
        if not all(
            _exact_bool(row[field])
            for field in ("file_exists", "integrity_passed", "ccd_audit_passed")
        ):
            raise ValueError("BASE_audit_integrity_mismatch")
        if row["blocking_reasons"]:
            raise ValueError("BASE_audit_has_blocking_reasons")
        if re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
            raise ValueError("BASE_audit_SHA_grammar_invalid")
        shas.append(expected_sha)
    if len(set(shas)) != 9:
        raise ValueError("BASE_audit_SHA_identity_not_unique")
    return by_component


def _component_identity(text: str, expected: str) -> tuple[str, str]:
    data_ids = [
        stripped[5:].strip()
        for line in text.splitlines()
        if (stripped := line.strip()).startswith("data_")
    ]
    chem_comp_ids: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("_chem_comp.id"):
            continue
        tokens = shlex.split(stripped, comments=False, posix=True)
        if len(tokens) == 2 and tokens[0] == "_chem_comp.id":
            chem_comp_ids.append(tokens[1])
    if len(data_ids) != 1 or len(chem_comp_ids) != 1:
        raise ValueError("ccd_component_identity_missing")
    if data_ids[0] != expected or chem_comp_ids[0] != expected:
        raise ValueError("ccd_component_identity_mismatch")
    return data_ids[0], chem_comp_ids[0]


def _component_count(
    vertices: set[str],
    edges: set[tuple[str, str]],
) -> int:
    if not vertices:
        return 0
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


def canonical_parent_graph_sha256(
    atoms: Iterable[ParentAtom],
    bonds: Iterable[tuple[str, str, str]],
) -> str:
    payload = {
        "atoms": [
            [
                atom.atom_id,
                canonicalize_element_symbol_v1(atom.type_symbol),
                atom.formal_charge,
            ]
            for atom in sorted(atoms, key=lambda item: item.atom_id)
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


def normalize_parent_bond_order(
    source_value_order: str,
    source_aromatic_flag: str,
) -> str:
    """Normalize CCD alternating aromatic edges through the predecessor helper."""

    if type(source_value_order) is not str or type(source_aromatic_flag) is not str:
        raise ValueError("bond_order_argument_type_invalid")
    order = source_value_order.strip().upper()
    flag = source_aromatic_flag.strip().upper()
    if flag == "Y":
        if order not in ("SING", "DOUB", "AROM"):
            raise ValueError("aromatic_flag_order_conflict")
        return normalize_bond_order("AROM", "Y")
    return normalize_bond_order(order, flag)


def _validate_parent_graph(
    atoms: tuple[ParentAtom, ...],
    bonds: tuple[ParentBond, ...],
) -> tuple[tuple[tuple[str, str, str, str, str], ...], int, str]:
    if not atoms:
        raise ValueError("parent_heavy_atom_table_empty")
    atom_ids = [atom.atom_id for atom in atoms]
    if len(atom_ids) != len(set(atom_ids)):
        raise ValueError("duplicate_ccd_atom_id")
    if [atom.row_index_0based for atom in atoms] != list(range(len(atoms))):
        raise ValueError("parent_heavy_atom_row_indices_not_contiguous")
    for atom in atoms:
        if type(atom.formal_charge) is not int:
            raise ValueError("parent_formal_charge_type_invalid")
        element = canonicalize_element_symbol_v1(atom.type_symbol)
        if element in EXPLICIT_HYDROGEN_TYPE_SYMBOLS:
            raise ValueError("explicit_hydrogen_in_parent_graph")
        if element not in SUPPORTED_ELEMENTS:
            raise ValueError("unsupported_element")

    normalized: list[tuple[str, str, str, str, str]] = []
    edges: set[tuple[str, str]] = set()
    edge_orders: set[tuple[str, str, str]] = set()
    atom_id_set = set(atom_ids)
    for bond in bonds:
        left, right = bond.atom_id_1, bond.atom_id_2
        if left not in atom_id_set or right not in atom_id_set:
            raise ValueError("chem_comp_bond_endpoint_not_in_atom_loop")
        if left == right:
            raise ValueError("parent_bond_self_loop")
        order = normalize_parent_bond_order(
            bond.source_value_order, bond.source_aromatic_flag
        )
        canonical_left, canonical_right = min(left, right), max(left, right)
        edge = (canonical_left, canonical_right)
        edge_order = (*edge, order)
        if edge in edges or edge_order in edge_orders:
            raise ValueError("duplicate_parent_bond")
        edges.add(edge)
        edge_orders.add(edge_order)
        normalized.append((
            canonical_left, canonical_right, bond.source_value_order,
            bond.source_aromatic_flag, order,
        ))
    component_count = _component_count(atom_id_set, edges)
    if component_count != 1:
        raise ValueError("parent_graph_disconnected")
    graph_sha = canonical_parent_graph_sha256(atoms, edge_orders)
    if (
        graph_sha
        != canonical_parent_graph_sha256(tuple(reversed(atoms)), edge_orders)
        or graph_sha
        != canonical_parent_graph_sha256(
            atoms, tuple(reversed(tuple(edge_orders)))
        )
    ):
        raise ValueError("parent_graph_SHA_nondeterministic")
    return tuple(sorted(normalized)), component_count, graph_sha


def _path_git_flags(repo_root: Path, relative_path: Path) -> tuple[bool, bool, bool]:
    ignored = _git(
        repo_root, "check-ignore", "-q", "--", relative_path.as_posix(),
        check=False,
    ).returncode == 0
    tracked = _git(
        repo_root, "cat-file", "-e",
        f"{BASE_COMMIT}:{relative_path.as_posix()}", check=False,
    ).returncode == 0
    staged = bool(_git(
        repo_root, "diff", "--cached", "--name-only", "--",
        relative_path.as_posix(),
    ).stdout)
    return ignored, tracked, staged


def _disposition(reasons: Sequence[str]) -> str:
    priority = (
        ("payload_missing", "blocked_missing"),
        ("payload_not_regular", "blocked_not_regular"),
        ("payload_symlink", "blocked_symlink"),
        ("payload_empty", "blocked_empty"),
        ("payload_oversize", "blocked_oversize"),
        ("payload_mode_invalid", "blocked_mode"),
        ("payload_not_ignored", "blocked_not_ignored"),
        ("payload_raw_tracked", "blocked_raw_tracked"),
        ("payload_raw_staged", "blocked_raw_staged"),
        ("payload_sha_mismatch", "blocked_sha_mismatch"),
        ("base_audit_mismatch", "blocked_audit_mismatch"),
        ("payload_decode_failed", "blocked_decode"),
        ("ccd_component_identity_missing", "blocked_component_identity"),
        ("ccd_component_identity_mismatch", "blocked_component_identity"),
    )
    for reason, disposition in priority:
        if reason in reasons:
            return disposition
    parse_reasons = {
        "chem_comp_atom_loop_missing", "chem_comp_bond_loop_missing",
        "chem_comp_atom_charge_missing_or_invalid",
        "parent_heavy_atom_table_empty",
    }
    if parse_reasons & set(reasons):
        return "blocked_parse"
    if reasons:
        return "blocked_graph_validation"
    return "admitted_sha_attested_local_ccd"


def _admit_component(
    repo_root: Path,
    component: str,
    audit_row: Mapping[str, str],
) -> ComponentAuthority:
    relative_path = CCD_ROOT / f"{component}.cif"
    absolute_path = repo_root / relative_path
    expected_sha = audit_row["sha256"]
    reasons: list[str] = []
    values: dict[str, Any] = {
        "ligand_comp_id": component,
        "source_relative_path": relative_path.as_posix(),
        "expected_sha256": expected_sha,
        "observed_sha256": "",
        "file_exists": False,
        "regular_file": False,
        "symlink": False,
        "file_size_bytes": 0,
        "mode": "",
        "ignored_by_project_gitignore": False,
        "BASE_tracked": False,
        "staged": False,
        "BASE_audit_integrity_passed": False,
        "payload_sha_matches": False,
        "decode_passed": False,
        "component_identity_passed": False,
        "parse_passed": False,
        "source_atom_row_count": 0,
        "explicit_hydrogen_atom_count": 0,
        "parent_heavy_atom_count": 0,
        "source_bond_row_count": 0,
        "hydrogen_involving_bond_count": 0,
        "parent_heavy_bond_count": 0,
        "unsupported_bond_order_count": 0,
        "parent_component_count": 0,
        "parent_graph_sha256": "",
    }
    try:
        file_stat = os.lstat(absolute_path)
    except FileNotFoundError:
        reasons.append("payload_missing")
        file_stat = None
    if file_stat is not None:
        values["file_exists"] = True
        values["symlink"] = stat.S_ISLNK(file_stat.st_mode)
        values["regular_file"] = stat.S_ISREG(file_stat.st_mode)
        values["file_size_bytes"] = file_stat.st_size
        values["mode"] = f"{stat.S_IMODE(file_stat.st_mode):04o}"
        if not values["regular_file"]:
            reasons.append("payload_not_regular")
        if values["symlink"]:
            reasons.append("payload_symlink")
        if file_stat.st_size == 0:
            reasons.append("payload_empty")
        if file_stat.st_size >= MAX_PAYLOAD_SIZE_BYTES:
            reasons.append("payload_oversize")
        if stat.S_IMODE(file_stat.st_mode) != 0o644:
            reasons.append("payload_mode_invalid")

    ignored, tracked, staged = _path_git_flags(repo_root, relative_path)
    values["ignored_by_project_gitignore"] = ignored
    values["BASE_tracked"] = tracked
    values["staged"] = staged
    if not ignored:
        reasons.append("payload_not_ignored")
    if tracked:
        reasons.append("payload_raw_tracked")
    if staged:
        reasons.append("payload_raw_staged")

    audit_integrity = (
        audit_row.get("het_id") == component
        and audit_row.get("ccd_raw_path") == relative_path.as_posix()
        and audit_row.get("sha256") == expected_sha
        and _exact_bool(audit_row.get("file_exists", ""))
        and _exact_bool(audit_row.get("integrity_passed", ""))
        and _exact_bool(audit_row.get("ccd_audit_passed", ""))
        and not audit_row.get("blocking_reasons")
    )
    values["BASE_audit_integrity_passed"] = audit_integrity
    if not audit_integrity:
        reasons.append("base_audit_mismatch")

    pre_read_reasons = {
        "payload_missing", "payload_not_regular", "payload_symlink",
        "payload_empty", "payload_oversize", "payload_mode_invalid",
        "payload_not_ignored", "payload_raw_tracked", "payload_raw_staged",
        "base_audit_mismatch",
    }
    payload = b""
    if not pre_read_reasons.intersection(reasons):
        payload = absolute_path.read_bytes()
        observed_sha = hashlib.sha256(payload).hexdigest()
        values["observed_sha256"] = observed_sha
        values["payload_sha_matches"] = observed_sha == expected_sha
        if observed_sha != expected_sha:
            reasons.append("payload_sha_mismatch")

    text = ""
    if not reasons:
        try:
            text = payload.decode("utf-8", "strict")
            values["decode_passed"] = True
        except UnicodeDecodeError:
            reasons.append("payload_decode_failed")
    if not reasons:
        try:
            _component_identity(text, component)
            values["component_identity_passed"] = True
        except ValueError as exc:
            reasons.append(str(exc))

    atoms: tuple[ParentAtom, ...] = ()
    bonds: tuple[ParentBond, ...] = ()
    normalized: tuple[tuple[str, str, str, str, str], ...] = ()
    graph_sha = ""
    component_count = 0
    if not reasons:
        try:
            atoms, bonds, stats_value = parse_ccd_component_with_stats(text)
            values.update({
                "parse_passed": True,
                "source_atom_row_count": stats_value.source_atom_row_count,
                "explicit_hydrogen_atom_count":
                    stats_value.explicit_hydrogen_atom_count,
                "parent_heavy_atom_count": stats_value.heavy_atom_count,
                "source_bond_row_count": stats_value.source_bond_row_count,
                "hydrogen_involving_bond_count":
                    stats_value.hydrogen_involving_bond_count,
                "parent_heavy_bond_count": stats_value.heavy_heavy_bond_count,
            })
            normalized, component_count, graph_sha = _validate_parent_graph(
                atoms, bonds
            )
            values["parent_component_count"] = component_count
            values["parent_graph_sha256"] = graph_sha
        except ValueError as exc:
            reason = str(exc)
            if reason in (
                "unsupported_ccd_bond_order",
                "unsupported_ccd_aromatic_flag",
                "aromatic_flag_order_conflict",
            ):
                values["unsupported_bond_order_count"] = 1
            reasons.append(reason)

    disposition = _disposition(reasons)
    values["admission_disposition"] = disposition
    values["blocking_reasons"] = ";".join(dict.fromkeys(reasons))
    values["verified"] = (
        not reasons
        and disposition == "admitted_sha_attested_local_ccd"
        and values["payload_sha_matches"]
        and values["component_identity_passed"]
        and values["parse_passed"]
        and component_count == 1
        and bool(graph_sha)
    )
    return ComponentAuthority(
        ligand_comp_id=component,
        source_path=relative_path,
        expected_sha256=expected_sha,
        observed_sha256=values["observed_sha256"],
        atoms=atoms,
        bonds=bonds,
        normalized_bonds=normalized,
        source_atom_row_count=values["source_atom_row_count"],
        explicit_hydrogen_atom_count=values["explicit_hydrogen_atom_count"],
        source_bond_row_count=values["source_bond_row_count"],
        hydrogen_involving_bond_count=values[
            "hydrogen_involving_bond_count"
        ],
        parent_component_count=component_count,
        graph_sha256=graph_sha,
        admission_row=values,
    )


def evaluate_failure_scenario(scenario: FailureScenario) -> ScenarioObservation:
    if type(scenario) is not FailureScenario:
        raise TypeError("scenario must be an exact FailureScenario")
    for field in dataclasses.fields(FailureScenario):
        value = getattr(scenario, field.name)
        if field.type == "bool" and type(value) is not bool:
            raise TypeError(f"{field.name} must be an exact bool")
        if field.type == "int" and type(value) is not int:
            raise TypeError(f"{field.name} must be an exact int")
    reasons: list[str] = []
    checks = (
        (not scenario.payload_exists, "payload_missing"),
        (not scenario.regular_file, "payload_not_regular"),
        (scenario.symlink, "payload_symlink"),
        (scenario.file_size_bytes == 0, "payload_empty"),
        (
            scenario.file_size_bytes >= MAX_PAYLOAD_SIZE_BYTES,
            "payload_oversize",
        ),
        (scenario.mode != 0o644, "payload_mode_invalid"),
        (
            not scenario.ignored_by_project_gitignore,
            "payload_not_ignored",
        ),
        (scenario.raw_tracked, "payload_raw_tracked"),
        (scenario.raw_staged, "payload_raw_staged"),
        (not scenario.payload_sha_matches, "payload_sha_mismatch"),
        (not scenario.base_audit_sha_matches, "base_audit_sha_mismatch"),
        (not scenario.decode_passed, "payload_decode_failed"),
        (
            not scenario.component_identity_present,
            "ccd_component_identity_missing",
        ),
        (
            not scenario.component_identity_matches,
            "ccd_component_identity_mismatch",
        ),
        (not scenario.atom_loop_present, "chem_comp_atom_loop_missing"),
        (not scenario.bond_loop_present, "chem_comp_bond_loop_missing"),
        (
            not scenario.charge_valid,
            "chem_comp_atom_charge_missing_or_invalid",
        ),
        (
            scenario.parent_heavy_atom_count == 0,
            "parent_heavy_atom_table_empty",
        ),
        (scenario.unsupported_element_count > 0, "unsupported_element"),
        (
            scenario.unsupported_bond_order_count > 0,
            "unsupported_ccd_bond_order",
        ),
        (
            scenario.duplicate_parent_atom_or_edge_count > 0,
            "duplicate_parent_atom_or_edge",
        ),
        (scenario.parent_component_count != 1, "parent_graph_disconnected"),
        (
            scenario.partial_materialization_attempted,
            "partial_materialization_attempted",
        ),
        (scenario.execution_boundary_crossed, "execution_boundary_crossed"),
    )
    reasons.extend(reason for condition, reason in checks if condition)
    closed = bool(reasons)
    return ScenarioObservation(
        reasons=tuple(reasons),
        fails_closed=closed,
        ready_for_current11_observed_projection=False,
        ready_for_reaction_family_rule_design=False,
        ready_for_role_proposal_generation=False,
        ready_for_mask_materialization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
    )


def mutation_signature(fields: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_failure_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    signatures: set[str] = set()
    for case, specification in FAILURE_MUTATIONS.items():
        fields = specification["fields"]
        expected = specification["expected_reasons"]
        for name, value in fields.items():
            baseline = getattr(BASELINE_SCENARIO, name)
            if type(value) is not type(baseline) or value == baseline:
                raise ValueError(f"invalid_failure_mutation:{case}:{name}")
        scenario = dataclasses.replace(BASELINE_SCENARIO, **fields)
        observation = evaluate_failure_scenario(scenario)
        signature = mutation_signature(fields)
        if signature in signatures:
            raise ValueError("duplicate_failure_mutation_signature")
        signatures.add(signature)
        expected_verified = set(expected) <= set(observation.reasons)
        verified = (
            expected_verified
            and observation.fails_closed
            and not observation.ready_for_current11_observed_projection
            and not observation.ready_for_reaction_family_rule_design
            and not observation.ready_for_role_proposal_generation
            and not observation.ready_for_mask_materialization
            and not observation.ready_for_model_integration
            and not observation.ready_for_training
        )
        rows.append({
            "failure_case": case,
            "mutation_signature": signature,
            "mutated_fields": json.dumps(
                fields, sort_keys=True, separators=(",", ":")
            ),
            "expected_reasons": ";".join(expected),
            "observed_reasons": ";".join(observation.reasons),
            "expected_reasons_verified": expected_verified,
            "fails_closed": observation.fails_closed,
            "ready_for_current11_observed_projection":
                observation.ready_for_current11_observed_projection,
            "ready_for_reaction_family_rule_design":
                observation.ready_for_reaction_family_rule_design,
            "ready_for_role_proposal_generation":
                observation.ready_for_role_proposal_generation,
            "ready_for_mask_materialization":
                observation.ready_for_mask_materialization,
            "ready_for_model_integration":
                observation.ready_for_model_integration,
            "ready_for_training": observation.ready_for_training,
            "verified": verified,
        })
    return rows


def _load_current11(
    repo_root: Path,
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    index_rows = _csv_rows(base_bytes(repo_root, FINAL_INDEX))
    graph_rows = _csv_rows(base_bytes(repo_root, GRAPH_EVIDENCE))
    if len(index_rows) != 11 or len(graph_rows) != 11:
        raise ValueError("Current11_row_count_mismatch")
    graph_by_sample = {row["sample_index_row_id"]: row for row in graph_rows}
    if len(graph_by_sample) != 11:
        raise ValueError("Current11_graph_sample_identity_not_unique")
    for row in index_rows:
        support = graph_by_sample.get(row["sample_index_row_id"])
        if (
            support is None
            or support["pdb_id"] != row["pdb_id"]
            or support["ligand_comp_id"] != row["ligand_comp_id"]
        ):
            raise ValueError("Current11_component_assignment_mismatch")
    if (
        tuple(dict.fromkeys(row["ligand_comp_id"] for row in index_rows))
        != EXACT9_COMPONENTS
        or set(row["ligand_comp_id"] for row in index_rows)
        != set(EXACT9_COMPONENTS)
    ):
        raise ValueError("Current11_component_closed_set_mismatch")
    return index_rows, graph_by_sample


def _authority_rows(
    components: Sequence[ComponentAuthority],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    atom_rows: list[dict[str, Any]] = []
    bond_rows: list[dict[str, Any]] = []
    for component in components:
        for atom in component.atoms:
            atom_rows.append({
                "ligand_comp_id": component.ligand_comp_id,
                "ccd_source_relative_path": component.source_path.as_posix(),
                "ccd_source_sha256": component.observed_sha256,
                "ccd_parser_contract_version": PARSER_CONTRACT_VERSION,
                "ccd_atom_id": atom.atom_id,
                "ccd_type_symbol": canonicalize_element_symbol_v1(
                    atom.type_symbol
                ),
                "ccd_formal_charge": atom.formal_charge,
                "ccd_heavy_atom_row_index_0based": atom.row_index_0based,
                "component_parent_graph_sha256": component.graph_sha256,
                "authority_class": AUTHORITY_CLASS,
                "verified": True,
            })
        for left, right, value_order, aromatic_flag, normalized in (
            component.normalized_bonds
        ):
            bond_rows.append({
                "ligand_comp_id": component.ligand_comp_id,
                "ccd_source_relative_path": component.source_path.as_posix(),
                "ccd_source_sha256": component.observed_sha256,
                "parent_ccd_atom_id_1": left,
                "parent_ccd_atom_id_2": right,
                "source_value_order": value_order,
                "source_aromatic_flag": aromatic_flag,
                "normalized_bond_order": normalized,
                "component_parent_graph_sha256": component.graph_sha256,
                "authority_class": AUTHORITY_CLASS,
                "verified": True,
            })
    return atom_rows, bond_rows


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    if _git(repo_root, "rev-parse", f"{BASE_COMMIT}:.gitignore").stdout.decode().strip() != GITIGNORE_BLOB:
        raise ValueError("BASE_gitignore_blob_mismatch")
    for path in FROZEN_BASE_SHA256:
        base_bytes(repo_root, path)
    audit = load_expected_audit(repo_root)
    components = tuple(
        _admit_component(repo_root, component, audit[component])
        for component in EXACT9_COMPONENTS
    )
    phase_a_passed = (
        len(components) == 9
        and all(component.admission_row["verified"] for component in components)
    )
    component_by_id = {
        component.ligand_comp_id: component for component in components
    }

    index_rows, graph_by_sample = _load_current11(repo_root)
    readiness: list[dict[str, Any]] = []
    phase_b_passed = phase_a_passed
    supporting_total = 0
    derived_total = 0
    for index_row in index_rows:
        component_id = index_row["ligand_comp_id"]
        component = component_by_id[component_id]
        support = graph_by_sample[index_row["sample_index_row_id"]]
        supporting_count = int(support["parent_ccd_heavy_atom_count"])
        derived_count = len(component.atoms)
        count_matches = supporting_count == derived_count
        supporting_total += supporting_count
        derived_total += derived_count
        if not (
            component.admission_row["verified"]
            and count_matches
            and component.graph_sha256
        ):
            phase_b_passed = False
        readiness.append({
            "sample_index_row_id": index_row["sample_index_row_id"],
            "pdb_id": index_row["pdb_id"],
            "ligand_comp_id": component_id,
            "local_ccd_admitted": component.admission_row["verified"],
            "component_parent_atom_authority_available": False,
            "component_parent_bond_order_authority_available": False,
            "component_parent_graph_valid": False,
            "component_parent_graph_sha256": "",
            "supporting_parent_heavy_atom_count": supporting_count,
            "derived_parent_heavy_atom_count": derived_count,
            "parent_heavy_atom_count_matches": count_matches,
            "observed_atom_projection_exact": False,
            "observed_projected_graph_available": False,
            "reaction_family_label_available": False,
            "approved_warhead_rule_available": False,
            "role_proposal_generation_ready": False,
            "minimal_seed_proposal_generation_ready": False,
            "human_gold_review_completed": False,
            "ready_for_mask_materialization": False,
            "ready_for_tensorization": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
            "blocking_reasons": "",
            "verified": False,
        })
    if supporting_total != 324 or derived_total != supporting_total:
        phase_b_passed = False
    transaction_passed = phase_a_passed and phase_b_passed
    atom_rows: list[dict[str, Any]] = []
    bond_rows: list[dict[str, Any]] = []
    if transaction_passed:
        atom_rows, bond_rows = _authority_rows(components)

    persistent_blockers = (
        "current11_observed_atom_projection_missing",
        "current11_observed_projected_graph_missing",
        "reaction_family_labels_missing",
        "approved_warhead_rules_missing",
        "role_proposals_missing",
        "minimal_seed_proposals_missing",
        "current11_human_gold_review_missing",
    )
    for row in readiness:
        component = component_by_id[row["ligand_comp_id"]]
        if transaction_passed:
            row.update({
                "component_parent_atom_authority_available": True,
                "component_parent_bond_order_authority_available": True,
                "component_parent_graph_valid": True,
                "component_parent_graph_sha256": component.graph_sha256,
            })
            blockers = persistent_blockers
        else:
            blockers = (
                "exact9_parent_authority_transaction_blocked",
                *persistent_blockers,
            )
        row["blocking_reasons"] = ";".join(blockers)
        row["verified"] = (
            row["local_ccd_admitted"] is transaction_passed
            and row["component_parent_atom_authority_available"]
                is transaction_passed
            and row["component_parent_bond_order_authority_available"]
                is transaction_passed
            and row["component_parent_graph_valid"] is transaction_passed
            and row["parent_heavy_atom_count_matches"] is transaction_passed
            and not any(
                row[field]
                for field in (
                    "observed_atom_projection_exact",
                    "observed_projected_graph_available",
                    "reaction_family_label_available",
                    "approved_warhead_rule_available",
                    "role_proposal_generation_ready",
                    "minimal_seed_proposal_generation_ready",
                    "human_gold_review_completed",
                    "ready_for_mask_materialization",
                    "ready_for_tensorization",
                    "ready_for_model_integration",
                    "ready_for_training",
                )
            )
        )

    failures = build_failure_matrix()
    admission_rows = [component.admission_row for component in components]
    payloads = {
        ADMISSION_FILE: _csv_bytes(ADMISSION_COLUMNS, admission_rows),
        ATOM_FILE: _csv_bytes(ATOM_COLUMNS, atom_rows),
        BOND_FILE: _csv_bytes(BOND_COLUMNS, bond_rows),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, readiness),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, failures),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "predecessor_source_sha256": FROZEN_BASE_SHA256[PREDECESSOR_SOURCE],
        "predecessor_manifest_sha256": FROZEN_BASE_SHA256[PREDECESSOR_MANIFEST],
        "gitignore_blob": GITIGNORE_BLOB,
        "exact9_components": list(EXACT9_COMPONENTS),
        "exact9_component_count": 9,
        "exact9_local_ccd_admitted_count": sum(
            row["verified"] for row in admission_rows
        ),
        "exact9_parent_atom_authority_available_count":
            9 if transaction_passed else 0,
        "exact9_parent_bond_authority_available_count":
            9 if transaction_passed else 0,
        "exact9_parent_graph_valid_count": 9 if transaction_passed else 0,
        "unique_component_parent_atom_row_count": len(atom_rows),
        "unique_component_parent_bond_row_count": len(bond_rows),
        "bond_order_distribution": {
            order: sum(
                row["normalized_bond_order"] == order for row in bond_rows
            )
            for order in NORMALIZED_BOND_ORDERS
        },
        "unsupported_bond_order_count": sum(
            int(row["unsupported_bond_order_count"]) for row in admission_rows
        ),
        "current11_row_count": len(readiness),
        "current11_parent_component_graph_coverage_count": (
            11 if transaction_passed else 0
        ),
        "current11_parent_component_bond_order_coverage_count": (
            11 if transaction_passed else 0
        ),
        "current11_sample_expanded_parent_atom_occurrence_count":
            derived_total,
        "supporting_parent_atom_occurrence_expected_count": 324,
        "supporting_parent_atom_occurrence_count_matches": (
            supporting_total == derived_total == 324
        ),
        "current11_observed_atom_projection_exact_count": 0,
        "current11_observed_projected_graph_available_count": 0,
        "reaction_family_label_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "role_proposal_generation_ready_count": 0,
        "minimal_seed_proposal_generation_ready_count": 0,
        "human_gold_review_completed_count": 0,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "failure_matrix_row_count": len(failures),
        "failure_mutation_signatures_unique": (
            len({row["mutation_signature"] for row in failures})
            == len(failures)
        ),
        "failure_expected_reasons_verified": all(
            row["expected_reasons_verified"] for row in failures
        ),
        "transaction_phase_a_passed": phase_a_passed,
        "transaction_phase_b_passed": phase_b_passed,
        "transaction_authority_materialized": transaction_passed,
        "raw_payload_read": any(row["observed_sha256"] for row in admission_rows),
        "raw_payload_modified": False,
        "raw_payload_tracked": False,
        "raw_payload_staged": False,
        "network_used": False,
        "download_performed": False,
        "role_or_seed_materialized": False,
        "mask_materialized": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_used": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "outcome": (
            "exact9_parent_component_graph_authority_materialized"
            if transaction_passed
            else "blocked_exact9_parent_component_graph_authority"
        ),
        "recommended_next_step": (
            "materialize_covapie_current11_observed_to_parent_atom_"
            "projection_authority_v1"
            if transaction_passed
            else "resolve_covapie_exact9_audited_ccd_parent_graph_"
            "authority_blockers_v1"
        ),
        "remaining_readiness_blockers": list(persistent_blockers),
        "evidence_sha256": {
            name: hashlib.sha256(payload).hexdigest()
            for name, payload in payloads.items()
        },
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return payloads


def materialize(repo_root: Path) -> dict[str, bytes]:
    payloads = build_evidence_payloads(repo_root)
    target = repo_root / OUTPUT_ROOT
    target.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_FILES:
        (target / name).write_bytes(payloads[name])
    return payloads


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize(repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

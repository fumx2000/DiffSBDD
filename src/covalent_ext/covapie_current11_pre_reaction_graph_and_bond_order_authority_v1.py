"""Resolve Current11 pre-reaction graph authority without guessing atom names."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import re
import shlex
import subprocess
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BASE_COMMIT = "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1"
BASE_PARENT = "335a0320e8bd8ee125e51f927e6cd26d0c05707e"
BASE_TREE = "509d5050530741e04caa1653bdb1e257f17345e3"
BASE_SUBJECT = "add CovaPIE ligand role and minimal seed annotation contract v1"
FORMAL_COMMIT_SUBJECT = "add CovaPIE current11 pre-reaction graph authority v1"
SCHEMA_VERSION = "covapie_current11_pre_reaction_graph_and_bond_order_authority_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION

SOURCE_INVENTORY_FILE = "covapie_pre_reaction_graph_source_inventory.csv"
PARENT_ATOM_FILE = "covapie_current11_parent_atom_authority.csv"
BOND_FILE = "covapie_current11_parent_and_projected_bond_authority.csv"
READINESS_FILE = "covapie_current11_graph_authority_readiness_matrix.csv"
FAILURE_FILE = "covapie_pre_reaction_graph_authority_failure_matrix.csv"
MANIFEST_FILE = "covapie_current11_pre_reaction_graph_and_bond_order_authority_manifest.json"
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    PARENT_ATOM_FILE,
    BOND_FILE,
    READINESS_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)

ROLE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
ROLE_SUMMARY = Path(
    "docs/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1_summary.md"
)
ROLE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1"
)
ROLE_MANIFEST = ROLE_ROOT / (
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_manifest.json"
)
ROLE_READINESS = ROLE_ROOT / "covapie_current11_role_annotation_input_readiness_matrix.csv"
GRAPH_EVIDENCE = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv"
)
FINAL_INDEX = Path(
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/"
    "final_dataset_index.csv"
)
ATOM_MAPPING = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
HEAVY_DISPOSITION = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_heavy_atom_disposition_and_index_projection_matrix.csv"
)
SAMPLE_PROJECTION = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_sample_heavy_atom_projection_validation_matrix.csv"
)
TOPOLOGY_REPORT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_"
    "design_gate_v0/ligand_topology_restoration_policy_design_gate_report.csv"
)
TOPOLOGY_SUMMARY = Path(
    "docs/real_covalent_confirmed_candidate_ligand_topology_restoration_"
    "policy_design_gate_v0_summary.md"
)
CCD_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ccd_acquisition_integrity_audit.csv"
)
RCSB_CURRENT_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_targeted_annotation_acquisition_smoke_v0/"
    "covapie_cys_sg_rcsb_ccd_extraction_audit.csv"
)
RCSB_JUG_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0/"
    "covapie_cys_sg_next_batch_rcsb_ccd_extraction_audit.csv"
)
STEP8_ATOMS = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_"
    "smoke_v0/step8_readonly_exported_ligand_atom_topology_table.csv"
)
STEP8_BONDS = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_"
    "smoke_v0/step8_readonly_exported_ligand_bond_topology_table.csv"
)

FROZEN_SHA256 = {
    ROLE_SOURCE: "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    ROLE_SUMMARY: "a3cf85a476a97e564e192963d23476f14c79af428046677a5c9a5b8a9ca1453c",
    ROLE_MANIFEST: "cf79865f91ef140b6c69010ce2e56c2ff24937a5aa7fa3eac0f8c53bc907764a",
    ROLE_READINESS: "6def11ca3c1ec974479c3fa96d3f2c985b994eed86d6132008236fb18bca3d4b",
    GRAPH_EVIDENCE: "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
    FINAL_INDEX: "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    ATOM_MAPPING: "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    HEAVY_DISPOSITION: "b53f438edffab32f78d07df839b8c8437ec4223e31bd8a8885deedf32497b4be",
    SAMPLE_PROJECTION: "63f1df49d9a6f4e0efbee6c8bb474deabaedea9cef91f27d2cf49f7caeee6f96",
    TOPOLOGY_REPORT: "e10301238d5da3e81820a091381c3d105a4544dea1c481bb1cfda134efc7138f",
    TOPOLOGY_SUMMARY: "e061c748fe7553c0545181225795d1d052922adff327e5e78a323ba2a168f7bd",
    CCD_AUDIT: "79cf1ef3ccb3431b804fbf7af8bb12eb654615d332df002c70d8b0fa011ca848",
    RCSB_CURRENT_AUDIT: "9a6a8b3e0f19a67b91bc6cfb16374a4914414e1f766bea860deb0e648a41dc06",
    RCSB_JUG_AUDIT: "6c923d92b2a0ddc305c698dd6a1378e24c624637cffa02f6c1ce43424a48d537",
    STEP8_ATOMS: "07c9477f412b5a31c0525faba12cf369a00dc682abdfdabd995bb9321e3a4a6e",
    STEP8_BONDS: "c6bf803e2a98eb3f18f701791a56085c54bf16cff875b148b5bd97e15f942841",
}

CURRENT_COMPONENTS = ("JUG", "E64", "ZYA", "PCM", "INP", "INA", "IN6", "IN3", "UFP")
CCD_ROOT = Path("data/raw/covalent_sources/ccd/independence_evidence_batch_000001")
NORMALIZED_BOND_ORDERS = ("single", "double", "triple", "aromatic")
SOURCE_ORDER_MAP = {"SING": "single", "DOUB": "double", "TRIP": "triple", "AROM": "aromatic"}
EXPLICIT_HYDROGEN_TYPE_SYMBOLS = ("H", "D", "T")
SUPPORTED_ELEMENTS = {
    "B", "C", "N", "O", "F", "P", "S", "CL", "BR", "I", "SI", "SE"
}

SOURCE_COLUMNS = (
    "source_path", "source_sha256", "source_kind", "BASE_tracked", "atom_named",
    "bond_order_present", "current11_component_coverage", "authority_class",
    "blocking_reason", "verified",
)
ATOM_COLUMNS = (
    "sample_index_row_id", "ligand_comp_id", "ccd_atom_id", "ccd_type_symbol",
    "ccd_formal_charge", "ccd_atom_row_index_0based",
    "retained_heavy_local_index_0based", "retained_heavy_local_index_valid",
    "source_full_atom_row_index", "observed_in_sample", "leaving_group_atom",
    "authority_source_path", "verified",
)
BOND_COLUMNS = (
    "sample_index_row_id", "ligand_comp_id", "parent_ccd_atom_id_1",
    "parent_ccd_atom_id_2", "source_value_order", "source_aromatic_flag",
    "normalized_bond_order", "retained_heavy_local_index_1",
    "retained_heavy_local_index_1_valid", "retained_heavy_local_index_2",
    "retained_heavy_local_index_2_valid", "projected_to_observed_graph",
    "projection_disposition", "authority_source_path", "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "descriptor_graph_support_present", "atom_named_graph_authority_present",
    "atom_named_parent_graph_available", "parent_bond_order_authority_available",
    "observed_atom_projection_exact", "leaving_group_projection_valid",
    "parent_graph_valid", "observed_graph_valid",
    "pre_reaction_connectivity_available", "pre_reaction_bond_order_available",
    "reaction_family_label_available", "approved_warhead_rule_available",
    "role_proposal_generation_ready", "minimal_seed_proposal_generation_ready",
    "human_gold_review_completed", "ready_for_mask_materialization",
    "ready_for_tensorization", "ready_for_model_integration", "ready_for_training",
    "blocking_reasons", "verified",
)
FAILURE_COLUMNS = (
    "failure_case", "mutation_signature", "mutated_fields", "expected_reasons",
    "observed_reasons", "expected_reasons_verified", "fails_closed",
    "ready_for_reaction_family_rule_design", "ready_for_role_proposal_generation",
    "ready_for_mask_materialization", "ready_for_model_integration",
    "ready_for_training", "verified",
)


@dataclass(frozen=True)
class ParentAtom:
    atom_id: str
    type_symbol: str
    formal_charge: int
    row_index_0based: int


@dataclass(frozen=True)
class ParentBond:
    atom_id_1: str
    atom_id_2: str
    source_value_order: str
    source_aromatic_flag: str


@dataclass(frozen=True)
class ObservedAtom:
    atom_name: str
    type_symbol: str
    source_full_atom_row_index: int
    retained_heavy_local_index_0based: int


@dataclass(frozen=True)
class CCDHeavyProjectionStats:
    source_atom_row_count: int
    explicit_hydrogen_atom_count: int
    heavy_atom_count: int
    source_bond_row_count: int
    hydrogen_involving_bond_count: int
    heavy_heavy_bond_count: int


@dataclass(frozen=True)
class GraphValidation:
    valid: bool
    reasons: tuple[str, ...]
    parent_graph_sha256: str
    observed_graph_sha256: str
    parent_component_count: int
    observed_component_count: int
    projected_atom_count: int
    projected_bond_count: int


@dataclass(frozen=True)
class AuthorityScenario:
    ccd_source_present: bool = True
    ccd_source_base_tracked: bool = True
    chem_comp_atom_loop_present: bool = True
    chem_comp_bond_loop_present: bool = True
    duplicate_ccd_atom_id_count: int = 0
    unsupported_element_count: int = 0
    duplicate_sample_atom_name_count: int = 0
    sample_atom_not_in_ccd_count: int = 0
    element_mismatch_count: int = 0
    reactive_atom_parent_match_count: int = 1
    reactive_atom_projection_match_count: int = 1
    unexplained_parent_missing_count: int = 0
    leaving_group_inconsistency_count: int = 0
    unexpected_observed_atom_count: int = 0
    absent_bond_endpoint_count: int = 0
    self_loop_bond_count: int = 0
    duplicate_undirected_bond_count: int = 0
    unsupported_bond_order_count: int = 0
    aromatic_order_conflict_count: int = 0
    parent_component_count: int = 1
    observed_component_count: int = 1
    atom_count_matches: bool = True
    projection_count_matches: bool = True
    atom_order_deterministic: bool = True
    bond_order_deterministic: bool = True
    graph_sha_matches: bool = True
    rdkit_validation_passed: bool = True
    execution_boundary_crossed: bool = False


@dataclass(frozen=True)
class ScenarioObservation:
    valid: bool
    reasons: tuple[str, ...]
    ready_for_reaction_family_rule_design: bool
    ready_for_role_proposal_generation: bool
    ready_for_mask_materialization: bool
    ready_for_model_integration: bool
    ready_for_training: bool


BASELINE_SCENARIO = AuthorityScenario()
BOOL_SCENARIO_FIELDS = (
    "ccd_source_present", "ccd_source_base_tracked", "chem_comp_atom_loop_present",
    "chem_comp_bond_loop_present", "atom_count_matches", "projection_count_matches",
    "atom_order_deterministic", "bond_order_deterministic", "graph_sha_matches",
    "rdkit_validation_passed", "execution_boundary_crossed",
)
COUNT_SCENARIO_FIELDS = tuple(
    field.name for field in dataclasses.fields(AuthorityScenario)
    if field.name not in BOOL_SCENARIO_FIELDS
)

FAILURE_MUTATIONS: dict[str, dict[str, Any]] = {
    "CCD source missing": {"fields": {"ccd_source_present": False}, "expected_reasons": ("ccd_source_missing",)},
    "CCD source not BASE tracked": {"fields": {"ccd_source_base_tracked": False}, "expected_reasons": ("ccd_source_not_BASE_tracked",)},
    "chem_comp_atom loop missing": {"fields": {"chem_comp_atom_loop_present": False}, "expected_reasons": ("chem_comp_atom_loop_missing",)},
    "chem_comp_bond loop missing": {"fields": {"chem_comp_bond_loop_present": False}, "expected_reasons": ("chem_comp_bond_loop_missing",)},
    "duplicate CCD atom_id": {"fields": {"duplicate_ccd_atom_id_count": 1}, "expected_reasons": ("duplicate_ccd_atom_id",)},
    "unsupported element": {"fields": {"unsupported_element_count": 1}, "expected_reasons": ("unsupported_element",)},
    "duplicate sample atom name": {"fields": {"duplicate_sample_atom_name_count": 1}, "expected_reasons": ("duplicate_sample_atom_name",)},
    "sample atom not in CCD": {"fields": {"sample_atom_not_in_ccd_count": 1}, "expected_reasons": ("sample_atom_not_in_ccd",)},
    "element mismatch": {"fields": {"element_mismatch_count": 1}, "expected_reasons": ("element_mismatch",)},
    "reactive atom absent from parent": {"fields": {"reactive_atom_parent_match_count": 0}, "expected_reasons": ("reactive_atom_absent_from_parent",)},
    "reactive atom absent from projection": {"fields": {"reactive_atom_projection_match_count": 0}, "expected_reasons": ("reactive_atom_absent_from_projection",)},
    "parent atom missing without leaving-group evidence": {"fields": {"unexplained_parent_missing_count": 1}, "expected_reasons": ("unexplained_parent_atom_missing",)},
    "leaving-group list inconsistent": {"fields": {"leaving_group_inconsistency_count": 1}, "expected_reasons": ("leaving_group_list_inconsistent",)},
    "unexpected observed atom": {"fields": {"unexpected_observed_atom_count": 1}, "expected_reasons": ("unexpected_observed_atom",)},
    "bond endpoint absent": {"fields": {"absent_bond_endpoint_count": 1}, "expected_reasons": ("bond_endpoint_absent",)},
    "bond self-loop": {"fields": {"self_loop_bond_count": 1}, "expected_reasons": ("bond_self_loop",)},
    "duplicate undirected bond": {"fields": {"duplicate_undirected_bond_count": 1}, "expected_reasons": ("duplicate_undirected_bond",)},
    "unsupported bond order": {"fields": {"unsupported_bond_order_count": 1}, "expected_reasons": ("unsupported_ccd_bond_order",)},
    "aromatic flag/order conflict": {"fields": {"aromatic_order_conflict_count": 1}, "expected_reasons": ("aromatic_flag_order_conflict",)},
    "parent graph disconnected": {"fields": {"parent_component_count": 2}, "expected_reasons": ("parent_graph_disconnected",)},
    "observed graph disconnected": {"fields": {"observed_component_count": 2}, "expected_reasons": ("observed_graph_disconnected",)},
    "atom count mismatch": {"fields": {"atom_count_matches": False}, "expected_reasons": ("atom_count_mismatch",)},
    "projection count mismatch": {"fields": {"projection_count_matches": False}, "expected_reasons": ("projection_count_mismatch",)},
    "nondeterministic atom order": {"fields": {"atom_order_deterministic": False}, "expected_reasons": ("nondeterministic_atom_order",)},
    "nondeterministic bond order": {"fields": {"bond_order_deterministic": False}, "expected_reasons": ("nondeterministic_bond_order",)},
    "graph SHA drift": {"fields": {"graph_sha_matches": False}, "expected_reasons": ("graph_sha_drift",)},
    "RDKit validation failure": {"fields": {"rdkit_validation_passed": False}, "expected_reasons": ("rdkit_validation_failed",)},
    "execution boundary crossed": {"fields": {"execution_boundary_crossed": True}, "expected_reasons": ("execution_boundary_crossed",)},
}


def _git(repo_root: Path, *arguments: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *arguments), cwd=repo_root, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def base_bytes(repo_root: Path, path: Path) -> bytes:
    if path.as_posix().startswith(("data/raw/", "checkpoints/")):
        raise ValueError(f"protected source must not be read as ordinary evidence: {path}")
    payload = _git(repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}")
    expected = FROZEN_SHA256.get(path)
    if expected and hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"frozen SHA mismatch: {path}")
    return payload


def base_path_tracked(repo_root: Path, path: Path) -> bool:
    result = subprocess.run(
        ("git", "cat-file", "-e", f"{BASE_COMMIT}:{path.as_posix()}"),
        cwd=repo_root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    return result.returncode == 0


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_bytes(columns: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({
            column: "true" if row.get(column) is True
            else "false" if row.get(column) is False
            else row.get(column, "")
            for column in columns
        })
    return stream.getvalue().encode("utf-8")


def _parse_loop(text: str, prefix: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
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
            line = lines[index].strip()
            if not line or line.startswith("#"):
                break
            if line == "loop_" or line.startswith("_") or line.startswith("data_"):
                break
            tokens.extend(shlex.split(lines[index], comments=False, posix=True))
            index += 1
        if len(tokens) % len(tags):
            raise ValueError(f"malformed loop: {prefix}")
        return tuple(tags), [
            dict(zip(tags, tokens[offset:offset + len(tags)]))
            for offset in range(0, len(tokens), len(tags))
        ]
    return (), []


def canonicalize_element_symbol_v1(type_symbol: str) -> str:
    if type(type_symbol) is not str:
        raise ValueError("element_symbol_type_invalid")
    canonical = type_symbol.strip().upper()
    if not canonical:
        raise ValueError("element_symbol_empty")
    return canonical


def parse_ccd_component_with_stats(
    text: str,
) -> tuple[
    tuple[ParentAtom, ...],
    tuple[ParentBond, ...],
    CCDHeavyProjectionStats,
]:
    if type(text) is not str:
        raise ValueError("ccd_text_type_invalid")
    atom_tags, atom_rows = _parse_loop(text, "_chem_comp_atom.")
    bond_tags, bond_rows = _parse_loop(text, "_chem_comp_bond.")
    if not atom_tags:
        raise ValueError("chem_comp_atom_loop_missing")
    if not bond_tags:
        raise ValueError("chem_comp_bond_loop_missing")
    if "_chem_comp_atom.atom_id" not in atom_tags:
        raise ValueError("chem_comp_atom_id_missing_or_invalid")
    if "_chem_comp_atom.type_symbol" not in atom_tags:
        raise ValueError("chem_comp_atom_type_symbol_missing_or_invalid")
    if "_chem_comp_atom.charge" not in atom_tags:
        raise ValueError("chem_comp_atom_charge_missing_or_invalid")
    for tag, reason in (
        ("_chem_comp_bond.atom_id_1", "chem_comp_bond_atom_id_1_missing_or_invalid"),
        ("_chem_comp_bond.atom_id_2", "chem_comp_bond_atom_id_2_missing_or_invalid"),
        ("_chem_comp_bond.value_order", "chem_comp_bond_value_order_missing_or_invalid"),
        ("_chem_comp_bond.pdbx_aromatic_flag", "chem_comp_bond_aromatic_flag_missing_or_invalid"),
    ):
        if tag not in bond_tags:
            raise ValueError(reason)

    source_atoms: list[tuple[str, str, int]] = []
    for row in atom_rows:
        atom_id = row.get("_chem_comp_atom.atom_id")
        if type(atom_id) is not str or not atom_id.strip():
            raise ValueError("chem_comp_atom_id_missing_or_invalid")
        raw_type_symbol = row.get("_chem_comp_atom.type_symbol")
        if type(raw_type_symbol) is not str or not raw_type_symbol.strip():
            raise ValueError("chem_comp_atom_type_symbol_missing_or_invalid")
        type_symbol = canonicalize_element_symbol_v1(raw_type_symbol)
        raw_charge = row.get("_chem_comp_atom.charge")
        if (
            type(raw_charge) is not str
            or re.fullmatch(r"[+-]?\d+", raw_charge.strip()) is None
        ):
            raise ValueError("chem_comp_atom_charge_missing_or_invalid")
        source_atoms.append((atom_id, type_symbol, int(raw_charge.strip())))
    all_atom_ids = [atom_id for atom_id, _, _ in source_atoms]
    if len(all_atom_ids) != len(set(all_atom_ids)):
        raise ValueError("duplicate_ccd_atom_id")
    type_symbol_by_id = {
        atom_id: type_symbol for atom_id, type_symbol, _ in source_atoms
    }
    explicit_hydrogen_ids = {
        atom_id
        for atom_id, type_symbol, _ in source_atoms
        if type_symbol in EXPLICIT_HYDROGEN_TYPE_SYMBOLS
    }
    heavy_source_atoms = [
        row
        for row in source_atoms
        if row[1] not in EXPLICIT_HYDROGEN_TYPE_SYMBOLS
    ]
    atoms = tuple(
        ParentAtom(
            atom_id=atom_id,
            type_symbol=type_symbol,
            formal_charge=formal_charge,
            row_index_0based=index,
        )
        for index, (atom_id, type_symbol, formal_charge)
        in enumerate(heavy_source_atoms)
    )

    source_bonds: list[ParentBond] = []
    hydrogen_involving_bond_count = 0
    for row in bond_rows:
        values: dict[str, str] = {}
        for tag, reason in (
            ("_chem_comp_bond.atom_id_1", "chem_comp_bond_atom_id_1_missing_or_invalid"),
            ("_chem_comp_bond.atom_id_2", "chem_comp_bond_atom_id_2_missing_or_invalid"),
            ("_chem_comp_bond.value_order", "chem_comp_bond_value_order_missing_or_invalid"),
            ("_chem_comp_bond.pdbx_aromatic_flag", "chem_comp_bond_aromatic_flag_missing_or_invalid"),
        ):
            value = row.get(tag)
            if type(value) is not str or not value.strip():
                raise ValueError(reason)
            values[tag] = value
        atom_id_1 = values["_chem_comp_bond.atom_id_1"]
        atom_id_2 = values["_chem_comp_bond.atom_id_2"]
        if atom_id_1 not in type_symbol_by_id or atom_id_2 not in type_symbol_by_id:
            raise ValueError("chem_comp_bond_endpoint_not_in_atom_loop")
        if atom_id_1 in explicit_hydrogen_ids or atom_id_2 in explicit_hydrogen_ids:
            hydrogen_involving_bond_count += 1
            continue
        source_bonds.append(
            ParentBond(
                atom_id_1=atom_id_1,
                atom_id_2=atom_id_2,
                source_value_order=values["_chem_comp_bond.value_order"].strip().upper(),
                source_aromatic_flag=values[
                    "_chem_comp_bond.pdbx_aromatic_flag"
                ].strip().upper(),
            )
        )
    bonds = tuple(source_bonds)
    if not atoms:
        raise ValueError("parent_heavy_atom_table_empty")
    stats = CCDHeavyProjectionStats(
        source_atom_row_count=len(source_atoms),
        explicit_hydrogen_atom_count=len(explicit_hydrogen_ids),
        heavy_atom_count=len(atoms),
        source_bond_row_count=len(bond_rows),
        hydrogen_involving_bond_count=hydrogen_involving_bond_count,
        heavy_heavy_bond_count=len(bonds),
    )
    return atoms, bonds, stats


def parse_ccd_component(
    text: str,
) -> tuple[tuple[ParentAtom, ...], tuple[ParentBond, ...]]:
    atoms, bonds, _ = parse_ccd_component_with_stats(text)
    return atoms, bonds


def normalize_bond_order(value_order: str, aromatic_flag: str) -> str:
    if type(value_order) is not str or type(aromatic_flag) is not str:
        raise ValueError("bond_order_argument_type_invalid")
    if not value_order.strip() or not aromatic_flag.strip():
        raise ValueError("bond_order_argument_empty")
    order = SOURCE_ORDER_MAP.get(value_order.strip().upper())
    if order is None:
        raise ValueError("unsupported_ccd_bond_order")
    flag = aromatic_flag.strip().upper()
    if flag not in ("Y", "N"):
        raise ValueError("unsupported_ccd_aromatic_flag")
    if (order == "aromatic") != (flag == "Y"):
        raise ValueError("aromatic_flag_order_conflict")
    return order


def _component_count(vertices: set[str], edges: set[tuple[str, str]]) -> int:
    if not vertices:
        return 0
    adjacency = {vertex: set() for vertex in vertices}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    count = 0
    remaining = set(vertices)
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
            list(edge) for edge in sorted(
                (min(a, b), max(a, b), order) for a, b, order in bonds
            )
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _invalid_graph_validation(reasons: Iterable[str]) -> GraphValidation:
    return GraphValidation(
        valid=False,
        reasons=tuple(dict.fromkeys(reasons)),
        parent_graph_sha256="",
        observed_graph_sha256="",
        parent_component_count=0,
        observed_component_count=0,
        projected_atom_count=0,
        projected_bond_count=0,
    )


def _validate_graph_authority_inputs(
    parent_atoms: object,
    parent_bonds: object,
    observed_atoms: object,
    leaving_group_atom_ids: object,
    *,
    reactive_atom_id: object,
    reaction_delta_class: object,
    parent_leaving_group_bond_verified: object,
    atom_inventory_reconciliation_passed: object,
    rdkit_validation_passed: object,
) -> tuple[str, ...]:
    reasons: list[str] = []
    containers = (
        (parent_atoms, "parent_atom_container_invalid"),
        (parent_bonds, "parent_bond_container_invalid"),
        (observed_atoms, "observed_atom_container_invalid"),
        (leaving_group_atom_ids, "leaving_group_container_invalid"),
    )
    for value, reason in containers:
        if type(value) not in (tuple, list):
            reasons.append(reason)

    if type(reactive_atom_id) is not str:
        reasons.append("reactive_atom_id_type_invalid")
    elif not reactive_atom_id:
        reasons.append("reactive_atom_id_empty")
    if type(reaction_delta_class) is not str:
        reasons.append("reaction_delta_class_type_invalid")
    if type(parent_leaving_group_bond_verified) is not bool:
        reasons.append("parent_leaving_group_bond_verified_type_invalid")
    if type(atom_inventory_reconciliation_passed) is not bool:
        reasons.append("atom_inventory_reconciliation_passed_type_invalid")
    if type(rdkit_validation_passed) is not bool:
        reasons.append("rdkit_validation_passed_type_invalid")

    valid_parent_records: list[ParentAtom] = []
    if type(parent_atoms) in (tuple, list):
        if not parent_atoms:
            reasons.append("parent_atom_table_empty")
        for value in parent_atoms:
            if type(value) is not ParentAtom:
                reasons.append("parent_atom_record_type_invalid")
            else:
                valid_parent_records.append(value)
                if type(value.atom_id) is not str:
                    reasons.append("parent_atom_id_type_invalid")
                elif not value.atom_id:
                    reasons.append("parent_atom_id_empty")
                if type(value.type_symbol) is not str:
                    reasons.append("parent_type_symbol_type_invalid")
                elif not value.type_symbol.strip():
                    reasons.append("parent_type_symbol_empty")
                else:
                    canonical_type_symbol = canonicalize_element_symbol_v1(
                        value.type_symbol
                    )
                    if (
                        canonical_type_symbol
                        in EXPLICIT_HYDROGEN_TYPE_SYMBOLS
                    ):
                        reasons.append("explicit_hydrogen_in_parent_graph")
                    elif canonical_type_symbol not in SUPPORTED_ELEMENTS:
                        reasons.append("unsupported_element")
                if type(value.formal_charge) is not int:
                    reasons.append("parent_formal_charge_type_invalid")
                if (
                    type(value.row_index_0based) is not int
                    or value.row_index_0based < 0
                ):
                    reasons.append("parent_row_index_type_invalid")
        if len(valid_parent_records) == len(parent_atoms):
            atom_ids = [
                value.atom_id
                for value in valid_parent_records
                if type(value.atom_id) is str
            ]
            if len(atom_ids) != len(set(atom_ids)):
                reasons.append("duplicate_ccd_atom_id")
            row_indices = [
                value.row_index_0based
                for value in valid_parent_records
                if type(value.row_index_0based) is int
                and value.row_index_0based >= 0
            ]
            if len(row_indices) != len(set(row_indices)):
                reasons.append("duplicate_ccd_atom_row_index")
            if (
                len(row_indices) == len(valid_parent_records)
                and set(row_indices) != set(range(len(valid_parent_records)))
            ):
                reasons.append("ccd_atom_row_indices_not_contiguous")

    if type(parent_bonds) in (tuple, list):
        for value in parent_bonds:
            if type(value) is not ParentBond:
                reasons.append("parent_bond_record_type_invalid")
                continue
            for field_name, type_reason, empty_reason in (
                ("atom_id_1", "parent_bond_atom_id_1_type_invalid", "parent_bond_atom_id_1_empty"),
                ("atom_id_2", "parent_bond_atom_id_2_type_invalid", "parent_bond_atom_id_2_empty"),
                ("source_value_order", "parent_bond_value_order_type_invalid", "parent_bond_value_order_empty"),
                ("source_aromatic_flag", "parent_bond_aromatic_flag_type_invalid", "parent_bond_aromatic_flag_empty"),
            ):
                field_value = getattr(value, field_name)
                if type(field_value) is not str:
                    reasons.append(type_reason)
                elif not field_value:
                    reasons.append(empty_reason)

    if type(observed_atoms) in (tuple, list):
        if not observed_atoms:
            reasons.append("observed_atom_table_empty")
        valid_observed_records: list[ObservedAtom] = []
        for value in observed_atoms:
            if type(value) is not ObservedAtom:
                reasons.append("observed_atom_record_type_invalid")
                continue
            valid_observed_records.append(value)
            if type(value.atom_name) is not str:
                reasons.append("observed_atom_name_type_invalid")
            elif not value.atom_name:
                reasons.append("observed_atom_name_empty")
            if type(value.type_symbol) is not str:
                reasons.append("observed_type_symbol_type_invalid")
            elif not value.type_symbol.strip():
                reasons.append("observed_type_symbol_empty")
            else:
                canonical_type_symbol = canonicalize_element_symbol_v1(
                    value.type_symbol
                )
                if canonical_type_symbol in EXPLICIT_HYDROGEN_TYPE_SYMBOLS:
                    reasons.append("explicit_hydrogen_in_observed_graph")
                elif canonical_type_symbol not in SUPPORTED_ELEMENTS:
                    reasons.append("unsupported_element")
            if (
                type(value.source_full_atom_row_index) is not int
                or value.source_full_atom_row_index < 0
            ):
                reasons.append("observed_source_row_index_type_invalid")
            if (
                type(value.retained_heavy_local_index_0based) is not int
                or value.retained_heavy_local_index_0based < 0
            ):
                reasons.append("observed_retained_local_index_type_invalid")
        if len(valid_observed_records) == len(observed_atoms):
            atom_names = [
                value.atom_name
                for value in valid_observed_records
                if type(value.atom_name) is str
            ]
            if len(atom_names) != len(set(atom_names)):
                reasons.append("duplicate_sample_atom_name")
            source_indices = [
                value.source_full_atom_row_index
                for value in valid_observed_records
                if type(value.source_full_atom_row_index) is int
                and value.source_full_atom_row_index >= 0
            ]
            if len(source_indices) != len(set(source_indices)):
                reasons.append("duplicate_observed_source_row_index")
            retained_indices = [
                value.retained_heavy_local_index_0based
                for value in valid_observed_records
                if type(value.retained_heavy_local_index_0based) is int
                and value.retained_heavy_local_index_0based >= 0
            ]
            if len(retained_indices) != len(set(retained_indices)):
                reasons.append("duplicate_observed_retained_local_index")
            if (
                len(retained_indices) == len(valid_observed_records)
                and set(retained_indices) != set(range(len(valid_observed_records)))
            ):
                reasons.append("observed_retained_local_indices_not_contiguous")

    if type(leaving_group_atom_ids) in (tuple, list):
        valid_leaving_ids: list[str] = []
        for value in leaving_group_atom_ids:
            if type(value) is not str:
                reasons.append("leaving_group_atom_id_type_invalid")
            elif not value:
                reasons.append("leaving_group_atom_id_empty")
            else:
                valid_leaving_ids.append(value)
        if len(valid_leaving_ids) != len(set(valid_leaving_ids)):
            reasons.append("duplicate_leaving_group_atom_id")
        parent_ids = {
            value.atom_id
            for value in valid_parent_records
            if type(value.atom_id) is str and value.atom_id
        }
        if (
            type(parent_atoms) in (tuple, list)
            and len(valid_parent_records) == len(parent_atoms)
            and any(value not in parent_ids for value in valid_leaving_ids)
        ):
            reasons.append("leaving_group_atom_not_in_parent")
    return tuple(dict.fromkeys(reasons))


def validate_graph_authority(
    parent_atoms: Sequence[ParentAtom],
    parent_bonds: Sequence[ParentBond],
    observed_atoms: Sequence[ObservedAtom],
    *,
    reactive_atom_id: str,
    leaving_group_atom_ids: Sequence[str] = (),
    reaction_delta_class: str = "",
    parent_leaving_group_bond_verified: bool = False,
    atom_inventory_reconciliation_passed: bool = False,
    rdkit_validation_passed: bool = True,
) -> GraphValidation:
    input_reasons = _validate_graph_authority_inputs(
        parent_atoms,
        parent_bonds,
        observed_atoms,
        leaving_group_atom_ids,
        reactive_atom_id=reactive_atom_id,
        reaction_delta_class=reaction_delta_class,
        parent_leaving_group_bond_verified=parent_leaving_group_bond_verified,
        atom_inventory_reconciliation_passed=atom_inventory_reconciliation_passed,
        rdkit_validation_passed=rdkit_validation_passed,
    )
    if input_reasons:
        return _invalid_graph_validation(input_reasons)
    parent_atoms = tuple(parent_atoms)
    parent_bonds = tuple(parent_bonds)
    observed_atoms = tuple(observed_atoms)
    leaving_group_atom_ids = tuple(leaving_group_atom_ids)

    reasons: list[str] = []
    parent_by_id = {atom.atom_id: atom for atom in parent_atoms}
    observed_by_name = {atom.atom_name: atom for atom in observed_atoms}
    missing_observed = set(observed_by_name) - set(parent_by_id)
    if missing_observed:
        reasons.extend(("sample_atom_not_in_ccd", "unexpected_observed_atom"))
    if any(
        name in parent_by_id
        and canonicalize_element_symbol_v1(
            observed_by_name[name].type_symbol
        )
        != canonicalize_element_symbol_v1(parent_by_id[name].type_symbol)
        for name in observed_by_name
    ):
        reasons.append("element_mismatch")
    if reactive_atom_id not in parent_by_id:
        reasons.append("reactive_atom_absent_from_parent")
    if reactive_atom_id not in observed_by_name:
        reasons.append("reactive_atom_absent_from_projection")

    normalized: list[tuple[str, str, str]] = []
    normalized_edge_keys: set[tuple[str, str]] = set()
    structurally_valid_bonds: list[
        tuple[ParentBond, tuple[str, str]]
    ] = []
    for bond in parent_bonds:
        if bond.atom_id_1 not in parent_by_id or bond.atom_id_2 not in parent_by_id:
            reasons.append("bond_endpoint_absent")
            continue
        if bond.atom_id_1 == bond.atom_id_2:
            reasons.append("bond_self_loop")
            continue
        key = tuple(sorted((bond.atom_id_1, bond.atom_id_2)))
        structurally_valid_bonds.append((bond, key))
    edge_key_counts = Counter(key for _, key in structurally_valid_bonds)
    if any(count > 1 for count in edge_key_counts.values()):
        reasons.append("duplicate_undirected_bond")
    for bond, key in structurally_valid_bonds:
        if edge_key_counts[key] != 1:
            continue
        try:
            order = normalize_bond_order(
                bond.source_value_order, bond.source_aromatic_flag
            )
        except ValueError as exc:
            reasons.append(str(exc))
            continue
        normalized.append((key[0], key[1], order))
        normalized_edge_keys.add(key)

    missing_parent = set(parent_by_id) - set(observed_by_name)
    leaving = set(leaving_group_atom_ids)
    if not missing_parent and leaving:
        reasons.append("leaving_group_list_inconsistent")
    elif missing_parent:
        if missing_parent != leaving:
            reasons.append(
                "unexplained_parent_atom_missing"
                if not leaving
                else "leaving_group_list_inconsistent"
            )
        elif not (
            reaction_delta_class == "covalent_leaving_group_loss"
            and parent_leaving_group_bond_verified is True
            and atom_inventory_reconciliation_passed is True
        ):
            reasons.append("unexplained_parent_atom_missing")
        elif any(
            not any(
                leaving_atom in edge and bool(set(edge) - leaving)
                for edge in normalized_edge_keys
            )
            for leaving_atom in leaving
        ):
            reasons.append("leaving_group_parent_bond_missing")

    parent_components = _component_count(
        set(parent_by_id), normalized_edge_keys
    )
    if parent_components != 1:
        reasons.append("parent_graph_disconnected")
    observed_edges = {
        (left, right)
        for left, right, _ in normalized
        if left in observed_by_name and right in observed_by_name
    }
    observed_components = _component_count(
        set(observed_by_name) & set(parent_by_id), observed_edges
    )
    if observed_components != 1:
        reasons.append("observed_graph_disconnected")
    if rdkit_validation_passed is False:
        reasons.append("rdkit_validation_failed")
    reasons = list(dict.fromkeys(reasons))
    projected_atoms = tuple(
        parent_by_id[name] for name in observed_by_name if name in parent_by_id
    )
    projected_bonds = tuple(
        edge
        for edge in normalized
        if edge[0] in observed_by_name and edge[1] in observed_by_name
    )
    if reasons:
        return GraphValidation(
            valid=False,
            reasons=tuple(reasons),
            parent_graph_sha256="",
            observed_graph_sha256="",
            parent_component_count=parent_components,
            observed_component_count=observed_components,
            projected_atom_count=len(projected_atoms),
            projected_bond_count=len(projected_bonds),
        )
    return GraphValidation(
        valid=True,
        reasons=(),
        parent_graph_sha256=_graph_sha(parent_atoms, normalized),
        observed_graph_sha256=_graph_sha(projected_atoms, projected_bonds),
        parent_component_count=parent_components,
        observed_component_count=observed_components,
        projected_atom_count=len(projected_atoms),
        projected_bond_count=len(projected_bonds),
    )


def mutation_signature(fields: Mapping[str, Any]) -> str:
    return "|".join(
        f"{key}={json.dumps(fields[key], sort_keys=True, separators=(',', ':'))}"
        for key in sorted(fields)
    )


def validate_scenario_types(scenario: AuthorityScenario) -> tuple[str, ...]:
    if type(scenario) is not AuthorityScenario:
        raise TypeError("scenario must be exact AuthorityScenario")
    reasons: list[str] = []
    for name in BOOL_SCENARIO_FIELDS:
        if type(getattr(scenario, name)) is not bool:
            reasons.append(f"scenario_field_type_invalid:{name}")
    for name in COUNT_SCENARIO_FIELDS:
        value = getattr(scenario, name)
        if type(value) is not int:
            reasons.append(f"scenario_field_type_invalid:{name}")
        elif value < 0:
            reasons.append(f"scenario_field_value_invalid:{name}")
    return tuple(reasons)


def evaluate_authority_scenario(scenario: AuthorityScenario) -> ScenarioObservation:
    reasons = list(validate_scenario_types(scenario))
    checks = (
        (not scenario.ccd_source_present, "ccd_source_missing"),
        (not scenario.ccd_source_base_tracked, "ccd_source_not_BASE_tracked"),
        (not scenario.chem_comp_atom_loop_present, "chem_comp_atom_loop_missing"),
        (not scenario.chem_comp_bond_loop_present, "chem_comp_bond_loop_missing"),
        (scenario.duplicate_ccd_atom_id_count != 0, "duplicate_ccd_atom_id"),
        (scenario.unsupported_element_count != 0, "unsupported_element"),
        (scenario.duplicate_sample_atom_name_count != 0, "duplicate_sample_atom_name"),
        (scenario.sample_atom_not_in_ccd_count != 0, "sample_atom_not_in_ccd"),
        (scenario.element_mismatch_count != 0, "element_mismatch"),
        (scenario.reactive_atom_parent_match_count != 1, "reactive_atom_absent_from_parent"),
        (scenario.reactive_atom_projection_match_count != 1, "reactive_atom_absent_from_projection"),
        (scenario.unexplained_parent_missing_count != 0, "unexplained_parent_atom_missing"),
        (scenario.leaving_group_inconsistency_count != 0, "leaving_group_list_inconsistent"),
        (scenario.unexpected_observed_atom_count != 0, "unexpected_observed_atom"),
        (scenario.absent_bond_endpoint_count != 0, "bond_endpoint_absent"),
        (scenario.self_loop_bond_count != 0, "bond_self_loop"),
        (scenario.duplicate_undirected_bond_count != 0, "duplicate_undirected_bond"),
        (scenario.unsupported_bond_order_count != 0, "unsupported_ccd_bond_order"),
        (scenario.aromatic_order_conflict_count != 0, "aromatic_flag_order_conflict"),
        (scenario.parent_component_count != 1, "parent_graph_disconnected"),
        (scenario.observed_component_count != 1, "observed_graph_disconnected"),
        (not scenario.atom_count_matches, "atom_count_mismatch"),
        (not scenario.projection_count_matches, "projection_count_mismatch"),
        (not scenario.atom_order_deterministic, "nondeterministic_atom_order"),
        (not scenario.bond_order_deterministic, "nondeterministic_bond_order"),
        (not scenario.graph_sha_matches, "graph_sha_drift"),
        (not scenario.rdkit_validation_passed, "rdkit_validation_failed"),
        (scenario.execution_boundary_crossed, "execution_boundary_crossed"),
    )
    reasons.extend(reason for failed, reason in checks if failed)
    valid = not reasons
    return ScenarioObservation(
        valid=valid,
        reasons=tuple(dict.fromkeys(reasons)),
        ready_for_reaction_family_rule_design=valid,
        ready_for_role_proposal_generation=False,
        ready_for_mask_materialization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
    )


def validate_failure_registry() -> tuple[str, ...]:
    baseline = {field.name: getattr(BASELINE_SCENARIO, field.name) for field in dataclasses.fields(AuthorityScenario)}
    signatures: list[str] = []
    for case, specification in FAILURE_MUTATIONS.items():
        if type(case) is not str or not case:
            raise ValueError("failure case invalid")
        if type(specification) is not dict or set(specification) != {"fields", "expected_reasons"}:
            raise ValueError(f"failure specification invalid:{case}")
        fields = specification["fields"]
        expected = specification["expected_reasons"]
        if type(fields) is not dict or not fields:
            raise ValueError(f"failure mutation invalid:{case}")
        if type(expected) is not tuple or not expected or any(type(item) is not str for item in expected):
            raise ValueError(f"expected reasons invalid:{case}")
        for name, value in fields.items():
            if name not in baseline or type(value) is not type(baseline[name]) or value == baseline[name]:
                raise ValueError(f"mutation field invalid:{case}:{name}")
        scenario = dataclasses.replace(BASELINE_SCENARIO, **fields)
        observed = evaluate_authority_scenario(scenario)
        if not set(expected) <= set(observed.reasons):
            raise ValueError(f"expected reason not observed:{case}")
        signatures.append(mutation_signature(fields))
    if len(signatures) != len(set(signatures)):
        raise ValueError("failure mutation signatures not unique")
    return tuple(signatures)


def _source_row(
    path: Path, sha: str, kind: str, tracked: bool, atom_named: bool,
    bond_order: bool, coverage: str, authority_class: str, blocking: str,
) -> dict[str, Any]:
    return {
        "source_path": path.as_posix(), "source_sha256": sha,
        "source_kind": kind, "BASE_tracked": tracked, "atom_named": atom_named,
        "bond_order_present": bond_order,
        "current11_component_coverage": coverage,
        "authority_class": authority_class, "blocking_reason": blocking,
        "verified": True,
    }


def build_source_inventory(repo_root: Path) -> list[dict[str, Any]]:
    for path in FROZEN_SHA256:
        base_bytes(repo_root, path)
    rows = [
        _source_row(ROLE_SOURCE, FROZEN_SHA256[ROLE_SOURCE], "predecessor_contract_source", True, False, False, "11/11", "gap_evidence", "predecessor_records_graph_authority_gap"),
        _source_row(ROLE_SUMMARY, FROZEN_SHA256[ROLE_SUMMARY], "predecessor_summary", True, False, False, "11/11", "gap_evidence", "summary_only"),
        _source_row(ROLE_MANIFEST, FROZEN_SHA256[ROLE_MANIFEST], "predecessor_manifest", True, False, False, "11/11", "gap_evidence", "manifest_only"),
        _source_row(ROLE_READINESS, FROZEN_SHA256[ROLE_READINESS], "predecessor_readiness", True, False, False, "11/11", "gap_evidence", "connectivity_and_bond_order_false_11_of_11"),
        _source_row(GRAPH_EVIDENCE, FROZEN_SHA256[GRAPH_EVIDENCE], "descriptor_graph_and_atom_inventory", True, True, False, "11/11;9/9_components", "supporting_only", "atom_inventory_without_atom_rows_formal_charge_or_bonds"),
        _source_row(FINAL_INDEX, FROZEN_SHA256[FINAL_INDEX], "current11_sample_index", True, True, False, "11/11", "supporting_only", "reactive_atom_name_only"),
        _source_row(ATOM_MAPPING, FROZEN_SHA256[ATOM_MAPPING], "reactive_atom_table_mapping", True, True, False, "11/11", "supporting_only", "reactive_atom_mapping_only"),
        _source_row(HEAVY_DISPOSITION, FROZEN_SHA256[HEAVY_DISPOSITION], "heavy_atom_projection", True, False, False, "11/11", "supporting_only", "projection_rows_do_not_map_all_atoms_to_CCD_atom_ids"),
        _source_row(SAMPLE_PROJECTION, FROZEN_SHA256[SAMPLE_PROJECTION], "sample_projection_summary", True, False, False, "11/11", "supporting_only", "counts_and_reactive_projection_only"),
        _source_row(TOPOLOGY_REPORT, FROZEN_SHA256[TOPOLOGY_REPORT], "historical_topology_policy", True, False, False, "0/11", "gap_evidence", "separate_three_candidate_design_no_topology_written"),
        _source_row(TOPOLOGY_SUMMARY, FROZEN_SHA256[TOPOLOGY_SUMMARY], "historical_topology_summary", True, False, False, "0/11", "gap_evidence", "summary_only"),
        _source_row(CCD_AUDIT, FROZEN_SHA256[CCD_AUDIT], "CCD_acquisition_audit", True, False, False, "9/9_components", "gap_evidence", "attests_ignored_CCD_files_but_contains_no_atom_or_bond_rows"),
        _source_row(RCSB_CURRENT_AUDIT, FROZEN_SHA256[RCSB_CURRENT_AUDIT], "CCD_descriptor_metadata", True, False, False, "8/9_components", "supporting_only", "descriptor_SMILES_not_atom_name_authority"),
        _source_row(RCSB_JUG_AUDIT, FROZEN_SHA256[RCSB_JUG_AUDIT], "CCD_descriptor_metadata", True, False, False, "1/9_components:JUG", "supporting_only", "descriptor_SMILES_not_atom_name_authority"),
        _source_row(STEP8_ATOMS, FROZEN_SHA256[STEP8_ATOMS], "historical_RDKit_atom_topology", True, False, False, "0/11", "supporting_only", "different_samples_RDKit_indices_not_CCD_atom_names"),
        _source_row(STEP8_BONDS, FROZEN_SHA256[STEP8_BONDS], "historical_RDKit_bond_topology", True, False, True, "0/11", "supporting_only", "different_samples_no_CCD_atom_name_mapping"),
    ]
    audit_rows = {row["het_id"]: row for row in _csv_rows(base_bytes(repo_root, CCD_AUDIT))}
    for component in CURRENT_COMPONENTS:
        path = CCD_ROOT / f"{component}.cif"
        if base_path_tracked(repo_root, path):
            raise ValueError(f"unexpected BASE CCD state requires explicit review:{path}")
        rows.append(_source_row(
            path, audit_rows[component]["sha256"],
            "untracked_CCD_path_attested_by_BASE_audit", False, False, False,
            f"1/9_components:{component}", "gap_evidence",
            "CCD_source_not_BASE_tracked;payload_not_read;atom_and_bond_contents_not_authority",
        ))
    return rows


def build_readiness(repo_root: Path) -> list[dict[str, Any]]:
    graph_rows = _csv_rows(base_bytes(repo_root, GRAPH_EVIDENCE))
    final_rows = _csv_rows(base_bytes(repo_root, FINAL_INDEX))
    if len(graph_rows) != 11 or len(final_rows) != 11:
        raise ValueError("Current11 cardinality mismatch")
    final_by_id = {row["sample_index_row_id"]: row for row in final_rows}
    output: list[dict[str, Any]] = []
    for graph in graph_rows:
        row_id = graph["sample_index_row_id"]
        final = final_by_id[row_id]
        if final["ligand_comp_id"] != graph["ligand_comp_id"]:
            raise ValueError("ligand component identity mismatch")
        reasons = [
            f"BASE_tracked_atom_named_CCD_source_missing:{graph['ligand_comp_id']}",
            "parent_atom_authority_unavailable",
            "parent_bond_order_authority_unavailable",
            "observed_to_parent_exact_projection_unavailable",
        ]
        if graph["ligand_comp_id"] == "ZYA":
            reasons.append("ZYA_F1_support_present_but_parent_CM_F1_bond_not_BASE_authority")
        output.append({
            "sample_index_row_id": row_id, "pdb_id": graph["pdb_id"],
            "ligand_comp_id": graph["ligand_comp_id"],
            "descriptor_graph_support_present": True,
            "atom_named_graph_authority_present": False,
            "atom_named_parent_graph_available": False,
            "parent_bond_order_authority_available": False,
            "observed_atom_projection_exact": False,
            "leaving_group_projection_valid": False,
            "parent_graph_valid": False, "observed_graph_valid": False,
            "pre_reaction_connectivity_available": False,
            "pre_reaction_bond_order_available": False,
            "reaction_family_label_available": False,
            "approved_warhead_rule_available": False,
            "role_proposal_generation_ready": False,
            "minimal_seed_proposal_generation_ready": False,
            "human_gold_review_completed": False,
            "ready_for_mask_materialization": False,
            "ready_for_tensorization": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
            "blocking_reasons": ";".join(reasons), "verified": True,
        })
    return output


def build_failure_matrix() -> list[dict[str, Any]]:
    validate_failure_registry()
    rows: list[dict[str, Any]] = []
    for case, specification in FAILURE_MUTATIONS.items():
        fields = specification["fields"]
        expected = specification["expected_reasons"]
        observed = evaluate_authority_scenario(
            dataclasses.replace(BASELINE_SCENARIO, **fields)
        )
        expected_reasons_verified = set(expected) <= set(observed.reasons)
        fails_closed = not observed.valid
        verified = (
            expected_reasons_verified
            and fails_closed
            and not observed.ready_for_reaction_family_rule_design
            and not observed.ready_for_role_proposal_generation
            and not observed.ready_for_mask_materialization
            and not observed.ready_for_model_integration
            and not observed.ready_for_training
        )
        rows.append({
            "failure_case": case, "mutation_signature": mutation_signature(fields),
            "mutated_fields": json.dumps(
                fields, sort_keys=True, separators=(",", ":")
            ),
            "expected_reasons": ";".join(expected),
            "observed_reasons": ";".join(observed.reasons),
            "expected_reasons_verified": expected_reasons_verified,
            "fails_closed": fails_closed,
            "ready_for_reaction_family_rule_design": observed.ready_for_reaction_family_rule_design,
            "ready_for_role_proposal_generation": observed.ready_for_role_proposal_generation,
            "ready_for_mask_materialization": observed.ready_for_mask_materialization,
            "ready_for_model_integration": observed.ready_for_model_integration,
            "ready_for_training": observed.ready_for_training,
            "verified": verified,
        })
    return rows


def heavy_projection_and_canonical_identity_probes_verified() -> bool:
    heavy_filtering_ccd = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
C1 C 0
O1 O 0
H1 H 0
H2 H 0
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
C1 O1 DOUB N
C1 H1 SING N
O1 H2 SING N
#
"""
    atoms, bonds, stats = parse_ccd_component_with_stats(
        heavy_filtering_ccd
    )
    if (
        tuple(
            (atom.atom_id, atom.type_symbol, atom.row_index_0based)
            for atom in atoms
        )
        != (("C1", "C", 0), ("O1", "O", 1))
        or tuple((bond.atom_id_1, bond.atom_id_2) for bond in bonds)
        != (("C1", "O1"),)
        or stats != CCDHeavyProjectionStats(4, 2, 2, 3, 2, 1)
    ):
        return False

    halogen_ccd = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
F1 F 0
CL1 Cl 0
BR1 br 0
I1 i 0
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
F1 CL1 SING N
CL1 BR1 SING N
BR1 I1 SING N
#
"""
    halogen_atoms, halogen_bonds, halogen_stats = (
        parse_ccd_component_with_stats(halogen_ccd)
    )
    if (
        tuple(atom.type_symbol for atom in halogen_atoms)
        != ("F", "CL", "BR", "I")
        or len(halogen_bonds) != 3
        or halogen_stats.explicit_hydrogen_atom_count != 0
        or halogen_stats.heavy_atom_count != 4
    ):
        return False

    atom_template = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
{atom_row}
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
C1 C1 SING N
#
"""
    bond_template = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
C1 C 0
O1 O 0
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
{bond_row}
#
"""
    parser_failures = (
        (
            atom_template.format(atom_row="'' C 0"),
            "chem_comp_atom_id_missing_or_invalid",
        ),
        (
            atom_template.format(atom_row="'   ' C 0"),
            "chem_comp_atom_id_missing_or_invalid",
        ),
        (
            atom_template.format(atom_row="C1 '' 0"),
            "chem_comp_atom_type_symbol_missing_or_invalid",
        ),
        (
            bond_template.format(bond_row="'' O1 SING N"),
            "chem_comp_bond_atom_id_1_missing_or_invalid",
        ),
        (
            bond_template.format(bond_row="C1 O1 '' N"),
            "chem_comp_bond_value_order_missing_or_invalid",
        ),
        (
            bond_template.format(bond_row="C1 O1 SING ''"),
            "chem_comp_bond_aromatic_flag_missing_or_invalid",
        ),
        (
            bond_template.format(bond_row="C1 X1 SING N"),
            "chem_comp_bond_endpoint_not_in_atom_loop",
        ),
    )
    for payload, expected_reason in parser_failures:
        try:
            parse_ccd_component(payload)
        except ValueError as exc:
            if str(exc) != expected_reason:
                return False
        else:
            return False

    bonds_for_case = (
        ParentBond("C1", "O1", "DOUB", "N"),
        ParentBond("C1", "F1", "SING", "N"),
    )
    uppercase_atoms = (
        ParentAtom("C1", "C", 0, 0),
        ParentAtom("O1", "O", 0, 1),
        ParentAtom("F1", "F", 0, 2),
    )
    lowercase_atoms = (
        ParentAtom("C1", "c", 0, 0),
        ParentAtom("O1", "o", 0, 1),
        ParentAtom("F1", "f", 0, 2),
    )
    uppercase_observed = (
        ObservedAtom("C1", "C", 0, 0),
        ObservedAtom("O1", "O", 1, 1),
    )
    lowercase_observed = (
        ObservedAtom("C1", "c", 0, 0),
        ObservedAtom("O1", "o", 1, 1),
    )
    case_results = tuple(
        validate_graph_authority(
            atom_rows,
            bonds_for_case,
            observed_rows,
            reactive_atom_id="C1",
            leaving_group_atom_ids=("F1",),
            reaction_delta_class="covalent_leaving_group_loss",
            parent_leaving_group_bond_verified=True,
            atom_inventory_reconciliation_passed=True,
        )
        for atom_rows, observed_rows in (
            (uppercase_atoms, uppercase_observed),
            (lowercase_atoms, lowercase_observed),
        )
    )
    if (
        not all(result.valid for result in case_results)
        or case_results[0].parent_graph_sha256
        != case_results[1].parent_graph_sha256
        or case_results[0].observed_graph_sha256
        != case_results[1].observed_graph_sha256
    ):
        return False

    for parent_rows, observed_rows, expected_reason in (
        (
            (ParentAtom("H1", "H", 0, 0),),
            (ObservedAtom("H1", "H", 0, 0),),
            "explicit_hydrogen_in_parent_graph",
        ),
        (
            (ParentAtom("C1", "C", 0, 0),),
            (ObservedAtom("C1", "D", 0, 0),),
            "explicit_hydrogen_in_observed_graph",
        ),
    ):
        result = validate_graph_authority(
            parent_rows,
            (),
            observed_rows,
            reactive_atom_id=observed_rows[0].atom_name,
        )
        if (
            result.valid
            or expected_reason not in result.reasons
            or result.parent_graph_sha256
            or result.observed_graph_sha256
        ):
            return False
    return True


def runtime_bypass_probes_verified() -> bool:
    atoms = (
        ParentAtom("C1", "C", 0, 0),
        ParentAtom("O1", "O", 0, 1),
        ParentAtom("F1", "F", 0, 2),
    )
    bonds = (
        ParentBond("C1", "O1", "DOUB", "N"),
        ParentBond("C1", "F1", "SING", "N"),
    )
    observed = (
        ObservedAtom("C1", "C", 5, 0),
        ObservedAtom("O1", "O", 8, 1),
    )

    def validate(
        parent_atom_value: object = atoms,
        parent_bond_value: object = bonds,
        observed_atom_value: object = observed,
        leaving_value: object = ("F1",),
        **overrides: object,
    ) -> GraphValidation:
        arguments: dict[str, object] = {
            "reactive_atom_id": "C1",
            "reaction_delta_class": "covalent_leaving_group_loss",
            "parent_leaving_group_bond_verified": True,
            "atom_inventory_reconciliation_passed": True,
            "rdkit_validation_passed": True,
        }
        arguments.update(overrides)
        return validate_graph_authority(
            parent_atom_value,
            parent_bond_value,
            observed_atom_value,
            leaving_group_atom_ids=leaving_value,
            **arguments,
        )

    probes = (
        (validate((ParentAtom("C1", "C", True, 0),), (), (ObservedAtom("C1", "C", 0, 0),), ()), "parent_formal_charge_type_invalid"),
        (validate((ParentAtom("C1", "C", 0, False),), (), (ObservedAtom("C1", "C", 0, 0),), ()), "parent_row_index_type_invalid"),
        (validate(parent_atom_value=(ParentAtom("C1", "C", 0, 0), ParentAtom("O1", "O", 0, 0))), "duplicate_ccd_atom_row_index"),
        (validate(parent_atom_value=(ParentAtom("C1", "C", 0, 0), ParentAtom("O1", "O", 0, 2))), "ccd_atom_row_indices_not_contiguous"),
        (validate(parent_bond_value=(ParentBond("C1", "O1", 1, "N"),)), "parent_bond_value_order_type_invalid"),
        (validate(observed_atom_value=(ObservedAtom("C1", "C", False, 0), ObservedAtom("O1", "O", 8, 1))), "observed_source_row_index_type_invalid"),
        (validate(observed_atom_value=(ObservedAtom("C1", "C", 5, True), ObservedAtom("O1", "O", 8, 1))), "observed_retained_local_index_type_invalid"),
        (validate(observed_atom_value=(ObservedAtom("C1", "C", 5, 0), ObservedAtom("O1", "O", 5, 1))), "duplicate_observed_source_row_index"),
        (validate(observed_atom_value=(ObservedAtom("C1", "C", 5, 0), ObservedAtom("O1", "O", 8, 0))), "duplicate_observed_retained_local_index"),
        (validate(observed_atom_value=(ObservedAtom("C1", "C", 5, 0), ObservedAtom("O1", "O", 8, 2))), "observed_retained_local_indices_not_contiguous"),
        (validate(parent_atom_value=set(atoms)), "parent_atom_container_invalid"),
        (validate(parent_atom_value=(atom for atom in atoms)), "parent_atom_container_invalid"),
        (validate(observed_atom_value={"C1": observed[0]}), "observed_atom_container_invalid"),
        (validate(reactive_atom_id=1), "reactive_atom_id_type_invalid"),
        (validate(parent_leaving_group_bond_verified=1), "parent_leaving_group_bond_verified_type_invalid"),
        (validate(atom_inventory_reconciliation_passed=1), "atom_inventory_reconciliation_passed_type_invalid"),
        (validate(rdkit_validation_passed=1), "rdkit_validation_passed_type_invalid"),
        (validate(leaving_value=("F1", "F1")), "duplicate_leaving_group_atom_id"),
        (validate(parent_bond_value=(bonds[0],)), "leaving_group_parent_bond_missing"),
        (
            validate(
                parent_bond_value=(
                    ParentBond("C1", "O1", "DOUB", "N"),
                    ParentBond("C1", "F1", "QUAD", "N"),
                )
            ),
            "unsupported_ccd_bond_order",
        ),
    )
    if not all(
        not result.valid
        and reason in result.reasons
        and result.parent_graph_sha256 == ""
        and result.observed_graph_sha256 == ""
        for result, reason in probes
    ):
        return False
    charge_template = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
{charge_column}
C1 C {charge}
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
C1 C1 SING N
#
"""
    for charge in (".", "?", "invalid", "''"):
        try:
            parse_ccd_component(
                charge_template.format(
                    charge_column="_chem_comp_atom.charge",
                    charge=charge,
                )
            )
        except ValueError as exc:
            if str(exc) != "chem_comp_atom_charge_missing_or_invalid":
                return False
        else:
            return False
    try:
        parse_ccd_component(
            charge_template.format(charge_column="", charge="")
        )
    except ValueError as exc:
        if str(exc) != "chem_comp_atom_charge_missing_or_invalid":
            return False
    else:
        return False
    return True


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    inventory = build_source_inventory(repo_root)
    readiness = build_readiness(repo_root)
    failures = build_failure_matrix()
    runtime_probes_verified = runtime_bypass_probes_verified()
    heavy_projection_probes_verified = (
        heavy_projection_and_canonical_identity_probes_verified()
    )
    failure_mutated_fields_canonical_json = all(
        json.dumps(
            json.loads(row["mutated_fields"]),
            sort_keys=True,
            separators=(",", ":"),
        )
        == row["mutated_fields"]
        for row in failures
    )
    failure_verified_is_derived = all(
        row["verified"]
        == (
            row["expected_reasons_verified"]
            and row["fails_closed"]
            and not row["ready_for_reaction_family_rule_design"]
            and not row["ready_for_role_proposal_generation"]
            and not row["ready_for_mask_materialization"]
            and not row["ready_for_model_integration"]
            and not row["ready_for_training"]
        )
        for row in failures
    )
    graph_rows = _csv_rows(base_bytes(repo_root, GRAPH_EVIDENCE))
    parent_support_total = sum(int(row["parent_ccd_heavy_atom_count"]) for row in graph_rows)
    observed_support_total = sum(int(row["observed_post_covalent_heavy_atom_count"]) for row in graph_rows)
    payloads = {
        SOURCE_INVENTORY_FILE: _csv_bytes(SOURCE_COLUMNS, inventory),
        PARENT_ATOM_FILE: _csv_bytes(ATOM_COLUMNS, ()),
        BOND_FILE: _csv_bytes(BOND_COLUMNS, ()),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, readiness),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, failures),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT, "parent": BASE_PARENT,
            "tree": BASE_TREE, "subject": BASE_SUBJECT,
        },
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "outcome": "blocked_BASE_tracked_atom_named_CCD_authority_absent",
        "source_inventory_row_count": len(inventory),
        "current11_row_count": len(readiness),
        "unique_ligand_component_count": len({row["ligand_comp_id"] for row in readiness}),
        "unique_ligand_components": list(dict.fromkeys(row["ligand_comp_id"] for row in readiness)),
        "current11_parent_heavy_atom_count_from_supporting_inventory": parent_support_total,
        "current11_observed_retained_heavy_atom_count_from_supporting_inventory": observed_support_total,
        "authoritative_parent_atom_row_count": 0,
        "authoritative_parent_bond_row_count": 0,
        "authoritative_observed_projected_bond_row_count": 0,
        "unexplained_missing_atom_count_in_authoritative_projection": 0,
        "atom_mapping_exact_one_count": 0,
        "unsupported_bond_order_count": 0,
        "parent_graph_valid_count": 0,
        "observed_graph_valid_count": 0,
        "pre_reaction_connectivity_available_count": 0,
        "pre_reaction_bond_order_available_count": 0,
        "reaction_family_label_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "role_proposal_generation_ready_count": 0,
        "minimal_seed_proposal_generation_ready_count": 0,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "failure_matrix_row_count": len(failures),
        "failure_mutation_signatures_unique": len({row["mutation_signature"] for row in failures}) == len(failures),
        "failure_expected_reasons_verified": all(row["expected_reasons_verified"] for row in failures),
        "graph_authority_public_input_exact_types_verified": runtime_probes_verified,
        "parent_atom_fields_exact_types_verified": runtime_probes_verified,
        "parent_atom_row_indices_unique_and_contiguous": runtime_probes_verified,
        "parent_bond_fields_exact_types_verified": runtime_probes_verified,
        "normalized_connectivity_uses_only_valid_bonds": runtime_probes_verified,
        "observed_atom_fields_exact_types_verified": runtime_probes_verified,
        "observed_source_row_indices_unique": runtime_probes_verified,
        "observed_retained_local_indices_unique_and_contiguous": runtime_probes_verified,
        "leaving_group_arguments_exact_types_verified": runtime_probes_verified,
        "leaving_group_parent_bond_reconstructed_and_verified": runtime_probes_verified,
        "unknown_ccd_formal_charge_rejected": runtime_probes_verified,
        "graph_invalid_inputs_do_not_emit_authority_sha": runtime_probes_verified,
        "failure_mutated_fields_canonical_json": failure_mutated_fields_canonical_json,
        "failure_verified_is_derived": failure_verified_is_derived,
        "runtime_bypass_probes_verified": runtime_probes_verified,
        "ccd_parent_graph_heavy_atoms_only": heavy_projection_probes_verified,
        "explicit_hydrogen_atoms_filtered": heavy_projection_probes_verified,
        "hydrogen_involving_bonds_filtered": heavy_projection_probes_verified,
        "halogens_preserved_as_heavy_atoms": heavy_projection_probes_verified,
        "parser_atom_fields_nonempty_verified": heavy_projection_probes_verified,
        "parser_bond_fields_nonempty_verified": heavy_projection_probes_verified,
        "parser_bond_endpoints_exist_verified": heavy_projection_probes_verified,
        "canonical_element_symbols_used_in_graph_sha": heavy_projection_probes_verified,
        "element_case_independent_graph_sha_verified": heavy_projection_probes_verified,
        "explicit_hydrogen_rejected_from_public_parent_graph": heavy_projection_probes_verified,
        "explicit_hydrogen_rejected_from_public_observed_graph": heavy_projection_probes_verified,
        "zya_f1_disposition": "supporting_evidence_only_parent_F1_not_materialized_without_BASE_authority",
        "descriptor_SMILES_used_as_atom_name_authority": False,
        "RDKit_used_as_atom_name_authority": False,
        "raw_payload_read": False,
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
        "remaining_readiness_blockers": [
            "BASE_TRACKED_ATOM_NAMED_CCD_COMPONENT_RECORDS_MISSING",
            "CURRENT11_PARENT_BOND_ORDER_AUTHORITY_MISSING",
            "CURRENT11_OBSERVED_TO_PARENT_EXACT_PROJECTION_MISSING",
            "reaction_family_labels_missing",
            "approved_warhead_rules_missing",
            "current11_human_gold_review_missing",
            "COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED",
            "COVALENT_GEOMETRY_AND_AUXILIARY_LABEL_CONTRACT_UNRESOLVED",
        ],
        "recommended_next_step": "resolve_covapie_current11_pre_reaction_graph_authority_blockers_v1",
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
    root = repo_root / OUTPUT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (root / name).write_bytes(payload)
    return payloads


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize(repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

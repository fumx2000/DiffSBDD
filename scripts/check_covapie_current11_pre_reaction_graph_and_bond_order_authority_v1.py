#!/usr/bin/env python3
"""Independent checker for the Current11 pre-reaction graph authority stage."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_pre_reaction_graph_and_bond_order_authority_v1 as stage,
)


BASE_COMMIT = "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1"
BASE_PARENT = "335a0320e8bd8ee125e51f927e6cd26d0c05707e"
BASE_TREE = "509d5050530741e04caa1653bdb1e257f17345e3"
BASE_SUBJECT = "add CovaPIE ligand role and minimal seed annotation contract v1"
FORMAL_COMMIT_SUBJECT = "add CovaPIE current11 pre-reaction graph authority v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / stage.SCHEMA_VERSION
EXACT10 = (
    Path("src/covalent_ext/covapie_current11_pre_reaction_graph_and_bond_order_authority_v1.py"),
    Path("tests/test_covapie_current11_pre_reaction_graph_and_bond_order_authority_v1.py"),
    Path("scripts/check_covapie_current11_pre_reaction_graph_and_bond_order_authority_v1.py"),
    Path("docs/covapie_current11_pre_reaction_graph_and_bond_order_authority_v1_summary.md"),
    *(OUTPUT_ROOT / name for name in stage.OUTPUT_FILES),
)
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
)


def _git(*arguments: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *arguments), cwd=ROOT, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if check and result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def _base(path: Path) -> bytes:
    payload = _git("show", f"{BASE_COMMIT}:{path.as_posix()}")
    assert hashlib.sha256(payload).hexdigest() == stage.FROZEN_SHA256[path]
    return payload


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _file_rows(name: str) -> list[dict[str, str]]:
    return _rows((ROOT / OUTPUT_ROOT / name).read_bytes())


def _bool(value: str) -> bool:
    assert value in ("true", "false")
    return value == "true"


def _independent_graph_sha(
    atoms: list[tuple[str, str, int]],
    bonds: list[tuple[str, str, str]],
) -> str:
    payload = {
        "atoms": [list(atom) for atom in sorted(atoms)],
        "bonds": [
            list(edge) for edge in sorted(
                (min(left, right), max(left, right), order)
                for left, right, order in bonds
            )
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def verify_base_and_sources() -> dict[str, int]:
    identity = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    assert identity == [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    for path in stage.FROZEN_SHA256:
        _base(path)

    graph_rows = _rows(_base(stage.GRAPH_EVIDENCE))
    final_rows = _rows(_base(stage.FINAL_INDEX))
    assert len(graph_rows) == len(final_rows) == 11
    final_by_id = {row["sample_index_row_id"]: row for row in final_rows}
    assert set(final_by_id) == {row["sample_index_row_id"] for row in graph_rows}
    components = {row["ligand_comp_id"] for row in graph_rows}
    assert components == set(stage.CURRENT_COMPONENTS)
    for row in graph_rows:
        assert final_by_id[row["sample_index_row_id"]]["ligand_comp_id"] == row["ligand_comp_id"]

    ccd_audit = {row["het_id"]: row for row in _rows(_base(stage.CCD_AUDIT))}
    assert set(stage.CURRENT_COMPONENTS) <= set(ccd_audit)
    for component in stage.CURRENT_COMPONENTS:
        raw_path = stage.CCD_ROOT / f"{component}.cif"
        result = subprocess.run(
            ("git", "cat-file", "-e", f"{BASE_COMMIT}:{raw_path.as_posix()}"),
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        assert result.returncode != 0
        assert len(ccd_audit[component]["sha256"]) == 64
    return {
        "sample_count": len(graph_rows),
        "component_count": len(components),
        "parent_support_count": sum(int(row["parent_ccd_heavy_atom_count"]) for row in graph_rows),
        "observed_support_count": sum(int(row["observed_post_covalent_heavy_atom_count"]) for row in graph_rows),
    }


def verify_synthetic_graph_contract() -> None:
    cif = """data_SYN
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
C1 C 0
O1 O 0
F1 F 0
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
C1 O1 DOUB N
C1 F1 SING N
#
"""
    atoms, bonds = stage.parse_ccd_component(cif)
    assert [(atom.atom_id, atom.type_symbol, atom.formal_charge) for atom in atoms] == [
        ("C1", "C", 0), ("O1", "O", 0), ("F1", "F", 0)
    ]
    observed = (
        stage.ObservedAtom("C1", "C", 0, 0),
        stage.ObservedAtom("O1", "O", 1, 1),
    )
    validation = stage.validate_graph_authority(
        atoms, bonds, observed, reactive_atom_id="C1",
        leaving_group_atom_ids=("F1",),
        reaction_delta_class="covalent_leaving_group_loss",
        parent_leaving_group_bond_verified=True,
        atom_inventory_reconciliation_passed=True,
    )
    assert validation.valid
    assert validation.projected_atom_count == 2
    assert validation.projected_bond_count == 1
    assert validation.parent_graph_sha256 == _independent_graph_sha(
        [("C1", "C", 0), ("O1", "O", 0), ("F1", "F", 0)],
        [("C1", "O1", "double"), ("C1", "F1", "single")],
    )
    assert validation.observed_graph_sha256 == _independent_graph_sha(
        [("C1", "C", 0), ("O1", "O", 0)],
        [("C1", "O1", "double")],
    )
    reversed_validation = stage.validate_graph_authority(
        tuple(reversed(atoms)), tuple(reversed(bonds)), tuple(reversed(observed)),
        reactive_atom_id="C1", leaving_group_atom_ids=("F1",),
        reaction_delta_class="covalent_leaving_group_loss",
        parent_leaving_group_bond_verified=True,
        atom_inventory_reconciliation_passed=True,
    )
    assert reversed_validation.parent_graph_sha256 == validation.parent_graph_sha256
    assert reversed_validation.observed_graph_sha256 == validation.observed_graph_sha256


def verify_runtime_bypass_probes() -> None:
    atoms = (
        stage.ParentAtom("C1", "C", 0, 0),
        stage.ParentAtom("O1", "O", 0, 1),
        stage.ParentAtom("F1", "F", 0, 2),
    )
    bonds = (
        stage.ParentBond("C1", "O1", "DOUB", "N"),
        stage.ParentBond("C1", "F1", "SING", "N"),
    )
    observed = (
        stage.ObservedAtom("C1", "C", 5, 0),
        stage.ObservedAtom("O1", "O", 8, 1),
    )

    def validate(
        parent_value=atoms,
        bond_value=bonds,
        observed_value=observed,
        leaving_value=("F1",),
        **overrides,
    ):
        arguments = {
            "reactive_atom_id": "C1",
            "reaction_delta_class": "covalent_leaving_group_loss",
            "parent_leaving_group_bond_verified": True,
            "atom_inventory_reconciliation_passed": True,
            "rdkit_validation_passed": True,
        }
        arguments.update(overrides)
        return stage.validate_graph_authority(
            parent_value, bond_value, observed_value,
            leaving_group_atom_ids=leaving_value, **arguments,
        )

    probes = (
        (validate(parent_value=(stage.ParentAtom("C1", "C", True, 0),)), "parent_formal_charge_type_invalid"),
        (validate(parent_value=(stage.ParentAtom("C1", "C", 0, False),)), "parent_row_index_type_invalid"),
        (validate(observed_value=(stage.ObservedAtom("C1", "C", False, 0), stage.ObservedAtom("O1", "O", 8, 1))), "observed_source_row_index_type_invalid"),
        (validate(observed_value=(stage.ObservedAtom("C1", "C", 5, True), stage.ObservedAtom("O1", "O", 8, 1))), "observed_retained_local_index_type_invalid"),
        (validate(observed_value=(stage.ObservedAtom("C1", "C", 5, 0), stage.ObservedAtom("O1", "O", 5, 1))), "duplicate_observed_source_row_index"),
        (validate(observed_value=(stage.ObservedAtom("C1", "C", 5, 0), stage.ObservedAtom("O1", "O", 8, 0))), "duplicate_observed_retained_local_index"),
        (validate(observed_value=(stage.ObservedAtom("C1", "C", 5, 0), stage.ObservedAtom("O1", "O", 8, 2))), "observed_retained_local_indices_not_contiguous"),
        (validate(parent_value=set(atoms)), "parent_atom_container_invalid"),
        (validate(parent_value=(atom for atom in atoms)), "parent_atom_container_invalid"),
        (validate(observed_value={"C1": observed[0]}), "observed_atom_container_invalid"),
        (validate(reactive_atom_id=1), "reactive_atom_id_type_invalid"),
        (validate(rdkit_validation_passed=1), "rdkit_validation_passed_type_invalid"),
        (validate(leaving_value=("F1", "F1")), "duplicate_leaving_group_atom_id"),
        (validate(bond_value=(bonds[0],)), "leaving_group_parent_bond_missing"),
    )
    for result, reason in probes:
        assert not result.valid
        assert reason in result.reasons
        assert result.parent_graph_sha256 == ""
        assert result.observed_graph_sha256 == ""

    atom_loop = """data_X
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
    for charge, expected in (("0", 0), ("1", 1), ("-1", -1)):
        parsed, _ = stage.parse_ccd_component(
            atom_loop.format(
                charge_column="_chem_comp_atom.charge", charge=charge
            )
        )
        assert parsed[0].formal_charge == expected
        assert type(parsed[0].formal_charge) is int
    for charge in (".", "?", "invalid", "''"):
        try:
            stage.parse_ccd_component(
                atom_loop.format(
                    charge_column="_chem_comp_atom.charge", charge=charge
                )
            )
        except ValueError as exc:
            assert str(exc) == "chem_comp_atom_charge_missing_or_invalid"
        else:
            raise AssertionError("unknown CCD formal charge accepted")
    try:
        stage.parse_ccd_component(
            atom_loop.format(charge_column="", charge="")
        )
    except ValueError as exc:
        assert str(exc) == "chem_comp_atom_charge_missing_or_invalid"
    else:
        raise AssertionError("missing CCD formal charge column accepted")


def verify_heavy_projection_and_canonical_identity() -> None:
    heavy_ccd = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
C1 C 0
O1 o 0
H1 H 0
H2 h 0
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
    atoms, bonds, stats = stage.parse_ccd_component_with_stats(heavy_ccd)
    assert atoms == (
        stage.ParentAtom("C1", "C", 0, 0),
        stage.ParentAtom("O1", "O", 0, 1),
    )
    assert bonds == (stage.ParentBond("C1", "O1", "DOUB", "N"),)
    assert stats == stage.CCDHeavyProjectionStats(4, 2, 2, 3, 2, 1)

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
    halogen_atoms, _, halogen_stats = stage.parse_ccd_component_with_stats(
        halogen_ccd
    )
    assert tuple(atom.type_symbol for atom in halogen_atoms) == (
        "F", "CL", "BR", "I"
    )
    assert tuple(atom.row_index_0based for atom in halogen_atoms) == (0, 1, 2, 3)
    assert halogen_stats.explicit_hydrogen_atom_count == 0

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
    failures = (
        (atom_template.format(atom_row="'' C 0"), "chem_comp_atom_id_missing_or_invalid"),
        (atom_template.format(atom_row="'   ' C 0"), "chem_comp_atom_id_missing_or_invalid"),
        (atom_template.format(atom_row="C1 '' 0"), "chem_comp_atom_type_symbol_missing_or_invalid"),
        (bond_template.format(bond_row="'' O1 SING N"), "chem_comp_bond_atom_id_1_missing_or_invalid"),
        (bond_template.format(bond_row="C1 '' SING N"), "chem_comp_bond_atom_id_2_missing_or_invalid"),
        (bond_template.format(bond_row="C1 O1 '' N"), "chem_comp_bond_value_order_missing_or_invalid"),
        (bond_template.format(bond_row="C1 O1 SING ''"), "chem_comp_bond_aromatic_flag_missing_or_invalid"),
        (bond_template.format(bond_row="C1 X1 SING N"), "chem_comp_bond_endpoint_not_in_atom_loop"),
    )
    for payload, expected in failures:
        try:
            stage.parse_ccd_component(payload)
        except ValueError as exc:
            assert str(exc) == expected
        else:
            raise AssertionError(f"parser accepted invalid field:{expected}")

    parent_upper = (
        stage.ParentAtom("C1", "C", 0, 0),
        stage.ParentAtom("O1", "O", 0, 1),
        stage.ParentAtom("F1", "F", 0, 2),
    )
    parent_lower = tuple(
        stage.ParentAtom(
            atom.atom_id,
            atom.type_symbol.lower(),
            atom.formal_charge,
            atom.row_index_0based,
        )
        for atom in parent_upper
    )
    graph_bonds = (
        stage.ParentBond("C1", "O1", "DOUB", "N"),
        stage.ParentBond("C1", "F1", "SING", "N"),
    )
    observed_upper = (
        stage.ObservedAtom("C1", "C", 0, 0),
        stage.ObservedAtom("O1", "O", 1, 1),
    )
    observed_lower = (
        stage.ObservedAtom("C1", "c", 0, 0),
        stage.ObservedAtom("O1", "o", 1, 1),
    )
    results = tuple(
        stage.validate_graph_authority(
            parent,
            graph_bonds,
            observed,
            reactive_atom_id="C1",
            leaving_group_atom_ids=("F1",),
            reaction_delta_class="covalent_leaving_group_loss",
            parent_leaving_group_bond_verified=True,
            atom_inventory_reconciliation_passed=True,
        )
        for parent, observed in (
            (parent_upper, observed_upper),
            (parent_lower, observed_lower),
        )
    )
    assert results[0].valid and results[1].valid
    assert results[0].parent_graph_sha256 == results[1].parent_graph_sha256
    assert results[0].observed_graph_sha256 == results[1].observed_graph_sha256

    for symbol in stage.EXPLICIT_HYDROGEN_TYPE_SYMBOLS:
        injected = stage.validate_graph_authority(
            (stage.ParentAtom("H1", symbol, 0, 0),),
            (),
            (stage.ObservedAtom("H1", symbol, 0, 0),),
            reactive_atom_id="H1",
        )
        assert "explicit_hydrogen_in_parent_graph" in injected.reasons
        assert "explicit_hydrogen_in_observed_graph" in injected.reasons
        assert injected.parent_graph_sha256 == injected.observed_graph_sha256 == ""


def verify_outputs(stats: dict[str, int]) -> str:
    expected = stage.build_evidence_payloads(ROOT)
    assert set(expected) == set(stage.OUTPUT_FILES)
    for name, payload in expected.items():
        assert (ROOT / OUTPUT_ROOT / name).read_bytes() == payload

    inventory = _file_rows(stage.SOURCE_INVENTORY_FILE)
    assert len(inventory) == 25
    raw_rows = [
        row for row in inventory
        if row["source_kind"] == "untracked_CCD_path_attested_by_BASE_audit"
    ]
    assert len(raw_rows) == 9
    assert all(
        row["BASE_tracked"] == "false"
        and row["authority_class"] == "gap_evidence"
        and row["atom_named"] == "false"
        and row["bond_order_present"] == "false"
        for row in raw_rows
    )
    assert not any(row["authority_class"] == "authoritative" for row in inventory)

    assert _file_rows(stage.PARENT_ATOM_FILE) == []
    assert _file_rows(stage.BOND_FILE) == []
    readiness = _file_rows(stage.READINESS_FILE)
    assert len(readiness) == stats["sample_count"] == 11
    false_fields = (
        "atom_named_graph_authority_present",
        "atom_named_parent_graph_available",
        "parent_bond_order_authority_available",
        "observed_atom_projection_exact",
        "leaving_group_projection_valid",
        "parent_graph_valid",
        "observed_graph_valid",
        "pre_reaction_connectivity_available",
        "pre_reaction_bond_order_available",
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
    assert all(_bool(row["descriptor_graph_support_present"]) for row in readiness)
    assert all(not _bool(row[field]) for row in readiness for field in false_fields)
    zya = [row for row in readiness if row["ligand_comp_id"] == "ZYA"]
    assert len(zya) == 1
    assert "ZYA_F1_support_present_but_parent_CM_F1_bond_not_BASE_authority" in zya[0]["blocking_reasons"]

    failures = _file_rows(stage.FAILURE_FILE)
    assert len(failures) == len(stage.FAILURE_MUTATIONS) == 28
    assert len({row["mutation_signature"] for row in failures}) == len(failures)
    for row in failures:
        mutation = json.loads(row["mutated_fields"])
        assert type(mutation) is dict and mutation
        assert row["mutated_fields"] == json.dumps(
            mutation, sort_keys=True, separators=(",", ":")
        )
        specification = stage.FAILURE_MUTATIONS[row["failure_case"]]
        assert mutation == specification["fields"]
        independent_signature = "|".join(
            f"{key}={json.dumps(mutation[key], sort_keys=True, separators=(',', ':'))}"
            for key in sorted(mutation)
        )
        assert row["mutation_signature"] == independent_signature
        scenario = dataclasses.replace(stage.BASELINE_SCENARIO, **mutation)
        observation = stage.evaluate_authority_scenario(scenario)
        expected_reasons = set(filter(None, row["expected_reasons"].split(";")))
        observed_reasons = set(filter(None, row["observed_reasons"].split(";")))
        assert expected_reasons == set(specification["expected_reasons"])
        assert observed_reasons == set(observation.reasons)
        assert expected_reasons <= observed_reasons
        assert row["expected_reasons_verified"] == "true"
        assert row["fails_closed"] == "true"
        assert row["ready_for_reaction_family_rule_design"] == "false"
        assert row["ready_for_role_proposal_generation"] == "false"
        assert row["ready_for_mask_materialization"] == "false"
        assert row["ready_for_model_integration"] == "false"
        assert row["ready_for_training"] == "false"
        derived_verified = (
            row["expected_reasons_verified"] == "true"
            and row["fails_closed"] == "true"
            and row["ready_for_reaction_family_rule_design"] == "false"
            and row["ready_for_role_proposal_generation"] == "false"
            and row["ready_for_mask_materialization"] == "false"
            and row["ready_for_model_integration"] == "false"
            and row["ready_for_training"] == "false"
        )
        assert row["verified"] == str(derived_verified).lower()

    manifest_bytes = (ROOT / OUTPUT_ROOT / stage.MANIFEST_FILE).read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["formal_base"] == {
        "commit": BASE_COMMIT, "parent": BASE_PARENT,
        "tree": BASE_TREE, "subject": BASE_SUBJECT,
    }
    assert manifest["unique_ligand_component_count"] == stats["component_count"] == 9
    assert manifest["current11_parent_heavy_atom_count_from_supporting_inventory"] == stats["parent_support_count"]
    assert manifest["current11_observed_retained_heavy_atom_count_from_supporting_inventory"] == stats["observed_support_count"]
    assert manifest["authoritative_parent_atom_row_count"] == 0
    assert manifest["authoritative_parent_bond_row_count"] == 0
    assert manifest["authoritative_observed_projected_bond_row_count"] == 0
    assert manifest["reaction_family_label_available_count"] == 0
    assert manifest["approved_warhead_rule_available_count"] == 0
    assert manifest["role_proposal_generation_ready_count"] == 0
    assert manifest["minimal_seed_proposal_generation_ready_count"] == 0
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert manifest["recommended_next_step"] == (
        "resolve_covapie_current11_pre_reaction_graph_authority_blockers_v1"
    )
    assert stage.MANIFEST_FILE not in manifest["evidence_sha256"]
    hardening_flags = (
        "graph_authority_public_input_exact_types_verified",
        "parent_atom_fields_exact_types_verified",
        "parent_atom_row_indices_unique_and_contiguous",
        "parent_bond_fields_exact_types_verified",
        "normalized_connectivity_uses_only_valid_bonds",
        "observed_atom_fields_exact_types_verified",
        "observed_source_row_indices_unique",
        "observed_retained_local_indices_unique_and_contiguous",
        "leaving_group_arguments_exact_types_verified",
        "leaving_group_parent_bond_reconstructed_and_verified",
        "unknown_ccd_formal_charge_rejected",
        "graph_invalid_inputs_do_not_emit_authority_sha",
        "failure_mutated_fields_canonical_json",
        "failure_verified_is_derived",
        "runtime_bypass_probes_verified",
        "ccd_parent_graph_heavy_atoms_only",
        "explicit_hydrogen_atoms_filtered",
        "hydrogen_involving_bonds_filtered",
        "halogens_preserved_as_heavy_atoms",
        "parser_atom_fields_nonempty_verified",
        "parser_bond_fields_nonempty_verified",
        "parser_bond_endpoints_exist_verified",
        "canonical_element_symbols_used_in_graph_sha",
        "element_case_independent_graph_sha_verified",
        "explicit_hydrogen_rejected_from_public_parent_graph",
        "explicit_hydrogen_rejected_from_public_observed_graph",
    )
    assert all(manifest[field] is True for field in hardening_flags)
    return hashlib.sha256(manifest_bytes).hexdigest()


def verify_boundaries() -> None:
    assert len(EXACT10) == len(set(EXACT10)) == 10
    assert all((ROOT / path).is_file() and not (ROOT / path).is_symlink() for path in EXACT10)
    assert not any(path.suffix.lower() in FORBIDDEN_SUFFIXES for path in EXACT10)
    for path in EXACT10:
        assert not _git("ls-files", "--error-unmatch", "--", path.as_posix(), check=False)
    status = _git("status", "--short", "--untracked-files=all").decode().splitlines()
    assert set(status) == {f"?? {path.as_posix()}" for path in EXACT10}
    assert _git("diff", "--cached", "--name-only") == b""
    assert _git("diff", "--name-only") == b""
    assert not any(
        path.name.endswith((".tmp", ".part", ".pyc"))
        for path in ROOT.rglob("*") if path.is_file()
    )
    assert not (ROOT / ".pytest_cache").exists()


def main() -> int:
    stats = verify_base_and_sources()
    verify_synthetic_graph_contract()
    verify_runtime_bypass_probes()
    verify_heavy_projection_and_canonical_identity()
    manifest_sha = verify_outputs(stats)
    if os.environ.get("COVAPIE_SKIP_CURRENT_TREE_BOUNDARY") != "1":
        verify_boundaries()
    print(f"BASE={BASE_COMMIT}")
    print("current11=11 unique_components=9 authoritative_components=0")
    print(
        f"supporting_parent_atoms={stats['parent_support_count']} "
        f"supporting_observed_retained_atoms={stats['observed_support_count']}"
    )
    print("authoritative_parent_atoms=0 parent_bonds=0 projected_bonds=0")
    print("graph_ready=0/11 bond_order_ready=0/11")
    print("failure_matrix=28/28_fail_closed")
    print("runtime_bypass_probes=verified")
    print("heavy_projection_and_canonical_identity=verified")
    print("reaction_family=0/11 approved_warhead_rule=0/11 role_seed=0/11 modules=0/5")
    print("ready_for_training=false")
    print("recommended_next_step=resolve_covapie_current11_pre_reaction_graph_authority_blockers_v1")
    print(f"manifest_sha256={manifest_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

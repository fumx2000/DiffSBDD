from __future__ import annotations

import csv
import dataclasses
import hashlib
import importlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_pre_reaction_graph_and_bond_order_authority_v1 as stage,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_covapie_current11_pre_reaction_graph_and_bond_order_authority_v1.py"
DOC = ROOT / "docs/covapie_current11_pre_reaction_graph_and_bond_order_authority_v1_summary.md"
EXACT10 = (
    ROOT / "src/covalent_ext/covapie_current11_pre_reaction_graph_and_bond_order_authority_v1.py",
    Path(__file__),
    CHECKER,
    DOC,
    *(ROOT / stage.OUTPUT_ROOT / name for name in stage.OUTPUT_FILES),
)


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode())))


def _base(path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{stage.BASE_COMMIT}:{path.as_posix()}"),
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout


def _synthetic():
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
    return atoms, bonds, observed


def _validate(atoms=None, bonds=None, observed=None, **kwargs):
    baseline = _synthetic()
    return stage.validate_graph_authority(
        atoms if atoms is not None else baseline[0],
        bonds if bonds is not None else baseline[1],
        observed if observed is not None else baseline[2],
        reactive_atom_id=kwargs.pop("reactive_atom_id", "C1"),
        leaving_group_atom_ids=kwargs.pop("leaving_group_atom_ids", ("F1",)),
        reaction_delta_class=kwargs.pop(
            "reaction_delta_class", "covalent_leaving_group_loss"
        ),
        parent_leaving_group_bond_verified=kwargs.pop(
            "parent_leaving_group_bond_verified", True
        ),
        atom_inventory_reconciliation_passed=kwargs.pop(
            "atom_inventory_reconciliation_passed", True
        ),
        **kwargs,
    )


def test_formal_base_identity() -> None:
    result = subprocess.run(
        ("git", "show", "-s", "--format=%H%n%P%n%T%n%s", stage.BASE_COMMIT),
        cwd=ROOT, text=True, stdout=subprocess.PIPE, check=True,
    ).stdout.splitlines()
    assert result == [
        stage.BASE_COMMIT, stage.BASE_PARENT, stage.BASE_TREE, stage.BASE_SUBJECT
    ]
    assert stage.FORMAL_COMMIT_SUBJECT == (
        "add CovaPIE current11 pre-reaction graph authority v1"
    )


def test_all_frozen_predecessor_sources_are_BASE_tracked_and_sha_bound() -> None:
    assert len(stage.FROZEN_SHA256) == 16
    for path, expected in stage.FROZEN_SHA256.items():
        payload = _base(path)
        assert hashlib.sha256(payload).hexdigest() == expected
        assert stage.base_bytes(ROOT, path) == payload


def test_current11_and_unique_component_count_are_evidence_derived() -> None:
    graph = _rows(_base(stage.GRAPH_EVIDENCE))
    assert len(graph) == 11
    observed_components = tuple(dict.fromkeys(row["ligand_comp_id"] for row in graph))
    assert observed_components == stage.CURRENT_COMPONENTS
    assert len(observed_components) == 9


def test_no_current_component_CCD_payload_is_BASE_tracked() -> None:
    for component in stage.CURRENT_COMPONENTS:
        path = stage.CCD_ROOT / f"{component}.cif"
        assert stage.base_path_tracked(ROOT, path) is False


def test_source_inventory_classifies_every_candidate_truthfully() -> None:
    rows = stage.build_source_inventory(ROOT)
    assert len(rows) == 25
    assert {row["authority_class"] for row in rows} <= {
        "authoritative", "supporting_only", "gap_evidence"
    }
    assert not any(row["authority_class"] == "authoritative" for row in rows)
    raw = [
        row for row in rows
        if row["source_kind"] == "untracked_CCD_path_attested_by_BASE_audit"
    ]
    assert len(raw) == 9
    assert all(
        row["BASE_tracked"] is False
        and row["atom_named"] is False
        and row["bond_order_present"] is False
        and "payload_not_read" in row["blocking_reason"]
        for row in raw
    )
    graph = next(row for row in rows if row["source_path"] == stage.GRAPH_EVIDENCE.as_posix())
    assert graph["atom_named"] is True
    assert graph["bond_order_present"] is False
    assert graph["authority_class"] == "supporting_only"


def test_empty_parent_and_bond_tables_are_explicit_not_zero_byte() -> None:
    payloads = stage.build_evidence_payloads(ROOT)
    assert _rows(payloads[stage.PARENT_ATOM_FILE]) == []
    assert _rows(payloads[stage.BOND_FILE]) == []
    assert payloads[stage.PARENT_ATOM_FILE].decode().strip() == ",".join(stage.ATOM_COLUMNS)
    assert payloads[stage.BOND_FILE].decode().strip() == ",".join(stage.BOND_COLUMNS)


def test_readiness_is_fail_closed_for_exact11() -> None:
    rows = stage.build_readiness(ROOT)
    assert len(rows) == 11
    assert all(row["descriptor_graph_support_present"] is True for row in rows)
    unavailable = (
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
    assert all(row[field] is False for row in rows for field in unavailable)


def test_zya_f1_is_not_deleted_or_falsely_materialized() -> None:
    graph = next(
        row for row in _rows(_base(stage.GRAPH_EVIDENCE))
        if row["ligand_comp_id"] == "ZYA"
    )
    assert graph["missing_parent_heavy_atom_ids"] == "F1"
    assert graph["leaving_group_atom_ids"] == "F1"
    assert graph["reaction_delta_class"] == "covalent_leaving_group_loss"
    readiness = next(
        row for row in stage.build_readiness(ROOT)
        if row["ligand_comp_id"] == "ZYA"
    )
    assert readiness["leaving_group_projection_valid"] is False
    assert "parent_CM_F1_bond_not_BASE_authority" in readiness["blocking_reasons"]
    assert stage.build_evidence_payloads(ROOT)[stage.PARENT_ATOM_FILE].count(b"F1") == 0


def test_ccd_parser_preserves_atom_names_rows_charge_and_bonds() -> None:
    text = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
CA C 0
NB N 1
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
CA NB DOUB N
#
"""
    atoms, bonds = stage.parse_ccd_component(text)
    assert atoms == (
        stage.ParentAtom("CA", "C", 0, 0),
        stage.ParentAtom("NB", "N", 1, 1),
    )
    assert bonds == (stage.ParentBond("CA", "NB", "DOUB", "N"),)


def test_ccd_parser_projects_explicit_hydrogens_to_heavy_graph_with_stats() -> None:
    text = """data_X
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
    atoms, bonds, stats = stage.parse_ccd_component_with_stats(text)
    assert atoms == (
        stage.ParentAtom("C1", "C", 0, 0),
        stage.ParentAtom("O1", "O", 0, 1),
    )
    assert bonds == (stage.ParentBond("C1", "O1", "DOUB", "N"),)
    assert stats == stage.CCDHeavyProjectionStats(
        source_atom_row_count=4,
        explicit_hydrogen_atom_count=2,
        heavy_atom_count=2,
        source_bond_row_count=3,
        hydrogen_involving_bond_count=2,
        heavy_heavy_bond_count=1,
    )
    assert stage.parse_ccd_component(text) == (atoms, bonds)


def test_ccd_parser_filters_deuterium_and_tritium_but_preserves_halogens() -> None:
    text = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
D1 D 0
T1 t 0
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
D1 F1 SING N
T1 I1 SING N
F1 CL1 SING N
CL1 BR1 SING N
BR1 I1 SING N
#
"""
    atoms, bonds, stats = stage.parse_ccd_component_with_stats(text)
    assert tuple((atom.atom_id, atom.type_symbol) for atom in atoms) == (
        ("F1", "F"), ("CL1", "CL"), ("BR1", "BR"), ("I1", "I")
    )
    assert tuple(atom.row_index_0based for atom in atoms) == (0, 1, 2, 3)
    assert len(bonds) == 3
    assert stats.explicit_hydrogen_atom_count == 2
    assert stats.heavy_atom_count == 4
    assert stats.hydrogen_involving_bond_count == 2
    assert stats.heavy_heavy_bond_count == 3


def test_ccd_parser_rejects_all_hydrogen_parent_graph() -> None:
    text = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
H1 H 0
D1 D 0
T1 T 0
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
H1 D1 SING N
#
"""
    with pytest.raises(ValueError, match="^parent_heavy_atom_table_empty$"):
        stage.parse_ccd_component(text)


@pytest.mark.parametrize(
    ("atom_row", "reason"),
    (
        ("'' C 0", "chem_comp_atom_id_missing_or_invalid"),
        ("'   ' C 0", "chem_comp_atom_id_missing_or_invalid"),
        ("C1 '' 0", "chem_comp_atom_type_symbol_missing_or_invalid"),
        ("C1 '   ' 0", "chem_comp_atom_type_symbol_missing_or_invalid"),
    ),
)
def test_ccd_parser_rejects_empty_atom_fields(
    atom_row: str, reason: str
) -> None:
    text = f"""data_X
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
    with pytest.raises(ValueError, match=f"^{reason}$"):
        stage.parse_ccd_component(text)


@pytest.mark.parametrize(
    ("bond_row", "reason"),
    (
        ("'' O1 SING N", "chem_comp_bond_atom_id_1_missing_or_invalid"),
        ("C1 '' SING N", "chem_comp_bond_atom_id_2_missing_or_invalid"),
        ("C1 O1 '' N", "chem_comp_bond_value_order_missing_or_invalid"),
        ("C1 O1 SING ''", "chem_comp_bond_aromatic_flag_missing_or_invalid"),
        ("C1 X1 SING N", "chem_comp_bond_endpoint_not_in_atom_loop"),
    ),
)
def test_ccd_parser_rejects_empty_bond_fields_and_unknown_endpoint(
    bond_row: str, reason: str
) -> None:
    text = f"""data_X
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
    with pytest.raises(ValueError, match=f"^{reason}$"):
        stage.parse_ccd_component(text)


def test_ccd_parser_fails_closed_on_missing_loops() -> None:
    with pytest.raises(ValueError, match="chem_comp_atom_loop_missing"):
        stage.parse_ccd_component("data_X\n#\n")
    atom_only = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
C1 C
#
"""
    with pytest.raises(ValueError, match="chem_comp_bond_loop_missing"):
        stage.parse_ccd_component(atom_only)


@pytest.mark.parametrize(("charge", "expected"), (("0", 0), ("1", 1), ("-1", -1)))
def test_ccd_parser_requires_and_preserves_exact_integer_charge(
    charge: str, expected: int
) -> None:
    text = f"""data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
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
    atoms, _ = stage.parse_ccd_component(text)
    assert atoms[0].formal_charge == expected
    assert type(atoms[0].formal_charge) is int


@pytest.mark.parametrize("charge", (".", "?", "invalid", "''"))
def test_ccd_parser_rejects_unknown_or_invalid_charge(charge: str) -> None:
    text = f"""data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
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
    with pytest.raises(
        ValueError, match="^chem_comp_atom_charge_missing_or_invalid$"
    ):
        stage.parse_ccd_component(text)


def test_ccd_parser_rejects_missing_charge_column_and_non_string_text() -> None:
    text = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
C1 C
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
C1 C1 SING N
#
"""
    with pytest.raises(
        ValueError, match="^chem_comp_atom_charge_missing_or_invalid$"
    ):
        stage.parse_ccd_component(text)
    with pytest.raises(ValueError, match="^ccd_text_type_invalid$"):
        stage.parse_ccd_component(b"data_X")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("source", "flag", "expected"),
    (("SING", "N", "single"), ("DOUB", "N", "double"),
     ("TRIP", "N", "triple"), ("AROM", "Y", "aromatic")),
)
def test_normalized_bond_order_closed_vocabulary(
    source: str, flag: str, expected: str
) -> None:
    assert stage.normalize_bond_order(source, flag) == expected
    assert expected in stage.NORMALIZED_BOND_ORDERS


def test_unsupported_and_aromatic_conflict_fail_closed() -> None:
    with pytest.raises(ValueError, match="unsupported_ccd_bond_order"):
        stage.normalize_bond_order("QUAD", "N")
    with pytest.raises(ValueError, match="aromatic_flag_order_conflict"):
        stage.normalize_bond_order("SING", "Y")
    with pytest.raises(ValueError, match="aromatic_flag_order_conflict"):
        stage.normalize_bond_order("AROM", "N")
    with pytest.raises(ValueError, match="bond_order_argument_type_invalid"):
        stage.normalize_bond_order(1, "N")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="bond_order_argument_empty"):
        stage.normalize_bond_order("", "N")


def test_exact_atom_name_projection_and_zya_style_leaving_group() -> None:
    result = _validate()
    assert result.valid
    assert result.reasons == ()
    assert result.projected_atom_count == 2
    assert result.projected_bond_count == 1
    assert result.parent_component_count == result.observed_component_count == 1


def test_element_and_exact_name_mapping_are_not_fuzzy() -> None:
    mismatch = _validate(observed=(
        stage.ObservedAtom("C1", "N", 0, 0),
        stage.ObservedAtom("O1", "O", 1, 1),
    ))
    assert "element_mismatch" in mismatch.reasons
    fuzzy = _validate(observed=(
        stage.ObservedAtom("c1", "C", 0, 0),
        stage.ObservedAtom("O1", "O", 1, 1),
    ))
    assert "sample_atom_not_in_ccd" in fuzzy.reasons
    assert "reactive_atom_absent_from_projection" in fuzzy.reasons


def test_duplicate_names_atoms_edges_self_loop_and_endpoint_fail_closed() -> None:
    atoms, bonds, observed = _synthetic()
    duplicate_atom = _validate(atoms=atoms + (dataclasses.replace(atoms[0]),))
    assert "duplicate_ccd_atom_id" in duplicate_atom.reasons
    duplicate_sample = _validate(observed=observed + (dataclasses.replace(observed[0]),))
    assert "duplicate_sample_atom_name" in duplicate_sample.reasons
    duplicate_edge = _validate(bonds=bonds + (stage.ParentBond("O1", "C1", "DOUB", "N"),))
    assert "duplicate_undirected_bond" in duplicate_edge.reasons
    self_loop = _validate(bonds=bonds + (stage.ParentBond("O1", "O1", "SING", "N"),))
    assert "bond_self_loop" in self_loop.reasons
    absent = _validate(bonds=bonds + (stage.ParentBond("O1", "X", "SING", "N"),))
    assert "bond_endpoint_absent" in absent.reasons


@pytest.mark.parametrize(
    ("atoms", "reason"),
    (
        ((stage.ParentAtom("C1", "C", True, 0),), "parent_formal_charge_type_invalid"),
        ((stage.ParentAtom("C1", "C", 0, False),), "parent_row_index_type_invalid"),
        ((stage.ParentAtom("C1", "C", 0, 0.0),), "parent_row_index_type_invalid"),
        ((stage.ParentAtom("", "C", 0, 0),), "parent_atom_id_empty"),
        ((stage.ParentAtom("C1", 6, 0, 0),), "parent_type_symbol_type_invalid"),
        (
            (
                stage.ParentAtom("C1", "C", 0, 0),
                stage.ParentAtom("O1", "O", 0, 0),
            ),
            "duplicate_ccd_atom_row_index",
        ),
        (
            (
                stage.ParentAtom("C1", "C", 0, 0),
                stage.ParentAtom("O1", "O", 0, 2),
            ),
            "ccd_atom_row_indices_not_contiguous",
        ),
        ((), "parent_atom_table_empty"),
    ),
)
def test_parent_atom_exact_field_and_row_index_contract(
    atoms: tuple[stage.ParentAtom, ...], reason: str
) -> None:
    result = stage.validate_graph_authority(
        atoms,
        (),
        (stage.ObservedAtom("C1", "C", 0, 0),),
        reactive_atom_id="C1",
    )
    assert not result.valid
    assert reason in result.reasons
    assert result.parent_graph_sha256 == result.observed_graph_sha256 == ""


def test_exact_dataclass_record_types_reject_dict_tuple_and_subclass() -> None:
    class ParentAtomSubclass(stage.ParentAtom):
        pass

    atoms, bonds, observed = _synthetic()
    cases = (
        (({"atom_id": "C1"},), bonds, observed, "parent_atom_record_type_invalid"),
        ((("C1", "C", 0, 0),), bonds, observed, "parent_atom_record_type_invalid"),
        ((ParentAtomSubclass("C1", "C", 0, 0),), bonds, observed, "parent_atom_record_type_invalid"),
        (atoms, ({"atom_id_1": "C1"},), observed, "parent_bond_record_type_invalid"),
        (atoms, bonds, ({"atom_name": "C1"},), "observed_atom_record_type_invalid"),
    )
    for parent_value, bond_value, observed_value, reason in cases:
        result = stage.validate_graph_authority(
            parent_value, bond_value, observed_value, reactive_atom_id="C1"
        )
        assert not result.valid
        assert reason in result.reasons
        assert result.parent_graph_sha256 == result.observed_graph_sha256 == ""


@pytest.mark.parametrize(
    ("bond", "reason"),
    (
        (stage.ParentBond(1, "O1", "SING", "N"), "parent_bond_atom_id_1_type_invalid"),
        (stage.ParentBond("", "O1", "SING", "N"), "parent_bond_atom_id_1_empty"),
        (stage.ParentBond("C1", 2, "SING", "N"), "parent_bond_atom_id_2_type_invalid"),
        (stage.ParentBond("C1", "O1", 1, "N"), "parent_bond_value_order_type_invalid"),
        (stage.ParentBond("C1", "O1", "SING", False), "parent_bond_aromatic_flag_type_invalid"),
    ),
)
def test_parent_bond_exact_field_contract(
    bond: stage.ParentBond, reason: str
) -> None:
    atoms, _, observed = _synthetic()
    result = stage.validate_graph_authority(
        atoms, (bond,), observed, reactive_atom_id="C1"
    )
    assert not result.valid
    assert reason in result.reasons
    assert result.parent_graph_sha256 == result.observed_graph_sha256 == ""


@pytest.mark.parametrize(
    ("observed", "reason"),
    (
        ((stage.ObservedAtom("C1", "C", False, 0),), "observed_source_row_index_type_invalid"),
        ((stage.ObservedAtom("C1", "C", 0, True),), "observed_retained_local_index_type_invalid"),
        ((stage.ObservedAtom("", "C", 0, 0),), "observed_atom_name_empty"),
        (
            (
                stage.ObservedAtom("C1", "C", 5, 0),
                stage.ObservedAtom("O1", "O", 5, 1),
            ),
            "duplicate_observed_source_row_index",
        ),
        (
            (
                stage.ObservedAtom("C1", "C", 5, 0),
                stage.ObservedAtom("O1", "O", 8, 0),
            ),
            "duplicate_observed_retained_local_index",
        ),
        (
            (
                stage.ObservedAtom("C1", "C", 5, 0),
                stage.ObservedAtom("O1", "O", 8, 2),
            ),
            "observed_retained_local_indices_not_contiguous",
        ),
        ((), "observed_atom_table_empty"),
    ),
)
def test_observed_atom_exact_fields_and_projection_indices(
    observed: tuple[stage.ObservedAtom, ...], reason: str
) -> None:
    atoms, bonds, _ = _synthetic()
    result = stage.validate_graph_authority(
        atoms, bonds, observed, reactive_atom_id="C1"
    )
    assert not result.valid
    assert reason in result.reasons
    assert result.parent_graph_sha256 == result.observed_graph_sha256 == ""


@pytest.mark.parametrize(
    ("which", "value", "reason"),
    (
        ("parent", set(), "parent_atom_container_invalid"),
        ("parent", frozenset(), "parent_atom_container_invalid"),
        ("parent", {}, "parent_atom_container_invalid"),
        ("parent", None, "parent_atom_container_invalid"),
        ("bond", iter(()), "parent_bond_container_invalid"),
        ("observed", {}, "observed_atom_container_invalid"),
        ("leaving", "F1", "leaving_group_container_invalid"),
    ),
)
def test_top_level_containers_fail_closed(
    which: str, value: object, reason: str
) -> None:
    atoms, bonds, observed = _synthetic()
    arguments = {
        "parent_atoms": atoms,
        "parent_bonds": bonds,
        "observed_atoms": observed,
        "leaving_group_atom_ids": ("F1",),
        "reactive_atom_id": "C1",
        "reaction_delta_class": "covalent_leaving_group_loss",
        "parent_leaving_group_bond_verified": True,
        "atom_inventory_reconciliation_passed": True,
    }
    arguments[{
        "parent": "parent_atoms",
        "bond": "parent_bonds",
        "observed": "observed_atoms",
        "leaving": "leaving_group_atom_ids",
    }[which]] = value
    result = stage.validate_graph_authority(**arguments)
    assert not result.valid
    assert reason in result.reasons
    assert result.parent_graph_sha256 == result.observed_graph_sha256 == ""


def test_generator_container_and_exact_other_argument_types_fail_closed() -> None:
    atoms, bonds, observed = _synthetic()
    generator_result = stage.validate_graph_authority(
        (atom for atom in atoms), bonds, observed, reactive_atom_id="C1"
    )
    assert generator_result.reasons == ("parent_atom_container_invalid",)
    cases = (
        ({"reactive_atom_id": 1}, "reactive_atom_id_type_invalid"),
        ({"reaction_delta_class": None}, "reaction_delta_class_type_invalid"),
        ({"parent_leaving_group_bond_verified": 1}, "parent_leaving_group_bond_verified_type_invalid"),
        ({"atom_inventory_reconciliation_passed": 1}, "atom_inventory_reconciliation_passed_type_invalid"),
        ({"rdkit_validation_passed": 1}, "rdkit_validation_passed_type_invalid"),
    )
    for overrides, reason in cases:
        arguments = {
            "reactive_atom_id": "C1",
            "leaving_group_atom_ids": ("F1",),
            "reaction_delta_class": "covalent_leaving_group_loss",
            "parent_leaving_group_bond_verified": True,
            "atom_inventory_reconciliation_passed": True,
            "rdkit_validation_passed": True,
        }
        arguments.update(overrides)
        result = stage.validate_graph_authority(atoms, bonds, observed, **arguments)
        assert not result.valid
        assert reason in result.reasons
        assert result.parent_graph_sha256 == result.observed_graph_sha256 == ""


def test_leaving_group_members_are_exact_unique_and_parent_bound() -> None:
    atoms, bonds, observed = _synthetic()
    for leaving, reason in (
        (("F1", "F1"), "duplicate_leaving_group_atom_id"),
        ((1,), "leaving_group_atom_id_type_invalid"),
        (("X",), "leaving_group_atom_not_in_parent"),
    ):
        result = stage.validate_graph_authority(
            atoms, bonds, observed, reactive_atom_id="C1",
            leaving_group_atom_ids=leaving,
            reaction_delta_class="covalent_leaving_group_loss",
            parent_leaving_group_bond_verified=True,
            atom_inventory_reconciliation_passed=True,
        )
        assert not result.valid
        assert reason in result.reasons
        assert result.parent_graph_sha256 == result.observed_graph_sha256 == ""


def test_leaving_group_parent_bond_is_reconstructed_not_trusted_from_bool() -> None:
    atoms, bonds, observed = _synthetic()
    passed = _validate()
    assert passed.valid
    missing_bond = _validate(bonds=(bonds[0],))
    assert not missing_bond.valid
    assert "leaving_group_parent_bond_missing" in missing_bond.reasons
    assert "parent_graph_disconnected" in missing_bond.reasons
    assert missing_bond.parent_graph_sha256 == missing_bond.observed_graph_sha256 == ""


def test_unsupported_bond_does_not_enter_connectivity_or_authority_sha() -> None:
    atoms, _, observed = _synthetic()
    result = _validate(bonds=(
        stage.ParentBond("C1", "O1", "DOUB", "N"),
        stage.ParentBond("C1", "F1", "QUAD", "N"),
    ))
    assert "unsupported_ccd_bond_order" in result.reasons
    assert "leaving_group_parent_bond_missing" in result.reasons
    assert "parent_graph_disconnected" in result.reasons
    assert result.parent_graph_sha256 == result.observed_graph_sha256 == ""


def test_unexplained_parent_missing_and_bad_leaving_list_fail_closed() -> None:
    unexplained = _validate(leaving_group_atom_ids=())
    assert "unexplained_parent_atom_missing" in unexplained.reasons
    inconsistent = _validate(leaving_group_atom_ids=("F1", "X"))
    assert "leaving_group_atom_not_in_parent" in inconsistent.reasons


def test_parent_and_observed_graph_sha_are_order_independent() -> None:
    atoms, bonds, observed = _synthetic()
    first = _validate()
    second = _validate(
        atoms=tuple(reversed(atoms)),
        bonds=tuple(reversed(bonds)),
        observed=tuple(reversed(observed)),
    )
    assert first.parent_graph_sha256 == second.parent_graph_sha256
    assert first.observed_graph_sha256 == second.observed_graph_sha256


def test_canonical_element_helper_and_case_independent_graph_sha() -> None:
    assert stage.canonicalize_element_symbol_v1(" c ") == "C"
    assert stage.canonicalize_element_symbol_v1("Cl") == "CL"
    with pytest.raises(ValueError, match="element_symbol_type_invalid"):
        stage.canonicalize_element_symbol_v1(6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="element_symbol_empty"):
        stage.canonicalize_element_symbol_v1("   ")
    atoms, bonds, observed = _synthetic()
    lowercase = stage.validate_graph_authority(
        tuple(
            dataclasses.replace(atom, type_symbol=atom.type_symbol.lower())
            for atom in atoms
        ),
        bonds,
        tuple(
            dataclasses.replace(atom, type_symbol=atom.type_symbol.lower())
            for atom in observed
        ),
        reactive_atom_id="C1",
        leaving_group_atom_ids=("F1",),
        reaction_delta_class="covalent_leaving_group_loss",
        parent_leaving_group_bond_verified=True,
        atom_inventory_reconciliation_passed=True,
    )
    uppercase = _validate()
    assert lowercase.valid == uppercase.valid is True
    assert lowercase.parent_graph_sha256 == uppercase.parent_graph_sha256
    assert lowercase.observed_graph_sha256 == uppercase.observed_graph_sha256


@pytest.mark.parametrize("symbol", stage.EXPLICIT_HYDROGEN_TYPE_SYMBOLS)
def test_public_parent_and_observed_explicit_hydrogen_injection_fails_closed(
    symbol: str,
) -> None:
    parent_result = stage.validate_graph_authority(
        (stage.ParentAtom("H1", symbol, 0, 0),),
        (),
        (stage.ObservedAtom("H1", symbol, 0, 0),),
        reactive_atom_id="H1",
    )
    assert "explicit_hydrogen_in_parent_graph" in parent_result.reasons
    assert "explicit_hydrogen_in_observed_graph" in parent_result.reasons
    assert parent_result.parent_graph_sha256 == parent_result.observed_graph_sha256 == ""
    observed_result = stage.validate_graph_authority(
        (stage.ParentAtom("C1", "C", 0, 0),),
        (),
        (stage.ObservedAtom("C1", symbol.lower(), 0, 0),),
        reactive_atom_id="C1",
    )
    assert "explicit_hydrogen_in_observed_graph" in observed_result.reasons
    assert observed_result.parent_graph_sha256 == observed_result.observed_graph_sha256 == ""


def test_rdkit_is_validation_only_and_failure_is_reported() -> None:
    result = _validate(rdkit_validation_passed=False)
    assert "rdkit_validation_failed" in result.reasons
    source = (ROOT / "src/covalent_ext/covapie_current11_pre_reaction_graph_and_bond_order_authority_v1.py").read_text()
    assert "RDKit_used_as_atom_name_authority" in source
    assert '"RDKit_used_as_atom_name_authority": False' in source


def test_scenario_baseline_and_exact_types() -> None:
    observed = stage.evaluate_authority_scenario(stage.BASELINE_SCENARIO)
    assert observed.valid
    assert observed.ready_for_reaction_family_rule_design
    assert not observed.ready_for_role_proposal_generation
    bad_bool = dataclasses.replace(stage.BASELINE_SCENARIO, ccd_source_present=1)
    assert stage.validate_scenario_types(bad_bool) == (
        "scenario_field_type_invalid:ccd_source_present",
    )
    bad_count = dataclasses.replace(stage.BASELINE_SCENARIO, unsupported_element_count=True)
    assert stage.validate_scenario_types(bad_count) == (
        "scenario_field_type_invalid:unsupported_element_count",
    )


def test_failure_matrix_uses_explicit_unique_dataclass_mutations() -> None:
    signatures = stage.validate_failure_registry()
    assert len(signatures) == len(set(signatures)) == 28
    rows = stage.build_failure_matrix()
    assert {row["failure_case"] for row in rows} == set(stage.FAILURE_MUTATIONS)
    assert all(
        row["expected_reasons_verified"] is True
        and row["fails_closed"] is True
        and row["ready_for_reaction_family_rule_design"] is False
        and row["ready_for_role_proposal_generation"] is False
        and row["ready_for_mask_materialization"] is False
        and row["ready_for_model_integration"] is False
        and row["ready_for_training"] is False
        for row in rows
    )
    for row in rows:
        mutation = json.loads(row["mutated_fields"])
        assert type(mutation) is dict and mutation
        assert row["mutated_fields"] == json.dumps(
            mutation, sort_keys=True, separators=(",", ":")
        )
        specification = stage.FAILURE_MUTATIONS[row["failure_case"]]
        assert mutation == specification["fields"]
        scenario = dataclasses.replace(stage.BASELINE_SCENARIO, **mutation)
        assert set(specification["expected_reasons"]) <= set(
            stage.evaluate_authority_scenario(scenario).reasons
        )


def test_runtime_bypass_probes_are_executed_not_manifest_only() -> None:
    assert stage.runtime_bypass_probes_verified() is True
    assert stage.heavy_projection_and_canonical_identity_probes_verified() is True


def test_descriptor_smiles_cannot_make_authority_ready() -> None:
    inventory = stage.build_source_inventory(ROOT)
    descriptor_rows = [
        row for row in inventory
        if row["source_kind"] in {
            "descriptor_graph_and_atom_inventory", "CCD_descriptor_metadata"
        }
    ]
    assert descriptor_rows
    assert all(row["authority_class"] == "supporting_only" for row in descriptor_rows)
    assert all(
        row["atom_named_graph_authority_present"] is False
        for row in stage.build_readiness(ROOT)
    )


def test_manifest_statistics_and_readiness_are_truthful() -> None:
    payloads = stage.build_evidence_payloads(ROOT)
    manifest = json.loads(payloads[stage.MANIFEST_FILE])
    assert manifest["current11_row_count"] == 11
    assert manifest["unique_ligand_component_count"] == 9
    assert manifest["current11_parent_heavy_atom_count_from_supporting_inventory"] == 324
    assert manifest["current11_observed_retained_heavy_atom_count_from_supporting_inventory"] == 323
    assert manifest["authoritative_parent_atom_row_count"] == 0
    assert manifest["authoritative_parent_bond_row_count"] == 0
    assert manifest["authoritative_observed_projected_bond_row_count"] == 0
    assert manifest["pre_reaction_connectivity_available_count"] == 0
    assert manifest["pre_reaction_bond_order_available_count"] == 0
    assert manifest["reaction_family_label_available_count"] == 0
    assert manifest["approved_warhead_rule_available_count"] == 0
    assert manifest["role_proposal_generation_ready_count"] == 0
    assert manifest["minimal_seed_proposal_generation_ready_count"] == 0
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert stage.MANIFEST_FILE not in manifest["evidence_sha256"]
    assert manifest["recommended_next_step"].endswith("authority_blockers_v1")
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


def test_all_evidence_is_byte_deterministic_and_matches_files() -> None:
    first = stage.build_evidence_payloads(ROOT)
    second = stage.build_evidence_payloads(ROOT)
    assert first == second
    assert set(first) == set(stage.OUTPUT_FILES)
    for name, payload in first.items():
        assert (ROOT / stage.OUTPUT_ROOT / name).read_bytes() == payload


def test_import_is_silent_and_side_effect_free(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        (
            sys.executable, "-B", "-c",
            "import covalent_ext.covapie_current11_pre_reaction_graph_and_bond_order_authority_v1",
        ),
        cwd=tmp_path, env=environment, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == b""
    assert list(tmp_path.iterdir()) == []


def test_exact10_scope_and_safety() -> None:
    assert len(EXACT10) == len(set(EXACT10)) == 10
    assert all(path.is_file() and not path.is_symlink() for path in EXACT10)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part"}
    assert not any(path.suffix.lower() in forbidden for path in EXACT10)
    source = EXACT10[0].read_text()
    assert "urllib" not in source
    assert "requests" not in source
    assert "torch" not in source
    assert "optimizer" not in source
    assert "backward(" not in source


def test_checker_constants_match_stage() -> None:
    spec = importlib.util.spec_from_file_location("current11_graph_checker", CHECKER)
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    assert checker.BASE_COMMIT == stage.BASE_COMMIT
    assert checker.FORMAL_COMMIT_SUBJECT == stage.FORMAL_COMMIT_SUBJECT
    assert tuple(path.resolve() for path in checker.EXACT10) == tuple(
        path.relative_to(ROOT).resolve() if not path.is_absolute() else path.resolve()
        for path in EXACT10
    )

from __future__ import annotations

import copy
import gzip
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
import torch

from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as ffq_successor,
)
from covalent_ext import covapie_ffq_real_structure_microbatch_alignment_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
ATOM_SITE_COLUMNS = (
    "_atom_site.group_PDB",
    "_atom_site.id",
    "_atom_site.type_symbol",
    "_atom_site.label_atom_id",
    "_atom_site.label_alt_id",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_seq_id",
    "_atom_site.Cartn_x",
    "_atom_site.Cartn_y",
    "_atom_site.Cartn_z",
    "_atom_site.occupancy",
    "_atom_site.auth_seq_id",
    "_atom_site.auth_comp_id",
    "_atom_site.auth_asym_id",
    "_atom_site.auth_atom_id",
    "_atom_site.pdbx_PDB_ins_code",
    "_atom_site.pdbx_PDB_model_num",
)
TARGET_ATOMS = (
    ("N", "N"),
    ("CA", "C"),
    ("C", "C"),
    ("O", "O"),
    ("CB", "C"),
    ("SG", "S"),
)
LIGAND_ORDER_0 = ("O3", "C2", "P1", "O1", "C1", "O4", "C3", "O2")
LIGAND_ORDER_1_WITH_H = (
    "H1", "O2", "C3", "O4", "C1", "O1", "P1", "C2", "O3"
)


def _record(pdb_id: str) -> dict[str, Any]:
    event_id = (
        "COVAPIE_CYS_SG_EVENT_V1:3VCY:A:CYS:116-:SG:E:FFQ:C1"
        if pdb_id == "3VCY"
        else "COVAPIE_CYS_SG_EVENT_V1:4R7U:A:CYS:116-:SG:F:FFQ:C1"
    )
    return ffq_successor._expected_record(
        {
            "canonical_event_id": event_id,
            "pdb_id": pdb_id,
            "completed_lane": (
                "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                if pdb_id == "3VCY"
                else "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
            ),
        }
    )


def _symbol(atom_id: str) -> str:
    if atom_id.startswith("H"):
        return "H"
    return atom_id[0]


def _row(
    *,
    group: str,
    atom_id: str,
    symbol: str,
    component: str,
    label_asym: str,
    label_seq: str,
    auth_asym: str,
    auth_seq: str,
    xyz: tuple[float, float, float],
    insertion: str = ".",
    altloc: str = ".",
) -> dict[str, str]:
    return {
        "_atom_site.group_PDB": group,
        "_atom_site.id": "",
        "_atom_site.type_symbol": symbol,
        "_atom_site.label_atom_id": atom_id,
        "_atom_site.label_alt_id": altloc,
        "_atom_site.label_comp_id": component,
        "_atom_site.label_asym_id": label_asym,
        "_atom_site.label_seq_id": label_seq,
        "_atom_site.Cartn_x": f"{xyz[0]:.3f}",
        "_atom_site.Cartn_y": f"{xyz[1]:.3f}",
        "_atom_site.Cartn_z": f"{xyz[2]:.3f}",
        "_atom_site.occupancy": "1.00",
        "_atom_site.auth_seq_id": auth_seq,
        "_atom_site.auth_comp_id": component,
        "_atom_site.auth_asym_id": auth_asym,
        "_atom_site.auth_atom_id": atom_id,
        "_atom_site.pdbx_PDB_ins_code": insertion,
        "_atom_site.pdbx_PDB_model_num": "1",
    }


def _payload(
    pdb_id: str,
    *,
    ligand_order: tuple[str, ...],
    extra_before_target: int,
    extra_after_target: int = 0,
    pocket_hydrogen: bool = False,
    unsupported_pocket_symbol: str | None = None,
    duplicate_sg: bool = False,
    omit_sg: bool = False,
    entry_id: str | None = None,
    base_override: float | None = None,
    whole_residue_far_atom: bool = False,
    cutoff_probe: str | None = None,
    near_nonstandard: bool = False,
    selected_residue_altloc_ab: bool = False,
    target_sg_altloc_ab: bool = False,
    far_altloc_b: bool = False,
) -> bytes:
    base = (
        base_override
        if base_override is not None
        else (10.0 if pdb_id == "3VCY" else 30.0)
    )
    ligand_asym = "E" if pdb_id == "3VCY" else "F"
    rows: list[dict[str, str]] = []

    for index in range(extra_before_target):
        rows.append(
            _row(
                group="ATOM",
                atom_id=f"X{index}",
                symbol=(unsupported_pocket_symbol if index == 0 else "C") or "C",
                component="ALA",
                label_asym="A",
                label_seq=str(100 + index),
                auth_asym="A",
                auth_seq=str(100 + index),
                xyz=(base + 1.0, base + 0.1 * index, base),
            )
        )
        if index == 0 and whole_residue_far_atom:
            rows.append(
                _row(
                    group="ATOM",
                    atom_id="X_FAR",
                    symbol="C",
                    component="ALA",
                    label_asym="A",
                    label_seq="100",
                    auth_asym="A",
                    auth_seq="100",
                    xyz=(base + 9.0, base, base),
                )
            )
    if selected_residue_altloc_ab:
        for altloc, delta in (("A", 0.0), ("B", 0.1)):
            rows.append(
                _row(
                    group="ATOM",
                    atom_id="ALT",
                    symbol="C",
                    component="ALA",
                    label_asym="A",
                    label_seq="170",
                    auth_asym="A",
                    auth_seq="170",
                    xyz=(base + 0.4 + delta, base, base),
                    altloc=altloc,
                )
            )
    for index, (atom_id, symbol) in enumerate(TARGET_ATOMS):
        if atom_id == "SG" and omit_sg:
            continue
        rows.append(
            _row(
                group="ATOM",
                atom_id=atom_id,
                symbol=symbol,
                component="CYS",
                label_asym="A",
                label_seq="116",
                auth_asym="A",
                auth_seq="116",
                xyz=(base + 1.0 + 0.1 * index, base, base),
                altloc=("A" if target_sg_altloc_ab and atom_id == "SG" else "."),
            )
        )
    if target_sg_altloc_ab:
        rows.append(
            _row(
                group="ATOM",
                atom_id="SG",
                symbol="S",
                component="CYS",
                label_asym="A",
                label_seq="116",
                auth_asym="A",
                auth_seq="116",
                xyz=(base + 1.55, base, base),
                altloc="B",
            )
        )
    if duplicate_sg:
        rows.append(
            _row(
                group="ATOM",
                atom_id="SG",
                symbol="S",
                component="CYS",
                label_asym="A",
                label_seq="116",
                auth_asym="A",
                auth_seq="116",
                xyz=(base + 1.7, base, base),
            )
        )
    for index in range(extra_after_target):
        rows.append(
            _row(
                group="ATOM",
                atom_id=f"Y{index}",
                symbol="N",
                component="GLY",
                label_asym="A",
                label_seq=str(130 + index),
                auth_asym="A",
                auth_seq=str(130 + index),
                xyz=(base + 0.5, base + 0.1 * index, base),
            )
        )
    if pocket_hydrogen:
        rows.append(
            _row(
                group="ATOM",
                atom_id="HPOC",
                symbol="H",
                component="ALA",
                label_asym="A",
                label_seq="140",
                auth_asym="A",
                auth_seq="140",
                xyz=(base + 0.3, base, base),
            )
        )
    if cutoff_probe is not None:
        if cutoff_probe not in {"exact", "inside"}:
            raise ValueError("unknown cutoff probe")
        ligand_x_max = base + 0.1 * max(
            index
            for index, atom_id in enumerate(ligand_order)
            if not atom_id.startswith("H")
        )
        distance = 8.0 if cutoff_probe == "exact" else 7.999
        rows.append(
            _row(
                group="ATOM",
                atom_id="CUT",
                symbol="C",
                component="SER",
                label_asym="A",
                label_seq="150",
                auth_asym="A",
                auth_seq="150",
                xyz=(ligand_x_max + distance, base, base),
            )
        )
    if near_nonstandard:
        rows.append(
            _row(
                group="ATOM",
                atom_id="MSE_C",
                symbol="C",
                component="MSE",
                label_asym="A",
                label_seq="160",
                auth_asym="A",
                auth_seq="160",
                xyz=(base + 0.2, base, base),
            )
        )
    if far_altloc_b:
        rows.append(
            _row(
                group="ATOM",
                atom_id="FARB",
                symbol="C",
                component="ALA",
                label_asym="A",
                label_seq="180",
                auth_asym="A",
                auth_seq="180",
                xyz=(base + 20.0, base + 20.0, base),
                altloc="B",
            )
        )
    rows.append(
        _row(
            group="ATOM",
            atom_id="FAR",
            symbol="C",
            component="GLY",
            label_asym="A",
            label_seq="999",
            auth_asym="A",
            auth_seq="999",
            xyz=(base + 20.0, base, base),
        )
    )
    for index, atom_id in enumerate(ligand_order):
        rows.append(
            _row(
                group="HETATM",
                atom_id=atom_id,
                symbol=_symbol(atom_id),
                component="FFQ",
                label_asym=ligand_asym,
                label_seq=".",
                auth_asym="A",
                auth_seq="501",
                xyz=(base + 0.1 * index, base, base),
            )
        )
    for index, row in enumerate(rows, start=1):
        row["_atom_site.id"] = str(index)

    lines = [
        f"data_{entry_id or pdb_id}",
        f"_entry.id {entry_id or pdb_id}",
        "#",
        "loop_",
        *ATOM_SITE_COLUMNS,
    ]
    lines.extend(" ".join(row[column] for column in ATOM_SITE_COLUMNS) for row in rows)
    lines.append("#")
    return gzip.compress(("\n".join(lines) + "\n").encode("utf-8"), mtime=0)


def _sample(
    pdb_id: str,
    task_id: int = 0,
    **payload_overrides: object,
) -> dict[str, object]:
    defaults: dict[str, object] = {
        "ligand_order": (
            LIGAND_ORDER_0 if pdb_id == "3VCY" else LIGAND_ORDER_1_WITH_H
        ),
        "extra_before_target": 0 if pdb_id == "3VCY" else 3,
        "extra_after_target": 2 if pdb_id == "3VCY" else 0,
    }
    defaults.update(payload_overrides)
    return {
        "cif_gz_payload": _payload(pdb_id, **defaults),
        "effective_supervision_record": _record(pdb_id),
        "canonical_task_id": task_id,
    }


def _build(
    task0: int = 0,
    task1: int = 0,
    *,
    samples: list[dict[str, object]] | None = None,
) -> subject.FFQRealStructureMicrobatchAlignmentV1:
    return subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=(
            [_sample("3VCY", task0), _sample("4R7U", task1)]
            if samples is None
            else samples
        )
    )


def _heavy_order(sample_ordinal: int) -> tuple[str, ...]:
    source = LIGAND_ORDER_0 if sample_ordinal == 0 else LIGAND_ORDER_1_WITH_H
    return tuple(atom_id for atom_id in source if not atom_id.startswith("H"))


def test_public_result_is_structural_only_and_has_exact_model_batch_schema() -> None:
    result = _build()
    assert set(result.model_input_batch) == {
        "lig_coords", "pocket_coords", "lig_one_hot", "pocket_one_hot",
        "lig_source_row_index", "pocket_source_row_index",
        "lig_parser_local_index", "pocket_parser_local_index",
        "num_lig_atoms", "num_pocket_nodes", "lig_mask", "pocket_mask",
    }
    assert result.structural_coordinates_centered is True
    assert result.model_forward is False
    assert result.training_performed is False


def test_batch_size_two_has_different_source_parser_lengths_and_pocket_counts() -> None:
    result = _build()
    assert result.model_input_batch["num_lig_atoms"].tolist() == [8, 8]
    assert result.model_input_batch["num_pocket_nodes"].tolist() == [8, 9]
    assert result.model_input_batch["lig_source_row_index"][8].item() > 8


def test_exact10_shapes_dtypes_and_one_hot_values() -> None:
    batch = _build().model_input_batch
    assert batch["lig_coords"].shape == (16, 3)
    assert batch["pocket_coords"].shape == (17, 3)
    assert batch["lig_coords"].dtype == batch["pocket_coords"].dtype == torch.float32
    assert batch["lig_one_hot"].shape == (16, 10)
    assert batch["pocket_one_hot"].shape == (17, 10)
    assert torch.equal(batch["lig_one_hot"].sum(1), torch.ones(16))
    assert torch.equal(batch["pocket_one_hot"].sum(1), torch.ones(17))


def test_ligand_and_pocket_offsets_are_explicit_prefix_sums() -> None:
    result = _build()
    assert result.ligand_node_offsets == (0, 8, 16)
    assert result.pocket_node_offsets == (0, 8, 17)


def test_flattened_membership_masks_match_offsets() -> None:
    batch = _build().model_input_batch
    assert batch["lig_mask"].tolist() == [0] * 8 + [1] * 8
    assert batch["pocket_mask"].tolist() == [0] * 8 + [1] * 9
    assert batch["lig_mask"].dtype == batch["pocket_mask"].dtype == torch.long


def test_target_cys_membership_covers_all_retained_atoms_per_sample() -> None:
    result = _build()
    mask = result.target_residue_membership_mask.squeeze(1)
    assert mask[:8].sum().item() == 6
    assert mask[8:].sum().item() == 6
    assert result.target_reactive_local_indices.tolist() == [5, 8]


def test_target_sg_is_exact_one_per_sample_and_uses_sulfur_channel() -> None:
    result = _build()
    reactive = result.target_residue_reactive_atom_mask.squeeze(1)
    assert reactive[:8].sum().item() == reactive[8:].sum().item() == 1
    channels = result.model_input_batch["pocket_one_hot"].argmax(1)
    assert channels[result.target_reactive_flat_indices].tolist() == [3, 3]


def test_ligand_c1_mapping_uses_identity_not_local_zero() -> None:
    result = _build()
    assert result.ligand_reactive_local_indices.tolist() == [4, 3]
    assert result.ligand_reactive_local_indices.tolist() != [0, 0]


def test_sample_local_to_flat_positive_pairs_apply_second_offsets() -> None:
    result = _build()
    assert result.positive_pair_batch_indices.tolist() == [0, 1]
    assert result.positive_pair_ligand_local_indices.tolist() == [4, 3]
    assert result.positive_pair_pocket_local_indices.tolist() == [5, 8]
    assert result.positive_pair_ligand_flat_indices.tolist() == [4, 11]
    assert result.positive_pair_pocket_flat_indices.tolist() == [5, 16]
    assert result.positive_pair_ligand_flat_indices[1].item() != 3
    assert result.positive_pair_pocket_flat_indices[1].item() != 8


def test_positive_pairs_never_cross_sample_membership() -> None:
    result = _build()
    batch = result.model_input_batch
    assert torch.equal(
        batch["lig_mask"][result.positive_pair_ligand_flat_indices],
        result.positive_pair_batch_indices,
    )
    assert torch.equal(
        batch["pocket_mask"][result.positive_pair_pocket_flat_indices],
        result.positive_pair_batch_indices,
    )


def test_task_A_sidecars_follow_the_exact_ligand_batch_order() -> None:
    result = _build(0, 0)
    expected = [
        atom_id in {"C1", "C2", "C3", "O1"}
        for sample in range(2)
        for atom_id in _heavy_order(sample)
    ]
    assert result.ligand_generation_mask.squeeze(1).tolist() == expected
    assert result.ligand_fixed_mask.squeeze(1).tolist() == [not x for x in expected]
    assert torch.equal(result.ligand_target_mask, result.ligand_generation_mask)
    assert torch.equal(result.ligand_context_mask, result.ligand_fixed_mask)


def test_task_B3_sidecars_generate_scaffold_and_fix_warhead() -> None:
    result = _build(3, 3)
    expected = [
        atom_id in {"O2", "O3", "O4", "P1"}
        for sample in range(2)
        for atom_id in _heavy_order(sample)
    ]
    assert result.canonical_task_ids.tolist() == [3, 3]
    assert result.ligand_generation_mask.squeeze(1).tolist() == expected
    assert result.ligand_fixed_mask.squeeze(1).tolist() == [not x for x in expected]


def test_task_C_structural_roles_exist_but_seed_and_full_supervision_do_not() -> None:
    result = _build(4, 4)
    assert result.canonical_task_ids.tolist() == [4, 4]
    assert result.ligand_generation_mask.all()
    assert not result.ligand_fixed_mask.any()
    assert result.task_C_role_mask_supported.tolist() == [True, True]
    assert result.task_C_minimal_seed_supervision_available.tolist() == [False, False]
    assert result.full_task_C_training_supervision_ready.tolist() == [False, False]


@pytest.mark.parametrize("task_id", [1, 2])
def test_tasks_B_and_B2_fail_closed_as_not_applicable(task_id: int) -> None:
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match="TASK_NOT_APPLICABLE",
    ):
        _build(task_id, 0)


def test_unsupported_nonhydrogen_in_model_bound_pocket_rejects_whole_sample() -> None:
    bad = _sample(
        "3VCY", unsupported_pocket_symbol="Zn", extra_before_target=1,
        extra_after_target=0,
    )
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match="POCKET_EXACT10_SAMPLE_REJECTED:0:unsupported_nonhydrogen",
    ):
        _build(samples=[bad, _sample("4R7U")])


def test_ligand_explicit_hydrogen_projection_preserves_source_to_local_remap() -> None:
    result = _build()
    source = result.model_input_batch["lig_source_row_index"][8:16]
    parser = result.model_input_batch["lig_parser_local_index"][8:16]
    assert len(source) == 8
    assert parser.tolist() == list(range(8))
    assert result.ligand_reactive_local_indices[1].item() == 3
    assert source.tolist() == sorted(source.tolist())


def test_pocket_explicit_hydrogen_is_removed_before_local_index_assignment() -> None:
    sample0 = _sample("3VCY", pocket_hydrogen=True)
    result = _build(samples=[sample0, _sample("4R7U")])
    assert result.model_input_batch["num_pocket_nodes"].tolist() == [8, 9]
    assert result.model_input_batch["pocket_parser_local_index"][:8].tolist() == list(range(8))


def test_checkpoint_pocket_keeps_far_atom_from_a_residue_with_one_close_atom() -> None:
    sample0 = _sample(
        "3VCY",
        extra_before_target=1,
        extra_after_target=0,
        whole_residue_far_atom=True,
    )
    result = _build(samples=[sample0])
    assert result.model_input_batch["num_pocket_nodes"].tolist() == [8]
    assert result.model_input_batch["pocket_source_row_index"].tolist()[:2] == [0, 1]


def test_checkpoint_cutoff_is_strictly_less_than_eight_angstrom() -> None:
    exact = _sample(
        "3VCY", extra_before_target=0, extra_after_target=0,
        cutoff_probe="exact",
    )
    inside = _sample(
        "3VCY", extra_before_target=0, extra_after_target=0,
        cutoff_probe="inside",
    )
    exact_result = _build(samples=[exact])
    inside_result = _build(samples=[inside])
    assert exact_result.model_input_batch["num_pocket_nodes"].tolist() == [6]
    assert inside_result.model_input_batch["num_pocket_nodes"].tolist() == [7]


def test_near_nonstandard_residue_is_not_checkpoint_pocket_eligible() -> None:
    sample0 = _sample(
        "3VCY", extra_before_target=0, extra_after_target=0,
        near_nonstandard=True,
    )
    result = _build(samples=[sample0])
    assert result.model_input_batch["num_pocket_nodes"].tolist() == [6]


def test_checkpoint_relevant_standard_residue_altloc_A_B_fails_closed() -> None:
    sample0 = _sample("3VCY", selected_residue_altloc_ab=True)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match="CHECKPOINT_POCKET_ALTLOC_SEMANTICS_AMBIGUOUS_V1",
    ):
        _build(samples=[sample0])


def test_target_cys_sg_altloc_A_B_fails_before_exact_one_mapping() -> None:
    sample0 = _sample("3VCY", target_sg_altloc_ab=True)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match="CHECKPOINT_POCKET_ALTLOC_SEMANTICS_AMBIGUOUS_V1",
    ):
        _build(samples=[sample0])


def test_far_away_standard_residue_altloc_B_does_not_block_or_enter_pocket() -> None:
    sample0 = _sample("3VCY", far_altloc_b=True)
    result = _build(samples=[sample0])
    assert result.model_input_batch["num_pocket_nodes"].tolist() == [8]
    assert 8 not in result.model_input_batch["pocket_source_row_index"].tolist()


def test_input_order_permutation_recomputes_offsets_and_preserves_local_semantics() -> None:
    forward = _build()
    reverse = _build(samples=[_sample("4R7U"), _sample("3VCY")])
    assert reverse.sample_identities == tuple(reversed(forward.sample_identities))
    assert reverse.pocket_node_offsets == (0, 9, 17)
    assert reverse.ligand_reactive_local_indices.tolist() == [3, 4]
    assert reverse.target_reactive_local_indices.tolist() == [8, 5]
    assert reverse.ligand_reactive_flat_indices.tolist() == [3, 12]
    assert reverse.target_reactive_flat_indices.tolist() == [8, 14]


def test_4r7u_exclusion_is_preserved_and_neither_sample_is_admitted() -> None:
    result = _build()
    assert result.human_training_exclusion_preserved.tolist() == [False, True]
    assert result.sample_training_admitted.tolist() == [False, False]


def test_geometry_and_warhead_type_training_boundaries_remain_unavailable() -> None:
    result = _build()
    assert result.geometry_target_available.tolist() == [False, False]
    assert result.warhead_type_target_available.tolist() == [False, False]


def test_single_sample_coordinates_use_joint_ligand_pocket_centering() -> None:
    result = _build()
    lig = result.model_input_batch["lig_coords"]
    pocket = result.model_input_batch["pocket_coords"]
    assert torch.allclose(
        torch.cat((lig[:8], pocket[:8])).mean(0),
        torch.zeros(3),
        atol=2e-6,
    )
    assert result.structural_coordinates_centered is True


def test_two_samples_are_centered_independently_not_as_one_batch() -> None:
    result = _build()
    batch = result.model_input_batch
    residuals = []
    for sample in range(2):
        coordinates = torch.cat(
            (
                batch["lig_coords"][batch["lig_mask"] == sample],
                batch["pocket_coords"][batch["pocket_mask"] == sample],
            )
        )
        residuals.append(coordinates.mean(0))
    assert all(torch.allclose(value, torch.zeros(3), atol=3e-6) for value in residuals)


def test_per_sample_centering_removes_translation_without_changing_identities() -> None:
    first = _sample("3VCY", base_override=10.0)
    translated = _sample("3VCY", base_override=100.0)
    result = _build(samples=[first, translated])
    batch = result.model_input_batch
    assert torch.allclose(batch["lig_coords"][:8], batch["lig_coords"][8:], atol=1e-5)
    assert torch.allclose(batch["pocket_coords"][:8], batch["pocket_coords"][8:], atol=1e-5)
    assert result.ligand_reactive_local_indices.tolist() == [4, 4]
    assert result.target_reactive_local_indices.tolist() == [5, 5]
    assert torch.equal(result.ligand_role_id[:8], result.ligand_role_id[8:])


def test_duplicate_target_sg_fails_closed() -> None:
    bad = _sample("3VCY", duplicate_sg=True)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match="TARGET_RESIDUE_REACTIVE_ATOM_NOT_EXACTLY_ONE",
    ):
        _build(samples=[bad, _sample("4R7U")])


def test_missing_target_sg_fails_closed() -> None:
    bad = _sample("3VCY", omit_sg=True)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match="TARGET_RESIDUE_REACTIVE_ATOM_NOT_EXACTLY_ONE",
    ):
        _build(samples=[bad, _sample("4R7U")])


def test_mmcif_entry_identity_mismatch_fails_closed() -> None:
    bad = _sample("3VCY", entry_id="9XYZ")
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match="MMCIF_ENTRY_EVENT_PDB_MISMATCH",
    ):
        _build(samples=[bad, _sample("4R7U")])


def test_deterministic_double_build_is_tensor_and_metadata_identical() -> None:
    first = _build()
    second = _build()
    assert first.sample_identities == second.sample_identities
    assert first.ligand_node_offsets == second.ligand_node_offsets
    assert first.pocket_node_offsets == second.pocket_node_offsets
    for key in first.model_input_batch:
        assert torch.equal(first.model_input_batch[key], second.model_input_batch[key])
    for field in (
        "ligand_role_id", "ligand_role_valid", "ligand_generation_mask",
        "ligand_fixed_mask", "target_residue_membership_mask",
        "target_residue_reactive_atom_mask", "target_reactive_flat_indices",
        "ligand_reactive_flat_indices", "positive_pair_batch_indices",
    ):
        assert torch.equal(getattr(first, field), getattr(second, field))


def test_single_sample_supported_without_hard_coded_batch_size_two() -> None:
    result = _build(samples=[_sample("3VCY")])
    assert result.ligand_node_offsets == (0, 8)
    assert result.pocket_node_offsets == (0, 8)
    assert result.positive_pair_batch_indices.tolist() == [0]


def test_import_has_no_stdout_stderr_or_filesystem_writes(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "src")))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import covalent_ext.covapie_ffq_real_structure_microbatch_alignment_v1",
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_unknown_sample_fields_fail_closed() -> None:
    bad = copy.deepcopy(_sample("3VCY"))
    bad["path"] = "must-not-be-consumed"
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match="SAMPLE_0_FIELDS_INVALID",
    ):
        _build(samples=[bad])

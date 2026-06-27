from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence, TypedDict

import torch

MaskType = Literal["A", "B", "B2", "C"]
LongFormMaskLevel = Literal[
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
]


class ProteinPocket(TypedDict, total=False):
    coords: Sequence[Sequence[float]]
    one_hot: Sequence[Sequence[float]]
    atom_names: Sequence[str]
    residue_ids: Sequence[str]
    residue_types: Sequence[str]


class LigandBond(TypedDict):
    atom1: int
    atom2: int
    bond_type: str


class PreReactionLigandGraph(TypedDict, total=False):
    atom_symbols: Sequence[str]
    bonds: Sequence[LigandBond]
    atom_names: Sequence[str]
    formal_charges: Sequence[int]


@dataclass(frozen=True)
class CovalentSample:
    protein_pocket: ProteinPocket
    pre_reaction_ligand_graph: PreReactionLigandGraph
    post_covalent_ligand_coords: Sequence[Sequence[float]]
    reactive_residue_type: str
    reactive_residue_id: str
    reactive_atom_name: str
    reactive_atom_coord: Sequence[float]
    warhead_type: str
    ligand_reactive_atom_id: int
    covalent_bond_atom_pair: tuple[str, int]
    scaffold_atoms: Sequence[int]
    linker_atoms: Sequence[int]
    warhead_atoms: Sequence[int]
    mask_type: MaskType


@dataclass(frozen=True)
class MaskResult:
    visible_atoms: tuple[int, ...]
    masked_atoms: tuple[int, ...]
    mask_type: str
    lig_fixed: torch.Tensor

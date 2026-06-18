from __future__ import annotations

from collections.abc import Sequence

import torch

from covalent_ext.schema import MaskResult, MaskType


def _normalize_atom_indices(name: str, atoms: Sequence[int], num_ligand_atoms: int) -> tuple[int, ...]:
    out = tuple(int(atom) for atom in atoms)
    invalid = [atom for atom in out if atom < 0 or atom >= num_ligand_atoms]
    if invalid:
        raise ValueError(f"{name} contains atom indices outside [0, {num_ligand_atoms}): {invalid}")
    if len(set(out)) != len(out):
        raise ValueError(f"{name} contains duplicate atom indices: {out}")
    return out


def _validate_partition(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    if num_ligand_atoms <= 0:
        raise ValueError("num_ligand_atoms must be positive")

    scaffold = _normalize_atom_indices("scaffold_atoms", scaffold_atoms, num_ligand_atoms)
    linker = _normalize_atom_indices("linker_atoms", linker_atoms, num_ligand_atoms)
    warhead = _normalize_atom_indices("warhead_atoms", warhead_atoms, num_ligand_atoms)

    seen: dict[int, str] = {}
    overlaps: list[str] = []
    for group_name, group_atoms in (
        ("scaffold_atoms", scaffold),
        ("linker_atoms", linker),
        ("warhead_atoms", warhead),
    ):
        for atom in group_atoms:
            if atom in seen:
                overlaps.append(f"{atom} in {seen[atom]} and {group_name}")
            seen[atom] = group_name
    if overlaps:
        raise ValueError("atom groups must be disjoint: " + "; ".join(overlaps))

    return scaffold, linker, warhead


def make_mask_result(mask_type: MaskType, visible_atoms: Sequence[int], num_ligand_atoms: int) -> MaskResult:
    visible = tuple(sorted(int(atom) for atom in visible_atoms))
    all_atoms = set(range(num_ligand_atoms))
    visible_set = set(visible)
    if len(visible_set) != len(visible):
        raise ValueError(f"visible_atoms contains duplicates: {visible}")
    if not visible_set.issubset(all_atoms):
        invalid = sorted(visible_set - all_atoms)
        raise ValueError(f"visible_atoms contains atom indices outside [0, {num_ligand_atoms}): {invalid}")

    masked = tuple(atom for atom in range(num_ligand_atoms) if atom not in visible_set)
    lig_fixed = torch.zeros(num_ligand_atoms, dtype=torch.long)
    if visible:
        lig_fixed[list(visible)] = 1

    return MaskResult(
        visible_atoms=visible,
        masked_atoms=masked,
        mask_type=mask_type,
        lig_fixed=lig_fixed,
    )


def build_four_level_mask(
    mask_type: MaskType,
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    scaffold, linker, warhead = _validate_partition(
        scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms
    )

    if mask_type == "A":
        visible_atoms = scaffold + linker
    elif mask_type == "B":
        visible_atoms = scaffold
    elif mask_type == "B2":
        visible_atoms = linker + warhead
    elif mask_type == "C":
        visible_atoms = ()
    else:
        raise ValueError(f"unsupported mask_type: {mask_type}")

    return make_mask_result(mask_type, visible_atoms, num_ligand_atoms)


def mask_warhead(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_four_level_mask("A", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


def mask_linker_and_warhead(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_four_level_mask("B", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


def mask_scaffold(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_four_level_mask("B2", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


def mask_whole_ligand(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_four_level_mask("C", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


MASK_BUILDERS = {
    "A": mask_warhead,
    "B": mask_linker_and_warhead,
    "B2": mask_scaffold,
    "C": mask_whole_ligand,
}


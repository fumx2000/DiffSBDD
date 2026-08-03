from __future__ import annotations

from collections.abc import Callable, Sequence

import torch

from covalent_ext.schema import CanonicalMaskSemantic, LongFormMaskLevel, MaskResult


CANONICAL_MASK_SEMANTICS: tuple[CanonicalMaskSemantic, ...] = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

CANONICAL_MASK_SEMANTIC_TO_LEVEL: dict[
    CanonicalMaskSemantic, LongFormMaskLevel
] = {
    "warhead_only": "A_warhead_only",
    "linker_plus_warhead": "B_linker_warhead",
    "scaffold_plus_warhead": "B2_scaffold_warhead",
    "scaffold_only": "B3_scaffold_only",
    "scaffold_plus_linker_plus_warhead": "C_scaffold_linker_warhead",
}

_CANONICAL_MASK_SEMANTIC_ERROR = "COVAPIE_CANONICAL_MASK_SEMANTIC_INVALID"


LONG_FORM_MASK_COMPONENTS: dict[LongFormMaskLevel, dict[str, tuple[str, ...]]] = {
    "A_warhead_only": {"target": ("warhead",), "context": ("scaffold", "linker")},
    "B_linker_warhead": {"target": ("linker", "warhead"), "context": ("scaffold",)},
    "B2_scaffold_warhead": {"target": ("scaffold", "warhead"), "context": ("linker",)},
    "B3_scaffold_only": {"target": ("scaffold",), "context": ("linker", "warhead")},
    "C_scaffold_linker_warhead": {"target": ("scaffold", "linker", "warhead"), "context": ()},
}


def _normalize_atom_indices(name: str, atoms: Sequence[int] | None, num_ligand_atoms: int) -> tuple[int, ...]:
    if atoms is None:
        raise ValueError(f"{name} is missing")
    out = tuple(int(atom) for atom in atoms)
    invalid = [atom for atom in out if atom < 0 or atom >= num_ligand_atoms]
    if invalid:
        raise ValueError(f"{name} contains atom indices outside [0, {num_ligand_atoms}): {invalid}")
    if len(set(out)) != len(out):
        raise ValueError(f"{name} contains duplicate atom indices: {out}")
    return out


def _validate_partition(
    scaffold_atoms: Sequence[int] | None,
    linker_atoms: Sequence[int] | None,
    warhead_atoms: Sequence[int] | None,
    num_ligand_atoms: int,
    require_nonempty_regions: bool = False,
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
    if require_nonempty_regions:
        empty = [
            name
            for name, group_atoms in (
                ("scaffold_atoms", scaffold),
                ("linker_atoms", linker),
                ("warhead_atoms", warhead),
            )
            if not group_atoms
        ]
        if empty:
            raise ValueError("atom groups must be nonempty for long-form masks: " + ", ".join(empty))

    return scaffold, linker, warhead


def make_mask_result(
    mask_type: LongFormMaskLevel,
    visible_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
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


def resolve_canonical_mask_semantic(
    mask_semantic: object,
) -> LongFormMaskLevel:
    if (
        type(mask_semantic) is not str
        or mask_semantic not in CANONICAL_MASK_SEMANTIC_TO_LEVEL
    ):
        raise ValueError(_CANONICAL_MASK_SEMANTIC_ERROR)
    return CANONICAL_MASK_SEMANTIC_TO_LEVEL[mask_semantic]


def _atoms_for_components(
    components: Sequence[str],
    scaffold: Sequence[int],
    linker: Sequence[int],
    warhead: Sequence[int],
) -> tuple[int, ...]:
    groups = {
        "scaffold": tuple(scaffold),
        "linker": tuple(linker),
        "warhead": tuple(warhead),
    }
    atoms: list[int] = []
    for component in components:
        atoms.extend(groups[component])
    return tuple(atoms)


def build_long_form_mask(
    mask_level: LongFormMaskLevel,
    scaffold_atoms: Sequence[int] | None,
    linker_atoms: Sequence[int] | None,
    warhead_atoms: Sequence[int] | None,
    num_ligand_atoms: int,
) -> MaskResult:
    if mask_level not in LONG_FORM_MASK_COMPONENTS:
        raise ValueError(f"unsupported mask_level: {mask_level}")
    scaffold, linker, warhead = _validate_partition(
        scaffold_atoms,
        linker_atoms,
        warhead_atoms,
        num_ligand_atoms,
        require_nonempty_regions=True,
    )
    context_components = LONG_FORM_MASK_COMPONENTS[mask_level]["context"]
    visible_atoms = _atoms_for_components(context_components, scaffold, linker, warhead)
    return make_mask_result(mask_level, visible_atoms, num_ligand_atoms)


def build_canonical_mask(
    *,
    mask_semantic: object,
    scaffold_atoms: Sequence[int] | None,
    linker_atoms: Sequence[int] | None,
    warhead_atoms: Sequence[int] | None,
    num_ligand_atoms: int,
) -> MaskResult:
    level = resolve_canonical_mask_semantic(mask_semantic)
    return build_long_form_mask(
        level,
        scaffold_atoms,
        linker_atoms,
        warhead_atoms,
        num_ligand_atoms,
    )


def mask_warhead_long_form(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_long_form_mask("A_warhead_only", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


def mask_linker_and_warhead_long_form(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_long_form_mask("B_linker_warhead", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


def mask_scaffold_and_warhead_long_form(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_long_form_mask("B2_scaffold_warhead", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


def mask_scaffold_only_long_form(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_long_form_mask("B3_scaffold_only", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


def mask_whole_ligand_long_form(
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    num_ligand_atoms: int,
) -> MaskResult:
    return build_long_form_mask("C_scaffold_linker_warhead", scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms)


LONG_FORM_MASK_BUILDERS: dict[LongFormMaskLevel, Callable[[Sequence[int], Sequence[int], Sequence[int], int], MaskResult]] = {
    "A_warhead_only": mask_warhead_long_form,
    "B_linker_warhead": mask_linker_and_warhead_long_form,
    "B2_scaffold_warhead": mask_scaffold_and_warhead_long_form,
    "B3_scaffold_only": mask_scaffold_only_long_form,
    "C_scaffold_linker_warhead": mask_whole_ligand_long_form,
}

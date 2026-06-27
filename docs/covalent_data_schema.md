# Covalent-ready Data Schema

This extension keeps the original DiffSBDD model and diffusion code unchanged.
It adds a data-layer convention for covalent-ready ligand reconstruction and
inpainting.

## Sample Fields

Each covalent-ready sample should contain these fields:

| Field | Type | Description |
| --- | --- | --- |
| `protein_pocket` | structured object | Pocket atoms or residues used as the protein context. This should remain compatible with DiffSBDD's pocket representation: coordinates, one-hot features, size, and batch mask. |
| `pre_reaction_ligand_graph` | structured object | Ligand graph before covalent bond formation. This is the chemical target graph: atom symbols, bonds, optional atom names, and optional charges. |
| `post_covalent_ligand_coords` | list of `[x, y, z]` | Ligand coordinates in a post-covalent-compatible pose. These coordinates are used as the coordinate reference for masked reconstruction. |
| `reactive_residue_type` | string | Residue type for the covalent residue, for example `CYS`. |
| `reactive_residue_id` | string | Residue identifier, for example `A:279`. |
| `reactive_atom_name` | string | Protein atom name participating in the covalent reaction, for example `SG`. |
| `reactive_atom_coord` | `[x, y, z]` | Coordinate of the protein reactive atom. |
| `warhead_type` | string | Warhead class or label, for example `acrylamide`, `chloroacetamide`, or dataset-specific tags. |
| `ligand_reactive_atom_id` | integer | Atom index in the pre-reaction ligand graph that reacts with the protein atom. |
| `covalent_bond_atom_pair` | pair | Pair identifying the protein reactive atom and ligand reactive atom. A minimal representation is `[reactive_residue_id:reactive_atom_name, ligand_reactive_atom_id]`. |
| `scaffold_atoms` | list of integers | Ligand atom indices assigned to the scaffold region. |
| `linker_atoms` | list of integers | Ligand atom indices assigned to the linker region. |
| `warhead_atoms` | list of integers | Ligand atom indices assigned to the warhead region. |
| `mask_type` | string | Legacy short mask token, one of `A`, `B`, `B2`, or `C`. Downstream tensor/batch paths use canonical long-form `mask_level` names listed below. |

## Legacy Short Mask Semantics

The legacy short API in `src/covalent_ext/masking.py` remains available for
backward compatibility. It is intentionally not reinterpreted when long-form
mask levels are added.

| Mask | Masked atoms | Visible/fixed atoms |
| --- | --- | --- |
| `A` | `warhead_atoms` | `scaffold_atoms + linker_atoms` |
| `B` | `linker_atoms + warhead_atoms` | `scaffold_atoms` |
| `B2` | `scaffold_atoms` | `linker_atoms + warhead_atoms` |
| `C` | all ligand atoms | none |

## Canonical Long-Form Mask Semantics

The canonical downstream mask levels are long-form names. These names are used
by tensor materialization, batch adapter, and masked-loss smoke evidence.

| Mask level | Target/masked atoms | Context/visible atoms | Use case |
| --- | --- | --- | --- |
| `A_warhead_only` | `warhead_atoms` | `scaffold_atoms + linker_atoms` | warhead replacement |
| `B_linker_warhead` | `linker_atoms + warhead_atoms` | `scaffold_atoms` | grow linker and warhead from known scaffold |
| `B2_scaffold_warhead` | `scaffold_atoms + warhead_atoms` | `linker_atoms` | co-design scaffold and warhead around linker geometry |
| `B3_scaffold_only` | `scaffold_atoms` | `linker_atoms + warhead_atoms` | scaffold hopping with fixed linker-warhead geometry |
| `C_scaffold_linker_warhead` | `scaffold_atoms + linker_atoms + warhead_atoms` | none | de novo full covalent ligand generation |

`B3_scaffold_only` is additive. It does not rename or replace
`B2_scaffold_warhead`.

The resulting `lig_fixed` vector follows DiffSBDD inpainting semantics:

- `1` means the atom is visible and fixed.
- `0` means the atom is masked and should be generated.
- Shape should be `[num_ligand_atoms]` for one ligand, matching the vector form
  accepted by `inpaint.py` before it is unsqueezed by diffusion code.

## Coordinate Assumption

The project should not assume true pre-covalent poses exist. The chemical graph
target is `pre_reaction_ligand_graph`, while ligand coordinates come from
`post_covalent_ligand_coords`.

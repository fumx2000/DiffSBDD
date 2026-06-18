# KRAS_G12C_5F2E Ligand Annotation Instructions

This note is for manually filling
`data/raw/covalent_small/metadata/KRAS_G12C_5F2E_5UT_annotation_template.csv`.
Do not write these roles into `manifest_real_small.csv` until the annotation has
passed the template checker and the manifest row generator.

## Known Reactive Atom

- PDB ID: `5F2E`.
- Ligand residue: `5UT A 204`.
- Reactive protein residue: `CYS A 12`.
- Protein reactive atom: `SG`.
- PDB ligand reactive atom: `C15`.
- Mapped SDF ligand reactive atom index: `29`.

Atom `29` must be assigned `final_role = warhead` because it is the ligand
reactive atom candidate mapped from PDB atom `C15`.

## Allowed Final Roles

The `final_role` column may contain only:

- `scaffold`
- `linker`
- `warhead`
- `unassigned`
- empty

Use `unassigned` or leave `final_role` empty when the chemistry is uncertain.
Record the uncertainty in the `notes` column instead of forcing a scaffold,
linker, or warhead assignment.

## Consistency Rules

- `scaffold`, `linker`, and `warhead` atom sets must not overlap.
- `warhead_atoms` must contain `ligand_reactive_atom_id = 29`.
- `scaffold`, `linker`, and `warhead` should each be non-empty before creating
  a manifest row.
- Run `scripts/print_annotation_roles.py` after manual edits to inspect the role
  counts.
- Run `scripts/manifest_row_from_annotation.py` only after the final roles are
  complete enough to create a manifest row.

## Current SDF Limitation

`data/raw/covalent_small/ligands/KRAS_G12C_5F2E_5UT.sdf` was extracted from PDB
HETATM and CONECT records. It is useful for the current workflow smoke test and
for post-covalent-compatible bound geometry inspection.

It should not be treated as the final scientific training ligand graph. PDB
CONECT records do not provide reliable bond order, and the pre-reaction ligand
graph may need to be restored or replaced before training data is used for
scientific modeling.

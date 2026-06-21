# BTK_C481_6DI9 Curation Notes

- PDB ID: `6DI9`
- Candidate sample ID: `BTK_C481_6DI9`
- Target: BTK C481
- Protein PDB path:
  `data/raw/covalent_small/proteins/BTK_C481_6DI9.pdb`
- Ligand residue: `GJJ A 701`
- Reactive residue: `CYS A 481`
- Protein reactive atom: `SG`
- PDB ligand reactive atom from LINK record: `C33`
- SDF ligand reactive atom index from mapping CSV: `19`

## Current Ligand Files

- Extracted ligand SDF:
  `data/raw/covalent_small/ligands/BTK_C481_6DI9_GJJ.sdf`
- Atom mapping CSV:
  `data/raw/covalent_small/metadata/BTK_C481_6DI9_GJJ_atom_mapping.csv`

## Extraction Summary

`GJJ A 701` was extracted from the PDB HETATM records using
`scripts/extract_pdb_ligand_to_sdf.py`.

- Extracted atom count: `33`
- Intra-ligand CONECT bonds written to SDF: `35`
- PDB atom `C33` maps to SDF atom index `19`
- PDB LINK records:
  - `CYS A 481 SG` altloc `A` <-> `GJJ A 701 C33`
  - `CYS A 481 SG` altloc `B` <-> `GJJ A 701 C33`

The raw PDB contains two CYS481 SG alternate positions:

```text
ATOM    658  SG ACYS A 481
ATOM    659  SG BCYS A 481
```

Both are connected to `GJJ A 701 C33` in LINK/CONECT records.

## Important Limitations

The current GJJ SDF was extracted from PDB HETATM coordinates and PDB CONECT
records. It should be treated as post-covalent-compatible bound geometry for
workflow testing.

PDB CONECT records do not provide reliable bond order. The extracted SDF may
therefore contain placeholder single bonds and must not be treated as the final
pre-reaction ligand graph for scientific training.

Do not fill `manifest_real_small.csv` yet. The sample still needs GJJ CCD /
ideal reference graph download, graph comparison, annotation template
generation, and manual scaffold/linker/warhead role curation.

## Next Manual Steps

- Download/check GJJ CCD CIF and ideal SDF reference files.
- Compare extracted GJJ graph against the GJJ reference graph.
- Confirm whether SDF atom index `19` should be the ligand reactive atom in the
  final selected ligand SDF.
- Generate a GJJ annotation template only after reference graph checks.
- Assign scaffold/linker/warhead roles manually before producing a manifest row.

## Reference Files and Annotation Aids

Reference and helper files are stored under:

- `data/raw/covalent_small/metadata/6DI9_reference/`
- `data/raw/covalent_small/metadata/BTK_C481_6DI9_GJJ_annotation_template.csv`
- `data/raw/covalent_small/metadata/BTK_C481_6DI9_GJJ_annotation_report.csv`
- `data/raw/covalent_small/metadata/BTK_C481_6DI9_GJJ_atom_indices.svg`

Downloaded reference files:

- `6DI9.cif`: RCSB mmCIF for the full 6DI9 structure.
- `GJJ.cif`: RCSB Chemical Component Dictionary definition for ligand `GJJ`.
- `GJJ_ideal.sdf`: RCSB ideal CCD ligand SDF.

Optional model-coordinate ligand downloads were attempted but were not
available from RCSB:

- `GJJ_model.sdf`: 404 Not Found.
- `GJJ_model.mol2`: 404 Not Found.

## Reference Graph Comparison

Extracted GJJ SDF:

- Atom count: `33`
- Bond count: `35`
- Element count: `C:24; N:6; O:3`
- Bond order summary: `single:35`
- Aromatic atom count reported by RDKit: `0`

GJJ ideal/reference SDF:

- Atom count: `63`
- Bond count: `65`
- Element count: `C:24; H:30; N:6; O:3`
- Bond order summary: `aromatic:12; double:4; single:49`
- Aromatic atom count reported by RDKit: `12`

Main differences:

- The reference ideal SDF includes `30` explicit hydrogens; the extracted SDF
  has no hydrogens.
- The extracted SDF has all intra-ligand CONECT bonds written as single bonds,
  so aromatic and double bond information is lost.
- The ideal/reference graph is useful for manual chemistry review, but its atom
  order must not be copied directly into the manifest.

For the reactive atom:

- Extracted SDF atom `19` maps to PDB atom `C33`.
- Simple element+graph matching did not produce a unique reference candidate
  because extracted bond orders are degraded to single bonds.
- Heavy-atom order gives a tentative reference atom `19`, with reference local
  graph `18:C:double; 51:H:single; 52:H:single`.
- This correspondence is tentative only. Final manifest atom indices must come
  from the final selected `ligand_sdf` atom order.

## Annotation Status

The GJJ annotation template marks SDF atom `19` as
`warhead_candidate / ligand_reactive_atom_candidate`.

No `final_role` values have been filled. The CYS481 `SG` altloc A/B issue must
remain documented during manual curation because both altlocs are linked to
`GJJ C33`. The next step is manual scaffold/linker/warhead assignment, aided by
the atom-index SVG and annotation report. Do not write `manifest_real_small.csv`
until those roles are checked.

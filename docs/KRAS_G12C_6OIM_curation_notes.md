# KRAS_G12C_6OIM Curation Notes

- PDB ID: `6OIM`
- Candidate sample ID: `KRAS_G12C_6OIM`
- Target: KRAS G12C
- Protein PDB path:
  `data/raw/covalent_small/proteins/KRAS_G12C_6OIM.pdb`
- Ligand residue: `MOV A 303`
- Reactive residue: `CYS A 12`
- Protein reactive atom: `SG`
- PDB ligand reactive atom from LINK record: `C25`
- SDF ligand reactive atom index from mapping CSV: `7`

## Current Ligand Files

- Extracted ligand SDF:
  `data/raw/covalent_small/ligands/KRAS_G12C_6OIM_MOV.sdf`
- Atom mapping CSV:
  `data/raw/covalent_small/metadata/KRAS_G12C_6OIM_MOV_atom_mapping.csv`

## Extraction Summary

`MOV A 303` was extracted from the PDB HETATM records using
`scripts/extract_pdb_ligand_to_sdf.py`.

- Extracted atom count: `41`
- Intra-ligand CONECT bonds written to SDF: `45`
- PDB atom `C25` maps to SDF atom index `7`
- PDB LINK: `CYS A 12 SG <-> MOV A 303 C25`

## Important Limitations

The current MOV SDF was extracted from PDB HETATM coordinates and PDB CONECT
records. It should be treated as post-covalent-compatible bound geometry for
workflow testing.

PDB CONECT records do not provide reliable bond order. The extracted SDF may
therefore contain placeholder single bonds and must not be treated as the final
pre-reaction ligand graph for scientific training.

Do not fill `manifest_real_small.csv` yet. The sample still needs MOV CCD /
ideal reference graph download, graph comparison, annotation template
generation, and manual scaffold/linker/warhead role curation.

## Next Manual Steps

- Download/check MOV CCD CIF and ideal SDF reference files.
- Compare extracted MOV graph against the MOV reference graph.
- Confirm whether SDF atom index `7` should be the ligand reactive atom in the
  final selected ligand SDF.
- Generate a MOV annotation template only after reference graph checks.
- Assign scaffold/linker/warhead roles manually before producing a manifest row.

## Reference Files and Annotation Aids

Reference and helper files are stored under:

- `data/raw/covalent_small/metadata/6OIM_reference/`
- `data/raw/covalent_small/metadata/KRAS_G12C_6OIM_MOV_annotation_template.csv`
- `data/raw/covalent_small/metadata/KRAS_G12C_6OIM_MOV_annotation_report.csv`
- `data/raw/covalent_small/metadata/KRAS_G12C_6OIM_MOV_atom_indices.svg`

Downloaded reference files:

- `6OIM.cif`: RCSB mmCIF for the full 6OIM structure.
- `MOV.cif`: RCSB Chemical Component Dictionary definition for ligand `MOV`.
- `MOV_ideal.sdf`: RCSB ideal CCD ligand SDF.

Optional model-coordinate ligand downloads were attempted but were not
available from RCSB:

- `MOV_model.sdf`: 404 Not Found.
- `MOV_model.mol2`: 404 Not Found.

## Reference Graph Comparison

Extracted MOV SDF:

- Atom count: `41`
- Bond count: `45`
- Element count: `C:30; F:2; N:6; O:3`
- Bond order summary: `single:45`
- Aromatic atom count reported by RDKit: `0`

MOV ideal/reference SDF:

- Atom count: `73`
- Bond count: `77`
- Element count: `C:30; F:2; H:32; N:6; O:3`
- Bond order summary: `aromatic:23; double:2; single:52`
- Aromatic atom count reported by RDKit: `22`

Main differences:

- The reference ideal SDF includes `32` explicit hydrogens; the extracted SDF
  has no hydrogens.
- The extracted SDF has all intra-ligand CONECT bonds written as single bonds,
  so aromatic and double bond information is lost.
- The ideal/reference graph is useful for manual chemistry review, but its atom
  order must not be copied directly into the manifest.

For the reactive atom:

- Extracted SDF atom `7` maps to PDB atom `C25`.
- Simple element+graph matching did not produce a unique reference candidate
  because extracted bond orders are degraded to single bonds.
- Heavy-atom order gives a tentative reference atom `7`, with reference local
  graph `6:C:single; 49:H:single; 50:H:single; 51:H:single`.
- This correspondence is tentative only. Final manifest atom indices must come
  from the final selected `ligand_sdf` atom order.

## Annotation Status

The MOV annotation template marks SDF atom `7` as
`warhead_candidate / ligand_reactive_atom_candidate`.

No `final_role` values have been filled. The next step is manual
scaffold/linker/warhead assignment, aided by the atom-index SVG and annotation
report. Do not write `manifest_real_small.csv` until those roles are checked.

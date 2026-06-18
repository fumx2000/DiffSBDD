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

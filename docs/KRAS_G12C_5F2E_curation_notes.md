# KRAS_G12C_5F2E Curation Notes

- PDB ID: 5F2E
- Candidate sample ID: `KRAS_G12C_5F2E`
- Target: KRAS G12C
- Ligand residue: `5UT A 204`
- Reactive residue: `CYS A 12`
- Protein reactive atom: `SG`
- PDB ligand reactive atom from LINK record: `C15`
- SDF ligand reactive atom index from mapping CSV: `29`

## Current Ligand Files

- Extracted ligand SDF:
  `data/raw/covalent_small/ligands/KRAS_G12C_5F2E_5UT.sdf`
- Atom mapping CSV:
  `data/raw/covalent_small/metadata/KRAS_G12C_5F2E_5UT_atom_mapping.csv`
- Annotation template:
  `data/raw/covalent_small/metadata/KRAS_G12C_5F2E_5UT_annotation_template.csv`

## Important Limitations

The current SDF was extracted from PDB HETATM coordinates and PDB CONECT
records. It should be treated as post-covalent-compatible bound geometry for
workflow testing.

PDB CONECT records do not provide reliable bond order. The extracted SDF may
therefore contain placeholder single bonds and should not be treated as the
final pre-reaction ligand graph for scientific training.

Do not fill `manifest_real_small.csv` until the ligand graph and
scaffold/linker/warhead atom annotations are manually checked.

## Next Manual Steps

- Confirm whether the extracted ligand SDF needs replacement with a curated
  RCSB/CovPDB/CovBinder/exported SDF.
- Confirm the pre-reaction ligand graph and bond orders.
- Confirm `ligand_reactive_atom_id = 29`.
- Fill `final_role` in the annotation template for scaffold/linker/warhead.
- Transfer confirmed atom groups into `manifest_real_small.csv`.

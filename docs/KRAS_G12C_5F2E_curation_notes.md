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

## Reference Files for Bond-Order / Pre-Reaction Graph Curation

Reference files are stored under
`data/raw/covalent_small/metadata/5F2E_reference/`.

- `5F2E.cif`: RCSB mmCIF for the full 5F2E structure.
- `5UT.cif`: RCSB Chemical Component Dictionary definition for ligand `5UT`.
- `5UT_ideal.sdf`: RCSB ideal CCD ligand SDF.
- `5UT_model.sdf` and `5UT_model.mol2`: optional RCSB model-coordinate
  ligand files if available from RCSB.

The extracted ligand SDF remains limited by PDB HETATM coordinates and PDB
CONECT records. CONECT is useful for connectivity but does not encode reliable
bond order, so the extracted SDF should not be used as the final scientific
training graph without curation.

The CCD CIF and ideal SDF can help confirm the ligand chemistry, warhead
substructure, and likely bond orders for a pre-reaction graph. These reference
files may use a different atom order from the extracted SDF. Final manifest atom
indices must always come from the final selected `ligand_sdf` atom order; do not
copy ideal/reference SDF atom indices directly into the manifest.

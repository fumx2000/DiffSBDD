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

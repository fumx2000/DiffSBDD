# Small Real Covalent Curation Log

Use one section per real sample. Do not add a sample to
`manifest_real_small.csv` until the source files and atom annotations have been
checked.

## Template

### sample_id

- Source database or paper:
- PDB ID / accession:
- Protein file path:
- Ligand file path:
- Reactive residue:
- Protein reactive atom:
- Ligand reactive atom:
- Warhead type:
- Scaffold/linker/warhead atom annotation rationale:
- Uncertainties:

## KRAS_G12C_5F2E

- Source database or paper: RCSB PDB entry 5F2E; KRAS G12C covalent inhibitor structure.
- PDB ID / accession: 5F2E.
- Protein file path: `data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb`.
- Ligand file path: `data/raw/covalent_small/ligands/KRAS_G12C_5F2E_5UT.sdf`.
- Reactive residue: `CYS A 12`.
- Protein reactive atom: `SG`.
- Ligand reactive atom: PDB atom `C15`; mapped candidate SDF atom index `29`.
- Warhead type: KRAS G12C covalent inhibitor electrophile; final label requires manual confirmation.
- Scaffold/linker/warhead atom annotation rationale: pending manual annotation in `KRAS_G12C_5F2E_5UT_annotation_template.csv`.
- Uncertainties: Current ligand SDF was extracted from PDB HETATM + CONECT and represents post-covalent-compatible bound geometry. PDB CONECT does not encode reliable bond order; extracted SDF bonds may be placeholder single bonds. Do not treat this as the final pre-reaction ligand graph without manual curation.

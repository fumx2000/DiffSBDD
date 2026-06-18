# First Real Covalent Samples Plan

The first real covalent set should contain only 3-5 manually curated examples.
This step is for careful sample selection and annotation, not full-database
ingestion.

## Selection Criteria

- Prefer CYS covalent complexes.
- The ligand structure must be clear, with an SDF available or reliably
  exportable from the source structure.
- The covalent bond atom pair must be clear: protein reactive atom and ligand
  reactive atom.
- The warhead type must be clear from the ligand chemistry or source
  annotation.
- The protein reactive residue numbering must be clear and traceable to the PDB
  file used in the manifest.
- Prefer small-molecule, drug-like ligands.
- Avoid cofactors, large peptides, protein crosslinks, glycans, metals, and
  complex post-translational modifications in the first batch.
- Use only 3-5 examples in the first pass. Do not attempt full CovPDB,
  CovBinder, or PDB-wide ingestion.

## Candidate Curation Workflow

1. Identify a candidate from CovPDB, CovBinder, PDB, or a covalent inhibitor
   paper.
2. Save the curated protein PDB under
   `data/raw/covalent_small/proteins/`.
3. Save the curated ligand SDF under
   `data/raw/covalent_small/ligands/`.
4. Confirm the reactive residue chain, residue number, residue type, and
   protein reactive atom.
5. Confirm the ligand reactive atom index in the SDF atom order.
6. Assign scaffold, linker, and warhead atom indices.
7. Record rationale and uncertainties in
   `data/raw/covalent_small/metadata/curation_log.md`.
8. Add the row to
   `data/raw/covalent_small/manifests/manifest_real_small.csv`.
9. Run `scripts/check_manifest_real_small.py`.
10. Build processed JSONL with `scripts/build_covalent_real_small.py`.
11. Run processed-data QA with `scripts/check_covalent_real_small.py`.

## Current Status

`manifest_real_small.csv` intentionally contains only the header until real
PDB/SDF files and manual annotations are available. No pseudo-real example
should be described as a real covalent sample.

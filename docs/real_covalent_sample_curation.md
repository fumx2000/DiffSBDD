# Real Covalent Sample Curation

This guide describes the manual curation process for a small real covalent
dataset. It deliberately avoids bulk download or automatic database ingestion.

## Source Selection

Choose a small number of real covalent complexes from trusted sources such as:

- CovPDB
- CovBinder
- PDB entries with clearly annotated covalent ligands
- Supporting information from covalent inhibitor papers

For each selected complex, record the source database, accession/PDB ID, paper
or URL, and any assumptions made during curation under
`data/raw/covalent_small/metadata/`.

## Raw Files

For each sample:

1. Save the protein structure as a PDB file under
   `data/raw/covalent_small/proteins/`.
2. Save the ligand as an SDF file under
   `data/raw/covalent_small/ligands/`.
3. Make sure the ligand atom order in the SDF is the atom order used for all
   ligand atom index annotations.

## Manual Annotations

Fill a manifest under `data/raw/covalent_small/manifests/` using the template:

```text
manifest_real_small_template.csv
```

For each sample, manually confirm:

- `reactive_residue_chain`
- `reactive_residue_id`
- `reactive_residue_type`, for example `CYS`
- `reactive_atom_name`, for example `SG`
- `ligand_reactive_atom_id`
- `warhead_type`
- `scaffold_atoms`
- `linker_atoms`
- `warhead_atoms`

The scaffold/linker/warhead atom indices must be zero-based ligand SDF atom
indices. The ligand reactive atom should be inside `warhead_atoms`.

## Processing Flow

Run the manifest checker first:

```bash
/home/fmx_25111030037/bin/micromamba run -r /home/fmx_25111030037/micromamba -n covdiff python scripts/check_manifest_real_small.py --manifest data/raw/covalent_small/manifests/<manifest>.csv
```

Then build processed JSONL:

```bash
/home/fmx_25111030037/bin/micromamba run -r /home/fmx_25111030037/micromamba -n covdiff python scripts/build_covalent_real_small.py --manifest data/raw/covalent_small/manifests/<manifest>.csv --output data/processed/covalent_real_small.jsonl
```

Then run processed-data QA:

```bash
/home/fmx_25111030037/bin/micromamba run -r /home/fmx_25111030037/micromamba -n covdiff python scripts/check_covalent_real_small.py --input data/processed/covalent_real_small.jsonl
```

## Important Warning

The existing `manifest_example.csv` uses DiffSBDD example files as a pseudo-real
smoke test. It verifies that file reading, manifest parsing, JSONL writing, and
mask QA work. It is not a real covalent complex and must not be described as
scientific training data.

# Small Real Covalent Raw Data

This directory is for manually curated small real covalent samples. It is not a
full database mirror and should not contain automatically downloaded bulk data.

Recommended layout:

```text
data/raw/covalent_small/
├── proteins/
│   └── <sample_id>.pdb
├── ligands/
│   └── <sample_id>.sdf
├── manifests/
│   └── manifest_real_small_template.csv
└── metadata/
    └── optional notes, source links, curation records
```

Use `manifest_example.csv` only as a pseudo-real smoke test for the processing
pipeline. It is not a validated real covalent sample.

For real samples, place curated protein PDB files under `proteins/`, curated
ligand SDF files under `ligands/`, and fill a manifest under `manifests/`.

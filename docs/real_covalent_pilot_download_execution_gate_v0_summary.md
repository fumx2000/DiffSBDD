# Real Covalent Pilot Download Execution Gate v0 Summary

Step 12T is a pilot download execution gate.

This step actually used the network to download 3 PDB/mmCIF .cif.gz files.

## Downloaded PDB IDs
- 6DI9
- 5F2E
- 6OIM

## Raw File Paths
- `data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz`
- `data/raw/covalent_sources/pdb_mmcif_direct/structures/5F2E.cif.gz`
- `data/raw/covalent_sources/pdb_mmcif_direct/structures/6OIM.cif.gz`

Raw files are not committed and must never be committed.

## Recorded Integrity Metadata
This step recorded SHA256, file size, gzip magic validation, and download provenance.

## Local Curated Provenance
Local curated provenance only records sample_index rows and does not read NPZ contents.

## Safety Boundary
No mmCIF parsing occurred.
No adapters, RDKit/UniProt/CD-HIT/geometry, or training ran.
No enriched sample_index, split assignments, leakage matrix, checkpoint, model, or tensor dump was written.

## Decision
- pdb_mmcif_download_success_count: 3
- provenance_row_count: 6
- data_raw_gitignored: true
- raw_files_staged: false
- ready_for_pilot_download_integrity_gate: true
- recommended_next_step: real_covalent_pilot_download_integrity_gate

The next step is real_covalent_pilot_download_integrity_gate: it should only check raw files, checksum, provenance, git-ignore, and staging. It should still not parse mmCIF. The step after that can start the minimal parser/adapter smoke.

# Real Covalent Pilot Download Manifest Gate v0 Summary

Step 12R is a pilot download manifest gate, not download execution, not network, not adapter execution, not enrichment, not split, not training.

This step created a small pilot download manifest only. It did not download data, create raw dirs, write raw files, run adapters, run RDKit/UniProt/CD-HIT/geometry, read NPZ contents, or run training.

## PDB/mmCIF Direct Pilot
- 6DI9
- 5F2E
- 6OIM

RCSB mmCIF URL template:
- https://files.rcsb.org/download/{pdb_id}.cif.gz

PDB/mmCIF direct license status:
- verified_cc0_for_pdb_archive

## Local Curated Pilot
- BTK_C481_6DI9_pre_reaction
- KRAS_G12C_5F2E_pre_reaction
- KRAS_G12C_6OIM_pre_reaction

## Blocked Sources
- CovPDB
- CovBinderInPDB
- CovalentInDB

All downloads disabled in this step.
All pilot jobs ready_for_execution=false.

## Dry-Run Readiness
- pilot_download_manifest_row_count: 9
- pilot_download_job_count: 6
- ready_to_run_pilot_download_dry_run=true
- ready_to_execute_pilot_download=false
- ready_to_download_large_scale_data_now=false

## Safety Boundary
No data download/network/raw dirs/raw files/adapters occurred.
No RDKit/UniProt/CD-HIT/geometry/NPZ/training occurred.
No enriched sample_index, split assignments, leakage matrix, final split, checkpoint, model, or tensor dump was written.

## Decision
- real_covalent_pilot_download_manifest_gate_passed: true
- recommended_next_step: real_covalent_pilot_download_dry_run_gate

# Real Covalent Pilot Download Dry-Run Gate v0 Summary

Step 12S is a pilot download dry-run gate, not download execution, not network, not adapter execution, not enrichment, not split, not training.

This step only validates manifest schema, URL strings, local output paths, checksum policy, provenance policy, and blocked source policy.

## PDB/mmCIF Direct Dry-Run Passed
- 6DI9
- 5F2E
- 6OIM

## Local Curated Dry-Run Passed
- BTK_C481_6DI9_pre_reaction
- KRAS_G12C_5F2E_pre_reaction
- KRAS_G12C_6OIM_pre_reaction

## Blocked As Expected
- CovPDB
- CovBinderInPDB
- CovalentInDB

## Dry-Run Result
- dry_run_total_rows: 9
- dry_run_passed_rows: 6
- dry_run_blocked_as_expected_rows: 3
- dry_run_failed_rows: 0
- ready_to_execute_pilot_download_after_dry_run=true
- pilot_download_execution_allowed_in_this_step=false
- ready_to_download_large_scale_data_now=false

## Safety Boundary
No data download/network/raw dirs/raw files/adapters occurred.
No RDKit/UniProt/CD-HIT/geometry/NPZ/training occurred.
No enriched sample_index, split assignments, leakage matrix, final split, checkpoint, model, or tensor dump was written.

## Next Step
The next step is real_covalent_pilot_download_execution_gate.
That next step should actually download 3 PDB/mmCIF .cif.gz files, but raw files cannot commit.

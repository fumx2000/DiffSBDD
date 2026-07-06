# CovaPIE External Metadata Index Download Smoke v0 Summary

This is CovaPIE external metadata index download smoke.
For a manual_user_supplied CovPDB source, this step does not download.
It only checks whether the configured manual metadata CSV exists.
If missing, the step is safely blocked and asks for the manual CovPDB metadata index CSV.
If present, it reads only the CSV header and at most 5 sample rows.
It does not copy the metadata CSV into the Step 13AN output root.
It does not verify external URLs.
It does not use internet, network, curl, wget, requests, urllib, or browser.
It does not download metadata or raw structures.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
Metadata index schema mapping and candidate materialization remain future steps.
Raw structure download remains forbidden.
It preserves one row = one covalent ligand-residue event.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

enabled_source_name: `CovPDB`
enabled_source_access_method: `manual_user_supplied`
source_metadata_index_url_or_local_path: `data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv`
metadata_index_file_checked: `True`
metadata_index_file_exists: `False`
metadata_index_file_read: `False`
metadata_index_download_or_copy_performed: `False`
metadata_index_file_copied_to_output_root: `False`
metadata_index_download_smoke_status: `blocked_due_to_missing_manual_metadata_index`
external_metadata_index_download_smoke_passed: `False`
ready_for_covapie_external_metadata_index_schema_probe_design_gate: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `provide_manual_covpdb_metadata_index_csv`
blocking_reasons: `['missing_manual_metadata_index_csv']`

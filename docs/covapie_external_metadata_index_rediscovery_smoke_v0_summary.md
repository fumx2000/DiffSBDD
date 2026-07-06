# CovaPIE External Metadata Index Rediscovery Smoke v0 Summary

This is CovaPIE external metadata index rediscovery smoke.
It is the rerun-equivalent of Step 13AN after Step 13AO generated the manual CovPDB metadata CSV.
It does not overwrite historical Step 13AN artifacts.
It reads only the local manual metadata CSV header and rows.
It does not use network.
It does not download metadata or raw structures.
It does not copy the metadata CSV into the Step 13AP output root.
It does not read raw structure contents.
It does not read SDF/PDB/mmCIF/gzip.
It does not use RDKit/Bio.PDB/gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index/final dataset/split/leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
It preserves one row = one covalent ligand-residue event policy, but event keys are not materialized yet.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

metadata_index_file_exists: `True`
metadata_index_file_read: `True`
metadata_index_row_count: `25`
metadata_index_column_count: `19`
first_5_pdb_ids: `['1A3B', '1A3E', '1A46', '1A54', '1A5G']`
first_5_het_codes: `['T29', 'T16', '00K', 'MDC', '00L']`
external_metadata_index_rediscovery_smoke_passed: `True`
metadata_index_rediscovery_status: `manual_metadata_index_discovered`
ready_for_covapie_external_metadata_index_schema_probe_design_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_external_metadata_index_schema_probe_design_gate`
blocking_reasons: `[]`

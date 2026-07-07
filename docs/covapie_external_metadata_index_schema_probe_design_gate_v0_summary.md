# CovaPIE External Metadata Index Schema Probe Design Gate v0 Summary

This is a CovaPIE schema probe design gate.
It reads the local CovPDB manual metadata CSV produced by Step 13AO and rediscovered by Step 13AP.
It does not modify the metadata CSV, Step 13AO artifacts, or Step 13AP artifacts.
It does not use network.
It does not download raw structures or ligand files.
It does not read raw/SDF/PDB/mmCIF/gzip content.
It does not use RDKit/Bio.PDB/gemmi.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

Current conclusion:
CovPDB list metadata is enough to identify PDB-level ligand records, but it is not enough to build a CovaPIE covalent event allowlist.
The list metadata lacks chain ID, residue name, residue index, residue atom name, and covalent bond atom pair.
Joining by pdb_id alone remains forbidden.
The next step should probe CovPDB complex-card metadata before any raw download.

metadata_csv_row_count: `25`
metadata_csv_column_count: `19`
allowlist_required_column_count: `15`
directly_mappable_allowlist_column_count: `4`
generated_future_allowlist_column_count: `5`
missing_critical_allowlist_column_count: `5`
missing_deferred_allowlist_column_count: `1`
minimal_event_key_materializable: `False`
preferred_event_key_materializable: `False`
one_row_one_covalent_event_enforceable: `False`
candidate_metadata_materialized: `False`
candidate_allowlist_materialized: `False`
ready_for_covapie_covpdb_complex_card_metadata_probe_design_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_covpdb_complex_card_metadata_probe_design_gate`
blocking_reasons: `[]`

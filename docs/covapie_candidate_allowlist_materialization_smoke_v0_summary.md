# CovaPIE Candidate Allowlist Materialization Smoke v0 Summary

This is CovaPIE candidate allowlist materialization smoke.
It only reads explicit metadata CSV if provided.
It does not search raw data or invent candidates.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
If metadata is missing, it is intentionally blocked and asks for explicit candidate metadata.
If metadata is valid, the next step is batch-scale raw-read smoke.
It keeps feature semantics audit and leakage/split design required before training.

input_metadata_path: `data/derived/covalent_small/covapie_candidate_allowlist_materialization_smoke_v0/input/covapie_candidate_metadata_for_allowlist.csv`
input_metadata_exists: `False`
input_metadata_read: `False`
input_metadata_row_count: `0`
included_candidate_count: `0`
materialization_status: `blocked_due_to_missing_explicit_metadata`
materialized_allowlist_written: `False`
materialized_allowlist_path: ``
blocked_header_only_written: `True`
blocked_header_only_path: `data/derived/covalent_small/covapie_candidate_allowlist_materialization_smoke_v0/covapie_batch_smoke_candidate_allowlist_materialized_blocked_header_only.csv`
candidate_rows_materialized: `False`
candidate_allowlist_created: `False`
ready_for_covapie_batch_scale_raw_read_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `provide_explicit_candidate_metadata_for_allowlist`
blocking_reasons: `['missing_explicit_candidate_metadata']`

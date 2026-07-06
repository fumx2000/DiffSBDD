# CovaPIE Batch-Scale Data Preparation Smoke v0 Summary

This is CovaPIE batch-scale data preparation smoke preflight.
It validates whether an explicit small-batch allowlist exists.
It does not search for raw data or invent candidates.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate samples or write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
If the allowlist is missing, it is intentionally blocked and the next step is candidate allowlist creation gate.
If a valid allowlist exists, the next step is batch-scale raw-read smoke.
It keeps feature semantics audit and leakage/split design required before training.

allowlist_exists: `False`
allowlist_read: `False`
allowlist_row_count: `0`
included_candidate_count: `0`
smoke_status: `blocked_due_to_missing_allowlist`
batch_scale_smoke_preflight_passed: `True`
covapie_batch_scale_data_preparation_smoke_passed: `False`
ready_for_covapie_candidate_allowlist_creation_gate: `True`
ready_for_covapie_batch_scale_raw_read_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_candidate_allowlist_creation_gate`
blocking_reasons: `missing_explicit_candidate_allowlist`

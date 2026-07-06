# CovaPIE Candidate Allowlist Creation Gate v0 Summary

This is CovaPIE candidate allowlist creation gate.
It creates only a header-only allowlist template.
It does not materialize real candidates.
It does not search raw data or invent candidates.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
The next step is candidate allowlist materialization smoke, which should only use explicit user or pipeline metadata.
It keeps feature semantics audit and leakage/split design required before training.

allowlist_template_path: `data/derived/covalent_small/covapie_candidate_allowlist_creation_gate_v0/templates/covapie_batch_smoke_candidate_allowlist_template.csv`
allowlist_template_written: `True`
allowlist_template_header_only: `True`
allowlist_template_data_row_count: `0`
candidate_rows_materialized: `False`
candidate_allowlist_created: `False`
candidate_allowlist_template_created: `True`
candidate_allowlist_creation_gate_passed: `True`
ready_for_covapie_candidate_allowlist_materialization_smoke: `True`
ready_for_covapie_batch_scale_raw_read_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_candidate_allowlist_materialization_smoke`

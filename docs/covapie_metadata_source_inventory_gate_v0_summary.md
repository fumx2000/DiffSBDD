# CovaPIE Metadata Source Inventory Gate v0 Summary

This is CovaPIE metadata source inventory gate.
It only scans existing `data/derived/covalent_small` CSV/JSON/MD artifacts.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
It reports coverage of the 15 required allowlist columns.
It reports whether existing derived artifacts are enough for 10-30 candidate materialization.
It keeps feature semantics audit and leakage/split design required before training.

scanned_artifact_count: `526`
possible_metadata_source_artifact_count: `111`
directly_available_column_count: `15`
derivable_column_count: `0`
missing_required_column_count: `0`
fully_covered_allowlist_candidate_count_estimate: `0`
enough_for_10_to_30_materialization: `False`
ready_for_covapie_candidate_metadata_assembly_design_gate: `False`
ready_for_user_or_pipeline_metadata: `True`
ready_for_covapie_batch_scale_raw_read_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `provide_or_generate_explicit_candidate_metadata_source`

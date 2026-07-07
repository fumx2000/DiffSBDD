# CovaPIE Candidate Metadata Materialization QA Gate v0 Summary

Step 13AZ is a read-only QA gate for the Step 13AY four-row candidate metadata smoke artifacts.
It validates content integrity, schema order, row identity, traceability to Step 13AX/13AW/13AO, unresolved `1A54/MDC` exclusion, boundary safety, git safety, canonical masks, feature semantics blockers, and leakage/split blockers.
It does not write new candidate metadata.
It does not write a candidate allowlist, sample_index, final_dataset, split assignments, or leakage matrix.
It does not use network access, raw downloads, raw text reads, RDKit/Bio.PDB/gemmi/gzip/torch, model calls, loss, optimizer, trainer.fit, or training.
The next allowed step is a candidate allowlist materialization design gate, not allowlist materialization smoke and not training.

qa_candidate_metadata_row_count: `4`
qa_candidate_metadata_column_count: `33`
qa_candidate_metadata_id_unique_count: `4`
qa_unresolved_exclusion_preserved: `True`
qa_traceability_passed: `True`
qa_content_integrity_passed: `True`
qa_boundary_safety_passed: `True`
qa_git_safety_passed: `True`
qa_training_blockers_passed: `True`
candidate_metadata_materialized_current_step: `False`
candidate_allowlist_materialized: `False`
ready_for_covapie_candidate_allowlist_materialization_design_gate: `True`
ready_for_covapie_candidate_allowlist_materialization_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_candidate_allowlist_materialization_design_gate`
blocking_reasons: `[]`

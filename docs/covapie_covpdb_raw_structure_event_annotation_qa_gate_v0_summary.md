# CovaPIE CovPDB Raw Structure Event Annotation QA Gate v0 Summary

Step 13AW is a read-only QA gate over Step 13AV derived artifacts.
It does not use network access, does not rerun Step 13AV, does not download raw files, and does not read raw mmCIF/PDB text.
It checks raw file presence and git safety only, while raw files remain untracked and uncommitted.
It validates download integrity, raw storage safety, format coverage, struct_conn coverage, atom_site validation, event candidate field integrity, preferred event acceptance, and unresolved event handling.
It accepts the four preferred event-key cases for a future candidate metadata materialization design gate.
It keeps the 1A54/MDC no-connectivity case blocked for manual review or future fallback design.
It does not materialize candidate metadata, allowlists, sample_index, final_dataset, splits, or leakage matrices.
It does not train.

qa_accepted_preferred_event_count: `4`
qa_blocked_unresolved_event_count: `1`
accepted_for_future_candidate_metadata_count: `4`
accepted_for_future_automatic_allowlist_count: `4`
raw_files_exist_count: `5`
raw_files_tracked: `False`
raw_files_staged: `False`
candidate_metadata_materialized: `False`
candidate_allowlist_materialized: `False`
ready_for_covapie_candidate_metadata_materialization_design_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_candidate_metadata_materialization_design_gate`
blocking_reasons: `[]`

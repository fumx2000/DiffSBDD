# CovaPIE Candidate Metadata Materialization Design Gate v0 Summary

Step 13AX is a candidate metadata materialization design gate.
It designs schema, field sources, deterministic row identity, validation rules, and the next first-four materialization smoke boundary.
It does not write candidate metadata rows.
It does not write an allowlist, sample_index, final_dataset, split assignments, or leakage matrix.
It does not use network access, raw downloads, raw text reads, RDKit/Bio.PDB/gemmi/gzip/torch, or training.
The future materialization smoke is limited to the four Step 13AW accepted preferred events.
The unresolved `1A54/MDC` event remains excluded until manual review or a future connectivity fallback design.

accepted_preferred_event_count: `4`
blocked_unresolved_event_count: `1`
candidate_metadata_schema_field_count: `33`
field_source_mapping_row_count: `33`
future_candidate_metadata_id_preview_count: `4`
future_candidate_metadata_id_unique_count: `4`
candidate_metadata_materialized: `False`
candidate_allowlist_materialized: `False`
ready_for_covapie_candidate_metadata_materialization_smoke: `True`
ready_for_covapie_candidate_allowlist_materialization_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_candidate_metadata_materialization_smoke`
blocking_reasons: `[]`

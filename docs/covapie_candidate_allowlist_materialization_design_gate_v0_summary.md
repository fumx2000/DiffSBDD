# CovaPIE Candidate Allowlist Materialization Design Gate v0 Summary

Step 13BA is a design gate for future candidate allowlist materialization.
It defines the future allowlist schema, candidate preview, unresolved exclusion policy, materialization plan, boundary safety, git safety, and training blockers.
It does not write a materialized candidate allowlist CSV or JSON.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not use network access, raw downloads, raw text reads, RDKit/Bio.PDB/gemmi/gzip/torch, model calls, loss, optimizer, trainer.fit, or training.
The preview is design-only and limited to the four Step 13AZ-validated candidate metadata rows.

Preview allowlist entry IDs:
- `allowlist::covpdb::1A3B::T29::H:SER195:OG-B`
- `allowlist::covpdb::1A3E::T16::H:SER195:OG-B`
- `allowlist::covpdb::1A46::00K::H:SER195:OG-C`
- `allowlist::covpdb::1A5G::00L::H:SER195:OG-C`

allowlist_schema_field_count: `25`
allowlist_candidate_preview_row_count: `4`
allowlist_entry_id_preview_unique_count: `4`
candidate_allowlist_materialized: `False`
candidate_allowlist_materialized_current_step: `False`
ready_for_covapie_candidate_allowlist_materialization_smoke: `True`
ready_for_covapie_batch_scale_raw_read_design_gate: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_candidate_allowlist_materialization_smoke`
blocking_reasons: `[]`

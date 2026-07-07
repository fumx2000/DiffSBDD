# CovaPIE Candidate Metadata Materialization Smoke v0 Summary

Step 13AY materializes a very small candidate metadata smoke artifact for the four accepted preferred events from Step 13AW/13AX.
It writes `covapie_candidate_metadata_smoke.csv` and `covapie_candidate_metadata_smoke.json`.
It does not write a candidate allowlist, sample_index, final_dataset, split assignments, or leakage matrix.
It does not use network access, raw downloads, raw text reads, RDKit/Bio.PDB/gemmi/gzip/torch, model calls, loss, optimizer, trainer.fit, or training.
Raw files remain external, untracked, unstaged, and uncommitted.
The unresolved `1A54/MDC` event remains excluded because `raw_no_connectivity_records_found`.

Materialized candidate metadata IDs:
- `covpdb::1A3B::T29::H:SER195:OG-B`
- `covpdb::1A3E::T16::H:SER195:OG-B`
- `covpdb::1A46::00K::H:SER195:OG-C`
- `covpdb::1A5G::00L::H:SER195:OG-C`

materialized_candidate_metadata_row_count: `4`
materialized_candidate_metadata_column_count: `33`
candidate_metadata_csv_written: `True`
candidate_metadata_json_written: `True`
candidate_metadata_materialized: `True`
candidate_allowlist_materialized: `False`
sample_index_written: `False`
final_dataset_written: `False`
split_assignments_written: `False`
leakage_matrix_written: `False`
ready_for_covapie_candidate_metadata_materialization_qa_gate: `True`
ready_for_covapie_candidate_allowlist_materialization_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_candidate_metadata_materialization_qa_gate`
blocking_reasons: `[]`

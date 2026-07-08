# CovaPIE Candidate Allowlist Materialization Smoke v0 Summary

Step 13BB materializes a first-four candidate allowlist smoke artifact from the Step 13BA design preview.
It writes CSV/JSON allowlist smoke rows only for the four eligible entries and preserves the unresolved `1A54/MDC` exclusion.
It does not download raw data, read raw `.cif/.pdb/.mmcif/.sdf/.gz` text, use RDKit/Bio.PDB/gemmi/gzip/torch, instantiate models, compute loss, or train.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.

Materialized allowlist entry IDs:
- `allowlist::covpdb::1A3B::T29::H:SER195:OG-B`
- `allowlist::covpdb::1A3E::T16::H:SER195:OG-B`
- `allowlist::covpdb::1A46::00K::H:SER195:OG-C`
- `allowlist::covpdb::1A5G::00L::H:SER195:OG-C`

materialized_allowlist_row_count: `4`
materialized_allowlist_column_count: `25`
candidate_allowlist_materialized: `True`
candidate_allowlist_materialized_current_step: `True`
candidate_metadata_materialized_current_step: `False`
ready_for_covapie_candidate_allowlist_qa_gate: `True`
ready_for_covapie_batch_scale_raw_read_design_gate: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_candidate_allowlist_qa_gate`
blocking_reasons: `[]`

# CovaPIE Candidate Allowlist QA Gate v0 Summary

Step 13BC is a QA gate for the Step 13BB four-row candidate allowlist smoke artifact.
It reads but does not rewrite the materialized allowlist CSV or JSON.
It validates schema and identity, CSV/JSON consistency, traceability to Step 13BA/13AY/13AZ/13BB evidence, the unresolved `1A54/MDC` exclusion, boundary safety, git safety, and training blockers.
It does not download or read raw structure files, use RDKit/Bio.PDB/gemmi/gzip/torch, instantiate models, compute loss, or train.
It does not write sample_index, final_dataset, split assignments, leakage matrix, or a new materialized allowlist.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows the batch raw read / extraction design gate next, not raw read smoke and not training.

source_allowlist_row_count: `4`
source_allowlist_column_count: `25`
source_allowlist_json_row_count: `4`
schema_identity_qa_passed: `True`
csv_json_consistency_qa_passed: `True`
traceability_qa_passed: `True`
unresolved_exclusion_qa_passed: `True`
candidate_allowlist_materialized_current_step: `False`
ready_for_covapie_batch_scale_raw_read_design_gate: `True`
ready_for_covapie_batch_scale_raw_read_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_batch_raw_read_extraction_design_gate`
blocking_reasons: `[]`

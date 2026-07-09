# CovaPIE CYS/SG Ready Candidate Materialization Gate v0 Summary

Step 14X materializes ready candidate records from the Step 14W ready materialization input manifest.

Ready candidates are evidence-complete candidates for downstream small pilot manifest and sample preparation. They are not final dataset samples, not sample index rows, and not training samples.

ready_candidate_count_current_step: `3`
ready_for_small_pilot_manifest_count: `3`
ready_for_sample_preparation_count: `3`
ready_for_training_candidate_count_current_step: `0`
accepted_pdb_het_pairs: `6BV6/JUG, 6BV8/JUG, 6BV5/JUG`
blocked_pdb_het_pairs: `1A54/MDC, 6BV9/JUG`
ready_for_covapie_small_pilot_manifest_rerun_gate: `True`
ready_for_covapie_sample_preparation_design_gate: `True`
ready_for_training: `False`
recommended_next_step: `covapie_small_pilot_manifest_rerun_gate`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.

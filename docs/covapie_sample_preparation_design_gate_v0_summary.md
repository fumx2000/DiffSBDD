# CovaPIE Sample Preparation Design Gate v0 Summary

Step 14Z designs the next sample preparation execution smoke for the three Step 14Y small pilot ready candidates.

This is a design gate only. It does not read raw CIF/mmCIF, parse struct_conn or atom_site, write atom tables, create a sample index, create a final dataset, write split/leakage artifacts, run a dataloader smoke, or train.

sample_preparation_input_count: `3`
required_artifact_plan_count: `3`
raw_access_plan_count: `3`
ready_for_sample_preparation_execution_smoke_count: `3`
ready_for_training_candidate_count_current_step: `0`
accepted_pdb_het_pairs: `6BV6/JUG, 6BV8/JUG, 6BV5/JUG`
blocked_pdb_het_pairs: `1A54/MDC, 6BV9/JUG`
ready_for_covapie_sample_preparation_execution_smoke: `True`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_sample_preparation_execution_smoke`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.

# CovaPIE Sample Preparation QA Gate v0 Summary

Step 14AB performs QA over Step 14AA sample preparation execution smoke outputs.

This QA gate reads derived execution outputs only. It does not read raw CIF/mmCIF, parse raw struct_conn or atom_site, modify atom tables, create a sample index, create a final dataset, write split/leakage artifacts, run a dataloader smoke, or train.

sample_qa_count: `3`
table_integrity_qa_count: `18`
event_pair_qa_count: `3`
qa_issue_count: `0`
sample_qa_passed_count: `3`
table_integrity_passed_count: `18`
event_pair_qa_passed_count: `3`
accepted_pdb_het_pairs: `6BV6/JUG, 6BV8/JUG, 6BV5/JUG`
ready_for_covapie_sample_index_design_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_sample_index_design_gate`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.

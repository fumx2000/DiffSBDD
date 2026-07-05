# Real Covalent Confirmed Candidate Sample Index Materialization Smoke v0 Summary

Step 13T writes a 3-row sample_index smoke artifact for the current CYS/SG golden samples.
It is not an enriched_sample_index, not a final_dataset, and not model input.
It does not run molecule parsing, raw structure parsing, forward, loss, backward, optimizer, training step, trainer fit, checkpoint save, model save, or tensor dump.

The materialized smoke sample_index preserves all five V1 canonical mask tasks:
`warhead_only`/`A`, `linker_plus_warhead`/`B`, `scaffold_plus_warhead`/`B2`, `scaffold_only`/`B3`, and `scaffold_plus_linker_plus_warhead`/`C`.
B3 scaffold_only remains included as a formal canonical task.
No extra mask task was added.

This smoke allows the next sample_index QA gate.
It does not allow model input materialization and does not allow training.
Feature semantics audit remains required before formal training.

sample_index_smoke_row_count: `3`
sample_index_audit_row_count: `3`
sample_index_written: `True`
enriched_sample_index_written: `False`
final_dataset_written: `False`
model_input_materialized: `False`
ready_for_sample_index_qa_gate: `True`
ready_for_model_input_design_gate: `False`
ready_to_train_now: `False`
recommended_next_step: `real_covalent_confirmed_candidate_sample_index_qa_gate`

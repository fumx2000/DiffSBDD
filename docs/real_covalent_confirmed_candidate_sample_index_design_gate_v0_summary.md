# Real Covalent Confirmed Candidate Sample Index Design Gate v0 Summary

Step 13S is a sample_index design gate only.
It defines the future sample_index schema, dependency contract, candidate contract, mask task contract, readiness boundary, and safety gate.
It does not write a real sample_index.
It does not write enriched_sample_index, final_dataset, split assignments, leakage matrix, or model input.
It does not run forward, loss, backward, optimizer, training step, trainer fit, checkpoint save, model save, or tensor dump.

The canonical V1 mask task set remains five tasks:
1. `warhead_only` with display alias `A`
2. `linker_plus_warhead` with display alias `B`
3. `scaffold_plus_warhead` with display alias `B2`
4. `scaffold_only` with display alias `B3`
5. `scaffold_plus_linker_plus_warhead` with display alias `C`

Long semantic mask names are the source of truth.
A/B/B2/B3/C aliases are display-only.
B3 scaffold_only is a formal V1 canonical mask task.
No sixth or seventh mask task was added.

This gate allows the next sample_index materialization smoke to begin.
It does not allow model input materialization and does not allow training.
Feature semantics audit remains required before formal training.

schema_contract_row_count: `47`
dependency_contract_row_count: `10`
candidate_contract_row_count: `3`
mask_task_contract_row_count: `5`
ready_for_sample_index_materialization_smoke: `True`
ready_to_write_sample_index_now: `False`
ready_for_model_input_design_gate: `False`
ready_to_train_now: `False`
recommended_next_step: `real_covalent_confirmed_candidate_sample_index_materialization_smoke`

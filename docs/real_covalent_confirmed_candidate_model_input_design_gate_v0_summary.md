# Real Covalent Confirmed Candidate Model Input Design Gate v0 Summary

Step 13V is a model_input design gate only.
It designs how the current sample_index smoke could map to DiffSBDD-compatible model input.
It does not materialize model input, tensors, NPZ, PT, split assignments, leakage matrix, or final_dataset.
It does not modify dataloader, forward, loss, or DiffSBDD main model code.

The five canonical mask tasks remain preserved, including scaffold_only/B3.
Long semantic mask names remain the source of truth and aliases remain display-only.
This gate explicitly records feature semantics audit requirements.
Step 12D was smoke legality only, not final feature semantics audit.
This gate allows model_input materialization smoke next.
It does not allow loader shape dry run and does not allow training.
Feature semantics audit remains required before formal training.

schema_contract_row_count: `53`
dependency_contract_row_count: `10`
sample_contract_row_count: `3`
mask_contract_row_count: `5`
feature_semantics_contract_row_count: `12`
ready_for_model_input_materialization_smoke: `True`
ready_for_loader_shape_dry_run: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `real_covalent_confirmed_candidate_model_input_materialization_smoke`

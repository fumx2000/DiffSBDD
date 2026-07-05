# Real Covalent Confirmed Candidate Model Input Materialization Smoke v0 Summary

Step 13W writes CSV/JSON-level model-input-like smoke artifacts.
It does not write real tensor or training model input.
It does not create PT or NPZ artifacts.
It does not modify dataloader, forward, loss, or DiffSBDD main model code.
It preserves the five canonical mask tasks, including scaffold_only/B3.
It keeps feature semantics audit required before formal training.

This smoke allows the model_input QA gate next.
It does not allow loader shape dry run and does not allow training.

model_input_smoke_index_row_count: `3`
model_input_smoke_feature_status_row_count: `12`
model_input_smoke_mask_status_row_count: `5`
model_input_materialization_smoke_audit_row_count: `3`
model_input_smoke_written: `True`
model_input_smoke_materialized: `True`
model_input_materialized: `False`
tensor_artifact_written: `False`
ready_for_model_input_qa_gate: `True`
ready_for_loader_shape_dry_run: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `real_covalent_confirmed_candidate_model_input_qa_gate`

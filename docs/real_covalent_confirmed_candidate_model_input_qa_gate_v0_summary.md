# Real Covalent Confirmed Candidate Model Input QA Gate v0 Summary

Step 13X is a model_input QA gate only.
It reads but does not modify the Step 13W CSV/JSON smoke artifacts.
It validates row identity, CYS/SG scope, sample contract consistency, sample_index consistency, ligand counts, endpoint counts, pocket dependencies, ligand topology dependencies, five canonical mask tasks including scaffold_only/B3, feature semantics audit status, tensor status, and loader/training boundaries.

This step does not generate tensor, NPZ, or PT artifacts.
It does not modify dataloader, forward, loss, or DiffSBDD main model code.
It does not run loader shape dry run.
It does not run forward, loss, backward, optimizer, training step, trainer fit, checkpoint save, model save, or tensor dump.
It allows the loader shape dry run design gate next.
It does not allow training.
Feature semantics audit remains required before formal training.

model_input_smoke_row_qa_audit_row_count: `3`
model_input_smoke_dependency_qa_audit_row_count: `10`
model_input_smoke_feature_qa_audit_row_count: `12`
model_input_smoke_mask_qa_audit_row_count: `5`
model_input_qa_passed: `True`
model_input_smoke_modified: `False`
model_input_materialized: `False`
tensor_artifact_written: `False`
ready_for_loader_shape_dry_run: `True`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate`

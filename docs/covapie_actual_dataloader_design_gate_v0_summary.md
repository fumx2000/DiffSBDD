# CovaPIE Actual Dataloader Design Gate v0 Summary

Step 13BW designs the future CovaPIE actual dataloader / adapter path.
It is a design gate only: it does not implement an actual dataloader, write actual dataloader smoke, write `dataloader_smoke.csv/json`, create tensors, import torch or numpy, load checkpoints, call model forward, compute loss, or train.
It reads `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, and `equivariant_diffusion/` as static references only and does not modify original DiffSBDD dataloader/model/loss code.
It keeps the five canonical masks unchanged, including `scaffold_only / B3`.
Because `feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false`, the next step is a feature semantics tensorization audit gate, not actual dataloader smoke and not training.

original_dataloader_static_reference_audit_row_count: `10`
original_dataloader_static_reference_audit_passed: `True`
actual_dataloader_adapter_design_contract_row_count: `12`
actual_dataloader_adapter_design_contract_passed: `True`
tensorization_input_contract_row_count: `14`
tensorization_input_contract_passed: `True`
batch_collate_contract_row_count: `10`
batch_collate_contract_passed: `True`
checkpoint_compatibility_contract_row_count: `10`
checkpoint_compatibility_contract_passed: `True`
feature_semantics_blocker_contract_row_count: `10`
feature_semantics_blocker_contract_passed: `True`
future_smoke_plan_row_count: `8`
future_smoke_plan_passed: `True`
safety_audit_passed: `True`
actual_dataloader_design_completed_current_step: `True`
actual_dataloader_smoke_written: `False`
real_dataloader_written: `False`
original_dataloader_modified: `False`
torch_imported: `False`
numpy_imported: `False`
torch_tensor_created: `False`
checkpoint_loaded: `False`
model_forward_called: `False`
loss_compute_called: `False`
training_allowed: `False`
feature_semantics_known_for_training: `False`
unknown_atom_feature_policy_finalized_for_training: `False`
ready_for_covapie_feature_semantics_tensorization_audit_gate: `True`
ready_for_covapie_actual_dataloader_adapter_smoke: `False`
ready_for_covapie_actual_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_feature_semantics_tensorization_audit_gate`
blocking_reasons: `[]`

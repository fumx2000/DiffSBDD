# CovaPIE Dataloader Smoke Design Gate v0 Summary

Step 13BT designs the next minimal metadata-only dataloader smoke.
It does not write metadata dataloader smoke, actual dataloader smoke, a real dataloader, final dataset artifacts, a new sample index, split assignments, leakage matrix, tensors, checkpoints, or training artifacts.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, run backward, create optimizers, call trainer.fit, or train.
It does not modify `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, `equivariant_diffusion/`, or original DiffSBDD model/dataloader/loss code.
The next allowed step is `covapie_metadata_dataloader_smoke`, which is still metadata-only and must not become actual PyTorch dataloader smoke.
The five canonical masks are preserved, including `scaffold_only / B3`.
Feature semantics and leakage/split blockers remain required before formal training, fine-tuning, or real parameter updates.

runtime_boundary_contract_row_count: `14`
runtime_boundary_contract_passed: `True`
metadata_dataset_api_contract_row_count: `10`
metadata_dataset_api_contract_passed: `True`
metadata_getitem_output_mapping_contract_row_count: `12`
metadata_getitem_output_mapping_contract_passed: `True`
tensorization_blocker_contract_row_count: `10`
tensorization_blocker_contract_passed: `True`
batch_collate_design_contract_row_count: `8`
batch_collate_design_contract_passed: `True`
checkpoint_runtime_risk_contract_row_count: `8`
checkpoint_runtime_risk_contract_passed: `True`
metadata_dataloader_smoke_plan_row_count: `10`
metadata_dataloader_smoke_plan_passed: `True`
metadata_dataloader_smoke_written: `False`
actual_dataloader_smoke_written: `False`
real_dataloader_written: `False`
original_dataloader_modified: `False`
torch_imported: `False`
torch_tensor_created: `False`
checkpoint_loaded: `False`
model_forward_called: `False`
training_allowed: `False`
ready_for_covapie_metadata_dataloader_smoke: `True`
ready_for_covapie_actual_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_metadata_dataloader_smoke`
blocking_reasons: `[]`

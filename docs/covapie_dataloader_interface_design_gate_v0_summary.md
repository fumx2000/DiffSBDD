# CovaPIE Dataloader Interface Design Gate v0 Summary

Step 13BQ designs the interface between the CovaPIE final dataset smoke preview and a future dataloader.
It does not implement a dataloader, write dataloader interface smoke, write actual dataloader smoke, import torch, create tensors, load checkpoints, call model forward, compute loss, run backward, create optimizers, call trainer.fit, or train.
It does not modify `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, `equivariant_diffusion/`, or any original DiffSBDD model/dataloader/loss code.
It does not write real `final_dataset.csv/json`, generic `final_dataset_smoke.csv/json`, a new sample index, split assignments, or a leakage matrix.
It reads Step 13BP/13BO/13BN/13BM/13BK/13BH/13BE derived artifacts and uses original DiffSBDD files only as static interface references.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics and leakage/split blockers remain required before formal training, fine-tuning, or real parameter updates.
This design gate allows dataloader interface smoke next, not actual dataloader smoke and not training.

dataloader_input_source_contract_row_count: `15`
dataloader_input_source_contract_passed: `True`
dataloader_field_mapping_contract_row_count: `45`
dataloader_field_mapping_contract_passed: `True`
dataloader_feature_interface_contract_row_count: `16`
dataloader_feature_interface_contract_passed: `True`
dataloader_mask_interface_contract_row_count: `8`
dataloader_mask_interface_contract_passed: `True`
dataloader_batch_collate_contract_row_count: `10`
dataloader_batch_collate_contract_passed: `True`
checkpoint_compatibility_contract_row_count: `8`
checkpoint_compatibility_contract_passed: `True`
dataloader_interface_smoke_plan_row_count: `10`
dataloader_interface_smoke_plan_passed: `True`
dataloader_interface_smoke_written: `False`
real_dataloader_written: `False`
original_dataloader_modified: `False`
torch_imported: `False`
torch_tensor_created: `False`
checkpoint_loaded: `False`
model_forward_called: `False`
training_allowed: `False`
feature_semantics_known_for_training: `False`
unknown_atom_feature_policy_finalized_for_training: `False`
ready_for_covapie_dataloader_interface_smoke: `True`
ready_for_covapie_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_dataloader_interface_smoke`
blocking_reasons: `[]`

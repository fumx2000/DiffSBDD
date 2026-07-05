# Real Covalent Confirmed Candidate DiffSBDD Loader Adapter Design Gate v0 Summary

Step 13AB is DiffSBDD loader adapter design gate only.
It does not implement the adapter.
It does not modify original DiffSBDD dataloader, forward, loss, equivariant_diffusion/, or lightning_modules.py.
It designs an external adapter under covalent_ext to preserve checkpoint compatibility.
It maps current 14 shape items, 5 canonical masks including scaffold_only/B3, and 3 auxiliary labels.
It keeps auxiliary labels out of loss integration for now.
It does not import torch, create tensors, instantiate loader, or train.
It keeps feature semantics audit required before formal training.
It allows adapter implementation smoke next, not training.

diffsbdd_loader_adapter_input_contract_row_count: `3`
diffsbdd_loader_adapter_source_discovery_audit_row_count: `30`
diffsbdd_loader_adapter_interface_contract_row_count: `12`
diffsbdd_loader_adapter_shape_mapping_contract_row_count: `14`
diffsbdd_loader_adapter_mask_mapping_contract_row_count: `5`
diffsbdd_loader_adapter_auxiliary_label_contract_row_count: `3`
diffsbdd_loader_adapter_execution_boundary_contract_row_count: `18`
diffsbdd_loader_adapter_feature_semantics_boundary_row_count: `12`
diffsbdd_loader_adapter_design_gate_passed: `True`
adapter_implemented: `False`
torch_imported: `False`
torch_tensor_created: `False`
ready_for_diffsbdd_loader_adapter_implementation_smoke: `True`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke`

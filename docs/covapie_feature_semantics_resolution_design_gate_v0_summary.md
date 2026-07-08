# CovaPIE Feature Semantics Resolution Design Gate v0 Summary

Step 13BY is a feature semantics resolution design gate.
It proposes resolution contracts for original DiffSBDD feature schema mapping, coordinate tensorization, atom feature schema, unknown atom policy, label semantics, and tensor shape/dtype policy.
It does not parse raw data, extract coordinates, create tensors, import torch or numpy, write actual dataloader smoke, write final datasets, write sample indexes, write split assignments, write leakage matrices, load checkpoints, run model forward, compute loss, or train.
It keeps `feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false`.
Step 12D, Step 13BM, Step 13BX, and Step 13BY do not replace the final training feature semantics audit.
The five canonical mask tasks are preserved, including `scaffold_only / B3`.
The next step is `covapie_feature_semantics_resolution_smoke`, not actual dataloader smoke and not training.

original_diffsbbd_feature_schema_mapping_design_row_count: `12`
original_diffsbbd_feature_schema_mapping_design_passed: `True`
coordinate_tensorization_resolution_contract_row_count: `8`
coordinate_tensorization_resolution_contract_passed: `True`
atom_feature_schema_resolution_contract_row_count: `12`
atom_feature_schema_resolution_contract_passed: `True`
unknown_atom_policy_resolution_contract_row_count: `8`
unknown_atom_policy_resolution_contract_passed: `True`
label_semantics_resolution_contract_row_count: `14`
label_semantics_resolution_contract_passed: `True`
tensor_shape_dtype_resolution_contract_row_count: `10`
tensor_shape_dtype_resolution_contract_passed: `True`
feature_semantics_resolution_smoke_plan_row_count: `8`
feature_semantics_resolution_smoke_plan_passed: `True`
safety_audit_passed: `True`
feature_semantics_known_for_training: `False`
unknown_atom_feature_policy_finalized_for_training: `False`
proposed_feature_schema_resolution_written: `True`
proposed_unknown_atom_policy_written: `True`
proposed_label_semantics_resolution_written: `True`
ready_for_covapie_feature_semantics_resolution_smoke: `True`
ready_for_covapie_actual_dataloader_adapter_smoke: `False`
ready_for_covapie_actual_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_feature_semantics_resolution_smoke`
blocking_reasons: `[]`

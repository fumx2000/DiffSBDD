# CovaPIE Feature Semantics Resolution Smoke v0 Summary

Step 13BZ reads the Step 13BY resolution design contracts and validates them against existing derived metadata previews and derived atom table CSVs.
It is a CSV/JSON-level feature semantics resolution smoke only.
It does not create tensors, import torch or numpy, instantiate a Dataset/DataLoader, load checkpoints, run model forward, compute loss, train, parse raw mmCIF, or extract coordinates from raw files.
It keeps `feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false`.
It preserves the five canonical mask tasks, including `scaffold_only / B3`.
Step 12D, Step 13BM, Step 13BX, Step 13BY, and Step 13BZ do not replace the final training feature semantics audit.
The next step is `covapie_feature_semantics_resolution_smoke_qa_gate`, not actual dataloader smoke and not training.

original_feature_schema_mapping_smoke_audit_row_count: `12`
original_feature_schema_mapping_smoke_audit_passed: `True`
coordinate_policy_resolution_smoke_audit_row_count: `8`
coordinate_policy_resolution_smoke_audit_passed: `True`
atom_feature_policy_resolution_smoke_audit_row_count: `12`
atom_feature_policy_resolution_smoke_audit_passed: `True`
unknown_atom_policy_resolution_smoke_audit_row_count: `8`
unknown_atom_policy_resolution_smoke_audit_passed: `True`
label_policy_resolution_smoke_audit_row_count: `14`
label_policy_resolution_smoke_audit_passed: `True`
tensor_shape_dtype_policy_smoke_audit_row_count: `10`
tensor_shape_dtype_policy_smoke_audit_passed: `True`
feature_semantics_resolution_readiness_audit_row_count: `10`
feature_semantics_resolution_readiness_audit_passed: `True`
safety_audit_passed: `True`
feature_semantics_known_for_training: `False`
unknown_atom_feature_policy_finalized_for_training: `False`
proposed_feature_schema_resolution_validated_by_smoke: `True`
proposed_unknown_atom_policy_validated_by_smoke: `True`
proposed_label_semantics_validated_by_smoke: `True`
derived_atom_tables_read_only: `True`
ready_for_covapie_feature_semantics_resolution_smoke_qa_gate: `True`
ready_for_covapie_actual_dataloader_adapter_smoke: `False`
ready_for_covapie_actual_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_feature_semantics_resolution_smoke_qa_gate`
blocking_reasons: `[]`

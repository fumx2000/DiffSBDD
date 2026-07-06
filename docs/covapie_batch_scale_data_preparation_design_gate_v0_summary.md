# CovaPIE Batch-Scale Data Preparation Design Gate v0 Summary

This is a CovaPIE batch-scale data preparation design gate.
It does not run batch-scale preparation.
It designs future 10-30 sample smoke only.
It preserves current CYS/SG-only scope.
It preserves five canonical mask tasks including scaffold_only/B3.
It defines candidate selection, sharding, failure taxonomy, provenance, output artifact, git safety, feature semantics, leakage/split placeholders, and execution boundary contracts.
It does not read raw data, SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize new samples, write sample index, split assignment, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
It keeps feature semantics audit and leakage/split design required before training.
It allows CovaPIE batch-scale data preparation smoke next, not training.

batch_scale_initial_min_candidate_count: `10`
batch_scale_initial_max_candidate_count: `30`
batch_scale_initial_shard_size: `5`
current_reactive_residue_scope: `cys_sg_only`
covapie_batch_scale_precondition_audit_row_count: `6`
covapie_batch_scale_input_source_contract_row_count: `8`
covapie_batch_scale_candidate_selection_contract_row_count: `12`
covapie_batch_scale_sharding_contract_row_count: `7`
covapie_batch_scale_failure_taxonomy_contract_row_count: `18`
covapie_batch_scale_provenance_contract_row_count: `14`
covapie_batch_scale_output_artifact_contract_row_count: `12`
covapie_batch_scale_git_safety_contract_row_count: `10`
covapie_batch_scale_mask_scope_contract_row_count: `5`
covapie_batch_scale_feature_semantics_boundary_row_count: `12`
covapie_batch_scale_leakage_split_placeholder_contract_row_count: `12`
covapie_batch_scale_execution_boundary_contract_row_count: `24`
batch_scale_design_gate_passed: `True`
ready_for_covapie_batch_scale_data_preparation_smoke: `True`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_batch_scale_data_preparation_smoke`

# Real Covalent Feature Semantics Audit v0 Summary

Step 12F is a feature semantics audit, not training.
It does not run model forward, compute loss, run backward, create an optimizer, or save checkpoint/model/tensor dump.
This audit exists because Step 12D/12E recorded UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False during smoke validation.

## Preconditions
- step12e_validated: true
- step12b_mask_level_aware_validator_validated: true
- input_source: real_covalent_training_tensor_materialized_v0
- selected_sample_index: data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv
- selected_artifact_is_real_covalent: true
- selected_artifact_is_synthetic_only: false

## Checkpoint 10D Feature Contract
- checkpoint_path: checkpoints/crossdocked_fullatom_cond.ckpt
- checkpoint_ligand_feature_dim: 10
- checkpoint_pocket_feature_dim: 10
- checkpoint_feature_semantics_source: repo_dataset_info_or_config
- checkpoint_feature_semantics_directly_encoded: true
- checkpoint_10d_mapping_matches_project_mapping: true
- checkpoint_10d_mapping_project: {"15": 7, "16": 3, "17": 6, "35": 5, "5": 4, "53": 8, "6": 0, "7": 1, "8": 2, "9": 9}

## Real Atom Vocabulary
- sample_count: 3
- sample_ids: BTK_C481_6DI9_pre_reaction, KRAS_G12C_5F2E_pre_reaction, KRAS_G12C_6OIM_pre_reaction
- ligand_atom_count_total: 104
- protein_atom_count_total: 5642
- ligand_atomic_numbers_unique: [6, 7, 8, 9, 17]
- protein_atomic_numbers_unique: [6, 7, 8, 9, 12, 15, 16, 17]
- ligand_unknown_atom_numbers: []
- protein_unknown_atom_numbers: [12]
- ligand_unknown_atom_count: 0
- protein_unknown_atom_count: 2
- unknown_atom_policy_triggered: true
- zero_vector_unknown_atom_policy_safe: false

## Conversion Semantics
- canonical_mask_levels: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, B3_scaffold_only, C_scaffold_linker_warhead
- audited_mask_level_count: 5
- passed_mask_level_count: 0
- failed_mask_level_count: 5
- all_checkpoint_compatible_batches_constructed: true
- all_ligand_one_hot_row_sums_valid: true
- all_pocket_one_hot_row_sums_valid: false
- all_ligand_unknown_atom_count_zero: true
- all_pocket_unknown_atom_count_zero: false
- no_synthetic_fallback_used: true

## Decision
- feature_semantics_dimension_contract_passed: false
- feature_semantics_mapping_confirmed: true
- feature_semantics_known_after_audit: false
- feature_semantics_mapping_source_needs_confirmation: false
- real_covalent_feature_semantics_audit_passed: false
- real_covalent_cuda_forward_backward_smoke_allowed: false
- real_covalent_single_optimizer_step_smoke_allowed: false
- recommended_next_step: real_covalent_feature_semantics_audit_debug

## Safety Boundary
- model_forward_called: false
- loss_compute_called: false
- backward_called: false
- optimizer_created: false
- optimizer_step_called: false
- training_step_called: false
- trainer_fit_called: false
- checkpoint_saved: false
- model_saved: false
- tensor_dump_saved: false
- npz_created: false
- original_diffsbdd_source_modified: false
- forbidden_artifacts_created: false

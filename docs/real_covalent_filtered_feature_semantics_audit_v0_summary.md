# Real Covalent Filtered Feature Semantics Audit v0 Summary

Step 12I is a filtered feature semantics audit, not training.
It does not run forward, calculate loss, run gradients, create an optimizer, or save checkpoint/model/tensor dump.
It uses the Step 12H production filter helper: `drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot`.
Original data is unchanged, and the production adapter is unchanged.

## Filtered Vocabulary
- sample_count: 3
- filtered_pocket_atom_numbers: [12]
- filtered_pocket_atom_symbols: ['Mg']
- pocket unknown count from 2 to 0: 2 -> 0
- ligand_unknown_atom_count_after_filter: 0
- unknown_atom_policy_triggered_after_filter: false
- zero_vector_unknown_atom_policy_safe_after_filter: true

## Feature Semantics Decision
- checkpoint_feature_semantics_source: repo_dataset_info_or_config
- checkpoint_10d_mapping_matches_project_mapping: true
- audited_mask_level_count: 5
- passed_mask_level_count: 5
- all_checkpoint_compatible_batches_constructed_after_filter: true
- all_ligand_one_hot_row_sums_valid_after_filter: true
- all_pocket_one_hot_row_sums_valid_after_filter: true
- feature_semantics_known_after_filter: true
- real_covalent_filtered_feature_semantics_audit_passed: true

## Scope Boundary
- This is not optimizer step permission.
- real_covalent_single_optimizer_step_smoke_allowed: false
- real_covalent_filtered_cuda_forward_backward_smoke_allowed: true
- Cys-first strategy: cys_with_known_reconstruction_template_only
- Non-Cys data policy: identify_classify_defer_until_template_gate
- reaction_family_template_audit_required_before_broad_covalent_training: true
- ligand_reconstruction_template_gate_required: true
- recommended_next_step: real_covalent_filtered_cuda_forward_backward_smoke

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

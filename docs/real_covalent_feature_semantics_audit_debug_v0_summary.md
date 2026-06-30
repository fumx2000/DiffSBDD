# Real Covalent Feature Semantics Audit Debug v0 Summary

Step 12G is an audit debug and projection policy design step, not training.
It does not run forward, calculate loss, run gradients, create an optimizer, or save checkpoint/model/tensor dump.
Step 12F clean block was caused by protein Mg / atomic_number=12 triggering the UNKNOWN_ATOM_FEATURE_POLICY path.

## Mg Localization
- mg_atom_count: 2
- mg_sample_ids: KRAS_G12C_5F2E_pre_reaction, KRAS_G12C_6OIM_pre_reaction
- Mg KRAS_G12C_5F2E_pre_reaction protein_atom_local_index=1455 coord=(10.7000, -1.2370, -3.3910) min_ligand_distance=4.4544 ligand_reactive_distance=6.3088
- Mg KRAS_G12C_6OIM_pre_reaction protein_atom_local_index=1336 coord=(-2.5120, 2.5880, 0.2200) min_ligand_distance=4.8937 ligand_reactive_distance=5.6123
- mg_min_distance_to_ligand: 4.454363822937012
- mg_max_distance_to_ligand: 4.893711090087891
- mg_min_distance_to_ligand_reactive_atom: 5.612326145172119
- mg_direct_ligand_contact_detected: false
- mg_close_to_ligand_detected: true

## Projection-Level Filter Debug
- filter_policy_name: drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot
- projection_filter_only_debug: true
- production_adapter_modified: false
- original_data_modified: false
- filtered_atom_numbers: [12]
- filtered_atom_symbols: ['Mg']
- total_removed_pocket_atom_count: 2
- post_filter_protein_unknown_atom_count: 0
- post_filter_ligand_unknown_atom_count: 0
- audited_mask_level_count: 5
- passed_mask_level_count: 5
- failed_mask_level_count: 0
- all_pocket_one_hot_row_sums_valid_after_filter: true
- ligand_masks_unchanged_after_filter: true
- ligand_reactive_atom_region_preserved: true

## Decision
- This step recommends a formal projection-level filter gate only if Mg is not in direct ligand contact.
- The next step is a filter gate, not an optimizer step.
- It does not allow a real covalent optimizer step.
- noncheckpoint_pocket_atom_filter_policy_recommended: true
- real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed: true
- real_covalent_single_optimizer_step_smoke_allowed: false
- recommended_next_step: real_covalent_noncheckpoint_pocket_atom_filter_gate

If a future structure review finds Mg directly participates in ligand binding geometry, the next step should be manual structure review rather than filtering.

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

# Real Covalent Feature Mapping Loader Gate v0 Summary

Step 12A is a real covalent feature mapping / loader gate, not training.
It does not run model forward, backward, optimizer, training_step, or trainer.fit.
It reads existing real covalent artifacts and writes only CSV/JSON/MD gate evidence.

## Artifact
- discovered_artifact_count: 1
- discovered_manifest_count: 56
- discovered_npz_count: 3
- selected_real_data_root: data/derived/covalent_small/training_tensor_materialized_v0
- selected_loader_or_tensor_artifact: data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv
- selected_artifact_is_real_covalent: true
- selected_artifact_is_synthetic_only: false

## Real Sample Contract
- audited_real_sample_count: 3
- passed_real_sample_count: 3
- failed_real_sample_count: 0
- canonical_mask_levels: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, B3_scaffold_only, C_scaffold_linker_warhead
- all_five_level_masks_available: true
- real_five_level_mask_contract_proven: true
- real_b3_target_is_scaffold: true
- real_b3_context_is_linker_warhead: true
- real_b3_reactive_atom_in_context: true
- real_b3_reactive_atom_in_target: false
- real_b2_b3_contrast_passed: true

## Loader And Mapping
- dataset_created: true
- dataloader_created: true
- batch_size: 2
- real_batch_adapter_gate_passed: true
- real_model_input_mapping_gate_passed: true
- real_covalent_feature_mapping_loader_gate_passed: true
- real_covalent_pretraining_smoke_allowed: true

## Safety Boundary
- model_forward_called: false
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

## Decision
- all_checks_passed: true
- recommended_next_step: real_covalent_pretraining_smoke_design

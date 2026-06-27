# B3 Scaffold-Only Mask Sweep v0 Summary

Step 11O is a five-level mask sweep, not training.
It uses only canonical long-form A/B/B2/B3/C mask levels.
It does not use short alias B3; legacy short-name ambiguity remains preserved and isolated.

## Canonical Levels
- A_warhead_only: target=['warhead'], context=['scaffold', 'linker']
- B_linker_warhead: target=['linker', 'warhead'], context=['scaffold']
- B2_scaffold_warhead: target=['scaffold', 'warhead'], context=['linker']
- B3_scaffold_only: target=['scaffold'], context=['linker', 'warhead']
- C_scaffold_linker_warhead: target=['scaffold', 'linker', 'warhead'], context=[]

## Observed Counts
- A_warhead_only: target_atoms=[5, 6] context_atoms=[0, 1, 2, 3, 4] target_count=2 context_count=5 status=passed
- B_linker_warhead: target_atoms=[3, 4, 5, 6] context_atoms=[0, 1, 2] target_count=4 context_count=3 status=passed
- B2_scaffold_warhead: target_atoms=[0, 1, 2, 5, 6] context_atoms=[3, 4] target_count=5 context_count=2 status=passed
- B3_scaffold_only: target_atoms=[0, 1, 2] context_atoms=[3, 4, 5, 6] target_count=3 context_count=4 status=passed
- C_scaffold_linker_warhead: target_atoms=[0, 1, 2, 3, 4, 5, 6] context_atoms=[] target_count=7 context_count=0 status=passed

## B2/B3 Contrast
- b2_target_includes_scaffold: true
- b2_target_includes_warhead: true
- b2_context_includes_linker: true
- b2_context_does_not_include_warhead: true
- b3_target_includes_scaffold: true
- b3_target_does_not_include_warhead: true
- b3_context_includes_linker: true
- b3_context_includes_warhead: true
- b3_context_does_not_include_scaffold: true
- b2_b3_target_masks_not_identical: true
- b2_b3_context_masks_not_identical: true
- b2_b3_contrast_passed: true

## Batch Adapter Sweep
- batch_adapter_sweep_row_count: 6
- all_batch_adapter_rows_passed: true
- b3_fallback_adapter_valid: true
- b3_explicit_key_adapter_valid: true

## Limits
- This step does not prove loss behavior, gradients, optimizer behavior, generation quality, or real loader readiness.
- It does not run model forward or write tensor dumps.

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
- original_diffsbdd_source_modified: false
- forbidden_artifacts_created: false

## Decision
- five_level_mask_sweep_passed: true
- canonical_five_level_mask_contract_proven: true
- b3_pretrained_masked_loss_smoke_allowed: true
- recommended_next_step: b3_pretrained_masked_loss_smoke

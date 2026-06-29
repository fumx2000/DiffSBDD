# Real Covalent Pretraining Smoke Design v0 Summary

Step 12C is design only, not training.
It does not run model forward, backward, optimizer, training_step, or trainer.fit.
It designs the next real covalent pretrained forward/loss smoke using existing real artifacts.

## Preconditions
- step12a_validated: true
- step12b_mask_level_aware_validator_validated: true
- selected_real_data_root: data/derived/covalent_small/training_tensor_materialized_v0
- selected_sample_index: data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv
- selected_artifact_is_real_covalent: true
- selected_artifact_is_synthetic_only: false

## Planned Next Smoke
- planned_next_stage: real_covalent_pretrained_forward_loss_smoke_v0
- planned_checkpoint_path: checkpoints/crossdocked_fullatom_cond.ckpt
- planned_batch_size: 2
- planned_num_workers: 0
- planned_mask_levels: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, B3_scaffold_only, C_scaffold_linker_warhead
- planned_use_mask_level_aware_validator: true
- planned_use_synthetic_fallback: false
- planned_allow_model_forward: true
- planned_allow_loss_compute: true
- planned_allow_backward: false
- planned_allow_optimizer: false
- planned_allow_optimizer_step: false
- planned_allow_training_step: false
- planned_allow_trainer_fit: false
- planned_allow_checkpoint_save: false
- planned_allow_model_save: false
- planned_allow_tensor_dump: false

## Reactive Atom Regions
- A_warhead_only: target
- B_linker_warhead: target
- B2_scaffold_warhead: target
- B3_scaffold_only: context
- C_scaffold_linker_warhead: target

## Blocking Policy
If the real batch cannot be converted into checkpoint-compatible model input, the next stage must cleanly block.
Synthetic 10D shape contracts may be referenced for shape comparison only; they are not an input source.
- planned_success_criteria_count: 16
- planned_blocking_criteria_count: 8

## Current Step Safety
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
- real_covalent_pretraining_smoke_design_passed: true
- real_covalent_forward_loss_smoke_plan_ready: true
- real_covalent_forward_loss_smoke_allowed: true
- all_checks_passed: true
- recommended_next_step: real_covalent_pretrained_forward_loss_smoke

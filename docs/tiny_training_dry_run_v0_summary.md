# Tiny Training Dry Run v0 Summary

Step 11L is a three-step tiny training dry run, not formal training or fine-tuning.
It uses the synthetic 10D shape contract from the previous optimizer smoke path, not a real covalent loader.
It uses only A_warhead_only and does not claim B/B2/C readiness.

## Execution
- previous_stage: tiny_training_dry_run_design_v0
- step11k_validated: true
- input_source: synthetic_10d_shape_contract
- selected_mask_levels: A_warhead_only
- checkpoint_path: checkpoints/crossdocked_fullatom_cond.ckpt
- requested_device: cpu
- resolved_device: cpu
- model_instantiated: true
- strict_load_success: true
- pretrained_weights_loaded: true
- optimizer_class: AdamW
- optimizer_lr: 1e-06
- optimizer_weight_decay: 0.0
- reuse_optimizer_across_steps: true
- step_count: 3

## Step Results
| step | mask_level | loss_value | backward | optimizer_step | grad_norm | parameter_delta_l2 | status |
| --- | --- | ---: | --- | --- | ---: | ---: | --- |
| 1 | A_warhead_only | 1.3758294582366943 | True | True | 53.11175310923403 | 0.0002464920766581291 | passed |
| 2 | A_warhead_only | 2.366245985031128 | True | True | 87.90408735301007 | 0.00021054462493646562 | passed |
| 3 | A_warhead_only | 2.434089183807373 | True | True | 74.02909413002023 | 0.0002015323036352596 | passed |

## Loss Trajectory
- loss_values: [1.3758294582366943, 2.366245985031128, 2.434089183807373]
- initial_loss_value: 1.3758294582366943
- final_loss_value: 2.434089183807373
- finite_loss_all_steps: true
- loss_decrease_required: false
- loss_decreased_optional: false
- loss_increased_warning: true

## Safety Boundary
- backward_call_count_total: 3
- optimizer_step_call_count_total: 3
- training_allowed: false
- formal_training_allowed: false
- finetune_allowed: false
- quality_claim_allowed: false
- training_step_called: false
- trainer_fit_called: false
- checkpoint_saved: false
- model_saved: false
- tensor_dump_saved: false
- original_source_files_modified: false
- forbidden_artifacts_created: false

## Decision
- tiny_training_dry_run_status: tiny_training_dry_run_passed
- tiny_training_dry_run_passed: true
- tiny_training_loop_plumbing_proven: true
- real_covalent_loader_gate_allowed: true
- b3_scaffold_only_mask_design_allowed: true
- recommended_next_step: b3_scaffold_only_mask_design

This dry run proves only in-memory loop plumbing on synthetic A_warhead_only inputs. It does not prove convergence, generation quality, real covalent data-loader readiness, or full mask-level training readiness.

# Few-Step Training Dry Run v0 Summary

This step runs a tightly capped four-step dry run for the masked covalent training loop.
It instantiates an in-memory DiffSBDD model, builds one AdamW optimizer, computes masked loss, calls backward, and executes optimizer.step for each fixed mask level.
It does not call training_step or trainer.fit.
It does not load or save checkpoints.
It does not save a model.
It does not run formal training or fine-tuning.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.

## Run Boundary
- stage: few_step_training_dry_run_no_checkpoint_v0
- previous_stage: training_loop_design_without_checkpoint_v0
- loop_name: masked_covalent_training_loop_v0
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB
- optimizer_class: AdamW
- optimizer_lr: 1e-06
- optimizer_weight_decay: 0.0
- max_steps: 4
- executed_steps: 4
- mask_order: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead
- mask_levels_seen: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead
- batch_size: 3
- shuffle: False
- seed: 4401

## Step Results
| step | mask_level | target | context | loss_total | backward | optimizer_step | grad_norm | max_grad_abs | param_delta_norm | max_param_delta_abs | status |
| ---: | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | A_warhead_only | 12 | 92 | 4.702907 | True | True | 36.652864 | 4.826686 | 0.00212338 | 0.00000101 | passed |
| 2 | B_linker_warhead | 30 | 74 | 5.700158 | True | True | 36.775534 | 4.208825 | 0.00154740 | 0.00000101 | passed |
| 3 | B2_scaffold_warhead | 86 | 18 | 5.942826 | True | True | 47.039617 | 5.349000 | 0.00149553 | 0.00000101 | passed |
| 4 | C_scaffold_linker_warhead | 104 | 0 | 6.075469 | True | True | 22.376805 | 2.701207 | 0.00147804 | 0.00000101 | passed |

## Global Result
- all_steps_passed: True
- all_losses_finite: True
- all_loss_total_requires_grad: True
- all_backward_success: True
- all_optimizer_steps_success: True
- all_gradients_finite: True
- all_gradients_nonzero: True
- all_parameter_updates_finite: True
- all_parameter_updates_nonzero: True
- all_post_step_params_finite: True
- stop_triggered: False
- stop_reason: 
- checkpoint_loaded: False
- checkpoint_saved: False
- training_step_called: False
- trainer_fit_called: False
- checkpoint_written: False
- archive_created: False
- model_saved: False
- formal_training_executed: False
- real_finetune_executed: False
- original_source_files_modified: False
- forbidden_artifacts_created: False
- all_checks_passed: True

## Recommendation
- few_step_training_dry_run_review_and_training_boundary

This is still a bounded dry run, not formal training. The next step should review the dry-run evidence and training boundary before any longer run or checkpoint policy is considered.

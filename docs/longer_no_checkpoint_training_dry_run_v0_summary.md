# Longer No-Checkpoint Training Dry Run v0 Summary

This step runs a bounded 12-step no-checkpoint dry run, not formal training.
It uses one fresh in-memory DiffSBDD model and one AdamW optimizer for the fixed loop.
The mask schedule is A/B/B2/C repeated for three complete cycles.
Loss decrease is not required, and no model-quality improvement is claimed.
It does not call training_step or trainer fit.
It does not load or save checkpoints.
It does not save a model or optimizer state.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.

## Run Boundary
- stage: longer_no_checkpoint_training_dry_run_v0
- previous_stage: longer_no_checkpoint_training_dry_run_design_v0
- loop_name: masked_covalent_training_loop_v0
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB
- optimizer_class: AdamW
- optimizer_lr: 1e-06
- optimizer_weight_decay: 0.0
- max_steps: 12
- executed_steps: 12
- dry_run_training_steps_executed: 12
- mask_schedule: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead, A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead, A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead
- mask_levels_seen: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead, A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead, A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead
- mask_counts_seen: {"A_warhead_only": 3, "B2_scaffold_warhead": 3, "B_linker_warhead": 3, "C_scaffold_linker_warhead": 3}
- batch_size: 3
- shuffle: False
- seed: 4401
- loss_decrease_required: False
- quality_claim_allowed: False

## Step Results
| step | cycle | mask_level | target | context | loss_original | loss_masked_x | loss_masked_h | loss_total | grad_norm | max_grad_abs | param_delta_norm | max_param_delta_abs | warning | stop | status |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 1 | A_warhead_only | 12 | 92 | 0.728759 | 2.281077 | 9.035510 | 4.816938 | 34.099036 | 5.166434 | 0.00212119 | 0.00000101 | False | False | passed |
| 2 | 1 | B_linker_warhead | 30 | 74 | 0.679789 | 2.636649 | 11.643035 | 5.645044 | 36.228825 | 5.575430 | 0.00158442 | 0.00000101 | False | False | passed |
| 3 | 1 | B2_scaffold_warhead | 86 | 18 | 0.689010 | 2.994613 | 11.152415 | 5.914106 | 45.650405 | 5.601943 | 0.00152269 | 0.00000101 | False | False | passed |
| 4 | 1 | C_scaffold_linker_warhead | 104 | 0 | 0.709467 | 3.084328 | 11.244324 | 6.042660 | 21.586429 | 3.227283 | 0.00149073 | 0.00000101 | False | False | passed |
| 5 | 2 | A_warhead_only | 12 | 92 | 0.737192 | 2.329640 | 11.926685 | 5.452169 | 20.791695 | 3.027795 | 0.00136493 | 0.00000101 | False | False | passed |
| 6 | 2 | B_linker_warhead | 30 | 74 | 0.703401 | 2.716179 | 12.984912 | 6.016563 | 31.966538 | 5.311038 | 0.00139012 | 0.00000101 | False | False | passed |
| 7 | 2 | B2_scaffold_warhead | 86 | 18 | 0.700370 | 3.130145 | 11.278865 | 6.086288 | 32.894753 | 5.877593 | 0.00140628 | 0.00000102 | False | False | passed |
| 8 | 2 | C_scaffold_linker_warhead | 104 | 0 | 0.682048 | 3.009262 | 10.539819 | 5.799273 | 24.666029 | 3.835530 | 0.00141171 | 0.00000102 | False | False | passed |
| 9 | 3 | A_warhead_only | 12 | 92 | 0.678683 | 3.411034 | 9.281235 | 5.945964 | 201.119884 | 36.474075 | 0.00131419 | 0.00000103 | False | False | passed |
| 10 | 3 | B_linker_warhead | 30 | 74 | 0.714474 | 3.178079 | 11.261170 | 6.144787 | 25.929107 | 4.433000 | 0.00130338 | 0.00000104 | False | False | passed |
| 11 | 3 | B2_scaffold_warhead | 86 | 18 | 0.700045 | 3.022909 | 10.703918 | 5.863738 | 23.435633 | 4.291727 | 0.00128202 | 0.00000104 | False | False | passed |
| 12 | 3 | C_scaffold_linker_warhead | 104 | 0 | 0.700474 | 3.056604 | 10.941938 | 5.945466 | 28.485119 | 5.209187 | 0.00123718 | 0.00000104 | False | False | passed |

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
- warnings_triggered: False
- warning_steps: []
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
- longer_no_checkpoint_training_dry_run_review

The next step is review of the longer dry-run evidence and boundary, not checkpointing or formal training.

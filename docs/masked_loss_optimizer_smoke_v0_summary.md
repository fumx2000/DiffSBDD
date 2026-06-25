# Masked Loss Optimizer Smoke v0 Summary

This step runs the first one-step optimizer smoke for the masked covalent loss.
It runs forward, computes masked loss, calls backward, and executes one optimizer.step().
It does not call training_step or trainer.fit.
It does not load or save checkpoints.
It does not save a model.
It does not run formal training or fine-tuning.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.

## Device And Optimizer
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB
- optimizer_class: AdamW
- optimizer_lr: 1e-06
- optimizer_weight_decay: 0.0

## One-Step Results
| mask_level | target | context | loss_total_dry | backward | optimizer_step | parameters_changed | trainable_parameters_changed | total_param_delta_norm | max_param_delta_abs | finite_delta | nonzero_delta |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| A_warhead_only | 12 | 92 | 6.018863 | True | True | 130 | 130 | 0.00214236 | 0.00000101 | True | True |
| B_linker_warhead | 30 | 74 | 5.623820 | True | True | 130 | 130 | 0.00212886 | 0.00000101 | True | True |
| B2_scaffold_warhead | 86 | 18 | 5.704935 | True | True | 130 | 130 | 0.00209948 | 0.00000101 | True | True |
| C_scaffold_linker_warhead | 104 | 0 | 5.648840 | True | True | 130 | 130 | 0.00210529 | 0.00000101 | True | True |

## Global Result
- all_mask_levels_passed: True
- all_backward_success: True
- all_optimizer_steps_success: True
- all_gradients_finite: True
- all_gradients_nonzero: True
- all_parameter_updates_finite: True
- all_parameter_updates_nonzero: True
- all_post_step_params_finite: True
- checkpoint_loaded: False
- checkpoint_saved: False
- model_saved: False
- training_executed: False
- recommended_next_step: training_loop_design_without_checkpoint

The next step is training loop design without checkpoint, not formal training.

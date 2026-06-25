# Masked Loss Backward Smoke v0 Summary

This step is the first backward smoke for the masked covalent loss.
It calls loss_total_dry.backward().
It does not run an optimizer step.
It does not call training_step or trainer.fit.
It does not load or save checkpoints.
It does not train or fine-tune a model.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.

## Device
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB

## Gradient Summary
| mask_level | target | context | loss_total_dry | parameters_with_grad | trainable_parameters_with_grad | total_grad_norm | max_grad_abs | finite_gradients | nonzero_gradients | grad_nan_count | grad_inf_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| A_warhead_only | 12 | 92 | 6.584611 | 130 | 130 | 28.027170 | 3.365876 | True | True | 0 | 0 |
| B_linker_warhead | 30 | 74 | 6.209672 | 130 | 130 | 27.717339 | 3.526812 | True | True | 0 | 0 |
| B2_scaffold_warhead | 86 | 18 | 6.321281 | 130 | 130 | 26.914097 | 3.162647 | True | True | 0 | 0 |
| C_scaffold_linker_warhead | 104 | 0 | 6.252922 | 130 | 130 | 27.997702 | 3.310892 | True | True | 0 | 0 |

## Global Result
- all_mask_levels_passed: True
- all_backward_success: True
- all_gradients_finite: True
- all_gradients_nonzero: True
- all_grad_nan_count_zero: True
- all_grad_inf_count_zero: True
- all_sources_unmodified: True
- optimizer_step_executed: False
- trainer_fit_called: False
- training_executed: False
- recommended_next_step: masked_loss_optimizer_smoke_one_step_no_checkpoint

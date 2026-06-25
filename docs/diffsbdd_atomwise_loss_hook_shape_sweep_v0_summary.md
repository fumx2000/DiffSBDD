# DiffSBDD Atomwise Loss Hook Shape Sweep v0 Summary

This step extends the Step 10K atomwise runtime probe from A to A/B/B2/C mask levels.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.
It does not load or save checkpoints.
It does not call training_step, backward, optimizer, trainer.fit, training, or fine-tuning.
It still does not compute a masked loss scalar; that is reserved for the next dry run.

## Device
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB

## Mask Sweep
| mask_level | target_atoms | context_atoms | behavior_preserved | captured | residual_x | residual_h | can_masked_x | can_masked_h |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| A_warhead_only | 12 | 92 | True | True | [104, 3] | [104, 11] | True | True |
| B_linker_warhead | 30 | 74 | True | True | [104, 3] | [104, 11] | True | True |
| B2_scaffold_warhead | 86 | 18 | True | True | [104, 3] | [104, 11] | True | True |
| C_scaffold_linker_warhead | 104 | 0 | True | True | [104, 3] | [104, 11] | True | True |

## Global Result
- all_mask_levels_passed: True
- all_default_behavior_preserved: True
- all_atomwise_tensors_captured: True
- all_residuals_finite: True
- all_targets_nonempty: True
- all_methods_restored: True
- all_sources_unmodified: True
- recommended_next_step: masked_loss_dry_run_without_backward

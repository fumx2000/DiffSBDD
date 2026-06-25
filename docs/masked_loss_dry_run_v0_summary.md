# Masked Loss Dry Run v0 Summary

This step computes masked covalent loss scalars for the first time.
It does not call backward, optimizer, trainer.fit, training, or fine-tuning.
It does not load or save checkpoints.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.

## Device
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB

## Masked Losses
| mask_level | target | context | loss_original | loss_masked_x | loss_masked_h | loss_total_dry | finite | requires_grad |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| A_warhead_only | 12 | 92 | 0.717626 | 3.864162 | 11.725685 | 6.926926 | True | True |
| B_linker_warhead | 30 | 74 | 0.718003 | 3.577101 | 11.865649 | 6.668234 | True | True |
| B2_scaffold_warhead | 86 | 18 | 0.718003 | 3.213859 | 11.038163 | 6.139494 | True | True |
| C_scaffold_linker_warhead | 104 | 0 | 0.718003 | 3.243302 | 11.186742 | 6.198653 | True | True |

A/B/B2 use target subsets. C is a full-ligand target by design.

## Global Result
- all_mask_levels_passed: True
- all_loss_scalars_finite: True
- all_loss_total_requires_grad: True
- all_target_masks_nonempty: True
- all_expected_target_counts: True
- all_expected_context_counts: True
- all_sources_unmodified: True
- recommended_next_step: masked_loss_backward_smoke_without_optimizer

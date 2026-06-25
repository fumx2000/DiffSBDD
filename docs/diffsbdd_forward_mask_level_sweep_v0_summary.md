# DiffSBDD Forward Mask-level Sweep v0 Summary

This step calls the real DiffSBDD forward path for all four mask levels: A, B, B2, and C.
It does not load a checkpoint.
It does not call training_step.
It does not run backward.
It does not run an optimizer step.
It does not call trainer.fit.
It does not train or fine-tune.
It does not save a model.
It does not modify DiffSBDD or equivariant_diffusion.
This is still not training; it is a forward sweep only.

- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB
- all_mask_levels_passed: True

| mask_level | target_atom_count | context_atom_count | forward_success | output_type | finite_tensor_outputs |
| --- | ---: | ---: | --- | --- | --- |
| A_warhead_only | 12 | 92 | true | tuple | true |
| B_linker_warhead | 30 | 74 | true | tuple | true |
| B2_scaffold_warhead | 86 | 18 | true | tuple | true |
| C_scaffold_linker_warhead | 104 | 0 | true | tuple | true |

- checkpoint_loaded: False
- checkpoint_saved: False
- training_step_called: False
- backward_called: False
- optimizer_step_executed: False
- trainer_fit_called: False
- training_executed: False
- real_finetune_executed: False
- recommended_next_step: diffsbdd_forward_loss_semantics_review_without_backward

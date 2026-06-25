# DiffSBDD Atomwise Loss Hook Prototype v0 Summary

This step implements a runtime hook/probe prototype.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.
It does not load or save checkpoints.
It does not call training_step, backward, optimizer, trainer.fit, training, or fine-tuning.

## Device
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB

## Forward Behavior
- mask_level: A_warhead_only
- model_initialized: True
- model_mode: train
- forward_no_probe_success: True
- forward_probe_success: True
- default_behavior_preserved: True
- output0_allclose: True
- output1_scalar_allclose: True

## Captured Tensors
- eps_t_lig_shape: [104, 14]
- net_out_lig_shape: [104, 14]
- ligand_mask_flat_shape: [104]
- net_out_lig_requires_grad: True
- tensor_first_dim_matches_ligand_atoms: True
- target_mask_nonempty: True
- residual_x_shape: [104, 3]
- residual_h_shape: [104, 11]
- residual_x_finite: True
- residual_h_finite: True
- can_compute_masked_x_loss_later: True
- can_compute_masked_h_loss_later: True

## Safety
- checkpoint_loaded: false
- checkpoint_saved: false
- training_step_called: false
- backward_called: false
- optimizer_step_executed: false
- trainer_fit_called: false
- training_executed: false
- real_finetune_executed: false
- checkpoint_written: false
- archive_created: false
- original_methods_restored: True
- original_source_files_modified: False

## Conclusion
- smoke_status: passed
- recommended_next_step: atomwise_loss_hook_shape_sweep_without_backward

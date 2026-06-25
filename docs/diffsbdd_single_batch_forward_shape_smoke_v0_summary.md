# DiffSBDD Single-batch Forward Shape Smoke v0 Summary

This step calls the real DiffSBDD forward path for the first time, without loading a checkpoint.
It is a single-batch shape smoke only.
It does not call training_step.
It does not run backward.
It does not run an optimizer step.
It does not call trainer.fit.
It does not save a model.
It does not modify DiffSBDD or equivariant_diffusion.

- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB
- mask_level: A_warhead_only
- model_initialized: True
- forward_called: True
- forward_success: True
- selected_forward_call_style: LigandPocketDDPM.forward(data_batch)
- output_type: tuple
- output_keys: ['0', '1']
- tensor_output_shapes: {'output.0': [3], 'output.1.eps_hat_lig_x': [], 'output.1.eps_hat_lig_h': [], 'output.1.error_t_lig': [], 'output.1.error_t_pocket': [], 'output.1.SNR_weight': [], 'output.1.loss_0': [], 'output.1.kl_prior': [], 'output.1.delta_log_px': [], 'output.1.neg_log_const_0': [], 'output.1.log_pN': []}
- finite_tensor_outputs: True
- scalar_loss_like_output_finite: True

- checkpoint_loaded: False
- checkpoint_saved: False
- training_step_called: False
- backward_called: False
- optimizer_step_executed: False
- trainer_fit_called: False
- training_executed: False
- real_finetune_executed: False
- recommended_next_step: diffsbdd_forward_mask_level_sweep_without_checkpoint

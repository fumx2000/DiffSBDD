# DiffSBDD Backward Smoke v0 Summary

This step is the first real DiffSBDD loss.backward smoke on the covalent batch.
It does not load checkpoints.
It does not call training_step.
It does not run an optimizer step.
It does not call trainer.fit.
It does not save a model.
It does not train or fine-tune.
It does not modify DiffSBDD or equivariant_diffusion.

- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB
- mask_level: A_warhead_only
- model_mode: train
- loss_reduction: mean
- scalar_loss_finite: True
- backward_success: True
- finite_gradients: True
- nonzero_gradients: True
- parameters_with_grad: 130
- trainable_parameters_with_grad: 130
- total_grad_norm: 1.0699462526416705
- max_grad_abs: 0.12681612372398376
- grad_nan_count: 0
- grad_inf_count: 0

Limitation: this only proves the original DiffSBDD full-ligand loss can backpropagate.
It does not prove that masked covalent loss is implemented.
A masked loss adapter is still required.

- recommended_next_step: masked_loss_adapter_design_without_diffsbdd_modification

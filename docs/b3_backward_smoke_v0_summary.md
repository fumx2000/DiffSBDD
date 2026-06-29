# B3 Backward Smoke v0 Summary

Step 11Q is a B3 backward smoke, not training.
It uses a fresh strict-loaded pretrained checkpoint-compatible model.
It uses canonical long-form `B3_scaffold_only` only with `synthetic_10d_shape_contract`.
It computes the B3 masked loss and executes exactly one controlled reverse pass.

## Loss
- checkpoint_path: checkpoints/crossdocked_fullatom_cond.ckpt
- requested_device: cpu
- resolved_device: cpu
- model_instantiated: true
- strict_load_success: true
- pretrained_weights_loaded: true
- pretrained_base_integration_proven: true
- model_forward_called: true
- loss_computed: true
- selected_loss_key: masked_loss_total_dry
- selected_loss_value: 26.204837799072266
- loss_requires_grad: true
- loss_finite: true

## B3 Contract
- b3_target_atom_count: 3
- b3_context_atom_count: 4
- b3_reactive_atom_in_context: true
- b3_reactive_atom_in_target: false

## Gradient Evidence
- backward_called: true
- backward_call_count: 1
- backward_success: true
- finite_nonzero_grad_exists: true
- trainable_parameter_count: 1005418
- parameters_with_grad_count: 111
- total_grad_norm: 1153.4507620392994
- max_abs_grad: 651.8541259765625
- grad_nan_count: 0
- grad_inf_count: 0

## Limits
- This does not prove convergence, generation quality, or real loader readiness.
- It does not create an optimizer and does not run a parameter update.

## Safety Boundary
- optimizer_created: false
- optimizer_step_called: false
- training_step_called: false
- trainer_fit_called: false
- checkpoint_saved: false
- model_saved: false
- tensor_dump_saved: false
- original_diffsbdd_source_modified: false
- forbidden_artifacts_created: false

## Decision
- b3_backward_smoke_passed: true
- b3_backward_gradient_contract_proven: true
- b3_finite_nonzero_gradient_proven: true
- b3_single_optimizer_step_smoke_allowed: true
- recommended_next_step: b3_single_optimizer_step_smoke

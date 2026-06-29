# B3 Single Optimizer Step Smoke v0 Summary

Step 11R is a B3 single AdamW update smoke, not training.
It uses a fresh strict-loaded pretrained checkpoint-compatible model.
It uses canonical long-form `B3_scaffold_only` only.
It computes the B3 masked loss, executes exactly one controlled reverse pass, and executes exactly one AdamW update step.

## Loss And Gradient
- checkpoint_path: checkpoints/crossdocked_fullatom_cond.ckpt
- requested_device: cpu
- resolved_device: cpu
- model_instantiated: true
- strict_load_success: true
- pretrained_weights_loaded: true
- pretrained_base_integration_proven: true
- selected_loss_key: masked_loss_total_dry
- selected_loss_value: 89.24312591552734
- loss_requires_grad: true
- loss_finite: true
- backward_call_count: 1
- finite_nonzero_grad_exists: true
- total_grad_norm: 2391.156354662466
- max_abs_grad: 1133.984130859375

## Optimizer Update
- optimizer_type: AdamW
- learning_rate: 1e-06
- weight_decay: 0.0
- optimizer_created: true
- optimizer_step_call_count: 1
- sampled_parameter_count: 20
- sampled_parameter_delta_l2: 0.00024675636571797375
- sampled_parameter_delta_max_abs: 1.0132789611816406e-06
- updated_parameter_tensors_count: 20
- parameter_update_finite: true
- parameter_update_nonzero: true

## B3 Contract
- b3_target_atom_count: 3
- b3_context_atom_count: 4
- b3_reactive_atom_in_context: true
- b3_reactive_atom_in_target: false

## Limits
- This does not prove convergence, generation quality, or real loader readiness.
- B3 tiny loop is optional, not the mainline next step.

## Safety Boundary
- training_step_called: false
- trainer_fit_called: false
- checkpoint_saved: false
- model_saved: false
- tensor_dump_saved: false
- original_diffsbdd_source_modified: false
- forbidden_artifacts_created: false

## Decision
- b3_single_optimizer_step_smoke_passed: true
- b3_parameter_update_contract_proven: true
- b3_finite_nonzero_parameter_update_proven: true
- b3_tiny_loop_optional: true
- real_covalent_feature_mapping_loader_gate_allowed: true
- recommended_next_step: real_covalent_feature_mapping_loader_gate

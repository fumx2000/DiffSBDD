# B3 Pretrained Masked Loss Smoke v0 Summary

Step 11P is B3 pretrained masked loss smoke, not training.
It uses a fresh strict-loaded pretrained checkpoint-compatible model.
It uses canonical long-form `B3_scaffold_only` only.
B3 target=['scaffold']; context=['linker', 'warhead'].

## Smoke Result
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
- selected_loss_value: 23.713951110839844
- loss_requires_grad: true
- loss_finite: true

## B3 Contract
- b3_target_atom_count: 3
- b3_context_atom_count: 4
- b3_reactive_atom_in_context: true
- b3_reactive_atom_in_target: false

## Limits
- This does not prove convergence, generation quality, or real loader readiness.
- It does not run a parameter update.

## Safety Boundary
- backward_called: false
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
- b3_pretrained_masked_loss_smoke_passed: true
- b3_pretrained_forward_loss_contract_proven: true
- b3_backward_smoke_allowed: true
- recommended_next_step: b3_backward_smoke

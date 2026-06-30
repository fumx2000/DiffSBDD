# Real Covalent Backward Smoke v0 Summary

Step 12E is a real covalent backward smoke, not training.
It uses the real covalent sample_index and does not use synthetic fallback.
It runs one forward/loss pass per canonical mask level, then one aggregate reverse pass.
It does not create an optimizer, call training_step, call trainer.fit, or save checkpoint/model/tensor dump.
Formal training still requires a separate feature semantics audit before optimizer or checkpointed training stages.

## Inputs
- input_source: real_covalent_training_tensor_materialized_v0
- selected_sample_index: data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv
- checkpoint_path: checkpoints/crossdocked_fullatom_cond.ckpt
- requested_device: cpu
- resolved_device: cpu
- batch_size: 2
- num_workers: 0

## Mask Levels
- canonical_mask_levels: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, B3_scaffold_only, C_scaffold_linker_warhead
- A_warhead_only expected reactive atom region: target
- B_linker_warhead expected reactive atom region: target
- B2_scaffold_warhead expected reactive atom region: target
- B3_scaffold_only expected reactive atom region: context
- C_scaffold_linker_warhead expected reactive atom region: target

## Pretrained Model
- model_instantiated: true
- strict_load_success: true
- pretrained_weights_loaded: true
- pretrained_base_integration_proven: true
- model_strict_loaded_once: true

## Forward/Loss Results
- model_forward_called: true
- model_forward_call_count: 5
- all_level_forward_call_count_exactly_one: true
- all_losses_computed: true
- all_losses_finite: true
- all_losses_require_grad: true
- selected_loss_key: masked_loss_total_dry

## Per-Level Loss Table
| mask_level | selected_loss_value | loss_finite | loss_requires_grad |
| --- | ---: | --- | --- |
| A_warhead_only | 71.62177276611328 | true | true |
| B_linker_warhead | 215.59085083007812 | true | true |
| B2_scaffold_warhead | 87.4021224975586 | true | true |
| B3_scaffold_only | 183.014404296875 | true | true |
| C_scaffold_linker_warhead | 1423.0787353515625 | true | true |

## Aggregate Backward
- aggregate_loss_reduction: mean
- aggregate_loss_value: 396.1415710449219
- aggregate_loss_finite: true
- aggregate_loss_requires_grad: true
- backward_called: true
- backward_call_count: 1
- backward_exactly_once: true
- backward_success: true
- trainable_parameter_count: 1005418
- parameters_with_grad_count: 111
- parameters_with_nonzero_grad_count: 111
- finite_nonzero_gradients: true
- total_grad_norm: 4582.194480699887
- max_abs_grad: 868.5007934570312
- grad_nan_count: 0
- grad_inf_count: 0

## Safety Boundary
- optimizer_created: false
- optimizer_step_called: false
- training_step_called: false
- trainer_fit_called: false
- checkpoint_saved: false
- model_saved: false
- tensor_dump_saved: false
- npz_created: false
- original_diffsbdd_source_modified: false
- forbidden_artifacts_created: false

## Decision
- real_covalent_backward_smoke_passed: true
- real_covalent_backward_contract_proven: true
- real_covalent_single_optimizer_step_smoke_allowed: true
- all_checks_passed: true
- recommended_next_step: real_covalent_single_optimizer_step_smoke

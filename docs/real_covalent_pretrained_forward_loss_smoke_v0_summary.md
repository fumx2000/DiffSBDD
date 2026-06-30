# Real Covalent Pretrained Forward/Loss Smoke v0 Summary

Step 12D is a real covalent pretrained forward/loss smoke, not training.
It uses the real covalent sample_index and does not use synthetic fallback.
It does not run backward, create an optimizer, call training_step, call trainer.fit, or save checkpoint/model/tensor dump.

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
- min_selected_loss_value: 103.82839965820312
- max_selected_loss_value: 215.79139709472656
- mean_selected_loss_value: 154.95272827148438

## Per-Level Loss Table
| mask_level | selected_loss_value | loss_finite | loss_requires_grad |
| --- | ---: | --- | --- |
| A_warhead_only | 215.79139709472656 | true | true |
| B_linker_warhead | 131.23306274414062 | true | true |
| B2_scaffold_warhead | 154.4330596923828 | true | true |
| B3_scaffold_only | 103.82839965820312 | true | true |
| C_scaffold_linker_warhead | 169.47772216796875 | true | true |

## Safety Boundary
- backward_called: false
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
- real_covalent_pretrained_forward_loss_smoke_passed: true
- real_covalent_forward_loss_contract_proven: true
- real_covalent_all_mask_levels_forward_loss_proven: true
- real_covalent_backward_smoke_allowed: true
- all_checks_passed: true
- recommended_next_step: real_covalent_backward_smoke

# Pretrained Masked Loss Smoke v0 Summary

Step 11F is a pretrained masked loss smoke, not training.
It strict-loads the checkpoint-compatible pretrained model and runs no-grad masked loss smoke over A/B/B2/C.
It uses a synthetic 10D shape-only contract, so it does not prove generation quality or loss decrease.

## Pretrained Base
- checkpoint_sha256: 07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c
- pretrained_weights_loaded: true
- pretrained_base_integration_proven: true
- strict_load_success: true

## Mask Levels
| mask_level | selected_primary_loss_key | selected_primary_loss_value | finite_loss | status |
| --- | --- | ---: | --- | --- |
| A_warhead_only | masked_loss_total_dry | 24.993852615356445 | true | passed |
| B_linker_warhead | masked_loss_total_dry | 64.95052337646484 | true | passed |
| B2_scaffold_warhead | masked_loss_total_dry | 16.925447463989258 | true | passed |
| C_scaffold_linker_warhead | masked_loss_total_dry | 508.4341735839844 | true | passed |

## Boundary
- synthetic_shape_smoke_only: true
- feature_semantics_known: false
- synthetic_mask_loss_adapter_used: true
- all_mask_levels_passed: true
- pretrained_masked_loss_smoke_passed: true
- microbatch_dry_run_allowed: true
- training_allowed: false
- formal_training_allowed: false
- finetune_allowed: false
- optimizer_allowed: false
- checkpoint_saved: false
- model_saved: false
- recommended_next_step: pretrained_masked_loss_microbatch_dry_run_design

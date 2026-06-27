# Pretrained Masked Loss Microbatch Backward Dry Run v0 Summary

Step 11H is a backward dry run, not formal training.
It uses fresh strict-loaded pretrained models per mask level and runs one isolated reverse pass for each mask.
It does not create an optimizer, does not step parameters, and does not save a checkpoint or model.

## Gradient Table
| mask_level | selected_loss_value | backward_success | parameters_with_grad_count | total_grad_norm | max_abs_grad | grad_nan_count | grad_inf_count |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| A_warhead_only | 3.3604235649108887 | true | 111 | 118.79651159480801 | 32.380165100097656 | 0 | 0 |
| B_linker_warhead | 1.626440405845642 | true | 111 | 46.53674739523468 | 10.102252960205078 | 0 | 0 |
| B2_scaffold_warhead | 1.6261783838272095 | true | 111 | 50.883000892148154 | 9.721502304077148 | 0 | 0 |
| C_scaffold_linker_warhead | 1.1443536281585693 | true | 111 | 40.13544704767323 | 7.900495529174805 | 0 | 0 |

## Boundary
- all_mask_levels_passed: true
- backward_call_count_total: 4
- finite_nonzero_grad_all_levels: true
- grad_nan_count_total: 0
- grad_inf_count_total: 0
- microbatch_backward_status: pretrained_microbatch_backward_dry_run_passed
- gradient_plumbing_proven: true
- optimizer_smoke_design_allowed: true
- optimizer_created: false
- optimizer_step_called: false
- training_allowed: false
- formal_training_allowed: false
- finetune_allowed: false
- checkpoint_saved: false
- model_saved: false
- recommended_next_step: optimizer_free_to_optimizer_smoke_design

This dry run proves gradient plumbing only. It does not prove loss decrease, generation quality, or real covalent data-loader training readiness.

# Single Optimizer Step Smoke v0 Summary

Step 11J is a single optimizer step smoke, not formal training.
It uses one fresh strict-loaded pretrained model, one A_warhead_only synthetic 10D microbatch, one reverse pass, and one optimizer step.
It does not save checkpoint, model, optimizer, full tensor, or parameter-delta tensor artifacts.

## Optimizer
- optimizer_class: AdamW
- optimizer_lr: 1e-06
- optimizer_weight_decay: 0.0
- selected_mask_level: A_warhead_only

## Loss And Gradient
- selected_loss_key: masked_loss_total_differentiable
- selected_loss_value: 1.6932651996612549
- loss_requires_grad: true
- loss_finite: true
- backward_call_count: 1
- total_grad_norm: 64.12879644470894
- max_abs_grad: 15.534242630004883
- grad_nan_count: 0
- grad_inf_count: 0

## Optimizer Step Delta
- optimizer_step_call_count: 1
- sampled_parameter_count: 20
- changed_parameter_count: 20
- unchanged_parameter_count: 0
- parameter_delta_l2_total: 0.0002464914740098643
- parameter_delta_max_abs: 1.0132789611816406e-06
- parameter_delta_mean_abs: 9.956481736214966e-07
- finite_parameter_delta: true
- delta_nan_count: 0
- delta_inf_count: 0

## Boundary
- single_optimizer_step_smoke_passed: true
- optimizer_plumbing_proven: true
- tiny_training_dry_run_design_allowed: true
- training_allowed: false
- formal_training_allowed: false
- finetune_allowed: false
- training_step_called: false
- trainer_fit_called: false
- checkpoint_saved: false
- model_saved: false
- tensor_dump_saved: false
- recommended_next_step: tiny_training_dry_run_design

This smoke does not prove loss decrease, generation quality, or real covalent data-loader training readiness.

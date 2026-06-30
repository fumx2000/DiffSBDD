# Real Covalent Filtered Single Optimizer Step Smoke v0 Summary

Step 12K is a filtered single optimizer step smoke, not formal training.
It uses the Step 12H production filter helper and validates Step 12J CUDA forward/backward smoke before the update.
AdamW is created exactly once, optimizer.step exactly once, and no checkpoint/model/tensor dump is saved.

## CUDA Execution
- cuda_available: true
- requested_device: cuda
- resolved_device: cuda:0
- cuda_device_name: NVIDIA A100-SXM4-80GB
- torch_version: 2.0.1

## Filtered Forward/Loss/Backward
- production_filter_helper_used: true
- all_filtered_batches_on_cuda: true
- model_strict_loaded_once: true
- model_device: cuda:0
- model_forward_call_count: 5
- loss_compute_call_count: 5
- selected_loss_key: masked_loss_total_dry
- aggregate_loss_reduction: mean
- aggregate_loss_value: 126.14019012451172
- backward exactly once: true

## Parameter Update
- optimizer_name: AdamW
- optimizer_lr: 1e-06
- optimizer_weight_decay: 0.0
- optimizer_create_count: 1
- optimizer_step_call_count: 1
- finite nonzero update: true
- parameters_checked_for_update_count: 115
- parameters_changed_count: 111
- total_update_norm: 0.0010044588690241347
- max_abs_update: 1.0132789611816406e-06

## Decision
- real_covalent_filtered_single_optimizer_step_smoke_passed: true
- real_covalent_filtered_single_update_contract_proven: true
- real_covalent_filtered_multi_step_training_allowed: false
- recommended_next_step: real_covalent_training_loop_design_gate

## Scope Boundary
- not formal training
- no checkpoint save
- no model save
- no tensor dump
- V1 remains Cys-first: cys_with_known_reconstruction_template_only
- Non-Cys data policy: identify_classify_defer_until_template_gate
- reaction_family_template_audit_required_before_broad_covalent_training: true
- ligand_reconstruction_template_gate_required: true

# Optimizer Smoke Design v0 Summary

Step 11I is an optimizer smoke design step, not training.
Step 11H already proved pretrained masked-loss gradient plumbing over A/B/B2/C.
This step only designs the next single optimizer-step smoke and writes evidence.

## Recommended 11J Boundary
- proposed_next_stage: optimizer_step_smoke_v0
- selected_initial_mask_level: A_warhead_only
- input_source: synthetic_10d_shape_contract
- model_policy: fresh_strict_loaded_pretrained_model
- optimizer_policy: single AdamW optimizer for smoke only
- optimizer_class: AdamW
- optimizer_import_path_next_step: torch.optim.AdamW
- optimizer_lr_recommended: 1e-06
- optimizer_weight_decay_recommended: 0.0
- optimizer_step_policy: single optimizer.step exactly once
- optimizer_step_call_count_next_step: 1
- checkpoint_save_allowed_next_step: false
- model_save_allowed_next_step: false

## Pass Conditions
- loss finite
- loss.requires_grad true
- backward_success true
- optimizer_created true
- optimizer_step_called true
- optimizer_step_call_count equals 1
- at least one parameter changed
- parameter_delta_l2_total finite positive
- parameter_delta_max_abs finite positive
- no NaN/Inf in changed parameters
- no checkpoint/model saved

## Non-Claims
- not formal training
- loss decrease is not required
- no generation quality claim
- no real covalent data-loader training claim

## Risks
- R1_synthetic_10d_contract: Synthetic 10D contract still does not prove real covalent feature semantics. Mitigation: Keep Step 11J as optimizer plumbing only and retain no quality claims.
- R2_in_memory_pretrained_weight_update: The optimizer step will change pretrained weights in memory only. Mitigation: Do not save checkpoint/model artifacts; discard model after measurement.
- R3_lr_too_large: Too-large learning rate may perturb parameters more than needed for a smoke test. Mitigation: Use AdamW with lr=1e-6 and weight_decay=0.0 for the first step smoke.
- R4_lr_too_small: Too-small learning rate may produce parameter deltas near floating-point precision. Mitigation: Require positive finite parameter delta summaries and report unchanged parameter counts.
- R5_optimizer_state_not_training_loop_readiness: AdamW state creation alone does not prove scheduler, clipping, accumulation, or loop readiness. Mitigation: Defer scheduler, clipping, and accumulation to later explicit gates.
- R6_scheduler_clipping_accumulation_untested: No scheduler, mixed precision, gradient accumulation, or clipping will be tested. Mitigation: State these as exclusions in the Step 11J report.
- R7_real_covalent_loader_unresolved: Real covalent loader and feature mapping remain outside this optimizer smoke. Mitigation: Keep synthetic shape-only labels and require later real-data mapping gates.
- R8_parameter_delta_tensor_leak: Parameter delta evidence must not write tensor dumps or model snapshots. Mitigation: Record only scalar summaries and sampled parameter names.

## Decision
- design_status: optimizer_smoke_design_ready
- optimizer_step_smoke_allowed: true
- this_design_creates_optimizer: false
- this_design_runs_optimizer_step: false
- this_design_runs_backward: false
- training_allowed: false
- formal_training_allowed: false
- finetune_allowed: false
- checkpoint_saved: false
- model_saved: false
- recommended_next_step: single_optimizer_step_smoke

# Pretrained Masked Loss Microbatch Design v0 Summary

Step 11G is a microbatch dry-run design step, not training.
Step 11F already proved checkpoint-compatible pretrained masked loss smoke over A/B/B2/C.
This step only designs the next backward-only microbatch dry run and writes evidence.

## 11H Boundary
- proposed_next_stage: pretrained_masked_loss_microbatch_dry_run_v0
- microbatch_backward_policy: isolated_backward_per_mask_level
- mask_levels_for_backward_dry_run: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead
- fresh_model_per_mask_level: true
- backward_allowed_next_step: true
- optimizer_allowed_next_step: false
- optimizer_step_allowed_next_step: false
- checkpoint_save_allowed_next_step: false
- model_save_allowed_next_step: false

## Input Source
- recommended_microbatch_input_source: synthetic_10d_shape_contract
- real_covalent_sample_available: true
- synthetic_10d_contract_available: true
- rationale: real covalent artifacts exist, but the checkpoint-compatible pretrained model still uses a synthetic 10D shape contract.

## Risks
- R1_synthetic_10d_semantics: Synthetic 10D contract is not the same as real covalent data feature semantics. Mitigation: Use Step 11H only for gradient plumbing; keep real feature mapping as a later gate.
- R2_reverse_pass_surface: The microbatch dry run may expose detached loss or in-place operation issues. Mitigation: Require loss.requires_grad, finite gradients, and isolated fresh model per mask level.
- R3_large_C_level_loss_scale: C mask loss scale is larger than other mask levels and may amplify gradients. Mitigation: Log total grad norm and max absolute grad for every mask level.
- R4_no_parameter_update_claim: No optimizer step means 11H cannot prove parameter update behavior. Mitigation: Keep 11H as backward-only; require a later explicit optimizer smoke gate.
- R5_fresh_model_runtime: Fresh model per mask level is slower but reduces gradient contamination. Mitigation: Accept slower runtime for the first pretrained microbatch dry run.
- R6_real_covalent_loader_gap: Real covalent feature mapping and loader integration remain unresolved for checkpoint-compatible 10D inputs. Mitigation: Do not claim real-data training readiness until a real feature mapping gate passes.

## Decision
- design_status: microbatch_dry_run_design_ready
- microbatch_backward_dry_run_allowed: true
- this_design_executes_backward: false
- this_design_creates_optimizer: false
- training_allowed: false
- formal_training_allowed: false
- finetune_allowed: false
- optimizer_step_allowed: false
- checkpoint_saved: false
- model_saved: false
- recommended_next_step: pretrained_masked_loss_microbatch_backward_dry_run

# Longer No-Checkpoint Training Dry Run Design v0 Summary

Step 10S is a design step, not training.
It does not instantiate a model, run forward, call backward, execute optimizer step, call training step, call trainer fit, load or save checkpoints, save a model, or fine-tune.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.

## Purpose
The 12-step dry run is intended to validate longer loop stability and boundary enforcement. It does not claim model quality or generation improvement.

## Schedule
- max_steps: 12
- batch_size: 3
- shuffle: False
- seed: 4401
- mask_schedule: A_warhead_only / B_linker_warhead / B2_scaffold_warhead / C_scaffold_linker_warhead repeated 3 cycles
- mask_counts: {"A_warhead_only": 3, "B2_scaffold_warhead": 3, "B_linker_warhead": 3, "C_scaffold_linker_warhead": 3}

## Loss Policy
- loss_weights: {"w_h": 0.2, "w_original": 1.0, "w_x": 1.0}
- loss_decrease_required: False
- quality_claim_allowed: False

## Still Forbidden
- checkpoint_allowed: False
- model_save_allowed: False
- checkpoint_load_allowed: False
- checkpoint_save_allowed: False
- trainer_fit_allowed: False
- training_step_allowed: False
- source_modification_allowed: False

## Hard Stop Conditions
- abort on non-finite loss
- abort on loss_total_requires_grad=false
- abort on non-finite gradients
- abort on gradients all zero
- abort on grad_nan_count > 0
- abort on grad_inf_count > 0
- abort on optimizer step failure
- abort on non-finite parameter delta
- abort on zero parameter delta
- abort on post-step parameter NaN/Inf
- abort on zero target mask
- abort on unexpected mask level
- abort on checkpoint/model artifact
- abort on source modification

## Checkpoint Boundary
Checkpoint discussion remains deferred until the 12-step no-checkpoint dry run passes, output/checkpoint naming and retention policies are reviewed, and explicit user approval is given.

## Recommended Next Step
- longer_no_checkpoint_training_dry_run

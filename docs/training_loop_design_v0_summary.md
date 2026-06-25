# Training Loop Design v0 Summary

Step 10P is a training loop design review, not training.
It does not instantiate a model, call backward, run an optimizer step, call training_step, call trainer.fit, or save checkpoints.
It does not save a model and does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.

## Why Not Formal Training Yet
Step 10O only proved a single in-memory optimizer step works. A controlled few-step dry run must first prove loop logging, stop conditions, output boundaries, and source immutability.

## Next Dry Run Shape
- loop_name: masked_covalent_training_loop_v0
- intended_next_stage: few_step_training_dry_run_no_checkpoint
- mask_schedule_name: balanced_A_B_B2_C_cycle
- mask_order: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead
- max_steps_initial_dry_run: 4
- batch_size: 3
- shuffle: False
- loss_weights: {"w_h": 0.2, "w_original": 1.0, "w_x": 1.0}

## Allowed Next-Stage Actions
- instantiate model
- build optimizer
- iterate over dataloader
- compute masked loss
- backward
- optimizer.step
- log scalar metrics

## Forbidden Next-Stage Actions
- trainer.fit
- training_step
- checkpoint loading
- checkpoint saving
- torch.save
- model saving
- archive writing
- modifying DiffSBDD source files
- source modification

## Required Stop Conditions
- max_steps hard cap
- finite loss required
- finite gradients required
- finite parameters after step required
- no NaN/Inf in loss/grad/params
- abort on unexpected mask level
- abort on missing target mask

## Required Logging Fields
- step
- mask_level
- sample_ids
- loss_original
- loss_masked_x
- loss_masked_h
- loss_total
- target_atom_count
- context_atom_count
- grad_norm
- max_grad_abs
- param_delta_norm
- max_param_delta_abs
- learning_rate
- optimizer_class
- cuda_device
- elapsed_seconds

## Checkpoint Boundary
- checkpoint_allowed: False
- model_save_allowed: False
Checkpoint discussion is deferred until a few-step loop passes, output naming and retention policies are reviewed, and explicit user approval is given.

## Rollback And Failure Handling
The few-step dry run should abort on first failed invariant, write report-only diagnostics, and discard the in-memory model instance. No checkpoint or model artifact should exist to roll back.

## Recommended Next Step
- few_step_training_dry_run_no_checkpoint

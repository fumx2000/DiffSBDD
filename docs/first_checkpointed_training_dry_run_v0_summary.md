# First Checkpointed Training Dry Run v0 Summary

This step runs a tightly bounded first checkpointed dry run, not formal training.
It executes the approved 12-step masked covalent loop and saves exactly one final dictionary checkpoint.
The checkpoint contains model_state_dict, optimizer_state_dict, scalar evidence, and run metadata.
It does not call training_step, trainer fit, or save a model object.
It does not fine-tune or claim model quality.
It does not modify DiffSBDD, equivariant_diffusion, or lightning_modules source files.

## Run
- stage: first_checkpointed_training_dry_run_v0
- previous_stage: checkpoint_output_policy_design_v0
- run_name: first_checkpointed_training_dry_run_v0
- run_root: data/derived/covalent_small/training_runs/first_checkpointed_training_dry_run_v0
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB
- optimizer_class: AdamW
- optimizer_lr: 1e-06
- optimizer_weight_decay: 0.0
- max_steps: 12
- executed_steps: 12
- mask_schedule: A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead, A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead, A_warhead_only, B_linker_warhead, B2_scaffold_warhead, C_scaffold_linker_warhead
- loss_weights: {"w_h": 0.2, "w_original": 1.0, "w_x": 1.0}

## Step Evidence
| step | mask_level | target | context | loss_total | grad_norm | param_delta_norm | checkpoint_saved | status |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | A_warhead_only | 12 | 92 | 4.682796 | 34.785995 | 0.00211840 | False | passed |
| 2 | B_linker_warhead | 30 | 74 | 5.677396 | 35.610003 | 0.00150072 | False | passed |
| 3 | B2_scaffold_warhead | 86 | 18 | 5.932877 | 45.385184 | 0.00145984 | False | passed |
| 4 | C_scaffold_linker_warhead | 104 | 0 | 6.065060 | 21.823963 | 0.00143695 | False | passed |
| 5 | A_warhead_only | 12 | 92 | 5.401952 | 20.327201 | 0.00131955 | False | passed |
| 6 | B_linker_warhead | 30 | 74 | 6.027043 | 31.498114 | 0.00130698 | False | passed |
| 7 | B2_scaffold_warhead | 86 | 18 | 6.077600 | 32.683584 | 0.00133486 | False | passed |
| 8 | C_scaffold_linker_warhead | 104 | 0 | 5.820906 | 24.949945 | 0.00135689 | False | passed |
| 9 | A_warhead_only | 12 | 92 | 5.914117 | 198.842681 | 0.00126422 | False | passed |
| 10 | B_linker_warhead | 30 | 74 | 6.143737 | 25.868097 | 0.00126969 | False | passed |
| 11 | B2_scaffold_warhead | 86 | 18 | 5.876759 | 23.465082 | 0.00124099 | False | passed |
| 12 | C_scaffold_linker_warhead | 104 | 0 | 6.016799 | 28.406167 | 0.00123013 | True | passed |

## Checkpoint
- checkpoint_saved: True
- checkpoint_path: data/derived/covalent_small/training_runs/first_checkpointed_training_dry_run_v0/checkpoints/checkpoint_step_000012.pt
- checkpoint_filename: checkpoint_step_000012.pt
- checkpoint_count: 1
- checkpoint_sha256: c121b6555f1b29f70bcc53a09cecff32fb7c3a5ad72a291d44de1052c5ef72e4
- checkpoint_size_bytes: 58022805
- checkpoint_payload_schema_valid: True
- checkpoint_metadata_written: True

## Resume Smoke
- checkpoint_loaded_for_resume_smoke: True
- resume_smoke_passed: True
- model_state_loaded: True
- optimizer_state_loaded: True
- completed_steps_verified: True
- mask_schedule_verified: True
- parameter_shapes_verified: True
- optimizer_step_during_resume_smoke: False
- second_checkpoint_saved: False

## Safety
- training_step_called: False
- trainer_fit_called: False
- model_saved: False
- formal_training_executed: False
- real_finetune_executed: False
- source_modification_allowed: False
- original_source_files_modified: False
- forbidden_artifacts_created: False
- unexpected_checkpoint_files_created: False
- all_checks_passed: True

## Recommendation
- first_checkpointed_training_dry_run_review

The next step is review of this first checkpointed dry-run evidence, not formal training.

# Real Covalent Training Loop Design Gate v0 Summary

Step 12L is a training loop design gate, not training.
Step 12K single optimizer step passed, but multi-step training is still not allowed.

## Leakage Policy
- PLANET v2.0-style soft overlap policy: protein sequence identity threshold 0.90 and ligand ECFP4 Tanimoto threshold 0.90.
- Protein cluster plus high ligand similarity is treated as soft overlap risk.
- Tapping-on-the-Black-Box-style warning: model evaluation is affected by train set content, size, and train/test similarity, so hard overlap and soft overlap must both be reported.
- parent complex group split is required.
- A/B/B2/B3/C mask levels not cross split.
- scaffold holdout and target cluster holdout are primary evaluation requirements.
- NLRP3 external case requires external holdout and overlap reporting.

## Cys-First Scope
- Cys-only convergence risk is acknowledged.
- cys_only_convergence_risk_level: moderate_to_high_without_diversity_controls
- V1 claim is Cys-focused / Cys-directed not universal covalent generation.
- train_ready_scope_v1: cys_with_known_reconstruction_template_only
- non_cys_mixing_allowed_in_v1_training: false
- scaffold, warhead, target, pocket geometry, linker length, reactive atom distance, and mask-level balance reports are required.

## Optimizer And LR Policy
- AdamW remains the optimizer policy.
- AdamW has already been smoked in Step 12K.
- lr=1e-6 first tiny run default.
- scheduler disabled for first tiny run.
- warmup+cosine after split/eval gate.
- ReduceLROnPlateau only after stable validation.
- LR finder not allowed now, especially not on the three-sample smoke.
- Aggressive lr values 5e-5 / 1e-4 require explicit debug gate.
- catastrophic forgetting guard is required for pretrained fine-tune.

## Training And Artifact Boundary
- max_steps_first_tiny_run: 10
- max_steps_smoke_run: 50
- formal_training_allowed: false
- multi_step_training_allowed_after_this_step: false
- checkpoint_save_allowed_after_this_step: false
- no model forward, no loss compute, no backward, no optimizer creation, no parameter update, no checkpoint/model/tensor dump in this step.

## Decision
- real_covalent_training_loop_design_gate_passed: true
- training_design_contract_defined: true
- leakage_aware_training_design_defined: true
- optimizer_lr_scheduler_policy_defined: true
- recommended_next_step: real_covalent_leakage_aware_split_design_gate

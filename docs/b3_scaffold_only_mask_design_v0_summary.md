# B3 Scaffold-Only Mask Design v0 Summary

Step 11M is a B3 scaffold-only mask design step. It is not implementation and not training.
B3 keeps linker + warhead visible and masks scaffold for scaffold hopping / core replacement.

## B2 vs B3
- B2_scaffold_warhead: keep linker; mask scaffold + warhead.
- B3_scaffold_only: keep linker + warhead; mask scaffold.
- B3 does not replace B2; it is an additive fifth mask level.

## Five-Level Mask Table
| mask_level | target | context | use_case |
| --- | --- | --- | --- |
| A_warhead_only | warhead | scaffold, linker | warhead replacement |
| B_linker_warhead | linker, warhead | scaffold | grow linker and warhead from known scaffold |
| B2_scaffold_warhead | scaffold, warhead | linker | co-design scaffold and warhead around linker geometry |
| B3_scaffold_only | scaffold | linker, warhead | scaffold hopping with fixed linker-warhead geometry |
| C_scaffold_linker_warhead | scaffold, linker, warhead | none | de novo full covalent ligand generation |

## B3 Invariants
- B3_I01_target_exactly_scaffold: target_components must equal scaffold
- B3_I02_context_exactly_linker_warhead: context_components must equal linker plus warhead
- B3_I03_target_count_positive: target_atoms_count must be greater than zero
- B3_I04_context_count_positive: context_atoms_count must be greater than zero
- B3_I05_linker_count_positive: linker_atoms_count must be greater than zero
- B3_I06_warhead_count_positive: warhead_atoms_count must be greater than zero
- B3_I07_scaffold_count_positive: scaffold_atoms_count must be greater than zero
- B3_I08_disjoint: target and context atom sets must be disjoint
- B3_I09_cover_assigned_regions: target plus context covers all scaffold/linker/warhead ligand atoms
- B3_I10_warhead_visible: warhead atoms must remain visible in context
- B3_I11_linker_visible: linker atoms must remain visible in context
- B3_I12_no_scaffold_context_leak: scaffold atoms must not leak into context
- B3_I13_covalent_labels_metadata_only: covalent atom-pair labels stay available as conditioning/evaluation metadata, not target leakage
- B3_I14_preserve_existing_levels: B3 must not alter A/B/B2/C semantics
- B3_I15_fail_safe_missing_labels: B3 must fail safely if scaffold/linker/warhead labels are missing or empty

## Implementation Boundary
- proposed_next_stage: b3_scaffold_only_mask_implementation_v0
- implementation_policy: additive_only
- do_not_rename_existing_b2: true
- do_not_change_existing_four_level_semantics: true
- this_design_modifies_mask_logic: false
- this_design_runs_model: false
- this_design_runs_backward: false
- this_design_creates_optimizer: false
- this_design_runs_optimizer.step: false
- training_allowed: false
- formal_training_allowed: false
- finetune_allowed: false
- checkpoint_saved: false
- model_saved: false
- tensor_dump_saved: false

## Roadmap
- Step 11N: b3_scaffold_only_mask_implementation_v0 - add B3 to mask logic and tests
- Step 11O: b3_scaffold_only_mask_sweep_v0 - run mask sweep including A/B/B2/B3/C and verify target/context counts
- Step 11P: b3_pretrained_masked_loss_smoke_v0 - strict-loaded model with B3 synthetic finite loss
- Step 11Q: b3_backward_smoke_v0 - B3 loss requires gradient and gradient values are finite
- Step 11R: b3_single_optimizer_step_smoke_v0 - one controlled parameter update on B3
- Step 11S: b3_tiny_training_dry_run_v0 - optional three-step B3 tiny loop
- Then: real_covalent_feature_mapping_loader_gate - gate real feature mapping and loader readiness before real data use

## Non-Claims
- This design does not prove generated scaffold quality.
- This design does not prove real covalent loader readiness.
- This design does not run model execution or parameter updates.

## Decision
- design_status: b3_scaffold_only_mask_design_ready
- b3_scaffold_only_mask_implementation_allowed: true
- recommended_next_step: b3_scaffold_only_mask_implementation

# Masked Loss Adapter Design v0 Summary

Step 10G and Step 10H proved that the original DiffSBDD full-ligand loss can forward and backward on the covalent batch.
The current original loss is a full-ligand objective.
The current forward path does not consume covalent target/context masks.
Therefore the current training path cannot be described as masked covalent training.
Current output0 is a per-sample loss and cannot directly support atom-level masked loss.
Current output1 is scalar diagnostics and cannot directly support target-atom masked loss.

## Source Findings
- atomwise_loss_exposed_by_current_forward: False
- nodewise_noise_exposed_by_current_forward: False
- can_build_masked_loss_from_current_output_only: False
- no_diffsbdd_modification_feasible: uncertain

## Proposed Loss Components
- loss_original = nll.mean()
- loss_masked_x = masked coordinate denoising loss over ligand target atoms
- loss_masked_h = masked feature denoising loss over ligand target atoms
- loss_warhead_type = optional warhead type classification auxiliary
- loss_reactive_pair = optional ligand reactive atom / residue atom pair auxiliary
- loss_geometry = optional covalent-ready geometry auxiliary

- formula: loss_total = 1.0*loss_original + 1.0*loss_masked_x + 0.2*loss_masked_h + 0.1*loss_warhead_type + 0.1*loss_reactive_pair + 0.1*loss_geometry

## Required Internal Signals
- ligand atom-wise predicted noise for coordinates
- ligand atom-wise target noise for coordinates
- ligand atom-wise predicted feature/noise logits or residuals
- ligand target/context/generation masks aligned to flattened ligand atoms
- optional xh_lig_hat for geometry auxiliary terms

## Adapter Input Contract
- model output raw loss-like tensor
- optional raw atomwise predicted noise / target noise if exposed later
- ligand_target_mask_flat
- ligand_context_mask_flat
- generation_mask_flat
- ligand_mask_flat
- sample_id
- mask_level
- ligand_reactive_atom_index
- residue reactive atom info
- warhead_type_label
- optional geometry labels

## Adapter Output Contract
- loss_total
- loss_original
- loss_masked_x
- loss_masked_h
- loss_aux
- diagnostics
- safety_flags

## Mask-level Policy
| mask_level | target | context | focus |
| --- | --- | --- | --- |
| A_warhead_only | warhead atoms | scaffold + linker | warhead geometry/reactivity |
| B_linker_warhead | linker + warhead | scaffold | linker trajectory + warhead placement |
| B2_scaffold_warhead | scaffold + warhead | linker | scaffold variation with warhead constraints |
| C_scaffold_linker_warhead | all ligand atoms | none | full ligand generation with covalent labels |

## Recommended Path
Implement a no-behavior-change hook/probe to expose ligand atom-wise denoising residuals, then run masked loss dry run before any optimizer smoke.

Minimal hook points:
- Expose or recompute ligand node-wise squared error before sum_except_batch in EnVariationalDiffusion.forward / ConditionalDDPM.forward.
- Expose net_out_lig and eps_t_lig or their coordinate/feature residuals before scatter_add reduction.
- Thread ligand_target_mask_flat/generation_mask_flat through a wrapper-side data contract without changing original forward behavior.
- Keep original nll.mean() available as loss_original and add masked losses in covalent_ext wrapper code.

- recommended_next_step: diffsbdd_atomwise_loss_hook_design_without_behavior_change

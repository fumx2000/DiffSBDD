# DiffSBDD Atomwise Loss Hook Design v0 Summary

This step is a source inspection and hook design only.
It does not modify DiffSBDD or equivariant_diffusion code.
It does not load or save checkpoints.
It does not call training_step, backward, optimizer, trainer.fit, training, or fine-tuning.

## Why a Hook Is Needed
Step 10I showed that the current DiffSBDD forward output is not enough to build atom-level masked losses.
output0 is a per-sample loss-like vector, and output1 contains reduced diagnostics.
Neither output exposes ligand atom-wise target noise, predicted noise, or unreduced residuals.

## Source Locations Found
- eps_t_lig locations: 18
- net_out_lig locations: 29
- squared_error locations: 11
- error_t_lig locations: 19
- reduction locations: 67

## Recommended Hook
- preferred_hook_point: B. Expose eps_t_lig and net_out_lig after dynamics through an optional no-behavior-change probe path
- recommended_hook_strategy: optional_no_behavior_change_atomwise_probe_for_eps_t_lig_and_net_out_lig
- The default forward return should not change.
- The original loss value should not change when the probe is disabled.
- Checkpoint compatibility should not be affected because no parameters, buffers, or state_dict keys are added.

## Captured Tensor Contract
- required: eps_t_lig, net_out_lig, ligand_mask_flat
- adapter_supplied: ligand_target_mask_flat, ligand_context_mask_flat, generation_mask_flat, sample_id, mask_level
- optional: xh_t_lig, alpha_t, sigma_t, gamma_t, t_int, ligand_size, batch_size

## Tensor Alignment Contract
- eps_t_lig, net_out_lig, ligand_mask_flat, and covalent target masks must share the same flattened ligand atom order.
- residual = eps_t_lig - net_out_lig
- residual_x = residual[:, :3]
- residual_h = residual[:, 3:]
- loss_masked_x = mean(sum(residual_x[target_mask] ** 2, dim=-1))
- loss_masked_h = mean(sum(residual_h[target_mask] ** 2, dim=-1))
- target_mask must contain at least one atom; empty target masks should block or use an explicit fallback.

## Masked Loss Readiness After Hook
- can_compute_masked_x_loss_after_hook: True
- can_compute_masked_h_loss_after_hook: True

## Implementation Phases
- Hook design report only
- No-behavior-change hook prototype in covalent_ext or optional return path
- Hook shape smoke
- Masked loss dry run without backward
- Masked loss backward smoke
- Only then optimizer smoke

## Conclusion
- design_status: ready
- recommended_next_step: atomwise_loss_hook_prototype_without_behavior_change
- Optimizer or training work should not begin before the hook prototype and masked-loss dry runs pass.

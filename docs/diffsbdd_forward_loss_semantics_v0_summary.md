# DiffSBDD Forward Loss Semantics v0 Summary

This step reviews DiffSBDD forward loss semantics without training.
It does not load checkpoints.
It does not save checkpoints.
It does not call training_step.
It does not run backward.
It does not run an optimizer step.
It does not call trainer.fit.
It does not train or fine-tune.
It does not modify DiffSBDD or equivariant_diffusion.

## Output 0
- semantics: LigandPocketDDPM.forward returns nll as output.0; training_step reduces it with nll.mean(0) as loss.
- output0_is_loss_like: True
- output0_is_per_sample_vector: True
- recommended_loss_reduction: mean
- training_step_reduction_semantics: nll.mean(0)

## Output 1 Diagnostics
- output1_keys: ['SNR_weight', 'delta_log_px', 'eps_hat_lig_h', 'eps_hat_lig_x', 'error_t_lig', 'error_t_pocket', 'kl_prior', 'log_pN', 'loss_0', 'neg_log_const_0']
- output1_is_diagnostics: True

## Mask Consumption
- mask_consumption_status: consumed_by_sampling_only
- lig_fixed_consumed_by_forward: False
- generation_mask_consumed_by_forward: False
- target_mask_consumed_by_forward: False
- current_forward_is_mask_aware: False
- current_forward_is_full_ligand_objective: True
- must_modify_loss_for_masked_training: True

The current forward sweep proves that the covalent batch can enter the real model.
It does not prove that a masked covalent training objective is implemented, because the training forward path does not consume the covalent target/context masks.
The next practical step can verify the original loss with a backward smoke, then design a masked loss adapter.

## Probe Summary
- requested_device: auto
- resolved_device: cuda:0
- output0_shape_by_mask_level: {'A_warhead_only': [3], 'B_linker_warhead': [3], 'B2_scaffold_warhead': [3], 'C_scaffold_linker_warhead': [3]}
- output0_finite_by_mask_level: {'A_warhead_only': True, 'B_linker_warhead': True, 'B2_scaffold_warhead': True, 'C_scaffold_linker_warhead': True}
- recommended_next_step: real_diffsbdd_backward_smoke_without_checkpoint_then_masked_loss_adapter_design

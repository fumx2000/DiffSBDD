# Pretrained Checkpoint Load Smoke v0 Summary

Step 11A is a pretrained DiffSBDD checkpoint load compatibility smoke, not training.
It reads checkpoint: `checkpoints/crossdocked_fullatom_cond.ckpt`.
Checkpoint present: True
Checkpoint sha256: `07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c`
Checkpoint size bytes: 17861341

## Payload Inspection
- payload type: dict
- top-level keys: epoch, global_step, pytorch-lightning_version, state_dict, loops, callbacks, optimizer_states, lr_schedulers, hparams_name, hyper_parameters
- has_state_dict: True
- state_dict_key_count: 122
- pretrained_checkpoint_readable: True
- pretrained_state_dict_extracted: True

## Load Compatibility
- model_class: LigandPocketDDPM
- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_name: NVIDIA A100-SXM4-80GB
- best_variant_name: raw
- strict_load_success: False
- nonstrict_load_success: True only for compatible tensors
- matched_key_count: 122
- shape_matched_key_count: 7
- shape_matched_ratio: 0.05737704918032787
- missing_key_count: 20
- unexpected_key_count: 0
- incompatible_shape_count: 115
- pretrained_partial_shape_load_success: True
- pretrained_full_architecture_compatible: False
- pretrained_effective_load_status: partial_shape_compatible_only
- pretrained_weights_loaded: False
- shape_mismatch_detected: True
- architecture_config_mismatch_suspected: True

Conclusion: the current model configuration and checkpoint architecture are clearly mismatched.
This cannot be claimed as successful pretrained base model integration.
Do not proceed to pretrained masked loss smoke from this result.
The next step must reconcile the checkpoint architecture/configuration.

## No-Grad Forward Smoke
- forward_smoke_attempted: True
- forward_smoke_success: True
- output_finite: True
- output_shape_summary: {"output.0": [3], "output.1.SNR_weight": [], "output.1.delta_log_px": [], "output.1.eps_hat_lig_h": [], "output.1.eps_hat_lig_x": [], "output.1.error_t_lig": [], "output.1.error_t_pocket": [], "output.1.kl_prior": [], "output.1.log_pN": [], "output.1.loss_0": [], "output.1.neg_log_const_0": []}

## Safety
- backward_called: False
- optimizer_created: False
- optimizer_step_called: False
- training_step_called: False
- trainer_fit_called: False
- checkpoint_saved: False
- model_saved: False
- formal_training_executed: False
- real_finetune_executed: False
- original_source_files_modified: False
- forbidden_artifacts_created: False

This step does not prove generation quality or loss improvement.
all_checks_passed_meaning: smoke_completed_and_mismatch_detected

## Recommendation
- pretrained_checkpoint_architecture_config_reconciliation

# Pretrained Checkpoint Architecture Reconciliation v0 Summary

Step 11B is architecture/config reconciliation, not training.
Step 11A proved the checkpoint is readable, but it did not prove current-model pretrained integration.

## Checkpoint Hyperparameters
- checkpoint_path: `checkpoints/crossdocked_fullatom_cond.ckpt`
- checkpoint_sha256: `07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c`
- checkpoint_size_bytes: 17861341
- checkpoint_hyper_parameters_keys: outdir, dataset, datadir, batch_size, lr, egnn_params, diffusion_params, num_workers, augment_noise, augment_rotation, clip_grad, eval_epochs, eval_params, visualize_sample_epoch, visualize_chain_epoch, auxiliary_loss, loss_params, mode, node_histogram, pocket_representation, virtual_nodes

## Current Config
- current_config_path: `configs/crossdock_fullatom_cond.yml`
- current_config_present: True
- current_config_not_checkpoint_config: True

## Inferred Architectures
- checkpoint atom feature dim: 10
- current atom feature dim: 11
- checkpoint EGNN hidden candidates: [128]
- current EGNN hidden candidates: [256]
- checkpoint EGNN block count: 5
- current EGNN block count: 6

## Mismatch Summary
- matched_key_count: 122
- shape_matched_key_count: 7
- shape_matched_ratio: 0.05737704918032787
- incompatible_shape_count: 115
- mismatch_category_counts: {"atom_decoder": 4, "atom_encoder": 4, "egnn_att_mlp": 5, "egnn_coord_mlp": 25, "egnn_cross_product_mlp": 25, "egnn_edge_mlp": 20, "egnn_node_mlp": 20, "egnn_other": 4, "other": 8}
- likely_root_causes: hidden_dim_mismatch, atom_feature_dim_mismatch, egnn_layer_count_mismatch, atom_encoder_decoder_dim_mismatch
- confidence_by_root_cause: {"atom_encoder_decoder_dim_mismatch": "medium", "atom_feature_dim_mismatch": "high", "egnn_layer_count_mismatch": "high", "hidden_dim_mismatch": "high"}

## Config Candidate Search
- best_config_candidate_path: `configs/crossdock_fullatom_joint.yml`
- best_config_candidate_score: 4
- candidate_instantiation_attempted: False

## Decision
- reconciliation_status: checkpoint_original_config_recovery_needed
- pretrained_masked_loss_smoke_allowed: False
- formal_training_allowed: False
- finetune_allowed: False
- quality_claim_allowed: False
- recommended_next_step: checkpoint_original_config_model_instantiation_design

Formal training, fine-tuning, and pretrained masked loss smoke remain forbidden until a checkpoint-compatible model is proven.

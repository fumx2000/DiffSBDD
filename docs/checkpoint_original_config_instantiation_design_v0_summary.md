# Checkpoint Original Config Instantiation Design v0 Summary

Step 11C is a design step, not training.
Step 11B showed that the current config and checkpoint original config are inconsistent.

## Checkpoint Target Config
- joint_nf: 32
- hidden_nf: 128
- n_layers: 5
- mode: pocket_conditioning
- pocket_representation: full-atom
- atom feature dim: 10
- residue feature dim: 10

## Current Config
- joint_nf: 128
- hidden_nf: 256
- n_layers: 6
- atom feature dim: 11

The current model must not proceed directly to pretrained masked loss smoke.
The checkpoint original config preview is written to `data/derived/covalent_small/checkpoint_original_config_instantiation_design_v0/checkpoint_original_config_preview.json`.
Wrapper needed: True
Proposed wrapper: `instantiate_checkpoint_compatible_model_v0` in `src/covalent_ext/checkpoint_compatible_model_instantiation.py`.

## Design Decision
- design_status: wrapper_needed_for_checkpoint_compatible_instantiation
- checkpoint_compatible_instantiation_feasible: True
- expected_shape_match_goal: {"acceptable_nonstrict_load_success_condition": "only after shape table documents known minor mismatches", "ideal_strict_load_success": true, "shape_matched_ratio_minimum": 0.8}
- recommended_next_step: checkpoint_compatible_instantiation_wrapper_prototype

Training, fine-tuning, and masked loss smoke remain forbidden until checkpoint-compatible instantiation is proven.

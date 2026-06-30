# Real Covalent Leakage-Aware Split Design Gate v0 Summary

Step 12M is a leakage-aware split design gate, not split implementation, not training.
Step 12L training loop design gate verified: true.
The current real covalent sample_index was read from data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv.

## Current Data Scope
- current_sample_count: 3
- sample_ids: BTK_C481_6DI9_pre_reaction, KRAS_G12C_5F2E_pre_reaction, KRAS_G12C_6OIM_pre_reaction
- current_dataset_is_small_smoke_set: true
- current_dataset_final_split_feasible: false
- This three-sample real covalent set is an engineering smoke set, insufficient for final train/valid/test leakage-aware split.

## Hard Overlap Policy
- Hard overlap zero tolerance is required.
- parent_complex_id, mask_parent_id, sample_id, PDB, UniProt, ligand InChIKey, canonical SMILES, and covalent bond atom pair cannot leak across claim-bearing splits.
- A/B/B2/B3/C mask levels follow the same parent complex and are not cross split.

## Soft Overlap Policy
- Protein sequence identity threshold: 0.90.
- Ligand ECFP4 Tanimoto threshold: 0.90.
- Protein cluster plus high ligand similarity is treated as risk.
- Scaffold, warhead, reaction family, target family, and NLRP3 external overlap reports are required.

## Required Future Outputs
- train/valid/test leakage matrix schema is defined.
- split manifest, split assignments, leakage matrix, scaffold holdout report, target cluster holdout report, warhead distribution report, reaction family distribution report, Cys train-ready inventory, and NLRP3 external overlap report are required later.
- No formal split, no split assignments, and no leakage matrix were written in this step.

## Safety Boundary
- No forward, no loss compute, no backward, no optimizer creation, no parameter update, no training loop call, no checkpoint/model/tensor dump.
- formal_training_allowed: false
- final_train_valid_test_split_allowed: false

## Decision
- real_covalent_leakage_aware_split_design_gate_passed: true
- split_design_contract_defined: true
- metadata_inventory_required_before_split: true
- recommended_next_step: real_covalent_split_metadata_inventory_gate

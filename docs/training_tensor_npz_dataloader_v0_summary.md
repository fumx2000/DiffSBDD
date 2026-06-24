# Training Tensor NPZ DataLoader v0 Summary

This step builds a minimal PyTorch Dataset and DataLoader from Step 9A `.npz` artifacts.
It checks one batch with batch_size=3.
It does not load checkpoints.
It does not initialize a model.
It does not train or fine-tune.
It does not modify DiffSBDD model code.

- dataset_name: covalent_small_pre_reaction_training_tensor_materialized_v0
- ligand_atom_coords_shape: [3, 41, 3]
- protein_atom_coords_shape: [3, 2306, 3]
- sanity_passed: True

| sample_id | ligand_atom_count | protein_atom_count | dataloader_sanity_status |
| --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | 33 | 2306 | passed |
| KRAS_G12C_5F2E_pre_reaction | 30 | 1723 | passed |
| KRAS_G12C_6OIM_pre_reaction | 41 | 1613 | passed |

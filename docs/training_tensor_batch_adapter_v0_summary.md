# Training Tensor Batch Adapter v0 Summary

This step adapts one DataLoader batch into a model-input-like covalent batch dictionary.
It checks A/B/B2/C mask levels.
It checks coordinate centering, generation/fixed masks, reactive atom inclusion, and shape consistency.
It does not load checkpoints.
It does not initialize a model.
It does not train or fine-tune.
It does not modify DiffSBDD model code.

- ligand_atom_coords_shape: [3, 41, 3]
- protein_atom_coords_shape: [3, 2306, 3]
- adapted_ligand_coords_shape: [3, 41, 3]
- adapted_protein_coords_shape: [3, 2306, 3]
- coordinate_center_shape: [3, 3]
- all_mask_levels_passed: True

| mask_level | rows | all_passed |
| --- | --- | --- |
| A_warhead_only | 3 | True |
| B2_scaffold_warhead | 3 | True |
| B_linker_warhead | 3 | True |
| C_scaffold_linker_warhead | 3 | True |

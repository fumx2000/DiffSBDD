# Training Tensor Model Input Mapping v0 Summary

This step maps adapted covalent batch into model-input-like tensors.
It computes mock reconstruction losses without loading any model.
It does not load checkpoint.
It does not initialize model.
It does not train/fine-tune.
It does not modify DiffSBDD model code.

- protein_x_shape: [3, 2306, 3]
- ligand_x_shape: [3, 41, 3]
- ligand_context_x_shape: [3, 41, 3]
- ligand_target_x_shape: [3, 41, 3]
- coordinate_center_shape: [3, 3]
- mock_loss_all_finite: True

| mask_level | rows | all_passed |
| --- | --- | --- |
| A_warhead_only | 3 | True |
| B2_scaffold_warhead | 3 | True |
| B_linker_warhead | 3 | True |
| C_scaffold_linker_warhead | 3 | True |

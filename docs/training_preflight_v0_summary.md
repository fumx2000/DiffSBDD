# Training Preflight v0 Summary

This step performs a final training preflight dry-run from NPZ artifacts to model-input-like tensors.
It checks data loading, batching, covalent batch adaptation, model input mapping, device transfer, and mock loss aggregation.
It does not load checkpoints.
It does not initialize a model.
It does not call DiffSBDD.
It does not train or fine-tune.
It does not modify DiffSBDD model code.

- dataset_len: 3
- batch_size: 3
- device: cpu
- protein_x_shape: [3, 2306, 3]
- ligand_x_shape: [3, 41, 3]
- ligand_context_x_shape: [3, 41, 3]
- ligand_target_x_shape: [3, 41, 3]
- mock_total_loss_all_finite: True

| mask_level | target_atom_count_total | mock_total_loss | preflight_status |
| --- | ---: | ---: | --- |
| A_warhead_only | 12 | 50.784523 | passed |
| B_linker_warhead | 30 | 49.513919 | passed |
| B2_scaffold_warhead | 86 | 60.426821 | passed |
| C_scaffold_linker_warhead | 104 | 58.391439 | passed |

Conclusion: if all rows are passed, the next step is DiffSBDD adapter or tiny model smoke test, not another gate.

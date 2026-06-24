# Training Tensor Materialized v0 Summary

This is actual minimal tensor-like materialization v0.
It writes readable `.npz` numeric artifacts for the three approved pre-reaction samples.
torch was not imported.
No DataLoader or Dataset was constructed.
No checkpoint was read.
No model was initialized.
No training was run.
No archive was created.

| sample_id | npz_path | ligand_atom_count | protein_atom_count | sanity_status |
| --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | data/derived/covalent_small/training_tensor_materialized_v0/samples/BTK_C481_6DI9_pre_reaction.npz | 33 | 2306 | passed |
| KRAS_G12C_5F2E_pre_reaction | data/derived/covalent_small/training_tensor_materialized_v0/samples/KRAS_G12C_5F2E_pre_reaction.npz | 30 | 1723 | passed |
| KRAS_G12C_6OIM_pre_reaction | data/derived/covalent_small/training_tensor_materialized_v0/samples/KRAS_G12C_6OIM_pre_reaction.npz | 41 | 1613 | passed |

All three samples passed sanity checks.

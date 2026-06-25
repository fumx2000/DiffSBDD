# DiffSBDD Adapter Shape Smoke v0 Summary

This step builds DiffSBDD-like flattened ligand/pocket batch fields from covalent model input.
It validates shape/mask/one-hot/size consistency without initializing or calling DiffSBDD.
It does not load or save checkpoint.
It does not train or fine-tune.
It does not modify DiffSBDD or equivariant_diffusion.
It is still not equivalent to a real DiffSBDD forward pass.

## Shape Smoke Results

| mask_level | ligand_atom_total | pocket_atom_total | target_atom_count | shape_smoke_status |
| --- | ---: | ---: | ---: | --- |
| A_warhead_only | 104 | 5642 | 12 | passed |
| B_linker_warhead | 104 | 5642 | 30 | passed |
| B2_scaffold_warhead | 104 | 5642 | 86 | passed |
| C_scaffold_linker_warhead | 104 | 5642 | 104 | passed |

- ligand_feature_dim: 11
- pocket_feature_dim: 11
- shape_sanity_all_passed: True
- mask_sanity_all_passed: True
- checkpoint_loaded: False
- checkpoint_saved: False
- diffsbdd_model_initialized: False
- diffsbdd_model_called: False
- training_executed: False
- recommended_next_step: diffsbdd_model_instantiation_dry_run_without_checkpoint_or_manual_interface_review

If all rows are passed, the next step can be DiffSBDD model instantiation dry-run without checkpoint.
If fields remain uncertain, use manual interface review before touching any real model path.

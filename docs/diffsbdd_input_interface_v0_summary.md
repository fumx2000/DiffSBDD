# DiffSBDD Input Interface v0 Summary

This step inspects the DiffSBDD input interface and builds a covalent-to-DiffSBDD-like adapter preview.
It does not initialize or call a real DiffSBDD model.
It does not load or save checkpoint.
It does not train or fine-tune.
It does not modify DiffSBDD model code or equivariant_diffusion.

## Inspected Entry Points
- dataset.ProcessedLigandPocketDataset.collate_fn
- lightning_modules.LigandPocketDDPM.get_ligand_and_pocket
- lightning_modules.LigandPocketDDPM.forward
- lightning_modules.LigandPocketDDPM.training_step
- equivariant_diffusion.en_diffusion.EnVariationalDiffusion.forward
- equivariant_diffusion.dynamics.EGNNDynamics.forward
- equivariant_diffusion.dynamics.EGNNDynamics.get_edges
- equivariant_diffusion.conditional_model.ConditionalDDPM.sample_given_pocket
- equivariant_diffusion.conditional_model.ConditionalDDPM.inpaint
- generate_ligands.main
- optimize.main

## Expected Input Fields
- data.lig_coords
- data.lig_one_hot
- data.lig_mask
- data.num_lig_atoms
- data.pocket_coords
- data.pocket_one_hot
- data.pocket_mask
- data.num_pocket_nodes
- ligand.x
- ligand.one_hot
- ligand.size
- ligand.mask
- pocket.x
- pocket.one_hot
- pocket.size
- pocket.mask
- lig_fixed

## Direct Covalent Mapping Fields
- ligand.x <- model_input.ligand_x[ligand_mask]
- ligand.size <- ligand_mask.sum(dim=1)
- ligand.mask <- flattened ligand batch indices
- pocket.x <- model_input.protein_x[protein_mask]
- pocket.size <- protein_mask.sum(dim=1)
- pocket.mask <- flattened protein batch indices
- lig_fixed <- fixed_ligand_atom_mask flattened over ligand_mask
- generation_mask_flat <- generation_mask flattened over ligand_mask
- ligand_context_mask_flat <- ligand_context_mask flattened over ligand_mask
- ligand_target_mask_flat <- ligand_target_mask flattened over ligand_mask
- coordinate_center <- model_input.coordinate_center

## Missing Or Uncertain Fields
- exact DiffSBDD dataset config must choose crossdock vs crossdock_full pocket representation
- ligand one-hot vocabulary uses crossdock_full preview mapping and should be confirmed against the target checkpoint config later
- pocket one-hot vocabulary uses protein atom atomic numbers as crossdock_full atom types; CA residue mode would require residue encodings
- edge_mask is not a top-level LigandPocketDDPM/DDPM input; EGNNDynamics constructs edges internally from masks
- names/receptors metadata are needed for some sampling/evaluation utilities but not for forward loss
- virtual_nodes mode is not represented in this preview

## Mask Level Results

| mask_level | target_atom_count | shape_sanity_passed | mask_sanity_passed | adapter_status |
| --- | ---: | --- | --- | --- |
| A_warhead_only | 12 | true | true | passed |
| B_linker_warhead | 30 | true | true | passed |
| B2_scaffold_warhead | 86 | true | true | passed |
| C_scaffold_linker_warhead | 104 | true | true | passed |

- checkpoint_loaded: False
- diffsbdd_model_initialized: False
- diffsbdd_model_called: False
- training_executed: False
- recommended_next_step: diffsbdd_adapter_shape_smoke_without_checkpoint

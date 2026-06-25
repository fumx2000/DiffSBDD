# DiffSBDD Model Instantiation Dry-run v0 Summary

This step imports the real DiffSBDD model class, inspects its constructor, and runs a constructor-only instantiation dry-run.
It does not read checkpoint files.
It does not call forward.
It does not call training_step.
It does not train or fine-tune.
It does not save checkpoints.
It does not modify DiffSBDD or equivariant_diffusion.

- model_class_name: LigandPocketDDPM
- constructor_signature_resolved: True
- config_status: ready
- config_source: configs/crossdock_fullatom_cond.yml
- dataset_info_source: constants.dataset_params['crossdock_full']
- atom_encoder_source: constants.dataset_params['crossdock_full']['atom_encoder']
- model_initialized: True
- parameter_count: 4822706
- trainable_parameter_count: 4822205
- module_count: 140
- smoke_status: passed

## Inspected Source Files
- lightning_modules.py
- equivariant_diffusion/en_diffusion.py
- equivariant_diffusion/dynamics.py
- equivariant_diffusion/conditional_model.py
- train.py
- generate_ligands.py
- optimize.py
- configs/crossdock_fullatom_cond.yml
- configs/crossdock_fullatom_joint.yml
- process_crossdock.py
- constants.py
- scripts/covalent_inpaint_demo.py

## Missing Or Uncertain Config Fields
- repository does not include the original processed size_distribution.npy; dry-run uses a minimal positive 2x2 histogram for constructor-only initialization
- configs/crossdock_fullatom_cond.yml names dataset as crossdock while process_crossdock.py full-atom branch uses constants.dataset_params['crossdock_full']; dry-run uses crossdock_full to match 11-dimensional full-atom fields
- configs/crossdock_fullatom_cond.yml does not explicitly set virtual_nodes; dry-run uses the constructor default false

- checkpoint_loaded: False
- checkpoint_saved: False
- forward_called: False
- diffsbdd_model_called: False
- training_step_called: False
- training_executed: False
- recommended_next_step: diffsbdd_single_batch_forward_shape_smoke_without_checkpoint

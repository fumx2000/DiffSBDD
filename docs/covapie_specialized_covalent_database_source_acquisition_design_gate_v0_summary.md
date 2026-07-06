# CovaPIE Specialized Covalent Database Source Acquisition Design Gate v0 Summary

This is CovaPIE specialized covalent database source acquisition design gate.
It prioritizes specialized covalent protein-ligand databases over blind PDB-wide scanning.
It does not verify any external database in this step.
It does not use internet, network, curl, wget, requests, or urllib.
It does not download metadata or raw structures.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
One metadata row must correspond to one covalent ligand-residue event, not merely one PDB entry.
Joining by pdb_id alone is forbidden.
Minimal event key: `pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name`.
Preferred event key: `pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name+covalent_bond_atom_pair`.
Next step is external metadata index download design gate.
It keeps feature semantics audit and leakage/split design required before training.

source_registry_contract_row_count: `5`
external_source_verified_current_step: `False`
external_network_access_used: `False`
external_metadata_downloaded: `False`
raw_structure_downloaded: `False`
ready_for_covapie_external_metadata_index_download_design_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_external_metadata_index_download_design_gate`

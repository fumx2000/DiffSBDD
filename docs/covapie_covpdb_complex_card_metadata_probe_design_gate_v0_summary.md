# CovaPIE CovPDB Complex Card Metadata Probe Design Gate v0 Summary

This is a CovaPIE complex-card metadata probe design gate.
It designs a future CovPDB complex-card HTML metadata acquisition smoke.
It does not fetch CovPDB complex-card pages in this step.
It does not use network.
It does not download raw structures, ligand SDF, ZIP/GZ, PDB, CIF, or mmCIF.
It does not read raw/SDF/PDB/mmCIF/gzip content.
It does not use RDKit/Bio.PDB/gemmi.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

The future acquisition smoke may only fetch HTML/text from CovPDB complex-card URLs already present in the committed metadata CSV.
The first acquisition smoke is capped at five cards, with no recursive crawling and no following download links.
Candidate metadata remains blocked until the minimal event key is explicit.
Automatic allowlist materialization remains blocked unless the preferred event key, including covalent_bond_atom_pair, is explicit.

metadata_csv_row_count: `25`
metadata_csv_column_count: `19`
complex_card_url_count: `25`
first_5_complex_card_urls: `['https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2037', 'https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2034', 'https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=1', 'https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=1614', 'https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2']`
target_field_contract_row_count: `18`
allowed_url_contract_row_count: `10`
forbidden_artifact_contract_row_count: `16`
parse_strategy_contract_row_count: `8`
event_key_resolution_contract_row_count: `7`
failure_taxonomy_row_count: `16`
ready_for_covapie_covpdb_complex_card_metadata_acquisition_smoke: `True`
ready_for_covapie_candidate_metadata_materialization: `False`
ready_for_covapie_candidate_allowlist_materialization_smoke: `False`
ready_for_covapie_batch_scale_raw_read_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_covpdb_complex_card_metadata_acquisition_smoke`
blocking_reasons: `[]`

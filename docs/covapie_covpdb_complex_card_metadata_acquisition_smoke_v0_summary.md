# CovaPIE CovPDB Complex Card Metadata Acquisition Smoke v0 Summary

This is a controlled CovPDB complex-card HTML metadata acquisition smoke.
It fetches only the first five allowed CovPDB complex-card URLs from the committed metadata CSV.
It does not save complete HTML.
It does not follow links.
It does not download raw structures, ligand SDF, ZIP/GZ, PDB, CIF, or mmCIF.
It does not read raw/SDF/PDB/mmCIF/gzip content.
It does not use RDKit/Bio.PDB/gemmi.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

attempted_card_count: `5`
fetched_card_count: `5`
fetch_succeeded_count: `5`
fetch_failed_count: `0`
first_5_complex_card_urls: `['https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2037', 'https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2034', 'https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=1', 'https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=1614', 'https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2']`
full_html_written: `False`
raw_html_artifact_written: `False`
minimal_event_key_resolved_card_count: `0`
preferred_event_key_resolved_card_count: `0`
partial_event_key_card_count: `0`
unresolved_card_count: `5`
future_candidate_metadata_possible_count: `0`
future_automatic_allowlist_possible_count: `0`
ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_covpdb_complex_card_metadata_acquisition_qa_gate`
blocking_reasons: `[]`

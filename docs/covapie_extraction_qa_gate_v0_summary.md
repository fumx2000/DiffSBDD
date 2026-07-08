# CovaPIE Extraction QA Gate v0 Summary

Step 13BF is an extraction QA gate for the Step 13BE derived extraction tables.
It reads only Step 13BE/13BD CSV and JSON artifacts and does not read raw CIF files, parse mmCIF, scan atom_site/struct_conn, or re-extract coordinates.
It validates event table schema and identity, atom table schema and endpoint coverage, geometry recomputation, traceability, boundary safety, git safety, and training blockers.
It does not write sample_index, final_dataset, split assignments, leakage matrix, or training inputs.
It does not use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows the sample index design gate next, not sample index smoke and not training.

source_extracted_event_row_count: `4`
source_extracted_event_column_count: `31`
source_protein_pocket_atom_row_count: `1071`
source_ligand_atom_row_count: `149`
extracted_event_table_qa_passed: `True`
extracted_atom_table_qa_passed: `True`
geometry_qa_passed: `True`
traceability_qa_passed: `True`
raw_data_read: `False`
mmcif_parse_current_step: `False`
ready_for_covapie_sample_index_design_gate: `True`
ready_for_covapie_sample_index_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_sample_index_design_gate`
blocking_reasons: `[]`

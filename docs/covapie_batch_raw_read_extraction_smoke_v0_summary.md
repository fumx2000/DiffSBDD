# CovaPIE Batch Raw Read Extraction Smoke v0 Summary

Step 13BE is the first controlled raw read / extraction smoke for the four CovaPIE allowlist CIF files.
It reads only the four allowlist raw `.cif` files, parses `_atom_site` and `_struct_conn` with a small Python standard-library parser, extracts event rows, writes protein pocket atom rows, and writes ligand atom rows.
It does not download raw data, create or copy raw files, use RDKit/Bio.PDB/gemmi/gzip/torch, instantiate models, compute loss, or train.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This smoke allows the extraction QA gate next, not sample index design and not training.

raw_file_read_count: `4`
extracted_event_table_row_count: `4`
extracted_protein_pocket_atom_row_count: `1071`
extracted_ligand_atom_row_count: `149`
extraction_success_count: `4`
extraction_blocked_count: `0`
covalent_connection_found_count: `4`
residue_atom_found_count: `4`
ligand_atom_found_count: `4`
raw_data_read: `True`
mmcif_text_read: `True`
sample_index_written: `False`
final_dataset_written: `False`
split_assignments_written: `False`
leakage_matrix_written: `False`
ready_for_covapie_extraction_qa_gate: `True`
ready_for_sample_index_design_gate: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_extraction_qa_gate`
blocking_reasons: `[]`

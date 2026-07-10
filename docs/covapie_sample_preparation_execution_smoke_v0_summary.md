# CovaPIE Sample Preparation Execution Smoke v0 Summary

Step 14AA executes sample preparation smoke for the three Step 14Z small pilot inputs.

This step reads ignored raw CIF/mmCIF files, parses atom_site and struct_conn, and writes per-sample protein, ligand, pocket, covalent event, and ligand-residue atom-pair CSV tables.

It is not a sample index, not a final dataset, not a dataloader smoke, and not a training sample.

input_sample_preparation_count: `3`
sample_execution_count: `3`
sample_preparation_passed_count: `3`
raw_file_resolved_count: `3`
protein_atom_table_written_count: `3`
ligand_atom_table_written_count: `3`
pocket_atom_table_written_count: `3`
covalent_event_table_written_count: `3`
ligand_residue_atom_pair_table_written_count: `3`
accepted_pdb_het_pairs: `6BV6/JUG, 6BV8/JUG, 6BV5/JUG`
ready_for_covapie_sample_preparation_qa_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_sample_preparation_qa_gate`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.

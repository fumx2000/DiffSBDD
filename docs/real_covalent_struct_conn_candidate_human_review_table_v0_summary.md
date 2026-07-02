# Real Covalent Struct Conn Candidate Human Review Table v0 Summary

Step 13B is an actual struct_conn candidate human review table.

This step read the Step 13A candidate-enriched stub CSV.
It did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF.
It did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
It did not run coordinate geometry, distance calculation, UniProt/CD-HIT, NPZ reads, or training.

The step generated a human-reviewable candidate table.
- human_review_table_row_count: 16
- candidate_like_review_row_count: 4
- high_priority_review_row_count: 4
- audit_review_row_count: 12

Candidate-like rows are sorted first. The table preserves ptnr1/ptnr2 atom identifiers, conn_type_id, pdbx_dist_value, and pdbx_role.

Manual review blank columns:
- manual_review_decision
- manual_review_notes
- manual_confirmed_covalent_bond
- manual_confirmed_ptnr1_role
- manual_confirmed_ptnr2_role
- manual_confirmed_ligand_comp_id
- manual_confirmed_residue_comp_id
- manual_confirmed_ligand_atom_id
- manual_confirmed_residue_atom_id
- manual_confirmed_warhead_type
- manual_exclusion_reason
- manual_reviewer
- manual_review_date

This step did not fill manual review decision.
It did not infer ligand/residue role, did not infer warhead_type, and did not claim covalent_bond_atom_pair is chemically verified.
All rows have human_review_required=true and training_ready=false.
This step did not write enriched sample_index and did not write final dataset.

Next step is manual fill of the human review table, not training.

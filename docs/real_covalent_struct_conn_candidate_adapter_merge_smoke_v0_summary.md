# Real Covalent Struct Conn Candidate Adapter Merge Smoke v0 Summary

Step 13A is an actual struct_conn candidate adapter merge smoke.

This step read the Step 12Y minimal adapter summary CSV.
This step read the Step 12Z struct_conn candidate table CSV.
It did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF.
It did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
It did not run coordinate geometry, distance calculation, UniProt/CD-HIT, NPZ reads, or training.

The smoke merged the candidate table and adapter summary by pdb_id and wrote a candidate-enriched stub CSV.
- enriched_stub_row_count: 16
- candidate_like_enriched_stub_count: 4

Each row preserves struct_conn ptnr1/ptnr2 atom identifiers and conn_type_id.
This step does not infer ligand/residue role, does not infer warhead_type, and does not claim covalent_bond_atom_pair is chemically verified.
All rows have human_review_required=true and training_ready=false.
This step did not write enriched sample_index and did not write final dataset.

Next step: `real_covalent_struct_conn_candidate_human_review_table`, used to produce a human-reviewable candidate connection table.

# Real Covalent Struct Conn Candidate Extraction Smoke v0 Summary

Step 12Z is an actual struct_conn candidate extraction smoke.

This step actually read 3 raw `.cif.gz` files and used standard library `gzip.open` for an in-memory text scan.
It only scanned the `_struct_conn` loop.
It did not network and did not re-download files.
It did not write raw/decompressed mmCIF/PDB/SDF/MOL2 outputs.
It did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
It did not run coordinate geometry, UniProt/CD-HIT, NPZ reads, adapter merge, or training.

The candidate table records struct_conn partner atom identifiers and conn_type_id.
It may record mmCIF-provided pdbx_dist_value, but it does not calculate distance.
It does not infer ligand/residue role, does not infer warhead_type, and does not claim covalent_bond_atom_pair is chemically verified.
It does not claim samples are training-ready.

## Counts
- candidate_table_row_count: 16
- total_struct_conn_row_count: 16
- total_candidate_like_struct_conn_count: 4
- processed_pdb_ids: 6DI9, 5F2E, 6OIM

Next step: `real_covalent_struct_conn_candidate_adapter_merge_smoke`, which should merge the struct_conn candidate table with the minimal adapter summary into a candidate-enriched stub.

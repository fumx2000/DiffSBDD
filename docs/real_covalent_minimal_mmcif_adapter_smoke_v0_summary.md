# Real Covalent Minimal mmCIF Adapter Smoke v0 Summary

Step 12Y is an actual minimal mmCIF adapter smoke.

This step actually read the Step 12W extracted summary CSV and mapped parser metadata into a minimal adapter summary.
It did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF.
It did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
It did not run coordinate geometry, UniProt/CD-HIT, NPZ reads, or training.

## Adapter Summary Rows
The smoke generated 3 minimal adapter summary rows:
- 6DI9
- 5F2E
- 6OIM

The adapter summary maps:
- sample_id
- pdb_id
- source_name
- source_stage
- raw_path
- entry_id
- data_block_id
- structure_title
- entity_count
- atom_site_row_count
- chem_comp_ids
- struct_conn_row_count
- covalent_connection_candidate_count
- covalent_annotation_status
- adapter_status

The smoke marks covalent_bond_atom_pair, residue/ligand atom annotation, coordinates, warhead_type, and pre/post reaction geometry as unresolved.
It does not claim samples are training-ready.
It did not write sample stub JSON and did not write enriched sample_index.

## Decision
- adapter_summary_row_count: 3
- unresolved_schema_field_count: 15
- all_unresolved_fields_set_to_unresolved: true
- all_training_ready_false: true
- ready_for_struct_conn_candidate_extraction_smoke: true
- recommended_next_step: real_covalent_struct_conn_candidate_extraction_smoke

Next step: `real_covalent_struct_conn_candidate_extraction_smoke`, which should actually extract candidate covalent linkage information from the mmCIF struct_conn loop.

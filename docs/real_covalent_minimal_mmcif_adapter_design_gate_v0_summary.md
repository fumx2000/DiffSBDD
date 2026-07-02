# Real Covalent Minimal mmCIF Adapter Design Gate v0 Summary

Step 12X is a minimal mmCIF adapter design gate.

This step does not network, does not download, does not read raw files, does not decompress, and does not parse mmCIF.
It does not run the adapter; it only defines the next adapter smoke contract.

Step 12Y may read only the Step 12W extracted summary CSV. It must not read raw `.cif.gz`, decompress raw files, or parse mmCIF.

## Metadata Mapping
Step 12Y maps parser metadata into a minimal adapter summary:
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

## Unresolved Fields
Step 12Y must mark unresolved fields and must not fabricate covalent_bond_atom_pair, residue atom annotation, ligand atom annotation, coordinates, warhead_type, or pre/post reaction geometry.

Step 12Y may only output CSV/JSON/MD adapter summary artifacts and must not claim samples are training-ready.
This is the last adapter-before-smoke design gate; the next step must actually run adapter smoke.

## Decision
- adapter_contract_row_count: 47
- adapter_input_contract_row_count: 3
- schema_mapping_row_count: 16
- not_yet_available_schema_field_row_count: 15
- adapter_policy_row_count: 13
- ready_for_minimal_mmcif_adapter_smoke: true
- recommended_next_step: real_covalent_minimal_mmcif_adapter_smoke

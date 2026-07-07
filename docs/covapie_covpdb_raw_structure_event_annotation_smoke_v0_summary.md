# CovaPIE CovPDB Raw Structure Event Annotation Smoke v0 Summary

This is a controlled first-five raw structure event annotation smoke.
It downloads only the first five allowed RCSB raw structure files from the Step 13AU contract.
It prefers mmCIF and uses PDB only as fallback if mmCIF download fails.
Raw files are stored under `data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0/` and must remain untracked.
It does not download ligand SDF, archives, validation reports, assemblies, or any non-contracted URL.
It does not copy raw files or full coordinate tables into `data/derived`.
It does not use RDKit/Bio.PDB/gemmi/gzip/torch.
It does not materialize candidate metadata or allowlists.
It does not train.

attempted_structure_count: `5`
raw_structure_download_succeeded_count: `5`
raw_structure_download_failed_count: `0`
selected_raw_formats: `{'1A3B': 'mmcif', '1A3E': 'mmcif', '1A46': 'mmcif', '1A54': 'mmcif', '1A5G': 'mmcif'}`
struct_conn_loop_found_count: `4`
atom_site_loop_found_count: `5`
pdb_link_record_found_count: `0`
pdb_conect_record_found_count: `0`
raw_resolves_preferred_event_key_count: `4`
raw_resolves_minimal_event_key_count: `0`
raw_partial_event_key_only_count: `0`
raw_no_connectivity_records_found_count: `1`
raw_multiple_candidate_links_count: `0`
raw_ligand_het_code_not_found_count: `0`
raw_protein_partner_not_found_count: `0`
raw_parse_failed_count: `0`
future_candidate_metadata_possible_count: `4`
future_automatic_allowlist_possible_count: `4`
candidate_metadata_materialized: `False`
candidate_allowlist_materialized: `False`
ready_for_covapie_covpdb_raw_structure_event_annotation_qa_gate: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_covpdb_raw_structure_event_annotation_qa_gate`
blocking_reasons: `[]`

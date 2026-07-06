# CovaPIE CovPDB Metadata-Only Acquisition Smoke v0 Summary

This is CovaPIE CovPDB metadata-only acquisition smoke.
It uses controlled urllib access to CovPDB HTML metadata pages only.
It writes the manual CovPDB metadata CSV only if real rows are parsed from the CovPDB Complexes list.
It does not download raw structures, SDF, PDB, mmCIF, ZIP, or gzip artifacts.
It does not read raw structure contents.
It does not use RDKit, Bio.PDB, gemmi, torch, tensors, checkpoints, model forward, loss, optimizer, trainer.fit, or training.
It does not materialize candidate metadata, allowlists, sample index, final dataset, split assignments, or leakage matrices.
It preserves five canonical mask tasks, including scaffold_only/B3.
It keeps feature semantics audit and leakage/split design required before formal training.

enabled_source_name: `CovPDB`
acquisition_scope: `covpdb_html_metadata_only`
network_access_used: `True`
fetched_urls: `['https://drug-discovery.vm.uni-freiburg.de/covpdb/complexes_list/initial=Allsortedby=protein_id']`
metadata_csv_written: `True`
metadata_csv_path: `data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv`
metadata_csv_row_count: `25`
metadata_csv_column_count: `19`
covpdb_metadata_only_acquisition_smoke_passed: `True`
metadata_only_acquisition_status: `covpdb_metadata_csv_written`
ready_for_covapie_external_metadata_index_download_smoke_rerun: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `rerun_covapie_external_metadata_index_download_smoke`
blocking_reasons: `[]`

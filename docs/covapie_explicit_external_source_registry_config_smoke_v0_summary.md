# CovaPIE Explicit External Source Registry Config Smoke v0 Summary

This is CovaPIE explicit external source registry config smoke.
It writes one explicit source config row for CovPDB.
It treats CovPDB as the first specialized covalent protein-ligand database source.
It uses a manual_user_supplied metadata CSV path.
It does not access the configured path.
It does not verify external URLs.
It does not use internet, network, curl, wget, requests, urllib, or browser.
It does not download metadata or raw structures.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
The configured CovPDB metadata CSV is expected to be supplied in a later step.
Future metadata index download smoke may block if the configured manual CSV is missing.
Metadata index download smoke remains metadata-only; raw structure download remains forbidden.
It preserves one row = one covalent ligand-residue event.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

source_registry_config_written: `True`
source_registry_config_row_count: `1`
enabled_source_name: `CovPDB`
enabled_source_access_method: `manual_user_supplied`
source_metadata_index_url_or_local_path: `data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv`
source_metadata_index_path_checked_current_step: `False`
source_metadata_index_file_opened: `False`
ready_for_covapie_external_metadata_index_download_smoke: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_external_metadata_index_download_smoke`
blocking_reasons: `[]`

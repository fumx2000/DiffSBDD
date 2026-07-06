# CovaPIE External Metadata Index Download Design Gate v0 Summary

This is CovaPIE external metadata index download design gate.
It designs future metadata index download from specialized covalent databases.
It does not configure a real external source in this step.
It does not verify any external database in this step.
It does not use internet, network, curl, wget, requests, urllib, or browser.
It does not download metadata or raw structures.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
Metadata index download smoke will be allowed only after external source registry configuration.
Raw structure download remains forbidden until candidate metadata and allowlist are materialized.
It preserves one row = one covalent ligand-residue event.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

metadata_index_root: `data/derived/covalent_small/external_metadata_index`
raw_structure_root: `data/raw/covalent_sources`
metadata_index_allowed_artifact_types: `['csv', 'tsv', 'json', 'jsonl']`
metadata_index_deferred_artifact_types: `['xlsx', 'html_table']`
metadata_index_forbidden_artifact_types: `['zip', 'pdb', 'mmcif', 'cif', 'sdf', 'mol2', 'gz']`
external_source_configured_current_step: `False`
external_metadata_downloaded: `False`
raw_structure_downloaded: `False`
ready_for_covapie_external_source_registry_configuration: `True`
ready_for_covapie_external_metadata_index_download_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_external_source_registry_configuration`

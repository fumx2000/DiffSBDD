# CovaPIE External Source Registry Configuration Gate v0 Summary

This is CovaPIE external source registry configuration gate.
It creates a header-only template for explicitly configuring external specialized covalent metadata sources.
It does not invent source names or URLs.
It does not configure a real external source unless explicit input CSV is present.
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
If explicit config is missing, the step is safely blocked and writes a header-only blocked config artifact.
If explicit config is valid with exactly one verified enabled source, the next step can be external metadata index download smoke.
Metadata index download smoke remains metadata-only; raw structure download remains forbidden.
It preserves one row = one covalent ligand-residue event.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

source_registry_config_template_written: `True`
source_registry_config_exists: `False`
source_registry_config_read: `False`
source_registry_config_row_count: `0`
configured_source_count: `0`
enabled_source_count: `0`
enabled_source_ready_for_download_smoke: `False`
configuration_status: `blocked_due_to_missing_explicit_source_registry_config`
ready_for_covapie_external_metadata_index_download_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `provide_explicit_external_source_registry_config`
blocking_reasons: `['missing_explicit_source_registry_config']`

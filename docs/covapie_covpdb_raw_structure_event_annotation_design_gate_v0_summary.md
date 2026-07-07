# CovaPIE CovPDB Raw Structure Event Annotation Design Gate v0 Summary

This is a design gate for a future controlled raw structure event annotation smoke.
It does not access the network.
It does not download raw structures.
It does not read raw PDB/mmCIF/SDF/gzip content.
It does not create `.pdb`, `.cif`, or `.mmcif` files.
It does not materialize candidate metadata or candidate allowlists.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or train.

The next smoke is designed to use the first five committed CovPDB metadata rows only.
Preferred raw format is mmCIF, using RCSB `{pdb_id}.cif` URLs.
PDB format is a fallback, using RCSB `{pdb_id}.pdb` URLs.
Raw files must be written only under `data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0/` and must remain untracked.

first5_pdb_ids: `['1A3B', '1A3E', '1A46', '1A54', '1A5G']`
first5_ligand_het_codes: `['T29', 'T16', '00K', 'MDC', '00L']`
preferred_raw_format: `mmcif`
fallback_raw_format: `pdb`
raw_download_executed: `False`
raw_file_created: `False`
ready_for_covapie_covpdb_raw_structure_event_annotation_smoke: `True`
ready_for_training: `False`
ready_to_train_now: `False`
feature_semantics_audit_required_before_training: `True`
leakage_split_design_required_before_training: `True`
recommended_next_step: `covapie_covpdb_raw_structure_event_annotation_smoke`
blocking_reasons: `[]`

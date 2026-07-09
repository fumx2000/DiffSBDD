# CovaPIE CYS/SG Discovery Download Manifest Gate v0 Summary

Step 14G writes a discovery-only raw structure download manifest for the Step 14E pending candidates.
PDB ID remains forbidden for event-level identity or training sample joins; it is only allowed here as a future raw evidence fetch key.
This step does not download, write raw files, parse raw files, create ready candidates, write sample manifests, write dataloader smoke, or train.

discovery_manifest_row_count: `25`
purpose: `evidence_discovery_only`
pdb_id_for_raw_evidence_discovery_allowed: `True`
pdb_id_for_event_identity_allowed: `False`
ready_for_covapie_cys_sg_discovery_download_smoke: `True`
ready_for_covapie_small_pilot_download_smoke: `False`
ready_for_training: `False`
recommended_next_step: `covapie_cys_sg_discovery_download_smoke`

Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.

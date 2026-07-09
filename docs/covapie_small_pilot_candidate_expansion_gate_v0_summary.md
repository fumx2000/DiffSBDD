# CovaPIE Small Pilot Candidate Expansion Gate v0 Summary

Step 14D expands candidates for the current `covpdb_manual_metadata_v0` / `CovPDB` source profile using only existing derived evidence.
It does not use PDB-only joins, fabricate event-level identity, auto-restore ligand topology, use the network, download files, write raw structures, read raw content, parse mmCIF, extract coordinates, write a new download manifest, write actual dataloader smoke, or train.

selected_for_manifest_rerun_count: `0`
insufficient_candidate_count_for_20_to_50_pilot: `True`
pdb_only_join_used: `False`
ready_for_covapie_small_pilot_download_manifest_rerun_gate: `False`
ready_for_covapie_small_pilot_manual_event_identity_curation_gate: `True`
ready_for_covapie_small_pilot_download_smoke: `False`
ready_for_training: `False`
recommended_next_step: `covapie_small_pilot_manual_event_identity_curation_gate`

Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.

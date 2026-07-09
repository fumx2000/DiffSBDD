# CovaPIE Small Pilot Download Manifest Gate v0 Summary

Step 14C writes source-profile-specific small pilot download manifest metadata.
It keeps `current_execution_source_specific=true` while preserving cross-source schema fields for future source registry and resolver contracts.
It does not use the network, download files, write raw structures, read raw content, parse mmCIF, extract coordinates, write actual dataloader smoke, write final datasets, write sample indexes, write split assignments, write leakage matrices, import torch or numpy, load checkpoints, run model forward, compute loss, or train.

The current profile is `covpdb_manual_metadata_v0` for `CovPDB`.
Because selected eligible event-level candidates are `0`, `ready_for_covapie_small_pilot_download_smoke` is `False`.
If fewer than 20 qualified candidates are selected, the next step is candidate expansion rather than download smoke.

current_source_profile: `covpdb_manual_metadata_v0`
current_source_database: `CovPDB`
cross_source_generalization_supported_by_schema: `True`
current_execution_source_specific: `True`
pdb_wide_blind_scan_allowed: `False`
selected_small_pilot_row_count: `0`
insufficient_candidate_count_for_20_to_50_pilot: `True`
source_profile_contract_passed: `True`
candidate_selection_audit_passed: `True`
manifest_schema_validation_audit_passed: `True`
network_boundary_audit_passed: `True`
readiness_contract_passed: `True`
safety_audit_passed: `True`
ready_for_covapie_small_pilot_download_smoke: `False`
ready_for_covapie_bulk_download_smoke: `False`
ready_for_covapie_actual_dataloader_adapter_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_small_pilot_candidate_expansion_gate`
blocking_reasons: `[]`

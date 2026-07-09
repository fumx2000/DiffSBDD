# CovaPIE Bulk Download Design Gate v0 Summary

Step 14B is a design gate for future small, medium, and bulk structure downloads.
It does not use the network, download files, write raw structures, write download manifest rows, read raw content, parse mmCIF, extract coordinates, write actual dataloader smoke, write final datasets, write sample indexes, write split assignments, write leakage matrices, import torch or numpy, load checkpoints, run model forward, compute loss, or train.

The next step is `covapie_small_pilot_download_manifest_gate`, not actual download smoke, not actual dataloader smoke, and not training.
Raw files must remain untracked and uncommitted.
The five canonical mask tasks are preserved, including `scaffold_only / B3`.
`feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false` remain unchanged.
Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.

candidate_source_contract_row_count: `10`
candidate_source_contract_passed: `True`
storage_layout_contract_row_count: `10`
storage_layout_contract_passed: `True`
download_manifest_schema_contract_row_count: `14`
download_manifest_schema_contract_passed: `True`
network_boundary_contract_row_count: `10`
network_boundary_contract_passed: `True`
pilot_scale_contract_row_count: `8`
pilot_scale_contract_passed: `True`
resume_checksum_contract_row_count: `8`
resume_checksum_contract_passed: `True`
failure_taxonomy_contract_row_count: `12`
failure_taxonomy_contract_passed: `True`
safety_audit_passed: `True`
ready_for_covapie_small_pilot_download_manifest_gate: `True`
ready_for_covapie_small_pilot_download_smoke: `False`
ready_for_covapie_bulk_download_smoke: `False`
ready_for_covapie_actual_dataloader_adapter_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_small_pilot_download_manifest_gate`
blocking_reasons: `[]`

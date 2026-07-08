# CovaPIE Metadata Dataloader Smoke v0 Summary

Step 13BU implements a minimal metadata-only Dataset-like shim under `src/covalent_ext`.
The shim reads the Step 13BR dataloader interface smoke preview and supports `__len__` plus `__getitem__`.
It returns Python dict metadata records only.
It does not inherit from torch Dataset, use torch DataLoader, import torch, create tensors, return numpy arrays, load checkpoints, call model forward, compute loss, train, or modify original DiffSBDD dataloader/model/loss code.
It does not read raw structures, parse mmCIF, download data, use RDKit/Bio.PDB/gemmi/gzip, write actual dataloader smoke, write real final dataset artifacts, write a new sample index, write split assignments, or write a leakage matrix.
It preserves the five canonical masks, including `scaffold_only / B3`.
The next step is metadata dataloader smoke QA gate, not actual dataloader smoke and not training.

metadata_dataset_len: `20`
metadata_dataloader_smoke_preview_row_count: `20`
metadata_dataloader_smoke_preview_column_count: `30`
len_getitem_audit_row_count: `20`
len_getitem_audit_passed: `True`
out_of_range_index_error_checked: `True`
key_coverage_audit_row_count: `12`
key_coverage_audit_passed: `True`
mask_distribution_audit_row_count: `5`
mask_distribution_audit_passed: `True`
blocker_runtime_audit_row_count: `12`
blocker_runtime_audit_passed: `True`
metadata_dataloader_smoke_written: `True`
actual_dataloader_smoke_written: `False`
real_dataloader_written: `False`
original_dataloader_modified: `False`
torch_imported: `False`
torch_tensor_created: `False`
checkpoint_loaded: `False`
model_forward_called: `False`
training_allowed: `False`
ready_for_covapie_metadata_dataloader_smoke_qa_gate: `True`
ready_for_covapie_actual_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_metadata_dataloader_smoke_qa_gate`
blocking_reasons: `[]`

# CovaPIE Split/Leakage Smoke v0 Summary

Step 13BK is a split/leakage smoke preview for the Step 13BH/13BI 20-row sample index and Step 13BJ design contract.
It materializes split units, parent-event grouping integrity, candidate-metadata grouping integrity, mask grouping integrity, and leakage risk smoke audits.
It does not write real train/val/test split assignments, a leakage matrix, final_dataset, a new sample_index, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
All five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
The current 20-row smoke remains too small for a real train/val/test split.
Feature semantics audit remains required before formal training, fine-tuning, or real parameter updates.
Leakage/split QA remains required before final dataset design and training.
This smoke allows split/leakage QA gate next, not feature audit, not final dataset, not dataloader smoke, and not training.

source_sample_index_row_count: `20`
source_unique_event_count: `4`
source_canonical_mask_task_count: `5`
split_unit_smoke_preview_row_count: `4`
parent_event_group_integrity_row_count: `4`
candidate_metadata_group_integrity_row_count: `4`
mask_task_grouping_integrity_row_count: `5`
split_leakage_risk_smoke_audit_row_count: `12`
split_unit_smoke_preview_passed: `True`
parent_event_group_integrity_passed: `True`
candidate_metadata_group_integrity_passed: `True`
mask_task_grouping_integrity_passed: `True`
split_leakage_risk_smoke_audit_passed: `True`
split_assignments_written: `False`
leakage_matrix_written: `False`
final_dataset_written: `False`
sample_index_written_current_step: `False`
ready_for_covapie_split_leakage_qa_gate: `True`
ready_for_covapie_feature_semantics_audit_gate: `False`
ready_for_covapie_final_dataset_design_gate: `False`
ready_for_covapie_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_split_leakage_qa_gate`
blocking_reasons: `[]`

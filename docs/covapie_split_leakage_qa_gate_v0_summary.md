# CovaPIE Split/Leakage QA Gate v0 Summary

Step 13BL is a QA gate for the Step 13BK split/leakage smoke preview.
It reads but does not rewrite the Step 13BK split unit preview CSV/JSON.
It validates split unit preview consistency, parent event grouping, candidate metadata grouping, canonical mask grouping, leakage risk status, boundary safety, git safety, and training blockers.
It does not write real split assignments, a leakage matrix, final_dataset, a new sample_index, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
All five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics audit remains required before formal training, fine-tuning, real parameter updates, or further training-prep progression.
Step 12D was smoke legality only, not final feature semantics audit.
This QA gate allows feature semantics audit gate next, not final dataset, not dataloader smoke, and not training.

source_sample_index_row_count: `20`
source_unique_event_count: `4`
source_canonical_mask_task_count: `5`
source_split_unit_preview_row_count: `4`
source_split_unit_preview_json_row_count: `4`
split_unit_preview_qa_row_count: `4`
group_integrity_qa_row_count: `8`
mask_integrity_qa_row_count: `5`
leakage_risk_qa_row_count: `12`
split_unit_preview_qa_passed: `True`
group_integrity_qa_passed: `True`
mask_integrity_qa_passed: `True`
leakage_risk_qa_passed: `True`
training_blockers_passed: `True`
split_assignments_written: `False`
leakage_matrix_written: `False`
final_dataset_written: `False`
sample_index_written_current_step: `False`
split_unit_preview_written_current_step: `False`
ready_for_covapie_feature_semantics_audit_gate: `True`
ready_for_covapie_final_dataset_design_gate: `False`
ready_for_covapie_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_feature_semantics_audit_gate`
blocking_reasons: `[]`

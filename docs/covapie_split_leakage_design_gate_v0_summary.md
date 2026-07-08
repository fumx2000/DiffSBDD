# CovaPIE Split/Leakage Design Gate v0 Summary

Step 13BJ is a split/leakage design gate for the Step 13BH/13BI 20-row sample index smoke.
It designs future split grouping keys, leakage rules, leakage risk classes, split unit preview, and the next split/leakage smoke plan.
It does not write split assignments, a leakage matrix, final_dataset, a new sample_index, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
All five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
The 20-row smoke is too small for a real train/val/test split, so this step only designs the policy.
Feature semantics audit remains required before formal training, fine-tuning, or real parameter updates.
Leakage/split gates remain required before final dataset design and training.
This gate allows split/leakage smoke next, not split QA, not final dataset, not dataloader smoke, and not training.

source_sample_index_row_count: `20`
source_unique_event_count: `4`
source_canonical_mask_task_count: `5`
split_grouping_key_contract_row_count: `13`
leakage_rule_contract_row_count: `15`
leakage_risk_design_audit_row_count: `12`
split_unit_design_preview_row_count: `4`
split_leakage_smoke_plan_row_count: `11`
split_assignments_written: `False`
leakage_matrix_written: `False`
final_dataset_written: `False`
sample_index_written_current_step: `False`
ready_for_covapie_split_leakage_smoke: `True`
ready_for_covapie_split_leakage_qa_gate: `False`
ready_for_covapie_final_dataset_design_gate: `False`
ready_for_covapie_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_split_leakage_smoke`
blocking_reasons: `[]`

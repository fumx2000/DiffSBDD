# CovaPIE Sample Index Smoke v0 Summary

Step 13BH writes the minimal CovaPIE sample index smoke artifacts.
It materializes only CSV/JSON smoke rows: 4 extracted covalent events expanded across 5 canonical mask tasks for 20 rows.
It reads Step 13BG design contracts, Step 13BF QA artifacts, and Step 13BE extracted derived tables.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, download data, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
It does not write final_dataset, split assignments, leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This step allows sample index QA gate next, not split/leakage design, not final dataset, and not training.

sample_index_row_count: `20`
sample_index_column_count: `31`
sample_index_json_row_count: `20`
unique_event_count: `4`
canonical_mask_task_count: `5`
planned_sample_count: `20`
observed_sample_count: `20`
sample_id_unique_count: `20`
b3_scaffold_only_included: `True`
no_extra_mask_tasks_added: `True`
row_qa_passed: `True`
mask_distribution_qa_passed: `True`
source_traceability_qa_passed: `True`
boundary_safety_passed: `True`
git_safety_passed: `True`
training_blockers_passed: `True`
ready_for_covapie_sample_index_qa_gate: `True`
ready_for_covapie_split_leakage_design_gate: `False`
ready_for_covapie_final_dataset_design_gate: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_sample_index_qa_gate`
blocking_reasons: `[]`

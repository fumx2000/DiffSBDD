# CovaPIE Sample Index QA Gate v0 Summary

Step 13BI is a QA gate for the Step 13BH 20-row sample index smoke.
It reads but does not modify the Step 13BH sample index CSV/JSON.
It validates schema order, CSV/JSON consistency, sample identity, mask distribution, source traceability, boundary safety, git safety, and training blockers.
It does not write a new sample index, final_dataset, split assignments, leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows split/leakage design gate next, not final dataset, not dataloader smoke, and not training.

source_sample_index_row_count: `20`
source_sample_index_column_count: `31`
source_sample_index_json_row_count: `20`
source_unique_event_count: `4`
source_sample_id_unique_count: `20`
source_canonical_mask_task_count: `5`
schema_csv_json_qa_passed: `True`
row_identity_qa_passed: `True`
mask_distribution_qa_passed: `True`
source_traceability_qa_passed: `True`
boundary_safety_passed: `True`
git_safety_passed: `True`
training_blockers_passed: `True`
sample_index_written_current_step: `False`
ready_for_covapie_split_leakage_design_gate: `True`
ready_for_covapie_final_dataset_design_gate: `False`
ready_for_covapie_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_split_leakage_design_gate`
blocking_reasons: `[]`

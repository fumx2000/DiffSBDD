# CovaPIE Sample Index Design Gate v0 Summary

Step 13BG is a design gate for a future sample index smoke step.
It reads only Step 13BF/13BE derived CSV and JSON artifacts and designs source artifact references, a 31-field sample index schema, and a 4 events x 5 mask task expansion contract.
It does not write `sample_index.csv`, `sample_index.json`, final_dataset, split assignments, leakage matrix, tensors, or training inputs.
It does not read raw CIF files, parse mmCIF, extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics audit, scaffold/linker/warhead annotation, auxiliary labels, and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows sample index smoke next, not sample index QA, not split/leakage design, and not training.

future_sample_index_schema_field_count: `31`
future_mask_task_expansion_row_count: `20`
future_unique_event_count: `4`
future_mask_task_count: `5`
future_planned_sample_count: `20`
sample_index_materialized_current_step: `False`
sample_index_written: `False`
ready_for_covapie_sample_index_smoke: `True`
ready_for_covapie_sample_index_qa_gate: `False`
ready_for_covapie_split_leakage_design_gate: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_sample_index_smoke`
blocking_reasons: `[]`

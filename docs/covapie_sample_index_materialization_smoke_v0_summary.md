# CovaPIE Sample Index Materialization Smoke v0 Summary

Step 14AD materializes a three-row `sample_index.csv` and matching `sample_index.json` from Step 14AC's validated design contracts and Step 14AA's committed derived atom/event tables. This is a structured index of prepared source artifacts, not a final dataset or training dataset.

The step does not read raw mmCIF, parse raw `struct_conn` or `atom_site`, access a network, modify source atom/event tables, create final-dataset, split, leakage, dataloader, tensor, checkpoint, or training artifacts, or modify DiffSBDD source code.

The five canonical masks remain unchanged, including `scaffold_only / B3`. Feature semantics are not known or finalized for training. A feature-semantics audit and leakage/split design gate remain required before formal training, fine-tuning, or real parameter updates.

- sample_index_row_count: `3`
- sample_index_schema_field_count: `33`
- schema_validation_passed_count: `33`
- row_traceability_passed_count: `3`
- materialization_issue_count: `0`
- ready_for_covapie_sample_index_qa_gate: `True`
- ready_for_training: `False`
- recommended_next_step: `covapie_sample_index_qa_gate`

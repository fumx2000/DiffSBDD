# CovaPIE Sample Index Design Gate v0 Summary

Step 14AC is a design gate for a future sample index materialization smoke.
It reads only Step 14AB QA-passed derived outputs and Step 14AA derived sample-preparation outputs.
It defines the source inventory, 33-field sample-index schema contract, field mapping, per-sample materialization plan, policy, safety, and downstream readiness contracts.

This step does not write `sample_index.csv` or `sample_index.json`.
It does not create a final dataset, split assignments, leakage matrix, dataloader smoke, tensors, checkpoints, or training artifacts.
It does not read raw mmCIF, parse raw `struct_conn` or `atom_site`, modify atom/event tables, use network, RDKit, Bio.PDB, gemmi, torch, model forward, loss, backward, optimizer, trainer.fit, or training.

The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics remain unknown for formal training, `UNKNOWN_ATOM_FEATURE_POLICY` remains not finalized for training, and feature-semantics audit plus leakage/split design remain required before formal training, fine-tuning, or real parameter updates.

sample_index_source_inventory_count: `3`
sample_index_schema_field_count: `33`
sample_index_field_mapping_count: `33`
sample_index_materialization_plan_count: `3`
eligible_for_sample_index_materialization_count: `3`
sample_index_written_current_step: `False`
ready_for_covapie_sample_index_materialization_smoke: `True`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_sample_index_materialization_smoke`
blocking_reasons: `[]`

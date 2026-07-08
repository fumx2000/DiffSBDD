# CovaPIE Final Dataset Smoke v0 Summary

Step 13BO materializes a CSV/JSON final dataset smoke preview only.
It writes `covapie_final_dataset_smoke_preview.csv` and `covapie_final_dataset_smoke_preview.json` using the Step 13BN schema and row lineage contracts.
It does not write real `final_dataset.csv/json`, generic `final_dataset_smoke.csv/json`, a new sample index, split assignments, a leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
It reads only derived Step 13BN/13BM/13BK/13BH/13BE CSV/JSON artifacts.
It does not read raw CIF/mmCIF/SDF/PDB/gzip, parse atom_site/struct_conn, extract coordinates, access network, download data, run RDKit, Bio.PDB, gemmi, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics and leakage/split blockers remain preserved before formal training, fine-tuning, or real parameter updates.
This smoke step allows final dataset QA gate next, not dataloader smoke and not training.

final_dataset_smoke_preview_row_count: `20`
final_dataset_smoke_preview_column_count: `45`
final_dataset_smoke_preview_json_row_count: `20`
schema_order_smoke_audit_passed: `True`
row_lineage_smoke_audit_row_count: `20`
row_lineage_smoke_audit_passed: `True`
mask_distribution_smoke_audit_row_count: `5`
mask_distribution_smoke_audit_passed: `True`
feature_blocker_smoke_audit_row_count: `13`
feature_blocker_smoke_audit_passed: `True`
real_final_dataset_written: `False`
generic_final_dataset_written: `False`
sample_index_written_current_step: `False`
split_assignments_written: `False`
leakage_matrix_written: `False`
dataloader_smoke_written: `False`
training_artifacts_written: `False`
feature_semantics_known_for_training: `False`
unknown_atom_feature_policy_finalized_for_training: `False`
ready_for_covapie_final_dataset_qa_gate: `True`
ready_for_covapie_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_final_dataset_qa_gate`
blocking_reasons: `[]`

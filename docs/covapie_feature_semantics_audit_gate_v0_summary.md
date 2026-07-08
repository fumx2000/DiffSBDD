# CovaPIE Feature Semantics Audit Gate v0 Summary

Step 13BM is a feature semantics audit gate after the split/leakage QA gate.
It reads derived CSV/JSON artifacts and static source text only.
It records current feature semantics for sample identity, event identity, ligand/protein atom sources, coordinates, canonical masks, conditioning, auxiliary labels, training blockers, and git safety.
It does not write final_dataset, a new sample_index, split assignments, a leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF/mmCIF/SDF/PDB/gzip, parse atom_site/struct_conn, run RDKit, Bio.PDB, gemmi, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
All five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Step 12D remains recorded as smoke legality only, not final feature semantics audit.
This gate allows CovaPIE final dataset design gate next, not final dataset smoke, dataloader smoke, or training.
Feature semantics are audited at the current contract level, but `feature_semantics_known_for_training` remains false and training remains blocked.

source_sample_index_row_count: `20`
source_unique_event_count: `4`
source_canonical_mask_task_count: `5`
feature_source_inventory_audit_row_count: `10`
feature_semantics_contract_row_count: `31`
coordinate_geometry_semantics_audit_row_count: `10`
mask_conditioning_semantics_audit_row_count: `8`
auxiliary_label_semantics_audit_row_count: `10`
feature_semantics_training_blocker_row_count: `13`
feature_semantics_audit_completed_current_step: `True`
feature_semantics_known_for_training: `False`
unknown_atom_feature_policy_finalized_for_training: `False`
final_dataset_written: `False`
sample_index_written_current_step: `False`
split_assignments_written: `False`
leakage_matrix_written: `False`
dataloader_smoke_written: `False`
training_artifacts_written: `False`
ready_for_covapie_final_dataset_design_gate: `True`
ready_for_covapie_final_dataset_smoke: `False`
ready_for_covapie_dataloader_smoke: `False`
ready_for_training: `False`
ready_to_train_now: `False`
recommended_next_step: `covapie_final_dataset_design_gate`
blocking_reasons: `[]`

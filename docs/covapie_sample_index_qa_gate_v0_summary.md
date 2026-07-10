# CovaPIE Sample Index QA Gate v0 Summary

Step 14AE independently rereads the committed Step 14AD sample index CSV/JSON and source derived tables. It recomputes semantic consistency, actual source row counts, event and bond-distance traceability, and SHA256 fingerprints without modifying the sample index.

QA approval permits the next final-dataset design gate only. It does not rewrite the source `eligible_for_final_dataset_design=false` field and does not make any sample training-ready. No raw structure data, final dataset, split, leakage matrix, dataloader output, tensor, checkpoint, or training artifact is created.

The five canonical masks remain unchanged, including `scaffold_only / B3`. Feature semantics remain unknown and not finalized for training; feature-semantics audit and leakage/split design remain required before formal training.

- sample_index_row_qa_passed_count: `3`
- sample_index_schema_qa_passed_count: `33`
- sample_index_source_traceability_qa_passed_count: `3`
- sample_index_fingerprint_verified_count: `2`
- qa_approved_for_final_dataset_design_count: `3`
- ready_for_covapie_final_dataset_design_gate: `True`
- ready_for_training: `False`
- recommended_next_step: `covapie_final_dataset_design_gate`

# CovaPIE CYS/SG Targeted Annotation Acquisition Smoke v0 Summary

Step 14L performs a controlled metadata-only annotation acquisition smoke from CovPDB ligand/complex pages and the RCSB Chemical Component Dictionary. It does not download raw coordinate files, read raw CIF content, write raw files, save HTML, create ready candidates, create sample/final/split/leakage artifacts, instantiate dataloaders, or train.

input_seed_candidate_count: `9`
input_acquisition_manifest_row_count: `29`
ligand_card_fetch_success_count: `8`
complex_card_resolved_count: `9`
complex_card_event_annotation_acquired_count: `9`
rcsb_ccd_fetch_success_count: `8`
acquired_annotation_candidate_count: `9`
ready_candidate_count_current_step: `0`
ready_for_training: `False`
recommended_next_step: `covapie_cys_sg_targeted_metadata_expansion_next_batch_gate`

All acquired annotation candidates remain pending manual review and are not event identities until review. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.

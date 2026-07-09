# CovaPIE CYS/SG Targeted Metadata Next Batch Acquisition Smoke v0 Summary

Step 14N performs a controlled metadata-only next-batch acquisition smoke from CovPDB HTML annotation pages and RCSB CCD metadata. It excludes the existing nine Step 14L acquired annotation candidates, writes only derived CSV/JSON/MD metadata artifacts, and does not save raw coordinates, HTML files, candidate-ready labels, sample indexes, final datasets, split/leakage artifacts, dataloader artifacts, checkpoints, tensors, or training outputs.

CovPDB optional ligand/protein name fields are cleaned when page navigation boilerplate is detected. The RCSB CCD `ccd_ligand_name` field remains the reliable ligand chemical name source in this smoke.

existing_candidate_count: `9`
total_candidate_target: `20`
additional_candidate_needed_before_step: `11`
complex_card_fetch_attempt_count: `40`
complex_card_fetch_success_count: `40`
complex_card_cys_event_annotation_count: `25`
new_candidate_count: `16`
combined_candidate_count: `25`
additional_candidate_needed_after_step: `0`
ready_candidate_count_current_step: `0`
ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate: `True`
ready_for_training: `False`
recommended_next_step: `covapie_cys_sg_acquired_annotation_manual_review_gate`

All next-batch acquired annotation candidates remain pending manual review and are not event identities until review. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.

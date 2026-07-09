# CovaPIE Manual Event Identity Support Evidence Acquisition Gate v0 Summary

Step 14F reads existing local CIF/mmCIF evidence, if present, to propose event-level identity support for the Step 14E pending manual curation template.
It does not modify the template, mark proposals ready, use PDB-only joins, download files, write raw structures, write a download manifest, write actual dataloader smoke, or train.

template_candidate_count: `25`
local_raw_available_count: `5`
local_raw_read_count: `5`
struct_conn_rows_detected_count: `47`
cys_sg_struct_conn_candidate_count: `0`
support_proposal_count: `0`
support_proposals_all_pending_manual_review: `True`
ready_candidate_count_current_step: `0`
ready_for_covapie_manual_event_identity_support_review_gate: `True`
ready_for_covapie_small_pilot_manual_event_identity_validation_gate: `False`
ready_for_training: `False`
recommended_next_step: `covapie_manual_event_identity_support_review_gate`

Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.

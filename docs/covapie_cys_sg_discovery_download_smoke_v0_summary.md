# CovaPIE CYS/SG Discovery Download Smoke v0 Summary

Step 14H downloads raw CIF files only for CYS/SG evidence discovery and parses `_struct_conn` with the Python standard library.
PDB IDs are used only as raw evidence fetch keys, never as event identity. Proposals remain pending manual review and no ready candidates, sample manifest, dataloader artifact, or training artifact is created.

download_success_count: `25`
download_failure_count: `0`
struct_conn_rows_detected_count: `163`
cys_sg_struct_conn_candidate_count: `86`
support_proposal_count: `86`
ready_for_covapie_cys_sg_discovery_support_review_gate: `True`
ready_for_covapie_cys_sg_targeted_metadata_expansion_gate: `False`
ready_for_training: `False`
recommended_next_step: `covapie_cys_sg_discovery_support_review_gate`

Raw CIF files are intentionally left untracked and uncommitted. Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
